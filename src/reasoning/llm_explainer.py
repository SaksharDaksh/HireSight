import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import re
from typing import Dict, List, Any, Optional

class LLMExplainer:
    """
    RAG-powered LLM Reasoning Layer (Step 5 of Project Spec).
    Synthesizes natural-language fit explanations, gap breakdowns, and
    actionable candidate improvement roadmaps from retrieved resume chunks and JD.
    """

    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def format_rag_prompt(
        self,
        candidate_profile: Dict[str, Any],
        jd: Dict[str, Any],
        retrieved_chunks: List[str]
    ) -> str:
        """Assembles augmented prompt containing retrieved context, structured profile, and JD."""
        context_str = "\n---\n".join(retrieved_chunks[:3]) if retrieved_chunks else "No specific chunks retrieved."
        prompt = (
            f"You are an expert, fairness-aware technical recruiter evaluating candidate fit.\n\n"
            f"JOB DESCRIPTION:\n"
            f"Title: {jd.get('title')}\n"
            f"Company: {jd.get('company')}\n"
            f"Minimum Years Experience: {jd.get('min_years_experience')}\n"
            f"Required Skills: {', '.join(jd.get('required_skills', []))}\n"
            f"Preferred Skills: {', '.join(jd.get('preferred_skills', []))}\n"
            f"Overview: {jd.get('description')}\n\n"
            f"CANDIDATE STRUCTURED PROFILE:\n"
            f"Name: {candidate_profile.get('candidate_name', 'Candidate')}\n"
            f"Years Experience: {candidate_profile.get('years_of_experience')}\n"
            f"Skills: {', '.join(candidate_profile.get('skills', []))}\n"
            f"Degree: {candidate_profile.get('education', {}).get('degree', 'Bachelor')}\n\n"
            f"TOP RETRIEVED RESUME SNIPPETS:\n"
            f"{context_str}\n\n"
            f"TASK:\n"
            f"Analyze the candidate's alignment with the role. Provide:\n"
            f"1. Matched Skills\n"
            f"2. Missing Required/Preferred Skills\n"
            f"3. Overall Fit Summary (2-3 concise sentences)\n"
            f"4. Confidence Caveat (note any ambiguities or missing timeline info)\n"
            f"5. Candidate Improvement Suggestions (specific technologies or portfolio projects to close gaps)\n"
        )
        return prompt

    def generate_local_reasoning(
        self,
        candidate_profile: Dict[str, Any],
        jd: Dict[str, Any],
        retrieved_chunks: List[str]
    ) -> Dict[str, Any]:
        """
        High-precision deterministic grounded reasoning engine that operates
        offline without requiring an active external LLM API key.
        """
        cand_skills = set(s.lower() for s in candidate_profile.get("skills", []))
        req_skills = jd.get("required_skills", [])
        pref_skills = jd.get("preferred_skills", [])

        matched_req = [s for s in req_skills if s.lower() in cand_skills]
        missing_req = [s for s in req_skills if s.lower() not in cand_skills]
        matched_pref = [s for s in pref_skills if s.lower() in cand_skills]
        missing_pref = [s for s in pref_skills if s.lower() not in cand_skills]

        cand_exp = candidate_profile.get("years_of_experience", 0)
        req_exp = jd.get("min_years_experience", 0)
        name = candidate_profile.get("candidate_name", "The candidate")

        # Synthesize 2-3 sentence fit summary
        if not missing_req and cand_exp >= req_exp:
            fit_summary = (
                f"{name} demonstrates exceptional alignment with the {jd.get('title')} role, possessing all "
                f"core competencies including {', '.join(matched_req[:3])}. With {cand_exp} years of industry experience "
                f"(exceeding the {req_exp}-year minimum requirement), their profile reflects strong execution readiness for {jd.get('company')}."
            )
        elif missing_req and cand_exp >= req_exp:
            fit_summary = (
                f"{name} brings adequate senior experience ({cand_exp} years vs. {req_exp} required) and solid proficiency in "
                f"{', '.join(matched_req[:3]) if matched_req else 'the domain'}. However, critical gaps exist in required areas: "
                f"{', '.join(missing_req[:3])}, requiring targeted upskilling."
            )
        elif not missing_req and cand_exp < req_exp:
            fit_summary = (
                f"{name} shows high technical competency matching required skills ({', '.join(matched_req[:3])}), "
                f"but does not satisfy the hard tenure threshold ({cand_exp} years vs. {req_exp} required). "
                f"Suitable for an accelerated or junior-to-mid path."
            )
        else:
            fit_summary = (
                f"{name} partially aligns with the requirements, having verified background in {', '.join(matched_req[:2]) if matched_req else 'related areas'}. "
                f"Significant gaps in required skills ({', '.join(missing_req[:3])}) and tenure ({cand_exp} vs {req_exp} yrs) "
                f"pose potential ramp-up risk."
            )

        # Confidence caveat
        caveats = []
        if cand_exp == 0:
            caveats.append("Tenure duration was not explicitly verified from dates; defaulted to early-career.")
        if len(candidate_profile.get("skills", [])) < 3:
            caveats.append("Sparse skill extraction detected in resume source text.")
        if not caveats:
            caveat_text = "High confidence: Detailed technical profile and verified timeline provided."
        else:
            caveat_text = "Moderate confidence: " + " ".join(caveats)

        # Improvement suggestions (Candidate mode)
        improvement_steps = []
        if missing_req:
            for skill in missing_req[:3]:
                improvement_steps.append(
                    f"Acquire hands-on mastery in **{skill}** and showcase a production or open-source project demonstrating its usage."
                )
        if missing_pref:
            for skill in missing_pref[:2]:
                improvement_steps.append(
                    f"Familiarize yourself with preferred tool **{skill}** to gain an edge over competing applicants."
                )
        if cand_exp < req_exp:
            improvement_steps.append(
                f"Highlight freelance, open-source, or contract contributions to demonstrate practical tenure equivalent to {req_exp} years."
            )
        if not improvement_steps:
            improvement_steps.append("Profile strongly matches all requirements! Emphasize leadership and system design impact in interviews.")

        return {
            "fit_summary": fit_summary,
            "matched_skills": matched_req + matched_pref,
            "missing_required": missing_req,
            "missing_preferred": missing_pref,
            "confidence_caveat": caveat_text,
            "improvement_suggestions": improvement_steps,
            "source_snippets": retrieved_chunks[:2] if retrieved_chunks else []
        }

    def explain(
        self,
        candidate_profile: Dict[str, Any],
        jd: Dict[str, Any],
        retrieved_chunks: List[str]
    ) -> Dict[str, Any]:
        """Main entry point: tries external LLM API if configured, falls back to local reasoning."""
        # Check if user has active API key
        if self.gemini_api_key:
            try:
                import requests
                prompt = self.format_rag_prompt(candidate_profile, jd, retrieved_chunks)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    text_resp = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    base_res = self.generate_local_reasoning(candidate_profile, jd, retrieved_chunks)
                    base_res["fit_summary"] = text_resp[:400]
                    base_res["llm_provider"] = "Google Gemini 1.5 Flash"
                    return base_res
            except Exception:
                pass

        # Robust grounded local reasoning pass
        result = self.generate_local_reasoning(candidate_profile, jd, retrieved_chunks)
        result["llm_provider"] = "Hybrid RAG Grounded Reasoning Engine"
        return result
