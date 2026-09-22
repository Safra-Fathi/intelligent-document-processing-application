import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent

TRAIN_FILE = BASE_DIR / "data" / "train" / "documents.csv"
DEV_FILE = BASE_DIR / "data" / "dev" / "documents.csv"

ARTIFACT_DIR = BASE_DIR / "artifacts" / "classifier-v1"
MODEL_FILE = ARTIFACT_DIR / "model.joblib"
METADATA_FILE = ARTIFACT_DIR / "metadata.json"

UNKNOWN_THRESHOLD = 0.70


def calculate_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    train_df = pd.read_csv(TRAIN_FILE)
    dev_df = pd.read_csv(DEV_FILE)

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=10000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )

    pipeline.fit(
        train_df["text"],
        train_df["label"],
    )

    predictions = pipeline.predict(dev_df["text"])

    report = classification_report(
        dev_df["label"],
        predictions,
        output_dict=True,
        zero_division=0,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(pipeline, MODEL_FILE)

    metadata = {
        "model_version": "classifier-v1",
        "model_type": "TF-IDF + Logistic Regression",
        "labels": list(
            pipeline.named_steps["classifier"].classes_
        ),
        "unknown_threshold": UNKNOWN_THRESHOLD,
        "training_data_sha256": calculate_hash(TRAIN_FILE),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dev_accuracy": report["accuracy"],
    }

    METADATA_FILE.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("Model trained successfully.")
    print(f"Development accuracy: {report['accuracy']:.4f}")
    print(f"Model saved to: {MODEL_FILE}")
    print(f"Metadata saved to: {METADATA_FILE}")


if __name__ == "__main__":
    main()