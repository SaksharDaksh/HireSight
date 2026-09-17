import re
from typing import Dict, List, Any, Set

class StructuredExtractor:
    """
    Structured extraction of candidate profiles and job requirements
    following Section 6 schema of the specification.
    """

    def __init__(self):
        # Comprehensive tech skills taxonomy
        self.skill_taxonomy = {
            "programming_languages": [
                "Python", "C++", "C#", "C", "Java", "JavaScript", "TypeScript", "Go", "Rust", "SQL", "R", "Bash"
            ],
            "ml_and_data_science": [
                "Machine Learning", "Deep Learning", "Scikit-Learn", "XGBoost", "LightGBM", "SHAP", "SMOTE",
                "Pandas", "NumPy", "PyTorch", "TensorFlow", "Keras", "Transformers", "NLP", "Computer Vision",
                "HuggingFace", "RAG", "Vector Databases", "EDA", "Statistical Testing", "A/B Testing"
            ],
            "databases_and_storage": [
                "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "ChromaDB"
            ],
            "cloud_and_devops": [
                "AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Ansible", "Prometheus", "Git", "GitHub"
            ],
            "web_and_apis": [
                "Flask", "FastAPI", "Django", "React", "HTML", "CSS", "REST APIs", "GraphQL", "Microservices", "Next.js", "Node.js"
            ],
            "bi_and_visualization": [
                "Power BI", "Tableau", "Matplotlib", "Seaborn", "Excel", "DAX", "Data Visualization"
            ]
        }

        # Flattened canonical dictionary with lowercase mapping
        self.flat_skills: Dict[str, str] = {}
        for category, skills in self.skill_taxonomy.items():
            for s in skills:
                self.flat_skills[s.lower()] = s

        # Regular expressions for demographic/profile fields
        self.email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
        self.phone_pattern = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
        self.exp_pattern = re.compile(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?", re.IGNORECASE)
        self.degree_pattern = re.compile(r"\b(bachelor'?s?|master'?s?|phd|b\.?s\.?|m\.?s\.?|b\.?tech|m\.?tech|associate|diploma)\b", re.IGNORECASE)
        self.prestige_institutions = [
            "Stanford University", "MIT", "Harvard University", "Oxford University",
            "Cambridge University", "UC Berkeley", "IIT Delhi", "IIT Kharagpur",
            "Yale University", "Tsinghua University"
        ]

    def extract_skills(self, text: str) -> List[str]:
        """Extract all recognized technical skills matching taxonomy."""
        extracted: Set[str] = set()
        cleaned_text = re.sub(r"[,/|()]", " ", text)
        words = cleaned_text.split()

        # 1. Single-word matching
        for word in words:
            w_clean = word.strip(".,;:!?-\"\'").lower()
            if w_clean in self.flat_skills:
                extracted.add(self.flat_skills[w_clean])

        # 2. Multi-word phrase matching (e.g., "Machine Learning", "Power BI", "Scikit-Learn", "REST APIs")
        lower_text = text.lower()
        for skill_lower, canonical_name in self.flat_skills.items():
            if " " in skill_lower or "-" in skill_lower:
                # Word boundary check for multi-word skill
                pattern = r"\b" + re.escape(skill_lower) + r"\b"
                if re.search(pattern, lower_text):
                    extracted.add(canonical_name)

        return sorted(list(extracted))

    def extract_years_experience(self, text: str) -> int:
        """Heuristic extraction of candidate's total years of experience."""
        matches = self.exp_pattern.findall(text)
        if matches:
            years = [int(m[0]) for m in matches if m[0].isdigit() and int(m[0]) <= 40]
            if years:
                return max(years)
        return 0

    def extract_education(self, text: str) -> Dict[str, str]:
        """Extract degree, field, and university/institution."""
        degree = "Bachelor"
        deg_match = self.degree_pattern.search(text)
        if deg_match:
            raw = deg_match.group(1).lower()
            if "phd" in raw:
                degree = "PhD"
            elif "master" in raw or "m." in raw:
                degree = "Master"
            else:
                degree = "Bachelor"

        institution = "Unspecified Institution"
        for inst in self.prestige_institutions:
            if re.search(r"\b" + re.escape(inst) + r"\b", text, re.IGNORECASE):
                institution = inst
                break

        if institution == "Unspecified Institution":
            # Search for generic 'University' or 'College'
            match = re.search(r"([A-Z][a-zA-Z\s]+(?:University|College|Institute|Polytechnic))", text)
            if match:
                institution = match.group(1).strip()

        return {
            "degree": degree,
            "field": "Computer Science / Engineering",
            "institution": institution
        }

    def extract_candidate_name(self, text: str, fallback_id: str = "candidate") -> str:
        """Extract candidate name from header or metadata."""
        match = re.search(r"(?:Candidate\s+Name|Name)\s*:\s*([A-Za-z\s'\-]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        first_line = text.strip().split("\n")[0].strip()
        if len(first_line) < 35 and not any(kw in first_line.lower() for kw in ["resume", "curriculum", "cv"]):
            return first_line
        return fallback_id.replace("_", " ").title()

    def extract_resume_profile(self, text: str, resume_id: str = "") -> Dict[str, Any]:
        """Full structured extraction complying with Section 6 JSON schema."""
        candidate_name = self.extract_candidate_name(text, fallback_id=resume_id)
        skills = self.extract_skills(text)
        years_exp = self.extract_years_experience(text)
        education = self.extract_education(text)

        # Extract contact signals
        email_match = self.email_pattern.search(text)
        phone_match = self.phone_pattern.search(text)

        return {
            "id": resume_id,
            "candidate_name": candidate_name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "years_of_experience": years_exp,
            "skills": skills,
            "education": education,
            "past_roles": [],
            "certifications": [],
            "raw_text": text
        }
