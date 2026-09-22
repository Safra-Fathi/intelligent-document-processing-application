import json
from pathlib import Path

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[3]

ARTIFACT_DIR = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "classifier-v1"
)

MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"


class DocumentClassifier:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise RuntimeError(
                f"Classifier model not found: {MODEL_PATH}"
            )

        if not METADATA_PATH.exists():
            raise RuntimeError(
                f"Classifier metadata not found: {METADATA_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

        self.metadata = json.loads(
            METADATA_PATH.read_text(encoding="utf-8")
        )

        self.threshold = float(
            self.metadata["unknown_threshold"]
        )

        self.version = self.metadata["model_version"]

    def predict(self, text: str) -> dict:
        if not text or not text.strip():
            return {
                "predicted_type": "UNKNOWN",
                "confidence": 0.0,
                "classifier_version": self.version,
            }

        probabilities = self.model.predict_proba([text])[0]

        classes = self.model.named_steps[
            "classifier"
        ].classes_

        best_index = probabilities.argmax()

        predicted_class = str(classes[best_index])
        confidence = float(probabilities[best_index])

        if confidence < self.threshold:
            predicted_class = "UNKNOWN"

        return {
            "predicted_type": predicted_class,
            "confidence": round(confidence, 4),
            "classifier_version": self.version,
        }


classifier = DocumentClassifier()