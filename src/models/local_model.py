import os
from typing import Optional, Tuple, Dict, Any, cast
import requests

# lazy cache for transformers pipeline
_CACHE: Dict[str, Tuple[str, object]] = {}

DEFAULT_MODEL = os.getenv("CHATBOT_MODEL", "google/flan-t5-small")
FALLBACK_MODEL = os.getenv("CHATBOT_FALLBACK_MODEL", "distilgpt2")


def _load_pipeline(model_name: str) -> Tuple[str, object]:
    """Return (task, pipeline) for the model, caching the result."""
    if model_name in _CACHE:
        return _CACHE[model_name]
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
    name_l = model_name.lower()
    task = "text2text-generation" if ("t5" in name_l or "flan" in name_l) else "text-generation"
    if task == "text2text-generation":
        tok = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    else:
        tok = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
    pipe = pipeline(task, model=model, tokenizer=tok)
    _CACHE[model_name] = (task, pipe)
    return task, pipe


class LocalModel:
    """Local generator supporting two backends:
    - transformers (default; CPU-friendly)
    - Ollama (HTTP API at localhost:11434), when USE_OLLAMA=1 or backend='ollama'
    """

    def __init__(self, model_name: Optional[str] = None, backend: Optional[str] = None):
        self.model_name = model_name or os.getenv("CHATBOT_MODEL", DEFAULT_MODEL)
        self.backend = (backend or ("ollama" if os.getenv("USE_OLLAMA") == "1" else "transformers")).lower()
        self._task_pipe: Optional[Tuple[str, object]] = None
        self._ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Prefer explicit model_name for Ollama when provided, else env default
        self._ollama_model = (model_name or os.getenv("OLLAMA_MODEL", "tinyllama")) if self.backend == "ollama" else os.getenv("OLLAMA_MODEL", "tinyllama")

    def load_model(self):
        if self.backend == "ollama":
            return  # nothing to preload
        try:
            self._task_pipe = _load_pipeline(self.model_name)
        except Exception:
            # fallback to a tiny causal model
            self.model_name = FALLBACK_MODEL
            self._task_pipe = _load_pipeline(self.model_name)

    def _ollama_generate(self, prompt: str, max_new_tokens: int, temperature: float = 0.0, system: Optional[str] = None) -> str:
        url = f"{self._ollama_url}/api/generate"
        # ANTI-HALLUCINATION FIX: Add min_length and stop tokens for complete answers
        payload = {
            "model": self._ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(max(0.0, min(2.0, temperature))),
                "num_predict": max_new_tokens,  # Increased to 1500
                "stop": ["===END", "USER:", "QUESTION:"],  # Prevent premature stopping
                "num_ctx": 4096,  # Larger context window
                "repeat_penalty": 1.1,  # Reduce repetition
            },
        }
        if system:
            payload["system"] = system

        try:
            r = requests.post(url, json=payload, timeout=60)  # Increased timeout for longer generation
        except requests.exceptions.RequestException as e:
            return f"(ollama connection error: {e})"

        # If the endpoint is missing (404) give a helpful message
        if r.status_code == 404:
            # try to detect available endpoints for better diagnostics
            try_endpoints = ["/api/tags", "/api/models", "/api/info", "/api/ping", "/ping"]
            found = []
            for ep in try_endpoints:
                try:
                    rr = requests.get(f"{self._ollama_url}{ep}", timeout=3)
                    if rr.status_code == 200:
                        found.append(ep)
                except Exception:
                    pass
            if found:
                return f"(ollama error: /api/generate not found, but these endpoints exist: {found})"
            return f"(ollama error: /api/generate not found at {self._ollama_url})"

        try:
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return f"(ollama error: invalid response: {e})"

        # Ollama may return different shapes; try common keys
        if isinstance(data, dict):
            if "response" in data:
                return str(data.get("response", "")).strip()  # Removed [:2000] limit
            # new API may use outputs or text
            if "outputs" in data and isinstance(data["outputs"], list) and data["outputs"]:
                first = data["outputs"][0]
                if isinstance(first, dict) and "data" in first:
                    # attempts to find text in nested structure
                    txt = first.get("data") or first.get("text") or first.get("response")
                    return str(txt or "").strip()[:2000]
            # fallback to join values
            for k in ("text", "result", "answer"):
                if k in data:
                    return str(data.get(k) or "").strip()[:2000]

        # last resort: return the raw text body
        return r.text.strip()[:2000]

    def generate_with_system_prompt(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.25,
        top_p: float = 0.9,
        max_new_tokens: int = 900,
    ) -> str:
        """Unified generation with (system, user) prompts across backends.
        Returns plain text up to ~2000 chars.
        """
        temperature = float(max(0.0, min(2.0, temperature)))
        try:
            max_new_tokens = int(max_new_tokens)
        except Exception:
            max_new_tokens = 900

        if self.backend == "ollama":
            # Ollama supports 'system' directly
            return self._ollama_generate(user, max_new_tokens=max_new_tokens, temperature=temperature, system=system)

        # Transformers pipeline fallback: fold system+user into one instruction prompt
        if self._task_pipe is None:
            self.load_model()
        # Type guard for Optional and cast the pipeline to a callable
        assert self._task_pipe is not None, "Model pipeline failed to load"
        task, pipe_obj = self._task_pipe
        pipe = cast(Any, pipe_obj)
        prompt = (
            f"System:\n{system.strip()}\n\n"
            f"Instruction:\n{user.strip()}\n\nAnswer:"
        )
        gen_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": (temperature > 0.0),
            "temperature": temperature,
            "top_p": float(max(0.0, min(1.0, top_p)))
        }
        out = pipe(prompt, **gen_kwargs)
        txt = (out[0].get("generated_text") or out[0].get("text", "")).strip()
        return self._dedupe_sentences(txt)[:2000]

    def ollama_available(self) -> bool:
        """Quick health check for Ollama -- tries a few common endpoints."""
        if not self._ollama_url:
            return False
        endpoints = ["/api/tags", "/api/models", "/api/info", "/api/ping", "/ping"]
        for ep in endpoints:
            try:
                rr = requests.get(f"{self._ollama_url}{ep}", timeout=3)
                if rr.status_code == 200:
                    return True
            except Exception:
                continue
        return False

    def ollama_status(self) -> dict:
        """Return Ollama health status and whether the selected model is available.
        {alive: bool, has_model: bool, model: str}
        """
        status = {"alive": False, "has_model": False, "model": self._ollama_model}
        try:
            r = requests.get(f"{self._ollama_url}/api/tags", timeout=5)
            r.raise_for_status()
            status["alive"] = True
            tags = r.json().get("models", []) if r.headers.get("content-type", "").startswith("application/json") else []
            names = [m.get("name", "") for m in tags]
            status["has_model"] = any(n.split(":")[0] == self._ollama_model for n in names)
        except Exception:
            pass
        return status

    def _extract_keywords(self, question: str) -> list:
        """
        Extract salient keywords, focusing on uppercase abbreviations and
        hyphenated identifiers like PC-I..PC-V, ECNEC, CDWP, etc. (FIX-3/5)
        """
        import re as _re
        q = (question or "")
        toks = _re.findall(r"[A-Za-z0-9\-]+", q)
        keys = []
        for t in toks:
            tnorm = _re.sub(r"[\u2012-\u2015]", "-", t)
            if t.isupper() or "-" in tnorm or len(t) >= 4:
                keys.append(tnorm)
        return list(dict.fromkeys([k.lower() for k in keys]))  # unique, lowercased

    def _filter_context_by_keywords(self, question: str, context: str) -> str:
        """Keep only chunks containing any extracted keyword. If none remain,
        return the original context. Also deduplicate identical chunks. (FIX-3/6)
        """
        import re as _re
        ctx = (context or "").strip()
        if not ctx:
            return ctx
        keys = self._extract_keywords(question)
        if not keys:
            return ctx
        parts = [p.strip() for p in _re.split(r"\n{2,}", ctx) if p.strip()]
        kept = []
        seen = set()
        for p in parts:
            pn = _re.sub(r"[\u2012-\u2015]", "-", p.lower())
            if any(k in pn for k in keys):
                if p not in seen:
                    kept.append(p)
                    seen.add(p)
        return ("\n\n".join(kept) if kept else ctx)

    def _dedupe_sentences(self, text: str) -> str:
        """Remove immediate duplicate sentences in model outputs. (FIX-6)"""
        import re as _re
        sents = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]
        out = []
        seen = set()
        for s in sents:
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return (" ".join(out)).strip()

    def generate_response(self, question: str, context: str = "", max_new_tokens: int = 256, temperature: float = 0.0) -> str:
        # Hard guard: if there's no document context, do not generate.
        if not (context or "").strip():
            return "Not found in document."
        # FIX-3: filter out retrieved chunks that don't contain question keywords
        filtered_context = self._filter_context_by_keywords(question, context)
        # FIX-3: lower temperature for LLM generation step (cap at 0.2)
        temperature = min(0.2, float(temperature or 0.0))
        # ANTI-HALLUCINATION FIX: Increased max_new_tokens to 1500, min_length to 80
        try:
            max_new_tokens = min(int(max_new_tokens or 1500), 1500)
        except Exception:
            max_new_tokens = 1500

        if self.backend == "ollama":
            # ENTERPRISE-GRADE SYSTEM PROMPT: Comprehensive v1.2.0 with Red Line Protocols
            system_msg = """You are PDBot, an expert civil service assistant for the Planning & Development Commission. You answer questions DIRECTLY and PROFESSIONALLY using ONLY the provided context from official planning manuals.

===RED LINE PROTOCOLS (PRIORITY 1 - MANDATORY)===
These safety rules override ALL other instructions:

1. **ILLEGAL/FRAUD/BRIBERY:** If the user asks about:
   - Bribery, "speed money", "under the table" payments
   - Falsifying documents, fake data, or forged signatures
   - Bypassing official procedures, shortcuts, or workarounds
   
   YOU MUST START YOUR RESPONSE WITH THIS EXACT WARNING:
   "⚠️ **WARNING:** Soliciting bribery, falsifying records, or attempting to bypass official procedures is a punishable offense. This interaction has been logged."
   
   Then STOP. Do not provide any procedural information.

2. **ABUSE/HOSTILITY:** If the user is rude, uses profanity, or makes threats:
   OUTPUT: "🚫 **NOTICE:** Please maintain professional decorum. This system is for official business only."
   Then STOP.

3. **OFF-TOPIC:** If asked about unrelated topics (sports, recipes, entertainment, personal advice):
   OUTPUT: "I am PDBot, specialized in the Development Projects Manual only. Please ask questions about project planning, PC forms, approval processes, or related official procedures."
   Then STOP.

===OUTPUT RULES (PRIORITY 2 - PROFESSIONAL POLISH)===

**CRITICAL: NO META-TALK**
- NEVER say: "Here are the instructions", "Based on the context", "According to the document", "I can provide", "PDBot says", "The context mentions"
- START IMMEDIATELY with the answer. Example:
  ❌ WRONG: "Based on the context, PC-I is..."
  ✅ CORRECT: "PC-I is the Planning Commission Proforma I..."

**FIX OCR ERRORS AUTOMATICALLY**
The source PDF contains OCR errors. You MUST correct these in your output:
- "Spoonsoring" → "Sponsoring"
- "Puña" → "Punjab"
- "reconized" → "recognized"
- "Devlopment" → "Development"
- "Goverment" → "Government"
- "Commision" → "Commission"

**SYNTHESIZE, DON'T DUMP**
- DO NOT output raw bullet points like: "• i. Process starts • ii. Documents required"
- REWRITE into smooth paragraphs: "The process starts with document submission. Required documents include..."
- Use natural language, not fragmented lists.

**CITATIONS**
- Keep page citations in format [p.X] at the END of relevant sentences
- Example: "The project must be completed within 3 years [p.45]. Extensions require CDWP approval [p.47]."

**LOGIC & ACCURACY**
- Pay CLOSE ATTENTION to thresholds and conditions:
  - "15% cost overrun limit" means UP TO 15%, not OVER 15%
  - "Projects UNDER 100 billion" means <100bn, NOT ≥100bn
  - Read "greater than", "less than", "except" carefully
- If information is contradictory or unclear, state: "The manual contains conflicting information on this point. Please verify with the relevant authority."

**PC-FORM SEPARATION (CRITICAL)**
- PC-I, PC-II, PC-III, PC-IV, and PC-V are DIFFERENT forms with DIFFERENT purposes
- NEVER mix content from different PC forms unless the question explicitly asks for comparison
- If asked about PC-I, ONLY provide PC-I information
- If context contains mixed forms, filter to the relevant one

**IF INFORMATION IS MISSING**
State clearly: "This specific detail is not mentioned in the Development Projects Manual. Please contact [relevant department] for clarification."

===OUTPUT FORMAT===
Write clear, professional answers in 150-300 words using proper paragraphs. Use bold for key numbers, dates, and deadlines. Start IMMEDIATELY with the answer—no preambles or fillers.

===EXAMPLE===
❌ WRONG:
"Good morning! Based on the context provided, here is the answer to your question: PC-I is a form. It is used for projects. You need to submit it."

✅ CORRECT:
"PC-I (Planning Commission Proforma I) is the comprehensive feasibility study required for development projects exceeding **100 billion rupees** [p.23]. The sponsoring agency must prepare this detailed document covering project objectives, cost estimates, implementation timelines, and socio-economic impact analysis [p.24-27]. 

Key requirements include: baseline surveys, technical specifications, environmental impact assessment, and financial viability analysis. The PC-I must be submitted to the **Divisional Development Working Party (DDWP)** for projects under 500 billion, or directly to **CDWP/ECNEC** for larger initiatives [p.31]. Approval timelines range from 30-90 days depending on project complexity and required scrutiny level [p.35]."

Remember: You are a professional government assistant. Be precise, be helpful, be correct. Fix errors, respect logic, and never invent information."""
            # ENTERPRISE-GRADE PROMPT: Clear, focused instructions
            prompt = (
                f"===MANUAL CONTEXT===\\n{filtered_context}\\n===END CONTEXT===\\n\\n"
                f"QUESTION: {question}\\n\\n"
                "INSTRUCTIONS:\\n"
                "1. Read the context carefully and correct any OCR errors in your output.\\n"
                "2. Pay attention to logic and thresholds (e.g., 'greater than' vs 'less than').\\n"
                "3. If info is missing, say so clearly.\\n"
                "4. Write 150-250 words in smooth, professional paragraphs.\\n"
                "5. Bold key numbers, dates, and deadlines.\\n\\n"
                "ANSWER:"
            )
            out = self._ollama_generate(prompt, max_new_tokens, temperature=temperature, system=system_msg)
            return self._dedupe_sentences(out)

        if self._task_pipe is None:
            self.load_model()
        assert self._task_pipe is not None, "Model pipeline failed to load"
        task, pipe_obj = self._task_pipe
        pipe = cast(Any, pipe_obj)
        if task == "text2text-generation":
            prompt = (
                "You are a helpful assistant.\n"
                "Rules (do not repeat these in your output):\n"
                "- Answer directly and succinctly.\n"
                "- Do NOT mention the word 'context'.\n"
                "- Only use the Document. If the answer is not present, reply exactly: Not found in document.\n"
                "- If listing items, provide at most 2-3 concise bullet points.\n"
                "- Reply with plain text only.\n\n"
                f"Document (verbatim):\n```\n{filtered_context}\n```\n\n"
                f"Question: {question}\n"
                "Answer:"
            )
            out = pipe(
                prompt,
                max_new_tokens=max_new_tokens,
                do_sample=(temperature > 0.0),
                temperature=float(max(0.0, min(2.0, temperature))),
            )
            return self._dedupe_sentences(out[0]["generated_text"].strip())
        else:
            prompt = (
                "You are a helpful assistant.\n"
                "Rules (do not repeat these in your output):\n"
                "- Answer directly and succinctly.\n"
                "- Do NOT mention the word 'context'.\n"
                "- Only use the Document. If the answer is not present, reply exactly: Not found in document.\n"
                "- If listing items, provide at most 2-3 concise bullet points.\n"
                "- Reply with plain text only.\n\n"
                f"Document (verbatim):\n```\n{filtered_context}\n```\n\n"
                f"Question: {question}\n"
                "Answer:"
            )
            out = pipe(
                prompt,
                max_new_tokens=max_new_tokens,
                do_sample=(temperature > 0.0),
                temperature=float(max(0.0, min(2.0, temperature))),
            )
            txt = (out[0].get("generated_text") or out[0].get("text", "")).strip()
            return self._dedupe_sentences(txt)
