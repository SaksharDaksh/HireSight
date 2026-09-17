import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import base64
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/web rendering
import matplotlib.pyplot as plt
import xgboost as xgb
import shap

from src.ml.train_xgboost import FEATURE_COLUMNS

class MatchSHAPExplainer:
    """
    Model Explainability layer using SHAP (SHapley Additive exPlanations)
    and Matplotlib for rendering feature contributions for candidate matches.
    """

    def __init__(self, model_path: str = "models/xgboost_matcher.json"):
        self.model = xgb.XGBClassifier()
        if os.path.exists(model_path):
            self.model.load_model(model_path)
        else:
            raise FileNotFoundError(f"Trained XGBoost model not found at {model_path}. Run train_xgboost.py first.")

        self.explainer = shap.TreeExplainer(self.model)
        self.feature_names = FEATURE_COLUMNS

    def explain_candidate(
        self,
        features_dict: dict,
        output_image_path: str = None
    ) -> dict:
        """
        Explain a single candidate match prediction using SHAP.
        Returns feature contributions and base64 encoded plot.
        """
        # Ensure correct column ordering
        row = [features_dict.get(col, 0.0) for col in self.feature_names]
        X_sample = pd.DataFrame([row], columns=self.feature_names)

        # Compute SHAP values
        shap_values = self.explainer(X_sample)
        values = shap_values.values[0]
        base_value = float(shap_values.base_values[0]) if hasattr(shap_values, "base_values") else 0.0

        # Create sorted attribution pairs
        contributions = []
        for name, val, f_val in zip(self.feature_names, values, row):
            contributions.append({
                "feature": name,
                "value": float(f_val),
                "shap_impact": round(float(val), 4),
                "direction": "positive" if val >= 0 else "negative"
            })

        # Sort by absolute impact
        contributions.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)

        # Generate Matplotlib Bar Chart
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
        
        # Color positive drivers emerald green and negative detractors crimson
        y_pos = np.arange(len(contributions))
        feature_labels = [c["feature"].replace("_", " ").title() for c in reversed(contributions)]
        impacts = [c["shap_impact"] for c in reversed(contributions)]
        colors = ["#10b981" if imp >= 0 else "#ef4444" for imp in impacts]

        bars = ax.barh(y_pos, impacts, color=colors, height=0.6, edgecolor="#334155", linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(feature_labels, fontsize=9, fontweight="medium")
        ax.axvline(0, color="#64748b", linestyle="--", linewidth=1.0)
        ax.set_xlabel("SHAP Value (Impact on Match Fit)", fontsize=10, fontweight="bold")
        ax.set_title("Feature Attribution Breakdown (SHAP)", fontsize=11, fontweight="bold", pad=12)
        ax.grid(axis="x", linestyle=":", alpha=0.6)

        # Annotate values on bars
        for bar, imp in zip(bars, impacts):
            x_val = bar.get_width()
            offset = 0.01 if imp >= 0 else -0.01
            ha = "left" if imp >= 0 else "right"
            ax.text(x_val + offset, bar.get_y() + bar.get_height()/2, f"{imp:+.2f}",
                    va="center", ha=ha, fontsize=8, color="#0f172a", fontweight="semibold")

        plt.tight_layout()

        # Render to base64
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")

        # Save to file if path requested
        if output_image_path:
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            with open(output_image_path, "wb") as f:
                buf.seek(0)
                f.write(buf.read())

        return {
            "base_value": round(base_value, 4),
            "top_positive_drivers": [c for c in contributions if c["direction"] == "positive"][:3],
            "top_negative_detractors": [c for c in contributions if c["direction"] == "negative"][:3],
            "all_contributions": contributions,
            "chart_base64": f"data:image/png;base64,{img_base64}"
        }

if __name__ == "__main__":
    explainer = MatchSHAPExplainer()
    sample_feat = {
        "semantic_similarity": 0.85,
        "required_skill_overlap": 0.90,
        "preferred_skill_overlap": 0.60,
        "skills_count": 8,
        "candidate_exp_years": 4,
        "required_exp_years": 3,
        "experience_delta": 1,
        "hard_constraint_met": 1.0,
        "degree_requirement_met": 1.0
    }
    res = explainer.explain_candidate(sample_feat, output_image_path="reports/sample_shap_waterfall.png")
    print("SHAP Base Value:", res["base_value"])
    print("Top Positive Drivers:", res["top_positive_drivers"])
    print("Top Negative Detractors:", res["top_negative_detractors"])
    print("Generated plot saved to reports/sample_shap_waterfall.png")
