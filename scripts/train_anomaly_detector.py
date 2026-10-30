"""Train and save an IsolationForest Anomaly Detector strictly on Benign Training Flows.

Outputs:
  models/anomaly_detector.joblib
  reports/anomaly_evaluation.json
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cyber_assistant.ml.features import extract_features, ALL_MODEL_FEATURES


def train_anomaly_model(db_path: Path, output_dir: Path, n_samples: int = 25000):
    print(f"Sampling {n_samples:,} benign flows from {db_path}...")
    conn = sqlite3.connect(db_path)
    df_benign = pd.read_sql(
        f"SELECT * FROM flows WHERE attack_family = 'benign' ORDER BY RANDOM() LIMIT {n_samples}",
        conn,
    )
    # Also load a sample of attack flows for validation evaluation
    df_attacks = pd.read_sql(
        "SELECT * FROM flows WHERE attack_family != 'benign' ORDER BY RANDOM() LIMIT 5000",
        conn,
    )
    conn.close()

    print(f"Extracted {len(df_benign):,} benign flows. Extracting features...")
    X_benign = extract_features(df_benign)
    X_attacks = extract_features(df_attacks)

    # Split benign data into Train (80%) and Test (20%)
    X_train_benign, X_test_benign = train_test_split(X_benign, test_size=0.20, random_state=42)

    print(f"Training IsolationForest on {len(X_train_benign):,} strictly benign training samples...")
    iso = IsolationForest(
        n_estimators=100,
        max_samples="auto",
        contamination=0.03,  # 3% expected anomaly rate in baseline
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_train_benign)

    # Evaluate on test benign vs attack flows
    benign_scores = -iso.score_samples(X_test_benign)  # higher = more anomalous
    attack_scores = -iso.score_samples(X_attacks)

    # Threshold chosen at 95th percentile of benign training distribution
    train_scores = -iso.score_samples(X_train_benign)
    threshold = float(np.percentile(train_scores, 97))

    benign_anomaly_rate = float(np.mean(benign_scores > threshold))
    attack_detection_rate = float(np.mean(attack_scores > threshold))

    print(f"Validation Threshold: {threshold:.4f}")
    print(f"Benign False Alarm Rate: {benign_anomaly_rate*100:.2f}%")
    print(f"Attack Anomaly Detection Rate: {attack_detection_rate*100:.2f}%")

    output_dir.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "model": iso,
        "feature_names": ALL_MODEL_FEATURES,
        "threshold": threshold,
        "benign_baseline_mean": X_train_benign.mean().to_dict(),
        "score_min": float(np.min(train_scores)),
        "score_max": float(np.percentile(attack_scores, 99)),
    }
    model_path = output_dir / "anomaly_detector.joblib"
    joblib.dump(model_bundle, model_path)
    print(f"Saved anomaly detector bundle to {model_path}")

    # Save evaluation report
    report = {
        "model_type": "IsolationForest",
        "training_samples_benign": len(X_train_benign),
        "test_samples_benign": len(X_test_benign),
        "test_samples_attacks": len(X_attacks),
        "threshold": threshold,
        "benign_false_alarm_rate": round(benign_anomaly_rate, 4),
        "attack_detection_rate": round(attack_detection_rate, 4),
        "benign_score_mean": round(float(np.mean(benign_scores)), 4),
        "attack_score_mean": round(float(np.mean(attack_scores)), 4),
    }
    report_path = Path("reports/anomaly_evaluation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved evaluation report to {report_path}")


if __name__ == "__main__":
    db = Path("data/cicids2017.sqlite3")
    out = Path("models")
    train_anomaly_model(db, out)
