"""Fine-tune a small open model (DistilBERT) to classify career-advisor questions
into intents. Runs on CPU. Trained model is saved to ml/model/ and is loaded by
advisor_model.py at inference time.

Usage (from the backend/ folder, with the ML deps installed):

    pip install -r requirements-ml.txt
    python -m ml.train

To improve it: add more lines to ml/train_data.jsonl (more example questions per
intent, including real user phrasings and typos), then run this again.
"""

import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

BASE_MODEL = "distilbert-base-uncased"      # small, open, ~66M params, CPU-friendly
HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "train_data.jsonl"
MODEL_DIR = HERE / "model"
EPOCHS = 20          # small dataset needs many passes for the classifier head to converge
LEARNING_RATE = 5e-5
MAX_LEN = 48


def load_data():
    texts, labels = [], []
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            texts.append(row["text"])
            labels.append(row["intent"])
    return texts, labels


class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
    }


def main():
    texts, label_names = load_data()
    intents = sorted(set(label_names))
    label2id = {name: i for i, name in enumerate(intents)}
    id2label = {i: name for name, i in label2id.items()}
    y = [label2id[name] for name in label_names]

    # Stratified split so every intent appears in both train and validation.
    x_train, x_val, y_train, y_val = train_test_split(
        texts, y, test_size=0.2, random_state=42, stratify=y
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    enc_train = tokenizer(x_train, truncation=True, padding="max_length", max_length=MAX_LEN)
    enc_val = tokenizer(x_val, truncation=True, padding="max_length", max_length=MAX_LEN)

    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(intents), id2label=id2label, label2id=label2id
    )

    args = TrainingArguments(
        output_dir=str(HERE / "_checkpoints"),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=20,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=IntentDataset(enc_train, y_train),
        eval_dataset=IntentDataset(enc_val, y_val),
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    print("\nValidation metrics:", {k: round(v, 3) for k, v in metrics.items() if isinstance(v, float)})

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print(f"\nSaved fine-tuned model to: {MODEL_DIR}")
    print("The advisor will now use it automatically (see advisor_model.py).")


if __name__ == "__main__":
    main()
