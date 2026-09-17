import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import glob
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from src.extraction.structured_extractor import StructuredExtractor
from src.embeddings.embed_store import VectorEmbeddingStore

class FeatureDatasetGenerator:
    """
    Constructs tabular feature vectors for candidate-job pairs
    for supervised ML ranking and classification.
    """

    def __init__(self):
        self.extractor = StructuredExtractor()
        self.embed_store = VectorEmbeddingStore()
        self.degree_hierarchy = {"Bachelor": 1, "Master": 2, "PhD": 3}

    def extract_pair_features(
        self,
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        ground_truth_label: int
    ) -> Dict[str, Any]:
        """Convert a resume-JD pair into a numerical feature vector."""
        cand_skills = set(s.lower() for s in resume_data.get("skills", []))
        req_skills = set(s.lower() for s in jd_data.get("required_skills", []))
        pref_skills = set(s.lower() for s in jd_data.get("preferred_skills", []))

        # 1. Overlap ratios
        matched_req = cand_skills.intersection(req_skills)
        matched_pref = cand_skills.intersection(pref_skills)
        req_ratio = len(matched_req) / len(req_skills) if req_skills else 1.0
        pref_ratio = len(matched_pref) / len(pref_skills) if pref_skills else 1.0

        # 2. Semantic text similarity
        resume_text = resume_data.get("raw_text", resume_data.get("summary", ""))
        jd_text = jd_data.get("description", "")
        sem_sim = self.embed_store.compute_pair_similarity(resume_text, jd_text)

        # 3. Experience & education features
        cand_exp = resume_data.get("years_experience", resume_data.get("years_of_experience", 0))
        min_exp = jd_data.get("min_years_experience", 0)
        exp_delta = cand_exp - min_exp
        hard_pass = 1.0 if cand_exp >= min_exp else 0.0

        cand_deg = resume_data.get("degree", "Bachelor")
        req_deg = jd_data.get("degree_required", "Bachelor")
        cand_deg_val = self.degree_hierarchy.get(cand_deg, 1)
        req_deg_val = self.degree_hierarchy.get(req_deg, 1)
        degree_match = 1.0 if cand_deg_val >= req_deg_val else 0.0

        return {
            "resume_id": resume_data.get("id"),
            "jd_id": jd_data.get("id"),
            "semantic_similarity": round(float(sem_sim), 4),
            "required_skill_overlap": round(float(req_ratio), 4),
            "preferred_skill_overlap": round(float(pref_ratio), 4),
            "skills_count": len(cand_skills),
            "candidate_exp_years": cand_exp,
            "required_exp_years": min_exp,
            "experience_delta": exp_delta,
            "hard_constraint_met": hard_pass,
            "degree_requirement_met": degree_match,
            "target_match": int(ground_truth_label)
        }

    def build_dataset(
        self,
        resumes_dir: str = "data/resumes",
        jds_dir: str = "data/job_descriptions",
        eval_path: str = "data/eval_labels.json"
    ) -> pd.DataFrame:
        """Pair all resumes with JDs to build a comprehensive feature dataset."""
        # Load JDs
        jds = []
        for f in glob.glob(os.path.join(jds_dir, "*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                jds.append(json.load(fp))

        # Load resumes
        resumes = []
        for f in glob.glob(os.path.join(resumes_dir, "*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                resumes.append(json.load(fp))

        # Load labels
        eval_data = {}
        if os.path.exists(eval_path):
            with open(eval_path, "r", encoding="utf-8") as fp:
                eval_data = json.load(fp)

        records = []
        for jd in jds:
            jd_id = jd["id"]
            top_candidates = eval_data.get(jd_id, {}).get("top_candidates", [])
            for res in resumes:
                res_id = res["id"]
                # Positive label if candidate is a verified top match or role aligns
                is_match = 1 if res_id in top_candidates else 0

                # Heuristic labeling for additional synthetic pairs
                cand_target = res.get("target_role", "").lower()
                jd_title = jd.get("title", "").lower()
                if not is_match and (cand_target in jd_title or jd_title in cand_target):
                    if res.get("years_experience", 0) >= jd.get("min_years_experience", 0):
                        is_match = 1

                feat = self.extract_pair_features(res, jd, is_match)
                records.append(feat)

        df = pd.DataFrame(records)
        return df

if __name__ == "__main__":
    generator = FeatureDatasetGenerator()
    df = generator.build_dataset()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/training_features.csv", index=False)
    print(f"Generated feature dataset with {len(df)} samples.")
    print("Class distribution:\n", df["target_match"].value_counts(normalize=True))
