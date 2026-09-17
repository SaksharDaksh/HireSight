import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from imblearn.over_sampling import SMOTE
import xgboost as xgb
from src.ml.dataset_generator import FeatureDatasetGenerator

FEATURE_COLUMNS = [
    "semantic_similarity",
    "required_skill_overlap",
    "preferred_skill_overlap",
    "skills_count",
    "candidate_exp_years",
    "required_exp_years",
    "experience_delta",
    "hard_constraint_met",
    "degree_requirement_met"
]

def train_and_evaluate_model():
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    csv_path = "data/training_features.csv"
    if not os.path.exists(csv_path):
        print("Generating training features dataset...")
        generator = FeatureDatasetGenerator()
        df = generator.build_dataset()
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    X = df[FEATURE_COLUMNS]
    y = df["target_match"]

    print("Initial class distribution:")
    print(y.value_counts())

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # 1. Baseline Model without SMOTE
    baseline_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        eval_metric="logloss"
    )
    baseline_model.fit(X_train, y_train)
    y_pred_base = baseline_model.predict(X_test)
    y_prob_base = baseline_model.predict_proba(X_test)[:, 1]

    # 2. Resampling with SMOTE for imbalanced class handling
    # Use k_neighbors=3 or min count if minority class is small
    minority_count = sum(y_train == 1)
    k_neighbors = min(3, minority_count - 1) if minority_count > 1 else 1
    smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

    print(f"SMOTE applied: Training size expanded from {len(X_train)} to {len(X_train_resampled)}.")
    print("Resampled class distribution:\n", pd.Series(y_train_resampled).value_counts())

    # 3. XGBoost Model with SMOTE
    smote_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        eval_metric="logloss"
    )
    smote_model.fit(X_train_resampled, y_train_resampled)
    y_pred_smote = smote_model.predict(X_test)
    y_prob_smote = smote_model.predict_proba(X_test)[:, 1]

    # Compare Metrics
    metrics = {
        "baseline_without_smote": {
            "accuracy": round(float(accuracy_score(y_test, y_pred_base)), 4),
            "precision": round(float(precision_score(y_test, y_pred_base, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred_base, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred_base, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, y_prob_base)), 4)
        },
        "with_smote_balanced": {
            "accuracy": round(float(accuracy_score(y_test, y_pred_smote)), 4),
            "precision": round(float(precision_score(y_test, y_pred_smote, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred_smote, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred_smote, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, y_prob_smote)), 4)
        },
        "feature_names": FEATURE_COLUMNS
    }

    # Save best model (SMOTE model)
    model_path = "models/xgboost_matcher.json"
    smote_model.save_model(model_path)

    metrics_path = "models/model_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n--- Training Results ---")
    print(json.dumps(metrics, indent=2))
    print(f"Trained XGBoost model saved to {model_path}")
    return smote_model, metrics

if __name__ == "__main__":
    train_and_evaluate_model()
