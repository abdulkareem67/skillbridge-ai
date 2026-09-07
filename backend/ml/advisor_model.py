"""Inference wrapper for the fine-tuned intent classifier.

Designed to be optional and safe: if the ML libraries aren't installed, or the
model hasn't been trained yet, `predict_intent` simply returns (None, 0.0) and the
advisor falls back to its keyword + fuzzy matching. This keeps the website running
whether or not the model is present.
"""

from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent / "model"

# Below this confidence we don't trust the model and let the advisor fall back.
CONFIDENCE_THRESHOLD = 0.60

_pipeline = None          # lazy-loaded HuggingFace pipeline
_load_attempted = False   # so we only try (and log) once


def _load():
    """Lazily load the classifier. Returns the pipeline or None on any failure."""
    global _pipeline, _load_attempted
    if _load_attempted:
        return _pipeline
    _load_attempted = True

    if not (MODEL_DIR / "config.json").exists():
        # Model not trained yet — run `python -m ml.train`.
        return None
    try:
        from transformers import pipeline  # heavy import; only when a model exists
        _pipeline = pipeline(
            "text-classification",
            model=str(MODEL_DIR),
            tokenizer=str(MODEL_DIR),
            truncation=True,
            max_length=48,
        )
    except Exception as exc:  # transformers/torch not installed, corrupt model, etc.
        print(f"[advisor_model] classifier unavailable, falling back to rules: {exc}")
        _pipeline = None
    return _pipeline


def is_available() -> bool:
    return _load() is not None


def predict_intent(text: str) -> tuple[str | None, float]:
    """Return (intent, confidence). (None, 0.0) means 'no confident prediction' —
    the caller should fall back to rule-based matching."""
    clf = _load()
    if clf is None or not text or not text.strip():
        return None, 0.0
    try:
        result = clf(text)[0]  # {"label": <intent>, "score": <float>}
    except Exception as exc:
        print(f"[advisor_model] prediction failed: {exc}")
        return None, 0.0

    label, score = result["label"], float(result["score"])
    if score < CONFIDENCE_THRESHOLD:
        return None, score
    return label, score


if __name__ == "__main__":
    # Quick manual check: python -m ml.advisor_model
    if not is_available():
        print("No trained model found. Train it first with:  python -m ml.train")
    else:
        for q in [
            "how i will aply for job",
            "which career suits me best",
            "prepair me for the intervew",
            "what is the weather today",
        ]:
            print(f"{q!r:40} -> {predict_intent(q)}")
