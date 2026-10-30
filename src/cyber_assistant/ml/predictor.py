"""Inference and explainability service for intrusion classification and risk scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd

from cyber_assistant.ml.features import extract_single_flow_features, extract_features

SEVERITY_LEVELS = [
    (0.85, "Critical"),
    (0.60, "High"),
    (0.35, "Medium"),
    (0.10, "Low"),
    (0.00, "Informational"),
]


class IntrusionPredictor:
    def __init__(self, model_path: Path | str | None = None):
        if model_path is None:
            model_path = Path("models/attack_classifier.joblib")
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model bundle not found at {self.model_path}")
        
        bundle = joblib.load(self.model_path)
        self.model = bundle["model"]
        self.classes = bundle["classes"]
        self.feature_names = bundle["feature_names"]
        self.benign_baseline = bundle.get("benign_baseline", {})

    def predict_flow(self, flow_dict: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single flow record and return attack prediction, risk score, and explainability."""
        X = extract_single_flow_features(flow_dict)
        probs = self.model.predict_proba(X)[0]
        prob_dict = {cls_name: float(round(p, 4)) for cls_name, p in zip(self.classes, probs)}
        
        predicted_family = str(self.model.predict(X)[0])
        confidence = prob_dict.get(predicted_family, 0.0)
        
        benign_prob = prob_dict.get("benign", 0.0)
        risk_score = float(round(1.0 - benign_prob, 4))
        
        severity = "Informational"
        for threshold, label in SEVERITY_LEVELS:
            if risk_score >= threshold:
                severity = label
                break

        # Compute explainability (Top anomalous features deviating from benign traffic)
        explanations = self._explain_flow(X.iloc[0].to_dict())

        return {
            "predicted_family": predicted_family,
            "confidence": confidence,
            "risk_score": risk_score,
            "severity": severity,
            "class_probabilities": prob_dict,
            "top_feature_attributions": explanations,
        }

    def _explain_flow(self, flow_features: dict[str, float]) -> list[dict[str, Any]]:
        """Identify key features that deviate significantly from typical benign baselines."""
        deviations = []
        for feat, val in flow_features.items():
            baseline = self.benign_baseline.get(feat, 0.0)
            diff = abs(val - baseline)
            rel_diff = diff / (abs(baseline) + 1.0)
            deviations.append({
                "feature": feat,
                "observed_value": round(float(val), 4),
                "benign_baseline": round(float(baseline), 4),
                "deviation_magnitude": round(float(rel_diff), 4),
            })
        
        # Sort by relative deviation descending and pick top 5
        deviations.sort(key=lambda x: x["deviation_magnitude"], reverse=True)
        return deviations[:5]
