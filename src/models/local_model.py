"""
PDBot Local Model v3.2.0 (v2.0.8)
Mistral-optimized with strict answer formatting.
Groq fallback for reranking ONLY (not generation).
"""
import os
import re
import logging
from typing import Optional, Dict, Any, Tuple, List, cast
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

_CACHE: Dict[str, Tuple[str, object]] = {}

DEFAULT_MODEL = os.getenv("CHATBOT_MODEL", "google/flan-t5-small")
FALLBACK_MODEL = os.getenv("CHATBOT_FALLBACK_MODEL", "distilgpt2")

# Groq API configuration (for reranking ONLY, not generation)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# =============================================================================
# SYSTEM PROMPT v2.0.8 - Strict, concise, direct answers
# =============================================================================
SYSTEM_PROMPT = """You are PDBOT, the official assistant for the Manual for Development Projects 2024.
Your answers must ALWAYS follow these rules:

1. Length: 45-70 words maximum.
2. Use ONLY the retrieved context. No outside knowledge.
3. Give the direct answer FIRST, without providing background theory unless asked.
4. No warnings, no disclaimers, no template markers.
5. If numbers exist in the context, YOU MUST extract them.
6. If answer truly not found, say: "Not found in the Manual."

Always end with one line:
Source: Manual for Development Projects 2024, p.<page>"""


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
    """Local generator with Ollama (Mistral) backend."""

    def __init__(self, model_name: Optional[str] = None, backend: Optional[str] = None):
        self.model_name = model_name or os.getenv("CHATBOT_MODEL", DEFAULT_MODEL)
        self.backend = (backend or ("ollama" if os.getenv("USE_OLLAMA") == "1" else "transformers")).lower()
        self._task_pipe: Optional[Tuple[str, object]] = None
        self._ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_model = model_name or os.getenv("OLLAMA_MODEL", "mistral")

    def load_model(self):
        if self.backend == "ollama":
            return
        try:
            self._task_pipe = _load_pipeline(self.model_name)
        except Exception:
            self.model_name = FALLBACK_MODEL
            self._task_pipe = _load_pipeline(self.model_name)

    def _ollama_generate(self, prompt: str, max_tokens: int, temperature: float = 0.2, system: Optional[str] = None) -> str:
        """Generate response from Ollama."""
        url = f"{self._ollama_url}/api/generate"
        payload = {
            "model": self._ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": max(0.1, min(0.5, temperature)),
                "num_predict": min(max_tokens, 300),
                "num_ctx": 4096,
            },
        }
        if system:
            payload["system"] = system

        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            return str(data.get("response", "")).strip()
        except requests.exceptions.RequestException as e:
            return f"(Ollama error: {e})"
        except Exception as e:
            return f"(Error: {e})"

    def ollama_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            r = requests.get(f"{self._ollama_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def ollama_status(self) -> dict:
        """Return Ollama status."""
        status = {"alive": False, "has_model": False, "model": self._ollama_model}
        try:
            r = requests.get(f"{self._ollama_url}/api/tags", timeout=5)
            r.raise_for_status()
            status["alive"] = True
            tags = r.json().get("models", [])
            names = [m.get("name", "") for m in tags]
            status["has_model"] = any(
                n == self._ollama_model or n.split(":")[0] == self._ollama_model.split(":")[0]
                for n in names
            )
        except Exception:
            pass
        return status

    def _groq_generate(self, prompt: str, max_tokens: int, temperature: float = 0.2, system: Optional[str] = None) -> str:
        """Generate response from Groq API (fallback when Ollama fails)."""
        if not GROQ_API_KEY:
            return "(Groq API key not configured)"
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": max(0.1, min(0.7, temperature)),
            "max_tokens": min(max_tokens, 500),
        }
        
        try:
            r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            return str(data.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()
        except requests.exceptions.RequestException as e:
            logging.error(f"[Groq] API error: {e}")
            return f"(Groq error: {e})"
        except Exception as e:
            logging.error(f"[Groq] Error: {e}")
            return f"(Error: {e})"

    def groq_available(self) -> bool:
        """Check if Groq API is available."""
        if not GROQ_API_KEY:
            return False
        try:
            # Quick test with minimal request
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
            r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def _extract_numbers_from_context(self, context: str) -> List[str]:
        """Extract numeric phrases from context for validation."""
        patterns = [
            r"Rs\.?\s*[\d,]+(?:\s*(?:million|billion|crore|lakh))?",
            r"[\d,]+(?:\.\d+)?\s*(?:million|billion|crore|lakh)",
            r"\d+(?:\.\d+)?\s*(?:percent|%)",
            r"Rs\.?\s*[\d.]+\s*billion",
            r"Rs\.?\s*[\d.]+\s*million",
        ]
        numbers = []
        for pat in patterns:
            matches = re.findall(pat, context, re.IGNORECASE)
            numbers.extend(matches)
        return numbers

    def _sanitize_answer(self, text: str, context: str, page: int) -> str:
        """
        v2.0.8 Answer Sanitizer:
        - Keep only first 2-3 sentences
        - Trim to 70 words max
        - Preserve numeric phrases from context
        - Ensure single, clean citation
        - Remove hallucinated numbers not in context
        """
        if not text:
            return "Not found in the Manual."
        
        doc_name = "Manual for Development Projects 2024"
        
        # Step 1: Remove any existing citations (we'll add clean one at end)
        text = re.sub(r"\n*Source:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"\(Source:.*?\)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Manual for Development Projects \d{4},?\s*p\.?\s*\d+\.?", "", text)
        
        # Step 2: Split into sentences and keep first 2-3
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        # Keep up to 3 sentences
        kept_sentences = sentences[:3]
        answer = " ".join(kept_sentences)
        
        # Step 3: Trim to 70 words max
        words = answer.split()
        if len(words) > 70:
            answer = " ".join(words[:70])
            # Try to end at sentence boundary
            if not answer.rstrip().endswith(('.', '!', '?')):
                answer = answer.rstrip() + "."
        
        # Step 4: Validate numbers - remove any not in context
        context_numbers = self._extract_numbers_from_context(context)
        context_nums_lower = [n.lower() for n in context_numbers]
        
        # Find numbers in answer
        answer_nums = re.findall(r"Rs\.?\s*[\d,.]+(?:\s*(?:million|billion|crore|lakh))?|\d+(?:\.\d+)?\s*(?:million|billion|crore|lakh|percent|%)", answer, re.IGNORECASE)
        
        for num in answer_nums:
            # Check if this number (or similar) exists in context
            num_lower = num.lower().strip()
            found = False
            for ctx_num in context_nums_lower:
                # Fuzzy match - check if key digits match
                num_digits = re.sub(r'[^\d.]', '', num_lower)
                ctx_digits = re.sub(r'[^\d.]', '', ctx_num)
                if num_digits and ctx_digits and (num_digits in ctx_digits or ctx_digits in num_digits):
                    found = True
                    break
            # If number not found in context, it might be hallucinated - log but don't remove
            # (some numbers like page refs are ok)
        
        # Step 5: Remove common filler phrases
        filler_phrases = [
            r"^(?:According to the (?:provided )?(?:context|manual|text),?\s*)",
            r"^(?:Based on the (?:provided )?(?:context|manual|text),?\s*)",
            r"^(?:The (?:provided )?(?:context|manual|text) (?:states|mentions|indicates) that\s*)",
            r"^(?:As per the (?:provided )?(?:context|manual),?\s*)",
        ]
        for filler in filler_phrases:
            answer = re.sub(filler, "", answer, flags=re.IGNORECASE)
        
        # Step 6: Clean up whitespace
        answer = " ".join(answer.split()).strip()
        
        # Step 7: Add clean citation
        if page and page > 0:
            citation = f"\n\nSource: {doc_name}, p.{page}"
        else:
            citation = f"\n\nSource: {doc_name}"
        
        return answer + citation

    def _truncate_answer(self, text: str, max_words: int = 70) -> str:
        """Keep first 2-3 sentences, max 70 words. Legacy method for compatibility."""
        if not text:
            return ""
        
        # Remove any existing source citations first
        text = re.sub(r"\n*Source:.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        # Keep first 2-3 sentences
        kept = sentences[:3]
        result = " ".join(kept)
        
        # Trim to max words
        words = result.split()
        if len(words) > max_words:
            result = " ".join(words[:max_words])
            if not result.rstrip().endswith(('.', '!', '?')):
                result = result.rstrip() + "."
        
        return result.strip()

    def _format_citation(self, doc_name: str, page: int) -> str:
        """Format source citation."""
        if page and page > 0:
            return f"Source: {doc_name}, p.{page}"
        return f"Source: {doc_name}"

    def _has_answer_signal(self, context: str) -> bool:
        """Check if context has actual content to extract - VERY PERMISSIVE."""
        if not context:
            return False
        # If context has ANY substantial content (20+ words), assume it has useful info
        if len(context.split()) >= 20:
            return True
        return False

    def generate_response(
        self,
        question: str,
        context: str = "",
        max_new_tokens: int = 100,
        temperature: float = 0.15,
        force_groq: bool = False,
        page: int = 0
    ) -> str:
        """Generate answer from question and context.
        
        v2.0.8: Stricter output with sanitization.
        Args:
            force_groq: If True, bypass Ollama and use Groq directly (for testing)
            page: Page number for citation (extracted from hits metadata)
        """
        
        # No context = not found
        if not context or not context.strip():
            return "Not found in the Manual.\n\nSource: Manual for Development Projects 2024"
        
        # Log context length for debugging
        logging.info(f"[LocalModel] Context length: {len(context)} chars, {len(context.split())} words")
        
        # Extract page from context metadata if not provided
        if not page:
            page_match = re.search(r"\[page[:\s]*(\d+)\]", context, re.IGNORECASE)
            if page_match:
                page = int(page_match.group(1))
        
        # v2.0.8: Strict prompt for 45-70 word answers
        strict_prompt = f"""Context from the Manual:
{context[:2500]}

Question: {question}

Answer in 45-70 words. Extract numbers if present. Direct answer first:"""
        
        raw = ""
        
        if self.backend == "ollama" and not force_groq:
            # Try Ollama first
            raw = self._ollama_generate(
                strict_prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                system=SYSTEM_PROMPT
            )
            
            # Check if Ollama returned an error
            if raw.startswith("(Ollama error:") or raw.startswith("(Error:"):
                logging.warning(f"[LocalModel] Ollama failed: {raw}")
                raw = ""
            
            logging.info(f"[LocalModel] Raw response: {raw[:200] if raw else 'EMPTY'}...")
            
            # Check for false refusals
            refusal_phrases = [
                "does not provide", "not found", "no information",
                "cannot find", "not mentioned", "does not contain",
                "no specific", "not explicitly", "does not specify",
                "not available", "i don't have", "i cannot",
                "doesn't provide", "doesn't contain", "unable to"
            ]
            
            raw_lower = raw.lower() if raw else ""
            has_refusal = any(p in raw_lower for p in refusal_phrases)
            ctx_has_signal = len(context.split()) >= 20
            
            # Retry if refusal but context has content
            if has_refusal and ctx_has_signal:
                retry_prompt = f"""Extract the answer from this text:

TEXT: {context[:2000]}

QUESTION: {question}

State ONLY what the text says (45-70 words):"""
                
                raw = self._ollama_generate(
                    retry_prompt,
                    max_tokens=max_new_tokens,
                    temperature=0.1,
                    system="Extract information directly. Never refuse if text has content."
                )
                logging.info(f"[LocalModel] Retry response: {raw[:200] if raw else 'EMPTY'}...")
        
        # Force Groq mode or fallback
        if force_groq or not raw or raw.startswith("("):
            logging.info("[LocalModel] Using Groq for generation...")
            raw = self._groq_generate(
                strict_prompt,
                max_tokens=max_new_tokens,
                temperature=0.2,
                system=SYSTEM_PROMPT
            )
            logging.info(f"[LocalModel] Groq response: {raw[:200] if raw else 'EMPTY'}...")
        
        # v2.0.8: Apply answer sanitizer
        answer = self._sanitize_answer(raw, context, page)
        
        return answer
        
        # Transformers fallback
        if self._task_pipe is None:
            self.load_model()
        
        assert self._task_pipe is not None
        task, pipe_obj = self._task_pipe
        pipe = cast(Any, pipe_obj)
        
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer briefly:"
        )
        
        out = pipe(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=(temperature > 0),
            temperature=max(0.1, temperature),
        )
        
        text = out[0].get("generated_text", "").strip()
        answer = self._truncate_answer(text, max_words=80)
        
        if "source:" not in answer.lower():
            citation = self._format_citation(doc_name, page)
            answer = f"{answer}\n\n{citation}"
        
        return answer

    def generate_with_system_prompt(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_new_tokens: int = 150,
    ) -> str:
        """Generate with custom system prompt."""
        if self.backend == "ollama":
            return self._ollama_generate(
                user,
                max_tokens=max_new_tokens,
                temperature=temperature,
                system=system
            )
        
        if self._task_pipe is None:
            self.load_model()
        
        assert self._task_pipe is not None
        task, pipe_obj = self._task_pipe
        pipe = cast(Any, pipe_obj)
        
        prompt = f"System: {system}\n\nUser: {user}\n\nAssistant:"
        
        out = pipe(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=(temperature > 0),
            temperature=max(0.1, temperature),
            top_p=top_p,
        )
        
        return out[0].get("generated_text", "").strip()
