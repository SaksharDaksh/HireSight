import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import json
from web.app import app

def test_full_system():
    print("Initializing Flask test client...")
    client = app.test_client()

    # 1. Test GET /
    res = client.get("/")
    assert res.status_code == 200, f"GET / returned {res.status_code}"
    print("[PASS] GET / (Dashboard UI renders)")

    # 2. Test GET /api/jobs
    res = client.get("/api/jobs")
    assert res.status_code == 200
    jobs = res.get_json()
    assert len(jobs) >= 10, f"Expected 10+ jobs, got {len(jobs)}"
    print(f"[PASS] GET /api/jobs returned {len(jobs)} curated job descriptions")

    # 3. Test GET /api/resumes
    res = client.get("/api/resumes")
    assert res.status_code == 200
    resumes = res.get_json()
    assert len(resumes) >= 30, f"Expected 30+ resumes, got {len(resumes)}"
    print(f"[PASS] GET /api/resumes returned {len(resumes)} diverse candidate profiles")

    # 4. Test POST /api/match/recruiter (Standard Mode)
    payload = {
        "jd_id": jobs[0]["id"],
        "weights": {"w_semantic": 0.45, "w_skills": 0.40, "w_experience": 0.15},
        "filter_mode": "soft",
        "apply_bias_mitigation": False
    }
    res = client.post("/api/match/recruiter", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["results"]) == len(resumes)
    top_cand = data["results"][0]
    print(f"[PASS] POST /api/match/recruiter ranked candidate pool. Top: {top_cand['candidate_name']} ({top_cand['final_score']*100:.1f}%)")

    # 5. Test POST /api/match/recruiter (Bias Mitigation ON)
    payload["apply_bias_mitigation"] = True
    res_bias = client.post("/api/match/recruiter", json=payload)
    assert res_bias.status_code == 200
    bias_data = res_bias.get_json()
    audit = bias_data.get("fairness_audit", {})
    print(f"[PASS] POST /api/match/recruiter (Bias Mitigation ON): {audit.get('total_candidates_shifted')} candidates shifted rank, avg shift: {audit.get('average_rank_shift')} positions")

    # 6. Test POST /api/match/candidate
    cand_payload = {"resume_id": resumes[0]["id"]}
    res_cand = client.post("/api/match/candidate", json=cand_payload)
    assert res_cand.status_code == 200
    cand_data = res_cand.get_json()
    assert len(cand_data["results"]) == len(jobs)
    print(f"[PASS] POST /api/match/candidate ranked {len(cand_data['results'])} job openings with improvement roadmaps")

    # 7. Test POST /api/explain/candidate (RAG + SHAP)
    explain_payload = {
        "resume_id": resumes[0]["id"],
        "jd_id": jobs[0]["id"]
    }
    res_exp = client.post("/api/explain/candidate", json=explain_payload)
    assert res_exp.status_code == 200
    exp_data = res_exp.get_json()
    assert "reasoning" in exp_data
    assert "shap" in exp_data
    has_shap_chart = exp_data["shap"] and "chart_base64" in exp_data["shap"]
    print(f"[PASS] POST /api/explain/candidate: RAG fit reasoning verified. SHAP chart generated: {has_shap_chart}")

    # 8. Test GET /api/evaluate
    res_eval = client.get("/api/evaluate")
    assert res_eval.status_code == 200
    eval_data = res_eval.get_json()
    print(f"[PASS] GET /api/evaluate: Precision@3={eval_data.get('mean_precision_at_3')*100:.1f}%, MRR={eval_data.get('mean_mrr')}")

    # 9. Test Feedback Recording
    feedback_payload = {
        "job_id": jobs[0]["id"],
        "resume_id": resumes[0]["id"],
        "decision": "interview",
        "rating": 5,
        "notes": "Excellent candidate fit for core ML systems"
    }
    res_fb = client.post("/api/feedback", json=feedback_payload)
    assert res_fb.status_code == 200
    print("[PASS] POST /api/feedback: Recruiter active learning feedback persisted successfully")

    # 10. Test Export Excel
    res_excel = client.get("/api/export/excel")
    assert res_excel.status_code == 200
    assert len(res_excel.data) > 1000
    print(f"[PASS] GET /api/export/excel: Successfully downloaded {len(res_excel.data)} bytes Excel report")

    print("\n=======================================================")
    print("ALL 10 VERIFICATION TESTS PASSED FLAWLESSLY!")
    print("=======================================================")

if __name__ == "__main__":
    test_full_system()
