import os
import json

def create_notebook():
    os.makedirs("notebooks", exist_ok=True)
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Fairness-Aware Resume ↔ Job Description Matcher\n",
                    "## Exploratory Data Analysis (EDA), SMOTE, XGBoost & SHAP Explainability\n",
                    "\n",
                    "This notebook demonstrates the end-to-end Machine Learning, Data Science, and Bias Mitigation pipeline:\n",
                    "1. **Exploratory Data Analysis (EDA)**: Parsing resumes and job descriptions, analyzing skill distributions and candidate experience.\n",
                    "2. **Handling Class Imbalance with SMOTE**: Resampling the severe imbalance between qualified candidate matches and non-matches.\n",
                    "3. **Supervised Modeling with XGBoost**: Training a gradient boosted decision tree classifier/ranker.\n",
                    "4. **Model Explainability with SHAP**: Decomposing individual candidate match decisions into mathematically grounded feature attributions.\n",
                    "5. **Demographic Bias Mitigation Audit**: Measuring ranking and score shifts when demographic and prestige signals are stripped."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os\n",
                    "import sys\n",
                    "import json\n",
                    "import glob\n",
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "import matplotlib.pyplot as plt\n",
                    "from collections import Counter\n",
                    "\n",
                    "# Scikit-Learn & ML Stack\n",
                    "from sklearn.model_selection import train_test_split\n",
                    "from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix\n",
                    "from imblearn.over_sampling import SMOTE\n",
                    "import xgboost as xgb\n",
                    "import shap\n",
                    "\n",
                    "print('All libraries successfully imported!')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Data Ingestion & Exploratory Data Analysis (EDA)\n",
                    "Let's load the structured training dataset generated from candidate-job pairings."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "df = pd.read_csv('../data/training_features.csv')\n",
                    "print(f'Total Samples: {len(df)}')\n",
                    "df.head()"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Class distribution check - Demonstrating Severe Imbalance\n",
                    "class_counts = df['target_match'].value_counts()\n",
                    "print('Target Match Distribution:')\n",
                    "print(class_counts)\n",
                    "\n",
                    "plt.figure(figsize=(6, 3.5))\n",
                    "colors = ['#ef4444', '#10b981']\n",
                    "plt.bar(['Non-Match (0)', 'Match (1)'], class_counts.values, color=colors, edgecolor='#1e293b')\n",
                    "plt.title('Severe Class Imbalance in Candidate-Job Pairs', fontsize=12, fontweight='bold')\n",
                    "plt.ylabel('Count')\n",
                    "for i, v in enumerate(class_counts.values):\n",
                    "    plt.text(i, v + 4, str(v), ha='center', fontweight='bold')\n",
                    "plt.grid(axis='y', linestyle=':', alpha=0.6)\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Handling Class Imbalance with SMOTE (Synthetic Minority Over-sampling Technique)\n",
                    "In recruitment screening, only a small fraction of applicants are qualified matches for any specific role (~9%). Standard classifiers easily collapse into predicting non-matches. We use **SMOTE** to synthesize minority match instances."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "feature_cols = [\n",
                    "    'semantic_similarity', 'required_skill_overlap', 'preferred_skill_overlap',\n",
                    "    'skills_count', 'candidate_exp_years', 'required_exp_years',\n",
                    "    'experience_delta', 'hard_constraint_met', 'degree_requirement_met'\n",
                    "]\n",
                    "X = df[feature_cols]\n",
                    "y = df['target_match']\n",
                    "\n",
                    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)\n",
                    "print(f'Raw Training Split: {len(X_train)} samples ({sum(y_train==1)} positive, {sum(y_train==0)} negative)')\n",
                    "\n",
                    "# Apply SMOTE\n",
                    "smote = SMOTE(random_state=42, k_neighbors=min(3, sum(y_train==1)-1))\n",
                    "X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)\n",
                    "\n",
                    "print(f'Balanced with SMOTE: {len(X_train_resampled)} samples ({sum(y_train_resampled==1)} positive, {sum(y_train_resampled==0)} negative)')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Supervised Model Training with XGBoost\n",
                    "We train an `XGBClassifier` on the balanced dataset and evaluate precision, recall, and ROC-AUC."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "model = xgb.XGBClassifier(\n",
                    "    n_estimators=100,\n",
                    "    max_depth=4,\n",
                    "    learning_rate=0.05,\n",
                    "    random_state=42,\n",
                    "    eval_metric='logloss'\n",
                    ")\n",
                    "model.fit(X_train_resampled, y_train_resampled)\n",
                    "\n",
                    "y_pred = model.predict(X_test)\n",
                    "y_prob = model.predict_proba(X_test)[:, 1]\n",
                    "\n",
                    "print('--- Classification Report ---')\n",
                    "print(classification_report(y_test, y_pred))\n",
                    "print(f'ROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}')"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. Model Explainability with SHAP (SHapley Additive exPlanations)\n",
                    "Using `shap.TreeExplainer` to demystify black-box predictions and attribute impact to individual features."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "explainer = shap.TreeExplainer(model)\n",
                    "shap_values = explainer(X_test)\n",
                    "\n",
                    "# Global Feature Importance via SHAP summary plot\n",
                    "plt.figure(figsize=(8, 5))\n",
                    "shap.summary_plot(shap_values, X_test, show=False)\n",
                    "plt.title('Global Feature Importance (SHAP)', fontsize=12, fontweight='bold')\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 5. Demographic Bias Mitigation Audit & Ranking Shift Analysis\n",
                    "Measuring the impact of demographic signal stripping (names, gender pronouns, prestige school bonuses) on ranking stability."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from src.evaluation.evaluate import Evaluator\n",
                    "evaluator = Evaluator(jds_dir='../data/job_descriptions', resumes_dir='../data/resumes', labels_path='../data/eval_labels.json')\n",
                    "results = evaluator.run_benchmark(k=3)\n",
                    "\n",
                    "print('Benchmark Accuracy & Bias Shift Summary:')\n",
                    "print(f'Mean Precision@3: {results[\"mean_precision_at_3\"]*100:.1f}%')\n",
                    "print(f'Mean Reciprocal Rank (MRR): {results[\"mean_mrr\"]:.3f}')\n",
                    "print(f'Overall Average Bias Mitigation Rank Shift: {results[\"overall_avg_bias_rank_shift\"]} positions')\n",
                    "\n",
                    "df_audit = pd.DataFrame(results['detailed_results'])\n",
                    "df_audit[['jd_id', 'title', 'precision_at_k', 'mrr', 'avg_bias_rank_shift', 'candidates_shifted']]"
                ]
            }
        ],
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.14.6"
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open("notebooks/exploration_and_eda.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

    print("Created notebooks/exploration_and_eda.ipynb")

if __name__ == "__main__":
    create_notebook()
