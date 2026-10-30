"""Unsupervised Anomaly Detection Service for Network Flow Telemetry.

Trained strictly on benign traffic to identify out-of-distribution network behavior
independently of supervised attack classifications.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd

from cyber_assistant.ml.features import extract_single_flow_features


class AnomalyDetector:
    def __init__(self, model_path: Path | str | None = None):
        if model_path is None:
            model_path = Path("models/anomaly_detector.joblib")
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Anomaly detector bundle not found at {self.model_path}")

        bundle = joblib.load(self.model_path)
        self.model = bundle["model"]
        self.feature_names = bundle["feature_names"]
        self.threshold = bundle.get("threshold", 0.55)
        self.score_min = bundle.get("score_min", 0.35)
        self.score_max = bundle.get("score_max", 0.75)
        self.benign_baseline_mean = bundle.get("benign_baseline_mean", {})

    def score_flow(self, flow_dict: dict[str, Any]) -> dict[str, Any]:
        """Compute an unsupervised anomaly score for a single flow dictionary.
        
        Returns:
            anomaly_score: normalized float between 0.0 (baseline benign) and 1.0 (highly abnormal)
            is_anomaly: bool indicating whether the flow exceeds the validation-calibrated threshold
            raw_score: raw IsolationForest negative sample score
        """
        X = extract_single_flow_features(flow_dict)
        raw_score = float(-self.model.score_samples(X)[0])
        is_anomaly = bool(raw_score > self.threshold)

        # Normalize score into [0.0, 1.0]
        denom = max(self.score_max - self.score_min, 1e-6)
        normalized = (raw_score - self.score_min) / denom
        anomaly_score = float(round(np.clip(normalized, 0.0, 1.0), 4))

        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "raw_anomaly_score": round(raw_score, 4),
            "threshold": round(self.threshold, 4),
        }
