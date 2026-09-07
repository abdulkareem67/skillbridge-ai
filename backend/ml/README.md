# Trainable AI Advisor — Intent Model

This folder contains a small, **trainable** AI model for the SkillBridge career
advisor. It fine-tunes **DistilBERT** (a small, open transformer from HuggingFace,
~66M parameters) to understand *what a user is asking* — even with new phrasings or
typos — and routes it to the right advisor answer.

It is a **classification** model (it picks the correct intent), which is exactly what
"understand questions better" needs. It is **not** a chatbot that writes free-form
text — your advisor's answers still come from `skills_engine.py`, so they stay
accurate and on-brand.

## Why this approach
- **You own it and train it** on your own data (`train_data.jsonl`).
- **Runs offline on CPU** — no API keys, no per-message cost, no internet needed.
- **Safe to ship**: if the model isn't trained or the libraries aren't installed,
  the advisor automatically falls back to keyword + fuzzy matching. The site never
  breaks.

## Files
| File | What it is |
|------|-----------|
| `train_data.jsonl` | Your labeled examples: `{"text": "...", "intent": "..."}`. **This is what you edit to train it.** |
| `train.py` | Fine-tunes DistilBERT on the data and saves the model to `ml/model/`. |
| `advisor_model.py` | Loads the trained model and predicts the intent at runtime. |
| `model/` | The trained model (created after you run training). |

## How to train

From the `backend/` folder:

```bash
# 1. Install the ML dependencies (one-time; ~a few hundred MB for torch)
pip install -r requirements-ml.txt

# 2. Train the model (downloads DistilBERT once, then fine-tunes — a few minutes on CPU)
python -m ml.train

# 3. (Optional) sanity-check predictions
python -m ml.advisor_model
```

After training, `ml/model/` will contain your fine-tuned model. Restart the web app
and the advisor will use it automatically.

## How to make it smarter
The model is only as good as its examples. To improve accuracy:

1. Open `train_data.jsonl`.
2. Add more lines for real questions your users ask — **including messy, misspelled,
   and Roman-Urdu phrasings** — each labeled with the correct `intent`.
3. Keep the intent names identical to the ones already in the file (they must match
   the intents handled in `app/skills_engine.py`).
4. Re-run `python -m ml.train`.

More examples per intent (aim for 20–40+ each) = better understanding.

## The intents
`greeting`, `thanks`, `about`, `getting_started`, `how_to_apply`, `skills_for_role`,
`match_score`, `career_fit`, `next_skill`, `cv_tips`, `interview_prep`,
`certifications`, and `fallback` (off-topic / unknown — the advisor ignores this and
gives its general help message).

## Deploying to your website
The model runs inside your existing FastAPI backend — there's nothing separate to
host. Just make sure the production server:

1. has the `requirements-ml.txt` packages installed, and
2. includes the `ml/model/` folder (commit it, or copy it during deployment).

If either is missing, the advisor still works using the rule-based matching — you
just don't get the model's extra understanding until both are present.

> Tip: a CPU with ~1 GB free RAM is enough to *run* the model for a website. If your
> host is very small (e.g. a 256 MB free tier), keep using the rule-based advisor —
> it needs no extra memory.
