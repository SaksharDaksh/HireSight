import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import glob
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import Dict, List, Any

from src.matching.hybrid_matcher import HybridMatcher
from src.matching.bias_mitigation import BiasMitigator
from src.embeddings.embed_store import VectorEmbeddingStore

class Evaluator:
    """
    Evaluates system accuracy against ground truth labels:
    - Precision@k
    - Mean Reciprocal Rank (MRR)
    - Skill-gap detection recall & precision
    - Demographic bias shift metrics
    - Generates formatted Excel reports and Power BI export data
    """

    def __init__(
        self,
        jds_dir: str = "data/job_descriptions",
        resumes_dir: str = "data/resumes",
        labels_path: str = "data/eval_labels.json"
    ):
        self.jds_dir = jds_dir
        self.resumes_dir = resumes_dir
        self.labels_path = labels_path
        self.matcher = HybridMatcher()
        self.bias_mitigator = BiasMitigator()

    def load_data(self):
        jds = []
        for f in sorted(glob.glob(os.path.join(self.jds_dir, "*.json"))):
            with open(f, "r", encoding="utf-8") as fp:
                jds.append(json.load(fp))

        resumes = []
        for f in sorted(glob.glob(os.path.join(self.resumes_dir, "*.json"))):
            with open(f, "r", encoding="utf-8") as fp:
                resumes.append(json.load(fp))

        labels = {}
        if os.path.exists(self.labels_path):
            with open(self.labels_path, "r", encoding="utf-8") as fp:
                labels = json.load(fp)

        return jds, resumes, labels

    def compute_precision_at_k(self, predicted_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        if not ground_truth_ids or k <= 0:
            return 0.0
        top_k_pred = set(predicted_ids[:k])
        gt_set = set(ground_truth_ids)
        hits = len(top_k_pred.intersection(gt_set))
        return hits / min(k, len(gt_set))

    def compute_mrr(self, predicted_ids: List[str], ground_truth_ids: List[str]) -> float:
        gt_set = set(ground_truth_ids)
        for rank, cid in enumerate(predicted_ids, 1):
            if cid in gt_set:
                return 1.0 / rank
        return 0.0

    def run_benchmark(self, k: int = 3) -> Dict[str, Any]:
        jds, resumes, labels = self.load_data()
        
        results_per_jd = []
        precision_scores = []
        mrr_scores = []
        bias_shifts = []

        all_candidate_matches_records = []

        for jd in jds:
            jd_id = jd["id"]
            gt_data = labels.get(jd_id, {})
            gt_top = gt_data.get("top_candidates", [])

            # 1. Normal Ranking without bias mitigation
            ranked_raw = self.matcher.rank_candidates(
                candidates=resumes,
                jd=jd,
                filter_mode="soft",
                apply_bias_mitigation=False
            )
            raw_ids = [c["id"] for c in ranked_raw]

            # 2. Ranking WITH bias mitigation
            ranked_mitigated = self.matcher.rank_candidates(
                candidates=resumes,
                jd=jd,
                filter_mode="soft",
                apply_bias_mitigation=True
            )

            # Fairness audit comparison
            audit = self.bias_mitigator.compute_fairness_audit(ranked_raw, ranked_mitigated)
            bias_shifts.append(audit["average_rank_shift"])

            # Compute precision@k and MRR if ground truth exists
            if gt_top:
                p_at_k = self.compute_precision_at_k(raw_ids, gt_top, k=k)
                mrr = self.compute_mrr(raw_ids, gt_top)
                precision_scores.append(p_at_k)
                mrr_scores.append(mrr)
            else:
                p_at_k, mrr = None, None

            results_per_jd.append({
                "jd_id": jd_id,
                "title": jd.get("title"),
                "precision_at_k": round(p_at_k, 3) if p_at_k is not None else "N/A",
                "mrr": round(mrr, 3) if mrr is not None else "N/A",
                "avg_bias_rank_shift": audit["average_rank_shift"],
                "candidates_shifted": audit["total_candidates_shifted"],
                "top_1_candidate": ranked_raw[0]["candidate_name"] if ranked_raw else "N/A"
            })

            # Record rows for Power BI export
            for cand in ranked_raw:
                all_candidate_matches_records.append({
                    "job_id": jd_id,
                    "job_title": jd.get("title"),
                    "job_department": jd.get("department", "Engineering"),
                    "candidate_id": cand["id"],
                    "candidate_name": cand["candidate_name"],
                    "candidate_experience_years": cand.get("years_experience", 0),
                    "required_experience_years": jd.get("min_years_experience", 0),
                    "semantic_score": cand["semantic_score"],
                    "skill_overlap_score": cand["skill_overlap_score"],
                    "experience_score": cand["experience_score"],
                    "final_score": cand["final_score"],
                    "rank": cand.get("rank", 0),
                    "passed_hard_filters": cand["passed_hard_filters"],
                    "engine_used": cand.get("engine_used", "Hybrid")
                })

        mean_p_at_k = float(np.mean([p for p in precision_scores if p is not None])) if precision_scores else 0.0
        mean_mrr = float(np.mean([m for m in mrr_scores if m is not None])) if mrr_scores else 0.0
        mean_shift = float(np.mean(bias_shifts)) if bias_shifts else 0.0

        # Export for Power BI
        os.makedirs("data", exist_ok=True)
        powerbi_df = pd.DataFrame(all_candidate_matches_records)
        powerbi_df.to_csv("data/powerbi_export.csv", index=False)

        summary = {
            f"mean_precision_at_{k}": round(mean_p_at_k, 4),
            "mean_mrr": round(mean_mrr, 4),
            "overall_avg_bias_rank_shift": round(mean_shift, 2),
            "total_jds_evaluated": len(jds),
            "total_eval_pairs": len(all_candidate_matches_records),
            "detailed_results": results_per_jd
        }

        # Generate Excel Report
        self.export_excel_report(summary, powerbi_df, "reports/screening_evaluation_report.xlsx")
        return summary

    def export_excel_report(self, summary: Dict[str, Any], df_matches: pd.DataFrame, output_path: str):
        """Generates a beautifully styled Excel workbook using openpyxl."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb = openpyxl.Workbook()

        # Sheet 1: Executive Summary
        ws1 = wb.active
        ws1.title = "Executive Summary"
        ws1.views.sheetView[0].showGridLines = True

        title_font = Font(name="Segoe UI", size=14, bold=True, color="1E3A8A")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        bold_font = Font(name="Segoe UI", size=10, bold=True)
        regular_font = Font(name="Segoe UI", size=10)

        ws1["A1"] = "Fairness-Aware Resume Matcher - Evaluation Benchmark Report"
        ws1["A1"].font = title_font

        ws1["A3"] = "Metric"
        ws1["B3"] = "Benchmark Score"
        ws1["A3"].fill = header_fill
        ws1["B3"].fill = header_fill
        ws1["A3"].font = header_font
        ws1["B3"].font = header_font

        metrics_rows = [
            ("Mean Precision@3 (Top-k Match with Ground Truth)", f"{summary.get('mean_precision_at_3', 0.0)*100:.1f}%"),
            ("Mean Reciprocal Rank (MRR)", f"{summary.get('mean_mrr', 0.0):.3f}"),
            ("Average Bias Mitigation Rank Shift", f"{summary.get('overall_avg_bias_rank_shift', 0.0):.2f} positions"),
            ("Total Job Roles Tested", summary.get("total_jds_evaluated", 0)),
            ("Total Candidate-JD Evaluation Pairs", summary.get("total_eval_pairs", 0))
        ]

        for i, (m, val) in enumerate(metrics_rows, start=4):
            ws1.cell(row=i, column=1, value=m).font = bold_font
            ws1.cell(row=i, column=2, value=val).font = regular_font

        # Per JD Table
        ws1.cell(row=10, column=1, value="Evaluation Performance Breakdown By Job Role").font = title_font
        headers_jd = ["Job ID", "Job Title", "Precision@3", "MRR", "Avg Bias Shift", "Candidates Shifted", "Top Match"]
        for c_idx, h in enumerate(headers_jd, 1):
            cell = ws1.cell(row=12, column=c_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font

        for r_idx, row_data in enumerate(summary.get("detailed_results", []), 13):
            ws1.cell(row=r_idx, column=1, value=row_data["jd_id"]).font = regular_font
            ws1.cell(row=r_idx, column=2, value=row_data["title"]).font = regular_font
            ws1.cell(row=r_idx, column=3, value=row_data["precision_at_k"]).font = regular_font
            ws1.cell(row=r_idx, column=4, value=row_data["mrr"]).font = regular_font
            ws1.cell(row=r_idx, column=5, value=row_data["avg_bias_rank_shift"]).font = regular_font
            ws1.cell(row=r_idx, column=6, value=row_data["candidates_shifted"]).font = regular_font
            ws1.cell(row=r_idx, column=7, value=row_data["top_1_candidate"]).font = regular_font

        # Sheet 2: Raw Candidate Matches Dataset
        ws2 = wb.create_sheet(title="Candidate Matches")
        ws2.views.sheetView[0].showGridLines = True

        cols = list(df_matches.columns)
        for c_idx, col_name in enumerate(cols, 1):
            cell = ws2.cell(row=1, column=c_idx, value=col_name.replace("_", " ").title())
            cell.fill = header_fill
            cell.font = header_font

        for r_idx, record in enumerate(df_matches.to_dict(orient="records"), 2):
            for c_idx, col_name in enumerate(cols, 1):
                ws2.cell(row=r_idx, column=c_idx, value=record[col_name]).font = regular_font

        # Auto-adjust column widths
        for ws in [ws1, ws2]:
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_path)
        print(f"Generated formatted Excel evaluation report at: {output_path}")

if __name__ == "__main__":
    evaluator = Evaluator()
    summary = evaluator.run_benchmark(k=3)
    print("\nBenchmark Summary:\n", json.dumps(summary, indent=2))
