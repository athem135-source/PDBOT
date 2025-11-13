import importlib
import importlib.util
import os
from types import ModuleType
from typing import Callable, List, Optional
from .local_model import LocalModel


class PretrainedModel:
    """
    Generic wrapper to call a user-provided predictor function for QA over the manual.

    Expected entrypoint formats:
      - "package.module:function_name"
      - "path/to/script.py:function_name"

    The function signature should be:
      def predict(question: str, context: str, chunks: List[str], raw_pages: List[str], model_path: Optional[str] = None) -> str

    Return a string answer. If no relevant context is provided, return "Not found in document.".
    """

    def __init__(self, entrypoint: str, model_path: str = "") -> None:
        self.entrypoint = (entrypoint or "").strip()
        self.model_path = (model_path or "").strip()
        self._func: Optional[Callable[..., str]] = None
        if self.entrypoint:
            self._func = self._load_function(self.entrypoint)

    def _load_function(self, entry: str) -> Callable[..., str]:
        if ":" not in entry:
            raise ValueError("Entrypoint must be in the form 'module:function' or 'path.py:function'")
        mod_spec, func_name = entry.split(":", 1)
        func_name = func_name.strip()

        # Path-based import
        if os.path.isfile(mod_spec) and mod_spec.endswith(".py"):
            spec = importlib.util.spec_from_file_location("custom_predictor", mod_spec)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module from path: {mod_spec}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        else:
            # Module import
            module = importlib.import_module(mod_spec)

        func = getattr(module, func_name, None)
        if not callable(func):
            raise AttributeError(f"Function '{func_name}' not found or not callable in '{mod_spec}'")
        return func  # type: ignore[return-value]

    def predict(self, question: str, context: str, chunks: List[str], raw_pages: List[str]) -> str:
        # Enforce strict grounding like the LLM mode
        if not (context or "").strip():
            return "Not found in document."
        if self._func is None:
            # No entrypoint given; provide a simple baseline that returns the top part of context
            snippet = context.strip().split("\n\n", 1)[0]
            return (snippet[:2000] if snippet else "Not found in document.")
        try:
            res = self._func(question=question, context=context, chunks=chunks, raw_pages=raw_pages, model_path=self.model_path)
        except TypeError:
            # Some implementations may not accept keyword args; try positional
            res = self._func(question, context, chunks, raw_pages, self.model_path)
        except Exception as e:
            return f"Error in pretrained model: {e}"
        out = str(res or "").strip()
        return out[:2000] if out else "Not found in document."

    # Unified generation entry used by Generative Mode prompts
    def generate_with_system_prompt(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.25,
        top_p: float = 0.9,
        max_new_tokens: int = 900,
    ) -> str:
        """Provide a generic text generation path for pretrained backend by
        delegating to a lightweight transformers LocalModel. This ensures the
        unified API works even if the custom entrypoint doesn't include a chat model.
        """
        lm = LocalModel(model_name=None, backend="transformers")
        return lm.generate_with_system_prompt(
            system,
            user,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
        )
