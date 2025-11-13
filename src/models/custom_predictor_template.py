"""
Template for integrating your own pretrained predictor.

Save this file as, for example, src/models/custom_predictor.py and update your
entrypoint in the app's sidebar to:

  src.models.custom_predictor:predict

Or use a path-based entry:

  path\to\custom_predictor.py:predict

Required signature:
  def predict(question: str, context: str, chunks: list[str], raw_pages: list[str], model_path: str | None = None) -> str

Notes:
- 'context' is a concatenation of the top-K retrieved chunks from your manual
- 'chunks' is a list of those retrieved chunk strings
- 'raw_pages' are full page texts (only when a PDF/TXT was processed)
- 'model_path' can point to your weights/artifacts if needed
- Return "Not found in document." if you cannot answer from provided context
"""
from __future__ import annotations
from typing import List, Optional


def predict(question: str, context: str, chunks: List[str], raw_pages: List[str], model_path: Optional[str] = None) -> str:
    # Example baseline: return the first sentence from the top chunk when available
    if not (context or "").strip():
        return "Not found in document."
    top = chunks[0] if chunks else context
    # Keep it short
    sent = top.strip().split(".")[0].strip()
    return sent + "." if sent and not sent.endswith(".") else (sent or "Not found in document.")
