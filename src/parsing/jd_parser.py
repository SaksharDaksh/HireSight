import os
import json
import re
from typing import Dict, Any, List

class JDParser:
    """
    Parses Job Descriptions (from JSON or raw text) into standardized schemas.
    """

    def __init__(self):
        self.exp_pattern = re.compile(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", re.IGNORECASE)
        self.degree_pattern = re.compile(r"\b(bachelor'?s?|master'?s?|phd|b\.?s\.?|m\.?s\.?|b\.?tech|m\.?tech)\b", re.IGNORECASE)

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Load JD from JSON or raw text."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return self.normalize_jd(data)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
                return self.parse_raw_text(raw_text)

    def parse_raw_text(self, text: str, title: str = "Target Position") -> Dict[str, Any]:
        """Extract structured JD attributes from unstructured text."""
        min_exp = 0
        exp_match = self.exp_pattern.search(text)
        if exp_match:
            min_exp = int(exp_match.group(1))

        degree = "Bachelor"
        deg_match = self.degree_pattern.search(text)
        if deg_match:
            d = deg_match.group(1).lower()
            if "phd" in d:
                degree = "PhD"
            elif "master" in d or "m." in d:
                degree = "Master"
            else:
                degree = "Bachelor"

        return {
            "id": f"custom_jd_{abs(hash(text)) % 10000}",
            "title": title,
            "company": "Hiring Organization",
            "department": "Engineering",
            "min_years_experience": min_exp,
            "degree_required": degree,
            "required_skills": [],
            "preferred_skills": [],
            "description": text.strip()
        }

    def normalize_jd(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure standard keys exist."""
        return {
            "id": data.get("id", f"jd_{abs(hash(str(data))) % 10000}"),
            "title": data.get("title", "Position"),
            "company": data.get("company", "Company"),
            "department": data.get("department", "General"),
            "min_years_experience": int(data.get("min_years_experience", 0)),
            "degree_required": data.get("degree_required", "Bachelor"),
            "required_skills": data.get("required_skills", []),
            "preferred_skills": data.get("preferred_skills", []),
            "description": data.get("description", "")
        }
