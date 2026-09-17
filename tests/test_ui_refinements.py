import os
import sys
import io
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from web.app import app

class TestUIRefinements(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_extract_text_txt(self):
        data = {
            'file': (io.BytesIO(b"Candidate Name: Jane Doe\nSkills: Python, C++, Docker\nExperience: 5 years software engineer."), "resume.txt")
        }
        res = self.client.post("/api/extract-text", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("Python", json_data["text"])
        print("[PASS] test_extract_text_txt:", json_data["text"][:50])

    def test_upload_resumes_batch(self):
        data = {
            'files': [
                (io.BytesIO(b"Candidate Name: Alice Smith\nSkills: Python, Machine Learning\nExperience: 4 years as Data Scientist at TechCorp."), "alice.txt"),
                (io.BytesIO(b"Candidate Name: Bob Jones\nSkills: C++, Linux, Multithreading\nExperience: 6 years Systems Developer at SystemsInc."), "bob.txt")
            ]
        }
        res = self.client.post("/api/upload/resumes-batch", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["count"], 2)
        print("[PASS] test_upload_resumes_batch: processed 2 candidates")

    def test_recruiter_match_with_custom_candidates(self):
        jd_text = "Looking for a Senior Python and ML Engineer with 3+ years experience in PyTorch and Docker."
        candidates = [
            {
                "id": "cand_1",
                "candidate_name": "Alice Smith",
                "skills": ["python", "machine learning", "pytorch"],
                "years_experience": 4,
                "degree": "Master",
                "summary": "Experienced ML Engineer with PyTorch and Python.",
                "raw_text": "Experienced ML Engineer with PyTorch, Python, Docker."
            },
            {
                "id": "cand_2",
                "candidate_name": "Bob Jones",
                "skills": ["c++", "linux"],
                "years_experience": 6,
                "degree": "Bachelor",
                "summary": "C++ Systems engineer.",
                "raw_text": "C++ Systems engineer."
            }
        ]
        payload = {
            "custom_jd_text": jd_text,
            "candidates": candidates,
            "weights": {"w_semantic": 0.33, "w_skills": 0.50, "w_experience": 0.17},
            "apply_bias_mitigation": True
        }
        res = self.client.post("/api/match/recruiter", json=payload)
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(len(json_data["results"]), 2)
        self.assertEqual(json_data["results"][0]["id"], "cand_1")
        print("[PASS] test_recruiter_match_with_custom_candidates: Rank 1 is", json_data["results"][0]["candidate_name"])

    def test_candidate_match_with_custom_jobs(self):
        resume_text = "Candidate Name: Jane Doe\nSkills: Python, SQL, Tableau, Pandas\nExperience: 3 years Data Analyst building dashboards."
        jobs = [
            {
                "id": "job_1",
                "title": "Data Analyst",
                "company": "AnalyticsPro",
                "description": "Seeking Data Analyst skilled in SQL, Tableau, and Python to analyze metrics.",
                "required_skills": ["sql", "tableau", "python"]
            },
            {
                "id": "job_2",
                "title": "C++ Graphics Engineer",
                "company": "GameStudio",
                "description": "Seeking C++ Graphics dev with OpenGL, Vulkan, and DirectX.",
                "required_skills": ["c++", "opengl", "vulkan"]
            }
        ]
        payload = {
            "custom_resume_text": resume_text,
            "jobs": jobs
        }
        res = self.client.post("/api/match/candidate", json=payload)
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(len(json_data["results"]), 2)
        self.assertEqual(json_data["results"][0]["job_id"], "job_1")
        print("[PASS] test_candidate_match_with_custom_jobs: Best match is", json_data["results"][0]["job_title"])

if __name__ == "__main__":
    unittest.main()
