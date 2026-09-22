from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parent

EVAL_FILE = BASE_DIR / "data" / "eval" / "documents.csv"

MODEL_FILE = (
    BASE_DIR
    / "artifacts"
    / "classifier-v1"
    / "model.joblib"
)


def main():
    eval_df = pd.read_csv(EVAL_FILE)

    model = joblib.load(MODEL_FILE)

    predictions = model.predict(
        eval_df["text"]
    )

    accuracy = accuracy_score(
        eval_df["label"],
        predictions,
    )

    print("\n=== CLASSIFICATION EVALUATION ===")
    print(f"Accuracy: {accuracy:.4f}")

    print("\nPrecision / Recall / F1:")
    print(
        classification_report(
            eval_df["label"],
            predictions,
            digits=4,
            zero_division=0,
        )
    )

    labels = list(
        model.named_steps["classifier"].classes_
    )

    print("Confusion Matrix:")
    print(f"Labels: {labels}")

    print(
        confusion_matrix(
            eval_df["label"],
            predictions,
            labels=labels,
        )
    )

    probabilities = model.predict_proba(
        eval_df["text"]
    )

    confidence = probabilities.max(axis=1)

    print("\nConfidence summary:")
    print(
        pd.Series(confidence).describe()
    )


if __name__ == "__main__":
    main()