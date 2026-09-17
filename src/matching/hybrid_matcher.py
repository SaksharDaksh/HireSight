import os
import subprocess
import json
import numpy as np
from typing import Dict, List, Any, Optional
from src.embeddings.embed_store import VectorEmbeddingStore
from src.matching.bias_mitigation import BiasMitigator

class HybridMatcher:
    """
    Hybrid Matching Engine implementing Step 1-4 of Section 7:
    - Toggleable hard/soft filters
    - Vector semantic similarity
    - Structured required/preferred skill overlap
    - Experience delta scoring
    - C++ accelerated scoring integration
    """

    def __init__(self, embed_store: Optional[VectorEmbeddingStore] = None):
        self.embed_store = embed_store or VectorEmbeddingStore()
        self.bias_mitigator = BiasMitigator()
        self.cpp_binary_path = os.path.join(os.path.dirname(__file__), "..", "core_cpp", "fast_matcher.exe")

    def run_cpp_similarity(self, text_a: str, text_b: str) -> Optional[Dict[str, float]]:
        """Call native C++ FastMatcher binary if compiled."""
        if not os.path.exists(self.cpp_binary_path):
            return None
        try:
            cmd = [
                self.cpp_binary_path,
                "--hybrid",
                text_a[:1000].replace("\n", " "),
                text_b[:1000].replace("\n", " ")
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                data = json.loads(result.stdout.strip())
                return data
        except Exception:
            return None
        return None

    def compute_skill_overlap(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Compute weighted skill overlap:
        - Required skills: 70% weight
        - Preferred skills: 30% weight
        """
        cand_set = {s.lower() for s in candidate_skills}
        req_set = {s.lower() for s in required_skills}
        pref_set = {s.lower() for s in preferred_skills}

        matched_req = [s for s in required_skills if s.lower() in cand_set]
        missing_req = [s for s in required_skills if s.lower() not in cand_set]

        matched_pref = [s for s in preferred_skills if s.lower() in cand_set]
        missing_pref = [s for s in preferred_skills if s.lower() not in cand_set]

        req_score = len(matched_req) / len(req_set) if req_set else 1.0
        pref_score = len(matched_pref) / len(pref_set) if pref_set else 1.0

        if req_set and pref_set:
            overlap_score = (0.7 * req_score) + (0.3 * pref_score)
        elif req_set:
            overlap_score = req_score
        elif pref_set:
            overlap_score = pref_score
        else:
            overlap_score = 0.5

        return {
            "score": float(overlap_score),
            "matched_required": matched_req,
            "missing_required": missing_req,
            "matched_preferred": matched_pref,
            "missing_preferred": missing_pref,
            "all_matched": matched_req + matched_pref,
            "all_missing": missing_req + missing_pref
        }

    def compute_experience_match(self, candidate_years: int, required_years: int) -> float:
        """Score based on years of experience relative to requirement."""
        if required_years <= 0:
            return 1.0
        if candidate_years >= required_years:
            # Full score, slight bonus for extra experience up to +3 years
            bonus = min(0.1, (candidate_years - required_years) * 0.02)
            return float(min(1.0, 0.9 + bonus))
        else:
            # Deficit penalty proportional to gap
            ratio = candidate_years / required_years
            return float(max(0.1, ratio * 0.8))

    def evaluate_candidate(
        self,
        candidate_profile: Dict[str, Any],
        jd: Dict[str, Any],
        weights: Dict[str, float] = None,
        filter_mode: str = "soft",  # "strict" or "soft"
        apply_bias_mitigation: bool = False
    ) -> Dict[str, Any]:
        """
        Score and analyze a single candidate against a JD.
        """
        weights = weights or {"w_semantic": 0.45, "w_skills": 0.40, "w_experience": 0.15}
        total_w = sum(weights.values())
        w_sem = weights.get("w_semantic", 0.45) / total_w
        w_skl = weights.get("w_skills", 0.40) / total_w
        w_exp = weights.get("w_experience", 0.15) / total_w

        resume_text = candidate_profile.get("raw_text", "")
        candidate_name = candidate_profile.get("candidate_name", "Candidate")
        redactions = {}

        if apply_bias_mitigation:
            resume_text, redactions = self.bias_mitigator.strip_demographics(
                resume_text, candidate_name=candidate_name
            )

        # 1. Hard Filter Check
        req_years = jd.get("min_years_experience", 0)
        cand_years = candidate_profile.get("years_of_experience", 0)
        hard_pass = cand_years >= req_years

        if filter_mode == "strict" and not hard_pass:
            return {
                "id": candidate_profile.get("id"),
                "candidate_name": "[Redacted]" if apply_bias_mitigation else candidate_name,
                "passed_hard_filters": False,
                "failure_reason": f"Required {req_years} years exp, candidate has {cand_years}",
                "final_score": 0.0,
                "semantic_score": 0.0,
                "skill_overlap_score": 0.0,
                "experience_score": 0.0,
                "matched_skills": [],
                "missing_skills": jd.get("required_skills", []),
                "redactions": redactions
            }

        # 2. Semantic Similarity
        # Check C++ engine first
        cpp_res = self.run_cpp_similarity(resume_text, jd.get("description", ""))
        if cpp_res and "cosine" in cpp_res:
            semantic_score = cpp_res["cosine"]
            engine_used = "C++17 FastMatcher"
        else:
            semantic_score = self.embed_store.compute_pair_similarity(
                resume_text, jd.get("description", "")
            )
            engine_used = "Scikit-Learn TF-IDF"

        # 3. Structured Skill Overlap
        skill_analysis = self.compute_skill_overlap(
            candidate_skills=candidate_profile.get("skills", []),
            required_skills=jd.get("required_skills", []),
            preferred_skills=jd.get("preferred_skills", [])
        )
        skill_score = skill_analysis["score"]

        # 4. Experience Match
        exp_score = self.compute_experience_match(cand_years, req_years)

        # 5. Final Score Fusion
        raw_final = (w_sem * semantic_score) + (w_skl * skill_score) + (w_exp * exp_score)
        
        # In legacy unmitigated mode, prestige university keywords artificially inflate scores
        prestige_bonus = 0.0
        if not apply_bias_mitigation:
            inst = candidate_profile.get("institution", "") or candidate_profile.get("education", {}).get("institution", "")
            raw_t = candidate_profile.get("raw_text", "")
            if any(p in inst or p in raw_t for p in ["Stanford", "Harvard", "MIT", "Oxford", "Cambridge", "Yale", "Berkeley"]):
                prestige_bonus = 0.07
                raw_final = min(1.0, raw_final + prestige_bonus)

        # Check for data sparsity (Credibility signal: "Not confident" handling)
        resume_words = len(resume_text.split())
        jd_words = len(jd.get("description", "").split())
        skills_detected = len(candidate_profile.get("skills", []))
        
        is_confident = True
        confidence_status = "High Confidence"
        confidence_reason = "Sufficient technical profile and tenure details verified."

        if resume_words < 20 or jd_words < 15:
            is_confident = False
            confidence_status = "Not Confident: Data Too Sparse"
            confidence_reason = f"Source text contains only {resume_words} words (JD: {jd_words} words), which is insufficient for an objective evaluation."
        elif skills_detected == 0:
            is_confident = False
            confidence_status = "Not Confident: No Technical Skills Detected"
            confidence_reason = "No verifiable technical competencies or skills could be extracted from the resume text."

        # In soft filter mode, apply 20% penalty if failing hard constraints
        if not hard_pass and filter_mode == "soft":
            final_score = raw_final * 0.8
        else:
            final_score = raw_final

        return {
            "id": candidate_profile.get("id"),
            "candidate_name": "[Redacted]" if apply_bias_mitigation else candidate_name,
            "years_experience": cand_years,
            "degree": candidate_profile.get("education", {}).get("degree", "Bachelor"),
            "institution": "[Redacted]" if apply_bias_mitigation else candidate_profile.get("education", {}).get("institution", ""),
            "passed_hard_filters": hard_pass,
            "semantic_score": round(float(semantic_score), 4),
            "skill_overlap_score": round(float(skill_score), 4),
            "experience_score": round(float(exp_score), 4),
            "final_score": round(float(final_score), 4),
            "engine_used": engine_used,
            "matched_skills": skill_analysis["all_matched"],
            "missing_skills": skill_analysis["missing_required"],
            "matched_required": skill_analysis["matched_required"],
            "missing_required": skill_analysis["missing_required"],
            "matched_preferred": skill_analysis["matched_preferred"],
            "missing_preferred": skill_analysis["missing_preferred"],
            "is_confident": is_confident,
            "confidence_status": confidence_status,
            "confidence_reason": confidence_reason,
            "redactions": redactions
        }

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        jd: Dict[str, Any],
        weights: Dict[str, float] = None,
        filter_mode: str = "soft",
        apply_bias_mitigation: bool = False
    ) -> List[Dict[str, Any]]:
        """Rank an entire pool of candidates against a JD."""
        evals = [
            self.evaluate_candidate(
                cand, jd, weights=weights, filter_mode=filter_mode, apply_bias_mitigation=apply_bias_mitigation
            )
            for cand in candidates
        ]
        # Sort descending by final_score
        evals.sort(key=lambda x: x["final_score"], reverse=True)
        for idx, item in enumerate(evals):
            item["rank"] = idx + 1
        return evals
