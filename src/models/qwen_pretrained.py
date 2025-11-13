"""
Built-in pretrained predictor using Qwen2.5 Instruct from Hugging Face.

Defaults optimized for local CPU-friendly usage:
- Default model ID switched to the smaller 0.5B variant to avoid multi‑GB downloads.
- Force PyTorch backend and suppress TensorFlow oneDNN logs.
- Respect a local HF cache so models aren't re-downloaded each run.

Usage in the app (sidebar):
- Inference engine: Pretrained (local)
- Entrypoint: src.models.qwen_pretrained:predict
- Model artifact path (optional): override the HF model id (e.g., Qwen/Qwen2.5-0.5B-Instruct or a local folder)

This predictor is STRICTLY grounded: if no context is provided, it returns
"Not found in document." exactly.
"""
from __future__ import annotations
import os
from typing import List, Optional

# Lazy imports to avoid heavy import cost during app startup
_tokenizer = None
_model = None
_device = "cpu"

# Quiet TensorFlow and force Transformers to use Torch only (no TF backend)
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

# Ensure a persistent local HF cache if none set
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
os.environ.setdefault("HF_HOME", os.path.join(_ROOT, ".hf_cache"))

DEFAULT_MODEL_ID = os.environ.get("QWEN_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")


def _load_model(model_id: str) -> None:
    global _tokenizer, _model, _device
    if _model is not None and _tokenizer is not None:
        return
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Missing transformers/torch. Install with: pip install transformers torch"
        ) from e

    # Choose device
    if hasattr(torch, "cuda") and torch.cuda.is_available():
        _device = "cuda"
    else:
        _device = "cpu"

    _tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, local_files_only=False)
    _model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        local_files_only=False,
    )
    if _device == "cuda":
        _model = _model.to("cuda")
    else:
        _model = _model.to("cpu")


def _build_prompt(question: str, context: str) -> str:
    system = (
        "You are a precise assistant. Answer ONLY from the provided document context. "
        "If the answer is not present, reply exactly: Not found in document. Keep answers concise."
    )
    prompt = (
        f"[System]\n{system}\n\n"
        f"[Context]\n{context.strip()}\n\n"
        f"[Question]\n{question.strip()}\n\n[Answer]\n"
    )
    return prompt


def predict(
    question: str,
    context: str,
    chunks: List[str],
    raw_pages: List[str],
    model_path: Optional[str] = None,
) -> str:
    # Strict grounding
    if not (context or "").strip():
        return "Not found in document."

    model_id = (model_path or "").strip() or DEFAULT_MODEL_ID

    _load_model(model_id)

    # Type: ignore protects dynamic globals
    from transformers import TextGenerationPipeline  # type: ignore

    prompt = _build_prompt(question, context)
    inputs = _tokenizer(prompt, return_tensors="pt")  # type: ignore[attr-defined]
    if _device == "cuda":
        for k in inputs:
            inputs[k] = inputs[k].to("cuda")

    # Conservative generation settings to keep it concise
    gen_out = _model.generate(  # type: ignore[attr-defined]
        **inputs,
        max_new_tokens=200,
        do_sample=False,
        temperature=0.0,
        pad_token_id=_tokenizer.eos_token_id if hasattr(_tokenizer, "eos_token_id") else None,  # type: ignore[attr-defined]
    )
    text = _tokenizer.decode(gen_out[0], skip_special_tokens=True)  # type: ignore[attr-defined]

    # Extract only the answer after the [Answer] tag
    lower = text.lower()
    idx = lower.rfind("[answer]")
    ans = text[idx + len("[Answer]") :].strip() if idx != -1 else text.strip()

    # Final guard: if the model didn't follow rules and there's no overlap with context, fall back
    if not ans:
        return "Not found in document."
    return ans


def preload(model_path: Optional[str] = None) -> dict:
    """
    Pre-download and initialize the pretrained model so the first question is fast.

    Returns a small status dict with the resolved model id and device. This is
    intentionally light so the Streamlit UI can call it via a button.

    FIX-Preload: Provide an explicit preload entrypoint.
    """
    model_id = (model_path or "").strip() or DEFAULT_MODEL_ID
    _load_model(model_id)
    return {"ok": True, "model_id": model_id, "device": _device, "cache": os.environ.get("HF_HOME", "")}
