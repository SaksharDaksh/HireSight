# HireSight — Application Walkthrough & User Guide

Welcome to **HireSight**, an explainable, fairness-aware AI resume and job description matching application. 

HireSight combines high-throughput C++ acceleration, supervised machine learning with SMOTE, explainable AI, retrieval-augmented generation (RAG), and proactive demographic bias mitigation into a simple, clean, and intuitive user interface designed for both recruiters and job candidates.

---

## 1. Quick Start: How to Run the App

1. Open PowerShell or your terminal in the project directory:
   ```powershell
   cd "c:\Users\Sakshar Daksh\Desktop\RESUMES\AntiGravity\resume job preference"
   ```

2. Start the web application:
   ```powershell
   python web/app.py
   ```

3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 2. User Interface Tour & Dark Mode

The top navigation bar features:
- **Brand Logo & Title**: `HireSight — Fairness-Aware Resume & Job Description Matcher`
- **Mode Switcher**: Easily toggle between **Recruiter Mode** and **Candidate Mode**.
- **Dark Mode Toggle**: A top-right button (`🌙 / ☀️`) that instantly toggles between Light Mode and Dark Mode, automatically persisting your preference in `localStorage`.

---

## 3. Recruiter Mode Walkthrough

Recruiter Mode allows hiring managers and recruiters to evaluate custom candidate pools against any custom job description. All preset dependencies have been removed, giving the recruiter total control over the candidate pool and job description.

```
+-----------------------------------------------------------------------------------------+
| [Target Job Description]                                [Match Scoring Priorities]      |
| - Paste full JD text                                    - Semantic Context: [Balanced]  |
| - Or upload JD document (PDF / TXT)                     - Required Skills:  [High]      |
|                                                         - Experience:       [Low]       |
| [Candidate Resumes to Screen]                                                           |
| - Multi-file upload box (PDF / TXT)                     [Demographic Bias Mitigation]   |
| - Live candidate counter and file removal tags          [ Toggle Switch: ON / OFF ]     |
+-----------------------------------------------------------------------------------------+
|                                  [Match & Rank Candidates]                              |
+-----------------------------------------------------------------------------------------+
| [Ranked Candidates Results Table]                                                       |
| Rank | Candidate | Fit Score | Top 3 Matched Skills | Top 3 Missing Skills | Confidence |
+-----------------------------------------------------------------------------------------+
```

### Step 1: Input the Target Job Description
- **Paste Text**: Paste the job description directly into the text area.
- **Upload a Document**: Click **"Or upload JD document"** to select a `.pdf` or `.txt` file. HireSight uses server-side `pdfplumber` to extract clean, uncorrupted text without gibberish.

### Step 2: Upload Candidate Resumes to Screen
- **No Preset Candidates**: The candidate pool is entirely user-defined.
- **Single or Batch Upload**: Click or drag-and-drop one or multiple `.pdf` / `.txt` resume files into the dashed upload dropzone.
- **Live Candidate Pool Tags**: Each uploaded candidate is listed as a removable tag with their name and verified experience. Click `✕` on any candidate tag to remove them, or click **Clear All** to reset the pool.

### Step 3: Set Scoring Priorities (No Percentage Math!)
- Rather than forcing recruiters to calculate exact percentages that sum to 100%, HireSight provides intuitive stepped priority sliders:
  - **Level 1**: `Low Priority`
  - **Level 2**: `Balanced`
  - **Level 3**: `High Priority`
  - **Level 4**: `Critical`
- Behind the scenes, HireSight automatically normalizes these priorities into mathematical weights:
  $$\text{Weight}_i = \frac{\text{Priority}_i}{\sum \text{Priority}}$$

### Step 4: Toggle Demographic Bias Mitigation
- **OFF**: Standard evaluation using raw candidate signals.
- **ON**: Automatically redacts candidate names, gendered pronouns, age indicators, and prestige university brand proxies.
- **Live Rank Shift Indicators**: When active, the table displays rank movement indicators:
  - `▲ +2` (Candidate moved up 2 positions based purely on verified merit)
  - `▼ -1` (Candidate moved down 1 position once brand proxies were stripped)
  - `=` (Rank remained unchanged)

### Step 5: Click "Match & Rank Candidates"
- Evaluates the uploaded candidates against the JD in real-time.
- Results table displays:
  - **Rank & Movement**: `#1`, `#2`, etc.
  - **Candidate**: Candidate name and verified experience/degree.
  - **Fit Score**: Percentage badge and visual progress bar.
  - **Top 3 Matched Skills**: Green pill badges showing verified matching competencies.
  - **Top 3 Missing Skills**: Red pill badges showing required skills the candidate lacks.
  - **Confidence Badge**: Displays `Confident` (green) or `⚠️ Too Sparse` (amber) if the JD or resume contains insufficient information.

### Step 6: Expand Candidate Row for Verifiable Evidence
- Click any candidate row to reveal:
  - **Plain-English Explanation**: Clear explanation of why the candidate fits or does not fit.
  - **Verified Resume Excerpt**: Verbatim snippet extracted directly from the candidate's resume proving the scoring rationale (zero hallucination).

---

## 4. Candidate Mode Walkthrough

Candidate Mode allows job seekers to input their own resume and compare it against a user-controlled pool of target jobs to identify their best matches and receive actionable skill-improvement roadmaps.

```
+-----------------------------------------------------------------------------------------+
| [Your Resume]                                           [Target Jobs to Compare Against]|
| - Paste resume text                                     - Upload job files (PDF / TXT)  |
| - Or upload resume (.pdf / .txt)                        - Or manually paste target jobs |
|   (Clean PDF extraction, NO gibberish!)                 - Optional: Quick-load 4 samples|
+-----------------------------------------------------------------------------------------+
|                               [Match Against Target Jobs]                               |
+-----------------------------------------------------------------------------------------+
| [Matching Job Opportunities Table]                                                      |
| Rank | Position & Company | Fit Score | Skills You Have | Skills You Need | Confidence  |
+-----------------------------------------------------------------------------------------+
```

### Step 1: Provide Your Resume
- **No Preset Candidates**: Input your own resume.
- **Paste Text**: Paste your resume text directly into the text area.
- **Upload File**: Upload your resume as a `.pdf` or `.txt` file.
  - **PDF Gibberish Fix**: Uploaded PDFs are parsed via server-side `pdfplumber`, extracting clean text directly into the editor without any `%PDF-1.4...` binary corruption.

### Step 2: Manage Your Target Jobs Comparison Pool
- **Full Transparency**: The job pool is not hidden or hardcoded. You choose exactly which jobs you want to compare against:
  1. **Upload Job Documents**: Upload multiple `.pdf` or `.txt` job description files.
  2. **Manually Paste Jobs**: Open the expandable paste form, enter a Job Title and Description, and click **"Add Job to Pool"**.
  3. **Quick-Load Helper**: Click **"Quick-load 4 sample tech jobs"** to instantly test with realistic positions (ML Engineer, Backend Lead, Data Analyst, DevOps).
- Remove individual jobs anytime using the `✕` button on each job tag, or click **Clear All**.

### Step 3: Click "Match Against Target Jobs"
- The matcher ranks your resume across all jobs in your comparison pool.
- The results table shows:
  - **Position & Company**: Target title and organization.
  - **Fit Score**: Percentage match.
  - **Skills You Have**: Skills identified from your resume that match the job.
  - **Skills You Need**: Gaps you need to acquire for the role.
  - **Confidence**: Flagging if your resume was too brief for a reliable evaluation.

### Step 4: Expand Role for Personalized Roadmap
- Click any job row to view:
  - **Match Fit Assessment**: Summary of your qualification alignment.
  - **Actionable Roadmap**: Step-by-step guidance on specific certifications, libraries, and portfolio projects to undertake to bridge the skill gap and maximize your score.
  - **Job Description Snippet**: Relevant excerpt from the job requirements.

---

## 5. Verification & Testing

To run the automated test suite verifying all refined workflows:
```powershell
python tests/test_ui_refinements.py
```
Expected output:
```
....
----------------------------------------------------------------------
Ran 4 tests in 0.132s

OK
[PASS] test_candidate_match_with_custom_jobs: Best match is Data Analyst
[PASS] test_extract_text_txt: Candidate Name: Jane Doe ...
[PASS] test_recruiter_match_with_custom_candidates: Rank 1 is [Redacted]
[PASS] test_upload_resumes_batch: processed 2 candidates
```
