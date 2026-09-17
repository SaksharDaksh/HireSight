import re
from typing import Dict, List, Any, Tuple

class BiasMitigator:
    """
    Implements demographic signal stripping and before/after fairness audit
    as detailed in Section 8 of the project specification.
    """

    def __init__(self):
        # Gendered pronouns & titles
        self.gender_patterns = [
            (re.compile(r"\b(he|she)\b", re.IGNORECASE), "they"),
            (re.compile(r"\b(him|her)\b", re.IGNORECASE), "them"),
            (re.compile(r"\b(his|hers?)\b", re.IGNORECASE), "their"),
            (re.compile(r"\b(himself|herself)\b", re.IGNORECASE), "themselves"),
            (re.compile(r"\b(mr\.|mrs\.|ms\.|miss)\b", re.IGNORECASE), "Candidate")
        ]

        # Age and graduation year indicators (e.g., "graduated in 1995", "class of 2002", "aged 45")
        self.age_patterns = [
            (re.compile(r"\b(?:class\s+of|graduated\s+in|year\s+of\s+graduation:?)\s*(?:19|20)\d{2}\b", re.IGNORECASE), "[Graduation Year Redacted]"),
            (re.compile(r"\b(?:age|aged)\s*[:=]?\s*\d{2}\b", re.IGNORECASE), "[Age Redacted]"),
            (re.compile(r"\b(19[6-9]\d|200\d)\b"), "[Year Redacted]")
        ]

        # Prestige institutions known to introduce socioeconomic bias
        self.prestige_institutions = {
            "Stanford University": "Accredited Premier University",
            "Stanford": "Accredited Premier University",
            "Harvard University": "Accredited Premier University",
            "Harvard": "Accredited Premier University",
            "MIT": "Accredited Premier University",
            "Massachusetts Institute of Technology": "Accredited Premier University",
            "Oxford University": "Accredited Premier University",
            "Cambridge University": "Accredited Premier University",
            "UC Berkeley": "Accredited Premier University",
            "Yale University": "Accredited Premier University",
            "IIT Delhi": "Accredited Premier University",
            "IIT Kharagpur": "Accredited Premier University"
        }

    def strip_demographics(self, text: str, candidate_name: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Mask candidate name, gendered pronouns, age indicators, and prestige institutions.
        Returns: (sanitized_text, audit_log_of_redactions)
        """
        redactions = {
            "name_masked": False,
            "pronouns_replaced": 0,
            "age_indicators_redacted": 0,
            "institutions_anonymized": []
        }

        sanitized = text

        # 1. Mask Candidate Name
        if candidate_name and len(candidate_name) > 2:
            # Mask full name
            name_pat = re.compile(re.escape(candidate_name), re.IGNORECASE)
            if name_pat.search(sanitized):
                sanitized = name_pat.sub("[Candidate Anonymized]", sanitized)
                redactions["name_masked"] = True

            # Also mask individual parts if 2+ words
            parts = candidate_name.split()
            if len(parts) >= 2:
                for part in parts:
                    if len(part) > 2:
                        p_pat = re.compile(r"\b" + re.escape(part) + r"\b", re.IGNORECASE)
                        sanitized = p_pat.sub("[Name Redacted]", sanitized)

        # 2. Neutralize Gendered Pronouns
        for pat, replacement in self.gender_patterns:
            matches = pat.findall(sanitized)
            if matches:
                redactions["pronouns_replaced"] += len(matches)
                sanitized = pat.sub(replacement, sanitized)

        # 3. Strip Age & Graduation Timelines
        for pat, replacement in self.age_patterns:
            matches = pat.findall(sanitized)
            if matches:
                redactions["age_indicators_redacted"] += len(matches)
                sanitized = pat.sub(replacement, sanitized)

        # 4. Anonymize Prestige Institutions
        for inst, generic in self.prestige_institutions.items():
            pattern = re.compile(r"\b" + re.escape(inst) + r"\b", re.IGNORECASE)
            if pattern.search(sanitized):
                sanitized = pattern.sub(generic, sanitized)
                if inst not in redactions["institutions_anonymized"]:
                    redactions["institutions_anonymized"].append(inst)

        return sanitized, redactions

    def compute_fairness_audit(
        self,
        raw_ranked_candidates: List[Dict[str, Any]],
        mitigated_ranked_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Quantifies ranking and score shifts when bias mitigation is toggled on vs off.
        """
        # Map IDs to original rank and score
        orig_map = {c["id"]: {"rank": idx + 1, "score": c["final_score"]} for idx, c in enumerate(raw_ranked_candidates)}
        
        comparison = []
        rank_shifts = []

        for idx, cand in enumerate(mitigated_ranked_candidates):
            cid = cand["id"]
            orig_info = orig_map.get(cid, {"rank": idx + 1, "score": cand["final_score"]})
            orig_rank = orig_info["rank"]
            new_rank = idx + 1
            rank_delta = orig_rank - new_rank  # Positive means candidate improved in rank

            orig_score = orig_info["score"]
            new_score = cand["final_score"]
            score_delta = round(new_score - orig_score, 4)

            rank_shifts.append(abs(rank_delta))
            comparison.append({
                "candidate_id": cid,
                "candidate_name": cand.get("candidate_name", cid),
                "original_rank": orig_rank,
                "mitigated_rank": new_rank,
                "rank_delta": rank_delta,
                "original_score": round(orig_score, 3),
                "mitigated_score": round(new_score, 3),
                "score_delta": score_delta,
                "shifted": rank_delta != 0
            })

        avg_shift = float(sum(rank_shifts) / len(rank_shifts)) if rank_shifts else 0.0
        max_shift = max(rank_shifts) if rank_shifts else 0
        total_shifted_candidates = sum(1 for item in comparison if item["shifted"])

        return {
            "comparison": comparison,
            "average_rank_shift": round(avg_shift, 2),
            "max_rank_shift": max_shift,
            "total_candidates_shifted": total_shifted_candidates,
            "impact_summary": (
                f"Bias mitigation caused rank shifts in {total_shifted_candidates} of {len(comparison)} candidates "
                f"with an average movement of {round(avg_shift, 1)} positions."
            )
        }
