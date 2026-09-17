# Power BI Dashboard Setup & Visual Modeling Guide

This document outlines how to import `data/powerbi_export.csv` into Microsoft Power BI to build an interactive executive recruitment analytics dashboard.

---

## 1. Dataset Schema (`powerbi_export.csv`)

| Field Name | Type | Description |
|---|---|---|
| `job_id` | String | Unique identifier of the Job Description |
| `job_title` | String | Target role title (e.g. Machine Learning Engineer) |
| `job_department` | String | Department (e.g., Engineering, AI & Data) |
| `candidate_id` | String | Candidate identifier (res_01, res_02, etc.) |
| `candidate_name` | String | Candidate Name |
| `candidate_experience_years` | Integer | Total years of verified candidate experience |
| `required_experience_years` | Integer | Minimum years required by JD |
| `semantic_score` | Decimal | Vector similarity score (0.0 to 1.0) |
| `skill_overlap_score` | Decimal | Weighted required & preferred skill match |
| `experience_score` | Decimal | Experience penalty/bonus match score |
| `final_score` | Decimal | Fused hybrid match score |
| `rank` | Integer | Candidate rank for this role |
| `passed_hard_filters` | Boolean | TRUE if candidate met hard constraints |
| `engine_used` | String | C++17 FastMatcher / Scikit-Learn |

---

## 2. Power BI DAX Measures

Paste these DAX measures into your Power BI model table:

### Average Match Score
```dax
Avg_Final_Score = AVERAGE('powerbi_export'[final_score])
```

### Qualified Candidate Count
```dax
Qualified_Candidates = 
CALCULATE(
    COUNTROWS('powerbi_export'),
    'powerbi_export'[passed_hard_filters] = TRUE()
)
```

### Top Quartile Fit Rate
```dax
Top_Quartile_Fit_Rate = 
DIVIDE(
    CALCULATE(COUNTROWS('powerbi_export'), 'powerbi_export'[final_score] >= 0.75),
    COUNTROWS('powerbi_export'),
    0
)
```

### Experience Gap Index
```dax
Avg_Experience_Delta = 
AVERAGE('powerbi_export'[candidate_experience_years]) - AVERAGE('powerbi_export'[required_experience_years])
```

---

## 3. Recommended Visualizations in Power BI

1. **Card Visuals (Top KPIs)**:
   - Total Evaluated Pairs (`COUNTROWS`)
   - Average Screening Fit (`[Avg_Final_Score]`)
   - Hard Filter Qualification Rate (`[Qualified_Candidates] / Total`)
2. **Scatter Plot (Semantic vs. Structured Skill Overlap)**:
   - X-Axis: `skill_overlap_score`
   - Y-Axis: `semantic_score`
   - Legend / Color: `passed_hard_filters`
   - Size: `candidate_experience_years`
3. **Stacked Bar Chart (Ranking by Job Title)**:
   - Axis: `job_title`
   - Values: `final_score` filtered to top 5 candidates
4. **Slicers**:
   - `job_title`
   - `passed_hard_filters`
   - `engine_used`
