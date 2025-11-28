"""
PDBot Local Model v3.1.0
Mistral-optimized with simple system prompt.
Groq fallback when Ollama fails.
"""
import os
import re
import logging
from typing import Optional, Dict, Any, Tuple, cast
import requests

_CACHE: Dict[str, Tuple[str, object]] = {}

DEFAULT_MODEL = os.getenv("CHATBOT_MODEL", "google/flan-t5-small")
FALLBACK_MODEL = os.getenv("CHATBOT_FALLBACK_MODEL", "distilgpt2")

# Groq API configuration (set GROQ_API_KEY environment variable)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Fast and capable

# =============================================================================
# SYSTEM PROMPT (Mistral-optimized, extremely simple)
# =============================================================================
SYSTEM_PROMPT = """You are PDBOT. Answer questions using the provided context.
If context is given, always extract and state the relevant information.
Provide complete answers in 4-7 sentences (around 120-150 words)."""


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

    def _truncate_answer(self, text: str, max_words: int = 150) -> str:
        """Keep first paragraph, max 150 words."""
        if not text:
            return ""
        
        # Take first two paragraphs for fuller answers
        paragraphs = text.strip().split("\n\n")
        first = " ".join(paragraphs[:2]) if len(paragraphs) > 1 else paragraphs[0] if paragraphs else text
        
        # Stop at list markers
        for marker in ["\n1.", "\n2.", "\n-", "\n*"]:
            if marker in first:
                first = first.split(marker)[0]
        
        # Cap at max words
        words = first.split()
        if len(words) > max_words:
            first = " ".join(words[:max_words])
        
        return first.strip()

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
        max_new_tokens: int = 150,
        temperature: float = 0.2,
        force_groq: bool = False
    ) -> str:
        """Generate answer from question and context.
        
        Args:
            force_groq: If True, bypass Ollama and use Groq directly (for testing)
        """
        
        # No context = not found
        if not context or not context.strip():
            return "Not found in the Manual."
        
        # Log context length for debugging
        import logging
        logging.info(f"[LocalModel] Context length: {len(context)} chars, {len(context.split())} words")
        
        # Extract page from context metadata (if embedded)
        page = 0
        page_match = re.search(r"\[page[:\s]*(\d+)\]", context, re.IGNORECASE)
        if page_match:
            page = int(page_match.group(1))
        
        doc_name = "Manual for Development Projects 2024"
        
        # v2.0.7: Force Groq mode for testing
        if force_groq:
            logging.info("[LocalModel] Force Groq mode enabled - bypassing Ollama")
            groq_prompt = f"""You are PDBOT, an assistant for the Manual for Development Projects.

Based on the following context, answer the question in 4-7 sentences.

Context:
{context[:3000]}

Question: {question}

Provide a direct, informative answer:"""
            
            raw = self._groq_generate(
                groq_prompt,
                max_tokens=max_new_tokens,
                temperature=0.3,
                system=SYSTEM_PROMPT
            )
            logging.info(f"[LocalModel] Groq (forced) response: {raw[:200] if raw else 'EMPTY'}...")
            
            answer = self._truncate_answer(raw, max_words=150)
            if "source:" not in answer.lower() and "p." not in answer.lower():
                citation = self._format_citation(doc_name, page)
                answer = f"{answer}\n\n{citation}"
            return answer
        
        if self.backend == "ollama":
            # Use a simpler, more direct prompt format
            prompt = f"""Context from Manual:
{context}

Question: {question}

Based on the context above, provide a direct answer:"""
            
            # Try Ollama first
            ollama_failed = False
            raw = self._ollama_generate(
                prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                system=SYSTEM_PROMPT
            )
            
            # Check if Ollama returned an error
            if raw.startswith("(Ollama error:") or raw.startswith("(Error:"):
                logging.warning(f"[LocalModel] Ollama failed: {raw}, falling back to Groq...")
                ollama_failed = True
            
            logging.info(f"[LocalModel] First response: {raw[:200] if raw else 'EMPTY'}...")
            
            # Check for false refusals - be very aggressive about catching these
            refusal_phrases = [
                "does not provide",
                "not found",
                "no information",
                "cannot find",
                "not mentioned",
                "does not contain",
                "no specific",
                "numeric value",
                "not explicitly",
                "does not specify",
                "not available",
                "i don't have",
                "i cannot",
                "insufficient",
                "doesn't provide",
                "doesn't contain",
                "doesn't mention",
                "not in the",
                "unable to",
                "no relevant"
            ]
            
            raw_lower = raw.lower()
            has_refusal = any(p in raw_lower for p in refusal_phrases)
            ctx_has_signal = self._has_answer_signal(context)
            
            logging.info(f"[LocalModel] has_refusal={has_refusal}, ctx_has_signal={ctx_has_signal}")
            
            # ALWAYS retry if we got a refusal and have context
            if has_refusal and ctx_has_signal:
                # Second attempt - very direct
                direct_prompt = f"""Read this text and answer the question.

TEXT:
{context[:3000]}

QUESTION: {question}

State what the text says about this topic:"""
                
                raw = self._ollama_generate(
                    direct_prompt,
                    max_tokens=max_new_tokens,
                    temperature=0.15,
                    system="Extract and state information from the given text. Do not refuse."
                )
                logging.info(f"[LocalModel] Retry 1 response: {raw[:200] if raw else 'EMPTY'}...")
                
                # Check if still refusing
                raw_lower = raw.lower()
                still_refusing = any(p in raw_lower for p in refusal_phrases)
                
                if still_refusing:
                    # Third attempt - just summarize the context
                    summary_prompt = f"""Summarize this text in 2-3 sentences, focusing on: {question}

TEXT:
{context[:2500]}

SUMMARY:"""
                    
                    raw = self._ollama_generate(
                        summary_prompt,
                        max_tokens=max_new_tokens,
                        temperature=0.2,
                        system="Summarize the given text."
                    )
                    logging.info(f"[LocalModel] Retry 2 response: {raw[:200] if raw else 'EMPTY'}...")
            
            # v2.0.7: GROQ FALLBACK - If Ollama failed or still refusing, try Groq
            raw_lower = raw.lower() if raw else ""
            final_refusal = any(p in raw_lower for p in refusal_phrases) or ollama_failed or raw.startswith("(")
            
            if final_refusal and ctx_has_signal:
                logging.info("[LocalModel] All Ollama attempts failed, trying Groq fallback...")
                groq_prompt = f"""You are PDBOT, an assistant for the Manual for Development Projects.

Based on the following context, answer the question in 4-7 sentences.

Context:
{context[:3000]}

Question: {question}

Provide a direct, informative answer:"""
                
                raw = self._groq_generate(
                    groq_prompt,
                    max_tokens=max_new_tokens,
                    temperature=0.3,
                    system=SYSTEM_PROMPT
                )
                logging.info(f"[LocalModel] Groq response: {raw[:200] if raw else 'EMPTY'}...")
            
            # Truncate to 150 words for fuller answers
            answer = self._truncate_answer(raw, max_words=150)
            
            # Add citation if not already present
            if "source:" not in answer.lower() and "p." not in answer.lower():
                citation = self._format_citation(doc_name, page)
                answer = f"{answer}\n\n{citation}"
            
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
