"""Train the CIC-IDS2017 Intrusion Risk & Attack Classification Model.

Uses stratified sampling across all attack families, extracts the 65 engineered features,
trains an ensemble classifier, evaluates classification metrics (Precision, Recall, F1),
and saves the trained model bundle with feature importance metadata.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cyber_assistant.ml.features import extract_features, ALL_MODEL_FEATURES  # noqa: E402


def sample_training_data(db_path: Path, max_per_class: int = 15_000) -> pd.DataFrame:
    """Extract a representative, stratified dataset across all attack families."""
    print(f"Connecting to {db_path} for stratified sample extraction...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT attack_family FROM flows")
    families = [r[0] for r in cur.fetchall()]

    dfs = []
    for fam in families:
        query = f"SELECT * FROM flows WHERE attack_family = ? ORDER BY RANDOM() LIMIT {max_per_class}"
        df_fam = pd.read_sql(query, conn, params=(fam,))
        print(f"  Loaded {len(df_fam):,} samples for family '{fam}'")
        dfs.append(df_fam)

    conn.close()
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Total sampled dataset: {len(combined):,} rows across {len(families)} families.")
    return combined


def train_model(
    db_path: Path,
    output_dir: Path,
    max_per_class: int = 15_000,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = sample_training_data(db_path, max_per_class=max_per_class)

    y_family = df["attack_family"].astype(str)
    y_label = df["attack_label"].astype(str)

    print("Extracting domain-engineered features...")
    X = extract_features(df)

    print(f"Feature matrix shape: {X.shape}")

    # Train / test split (80 / 20)
    X_train, X_test, y_train, y_test, label_train, label_test = train_test_split(
        X, y_family, y_label, test_size=0.20, random_state=42, stratify=y_family
    )

    print(f"Training set: {len(X_train):,} samples. Test set: {len(X_test):,} samples.")
    print("Training HistGradientBoostingClassifier for multi-class attack triage...")

    # HistGradientBoostingClassifier handles large feature tables fast and natively supports class weighting
    model = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    print("Evaluating model performance on test set...")
    preds = model.predict(X_test)
    report = classification_report(y_test, preds, zero_division=0)
    print("\n=== Classification Report ===")
    print(report)

    # Compute baseline feature means for benign traffic (for real-time feature attribution in investigations)
    benign_mask = (y_family == "benign")
    benign_baseline = X[benign_mask].mean().to_dict()

    bundle = {
        "model": model,
        "classes": list(model.classes_),
        "feature_names": ALL_MODEL_FEATURES,
        "benign_baseline": benign_baseline,
        "report": report,
    }

    model_path = output_dir / "attack_classifier.joblib"
    joblib.dump(bundle, model_path)
    print(f"\nSaved trained model bundle to {model_path} ({model_path.stat().st_size:,} bytes).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/cicids2017.sqlite3"))
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    parser.add_argument("--max-per-class", type=int, default=15_000)
    args = parser.parse_args()

    train_model(args.db, args.output_dir, args.max_per_class)


if __name__ == "__main__":
    main()
