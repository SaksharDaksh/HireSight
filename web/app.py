import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import glob
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.parsing.resume_parser import ResumeParser
from src.parsing.jd_parser import JDParser
from src.extraction.structured_extractor import StructuredExtractor
from src.embeddings.embed_store import VectorEmbeddingStore
from src.matching.hybrid_matcher import HybridMatcher
from src.matching.bias_mitigation import BiasMitigator
from src.ml.shap_explainer import MatchSHAPExplainer
from src.ml.dataset_generator import FeatureDatasetGenerator
from src.reasoning.llm_explainer import LLMExplainer
from src.evaluation.evaluate import Evaluator
from src.db import DatabaseManager

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Initialize Core Services
resume_parser = ResumeParser()
jd_parser = JDParser()
extractor = StructuredExtractor()
embed_store = VectorEmbeddingStore()
hybrid_matcher = HybridMatcher(embed_store=embed_store)
bias_mitigator = BiasMitigator()
llm_explainer = LLMExplainer()
db_manager = DatabaseManager()

# Initialize ML SHAP Explainer
try:
    shap_explainer = MatchSHAPExplainer()
except Exception as e:
    print(f"SHAP explainer init note: {e}")
    shap_explainer = None

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Helper to load existing JDs and Resumes
def load_all_jds():
    jds = []
    for f in sorted(glob.glob("data/job_descriptions/*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            jds.append(json.load(fp))
    return jds

def load_all_resumes():
    resumes = []
    for f in sorted(glob.glob("data/resumes/*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            resumes.append(json.load(fp))
    return resumes

@app.route("/")
def index():
    return render_template("index.html")

# ----------------- REST APIs ----------------- #

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Retrieve all available job descriptions."""
    return jsonify(load_all_jds())

@app.route("/api/resumes", methods=["GET"])
def get_resumes():
    """Retrieve all available resumes."""
    resumes = load_all_resumes()
    return jsonify(resumes)

@app.route("/api/extract-text", methods=["POST"])
def extract_text():
    """Extract clean plain text from an uploaded PDF or TXT file."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    text = resume_parser.parse_file(save_path)
    clean = resume_parser.clean_text(text)

    try:
        os.remove(save_path)
    except Exception:
        pass

    return jsonify({
        "status": "success",
        "text": clean,
        "filename": filename
    })

@app.route("/api/upload/resumes-batch", methods=["POST"])
def upload_resumes_batch():
    """Upload multiple resume files (PDF/TXT), extract profiles, and return list."""
    uploaded_files = request.files.getlist("files")
    if not uploaded_files and "file" in request.files:
        uploaded_files = [request.files["file"]]
    if not uploaded_files:
        return jsonify({"status": "error", "message": "No files uploaded"}), 400

    profiles = []
    for file in uploaded_files:
        if file.filename == "":
            continue
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        text = resume_parser.parse_file(save_path)
        clean_text = resume_parser.clean_text(text)
        custom_id = f"cand_{abs(hash(clean_text + filename)) % 100000}"
        prof = extractor.extract_resume_profile(clean_text, resume_id=custom_id)
        prof["raw_text"] = clean_text
        prof["filename"] = filename

        # Fallback candidate name from filename if not extracted
        if not prof.get("candidate_name") or prof.get("candidate_name") == "Candidate":
            base_name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
            prof["candidate_name"] = base_name

        profiles.append(prof)
        try:
            os.remove(save_path)
        except Exception:
            pass

    return jsonify({
        "status": "success",
        "candidates": profiles,
        "count": len(profiles)
    })

@app.route("/api/match/recruiter", methods=["POST"])
def match_recruiter():
    """
    Ranks uploaded resumes against a pasted or uploaded JD.
    No preset JD or preset candidates required.
    """
    data = request.get_json() or {}
    custom_jd_text = data.get("custom_jd_text", "").strip()
    candidates = data.get("candidates", [])
    weights = data.get("weights", {"w_semantic": 0.45, "w_skills": 0.40, "w_experience": 0.15})
    filter_mode = data.get("filter_mode", "soft")
    apply_bias = data.get("apply_bias_mitigation", False)

    if not custom_jd_text:
        return jsonify({"status": "error", "message": "Please paste or upload a Job Description."}), 400

    if not candidates:
        return jsonify({"status": "error", "message": "No candidate resumes in pool. Please upload candidate resumes to screen."}), 400

    target_jd = jd_parser.parse_raw_text(custom_jd_text, title="Target Position")
    target_jd["required_skills"] = extractor.extract_skills(custom_jd_text)
    target_jd["description"] = custom_jd_text

    jd_words = len(custom_jd_text.split())
    jd_sparse = jd_words < 15

    # Compute unmitigated and mitigated rankings
    ranked_unmitigated = hybrid_matcher.rank_candidates(
        candidates=candidates, jd=target_jd, weights=weights, filter_mode=filter_mode, apply_bias_mitigation=False
    )
    ranked_mitigated = hybrid_matcher.rank_candidates(
        candidates=candidates, jd=target_jd, weights=weights, filter_mode=filter_mode, apply_bias_mitigation=True
    )

    fairness_audit = bias_mitigator.compute_fairness_audit(ranked_unmitigated, ranked_mitigated)
    delta_map = {item["candidate_id"]: item for item in fairness_audit.get("comparison", [])}

    active_results = ranked_mitigated if apply_bias else ranked_unmitigated
    cands_map = {c["id"]: c for c in candidates}

    for cand in active_results:
        cid = cand["id"]
        orig = cands_map.get(cid, {})
        chunks = resume_parser.chunk_resume(orig.get("raw_text", ""))
        snippet = orig.get("summary", "")
        if not snippet and chunks:
            snippet = chunks[0].get("content", "")
        if not snippet:
            snippet = orig.get("raw_text", "")[:350]

        cand["resume_snippet"] = snippet[:400].strip()
        cand["top_matched_skills"] = cand.get("matched_skills", [])[:3]
        cand["top_missing_skills"] = cand.get("missing_skills", [])[:3]

        if cid in delta_map:
            cand["rank_delta"] = delta_map[cid]["rank_delta"]
            cand["score_delta"] = delta_map[cid]["score_delta"]
            cand["original_rank"] = delta_map[cid]["original_rank"]
        else:
            cand["rank_delta"] = 0
            cand["score_delta"] = 0.0

        if jd_sparse:
            cand["is_confident"] = False
            cand["confidence_status"] = "Not Confident: JD Too Sparse"
            cand["confidence_reason"] = f"Job Description contains only {jd_words} words. Detailed requirements are missing."

        exp = llm_explainer.explain(
            candidate_profile=orig,
            jd=target_jd,
            retrieved_chunks=[snippet]
        )
        cand["explanation"] = exp.get("fit_summary", "")

    return jsonify({
        "status": "success",
        "job": target_jd,
        "results": active_results,
        "bias_mitigation_active": apply_bias,
        "fairness_audit": fairness_audit
    })

@app.route("/api/match/candidate", methods=["POST"])
def match_candidate():
    """
    Ranks user's resume against user-uploaded or provided target jobs.
    """
    data = request.get_json() or {}
    custom_resume_text = data.get("custom_resume_text", "").strip()
    target_jobs = data.get("jobs", [])

    if not custom_resume_text:
        return jsonify({"status": "error", "message": "Please paste or upload your resume."}), 400

    if not target_jobs:
        return jsonify({"status": "error", "message": "No jobs in pool. Please add or upload the job descriptions you want to match against."}), 400

    target_resume = extractor.extract_resume_profile(custom_resume_text, resume_id="applicant")
    target_resume["raw_text"] = custom_resume_text

    cand_words = len(custom_resume_text.split())
    cand_sparse = cand_words < 20

    evaluations = []
    for jd_item in target_jobs:
        jd_text = jd_item.get("description", jd_item.get("text", ""))
        jd = jd_parser.parse_raw_text(jd_text, title=jd_item.get("title", "Target Position"))
        jd["id"] = jd_item.get("id", f"job_{abs(hash(jd_text)) % 10000}")
        jd["company"] = jd_item.get("company", "Hiring Organization")
        jd["required_skills"] = jd_item.get("required_skills") or extractor.extract_skills(jd_text)
        jd["description"] = jd_text

        res_eval = hybrid_matcher.evaluate_candidate(target_resume, jd, filter_mode="soft")

        res_snippet = target_resume.get("summary", target_resume.get("raw_text", ""))[:350].strip()
        explanation = llm_explainer.explain(
            candidate_profile=target_resume,
            jd=jd,
            retrieved_chunks=[res_snippet]
        )

        res_eval["job_title"] = jd.get("title")
        res_eval["company"] = jd.get("company")
        res_eval["department"] = jd.get("department", "Engineering")
        res_eval["job_id"] = jd.get("id")
        res_eval["jd_snippet"] = jd.get("description", "")[:350].strip()
        res_eval["resume_snippet"] = res_snippet
        res_eval["top_matched_skills"] = res_eval.get("matched_skills", [])[:3]
        res_eval["top_missing_skills"] = res_eval.get("missing_skills", [])[:3]
        res_eval["improvement_suggestions"] = explanation.get("improvement_suggestions", [])
        res_eval["fit_summary"] = explanation.get("fit_summary", "")

        if cand_sparse:
            res_eval["is_confident"] = False
            res_eval["confidence_status"] = "Not Confident: Resume Too Sparse"
            res_eval["confidence_reason"] = f"Resume text has only {cand_words} words. Detailed experience timeline is missing."

        evaluations.append(res_eval)

    evaluations.sort(key=lambda x: x["final_score"], reverse=True)
    for idx, e in enumerate(evaluations):
        e["rank"] = idx + 1

    return jsonify({
        "status": "success",
        "candidate": target_resume,
        "results": evaluations
    })

@app.route("/api/explain/candidate", methods=["POST"])
def explain_candidate():
    """
    Generates RAG context reasoning, SHAP feature impact chart, and skill gap breakdown.
    """
    data = request.get_json() or {}
    resume_id = data.get("resume_id")
    jd_id = data.get("jd_id")

    all_resumes = load_all_resumes()
    all_jds = load_all_jds()

    cand = next((r for r in all_resumes if r["id"] == resume_id), None)
    jd = next((j for j in all_jds if j["id"] == jd_id), None)

    if not cand or not jd:
        return jsonify({"error": "Candidate or Job not found"}), 404

    # Extract chunks
    chunks = resume_parser.chunk_resume(cand.get("raw_text", ""))
    chunk_texts = [c["content"] for c in chunks]

    # LLM Reasoning pass
    reasoning = llm_explainer.explain(cand, jd, chunk_texts)

    # SHAP TreeExplainer pass
    shap_data = None
    if shap_explainer:
        feat_gen = FeatureDatasetGenerator()
        features = feat_gen.extract_pair_features(cand, jd, ground_truth_label=1)
        try:
            shap_data = shap_explainer.explain_candidate(features)
        except Exception as e:
            print("SHAP explanation error:", e)

    return jsonify({
        "status": "success",
        "candidate_name": cand.get("candidate_name"),
        "job_title": jd.get("title"),
        "reasoning": reasoning,
        "shap": shap_data
    })

@app.route("/api/upload/resume", methods=["POST"])
def upload_resume():
    """Uploads a PDF or text resume, parses it, and adds it to the candidate pool."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    text = resume_parser.parse_file(save_path)
    clean_text = resume_parser.clean_text(text)
    custom_id = f"res_uploaded_{abs(hash(clean_text)) % 10000}"
    profile = extractor.extract_resume_profile(clean_text, resume_id=custom_id)
    profile["raw_text"] = clean_text

    # Save to disk and database
    with open(f"data/resumes/{custom_id}.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    db_manager.save_resume(profile)

    return jsonify({
        "status": "success",
        "message": f"Resume '{filename}' parsed successfully",
        "candidate": profile
    })

@app.route("/api/upload/jd", methods=["POST"])
def upload_jd():
    """Uploads a custom JD text or file."""
    if "file" in request.files:
        file = request.files["file"]
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        text = request.form.get("text", "")

    title = request.form.get("title", "Custom Position")
    jd = jd_parser.parse_raw_text(text, title=title)
    jd["required_skills"] = extractor.extract_skills(text)
    
    with open(f"data/job_descriptions/{jd['id']}.json", "w", encoding="utf-8") as f:
        json.dump(jd, f, indent=2)
    db_manager.save_job(jd)

    return jsonify({
        "status": "success",
        "message": f"Job description '{title}' created",
        "job": jd
    })

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Record recruiter active learning feedback."""
    data = request.get_json() or {}
    job_id = data.get("job_id")
    resume_id = data.get("resume_id")
    decision = data.get("decision", "interview")
    rating = int(data.get("rating", 4))
    notes = data.get("notes", "")

    db_manager.record_feedback(job_id, resume_id, decision, rating, notes)
    return jsonify({"status": "success", "message": "Feedback recorded for active learning"})

@app.route("/api/evaluate", methods=["GET"])
def run_evaluation():
    """Run full benchmark test and return metrics."""
    evaluator = Evaluator()
    summary = evaluator.run_benchmark(k=3)
    return jsonify(summary)

@app.route("/api/export/excel", methods=["GET"])
def download_excel_report():
    """Download the generated Excel evaluation report."""
    report_path = os.path.abspath("reports/screening_evaluation_report.xlsx")
    if not os.path.exists(report_path):
        evaluator = Evaluator()
        evaluator.run_benchmark(k=3)
    return send_file(report_path, as_attachment=True, download_name="Screening_Evaluation_Report.xlsx")

@app.route("/api/export/powerbi", methods=["GET"])
def download_powerbi_csv():
    """Download dataset for Power BI."""
    csv_path = os.path.abspath("data/powerbi_export.csv")
    if not os.path.exists(csv_path):
        evaluator = Evaluator()
        evaluator.run_benchmark(k=3)
    return send_file(csv_path, as_attachment=True, download_name="powerbi_export.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
