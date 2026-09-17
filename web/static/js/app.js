// ==========================================================
// HireSight - Simplified, Intuitive Client Application Logic
// ==========================================================

let appMode = "recruiter"; // 'recruiter' | 'candidate'
let recruiterCandidatePool = []; // In-memory pool of uploaded candidates
let candidateTargetJobs = [];    // User-controlled pool of target jobs to screen against
let recruiterResults = [];
let candidateResults = [];
let expandedRecruiterRowId = null;
let expandedCandidateRowId = null;

// On Page Load
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    updateSteppedSliderUI('semantic');
    updateSteppedSliderUI('skills');
    updateSteppedSliderUI('exp');
    renderRecruiterPool();
    renderCandidateJobsList();
});

// ---------------- Dark / Light Mode ---------------- //
function initTheme() {
    const savedTheme = localStorage.getItem("hiresight-theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
        document.body.classList.add("dark-mode");
        updateThemeIcon(true);
    } else {
        document.body.classList.remove("dark-mode");
        updateThemeIcon(false);
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("hiresight-theme", isDark ? "dark" : "light");
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const icon = document.getElementById("theme-icon");
    if (!icon) return;
    if (isDark) {
        icon.className = "fa-solid fa-sun";
        icon.title = "Switch to Light Mode";
    } else {
        icon.className = "fa-solid fa-moon";
        icon.title = "Switch to Dark Mode";
    }
}

// ---------------- Navigation & Mode Switching ---------------- //
function setAppMode(mode) {
    appMode = mode;
    const btnRecruiter = document.getElementById("btn-recruiter-mode");
    const btnCandidate = document.getElementById("btn-candidate-mode");
    const secRecruiter = document.getElementById("section-recruiter");
    const secCandidate = document.getElementById("section-candidate");

    if (mode === "recruiter") {
        btnRecruiter.classList.add("active");
        btnCandidate.classList.remove("active");
        secRecruiter.classList.add("active");
        secCandidate.classList.remove("active");
    } else {
        btnCandidate.classList.add("active");
        btnRecruiter.classList.remove("active");
        secCandidate.classList.add("active");
        secRecruiter.classList.remove("active");
    }
}

// ============================================================
// RECRUITER MODE HANDLERS
// ============================================================

// 1. Job Description File Upload (Handles PDF / TXT via backend text extraction)
async function handleJdFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    showToast(`Extracting text from "${file.name}"...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/extract-text", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success") {
            document.getElementById("recruiter-jd-text").value = data.text;
            showToast(`Clean text from "${file.name}" loaded into JD box!`);
        } else {
            showToast("Extraction error: " + (data.message || "Failed to parse file"));
        }
    } catch (e) {
        showToast("Upload error: " + e.message);
    } finally {
        event.target.value = "";
    }
}

// 2. Candidate Batch Resume Upload
async function handleBatchResumeUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    showToast(`Processing ${files.length} candidate file(s)...`);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
    }

    try {
        const res = await fetch("/api/upload/resumes-batch", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success" && data.candidates) {
            // Append candidates to existing recruiter pool
            recruiterCandidatePool.push(...data.candidates);
            renderRecruiterPool();
            showToast(`Successfully added ${data.candidates.length} candidate(s) to screening pool!`);
        } else {
            showToast("Upload failed: " + (data.message || "Could not process files"));
        }
    } catch (e) {
        showToast("Error processing resumes: " + e.message);
    } finally {
        event.target.value = "";
    }
}

function renderRecruiterPool() {
    const listEl = document.getElementById("recruiter-pool-list");
    const countEl = document.getElementById("recruiter-pool-count");
    const clearBtn = document.getElementById("btn-clear-recruiter-pool");

    if (!listEl) return;

    const count = recruiterCandidatePool.length;
    countEl.innerText = `${count} candidate${count === 1 ? '' : 's'} in screening pool`;
    if (clearBtn) {
        clearBtn.style.display = count > 0 ? "inline-flex" : "none";
    }

    if (count === 0) {
        listEl.innerHTML = '<span style="font-size: 12px; color: var(--text-light); font-style: italic;">No candidates uploaded yet.</span>';
        return;
    }

    listEl.innerHTML = recruiterCandidatePool.map((c, idx) => `
        <div class="file-pill">
            <i class="fa-solid fa-user-check" style="color: var(--primary);"></i>
            <span class="file-name" title="${escapeHtml(c.candidate_name)}">${escapeHtml(c.candidate_name)}</span>
            <button class="file-remove" onclick="removeRecruiterCandidate(${idx})" title="Remove candidate">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `).join("");
}

function removeRecruiterCandidate(idx) {
    if (idx >= 0 && idx < recruiterCandidatePool.length) {
        recruiterCandidatePool.splice(idx, 1);
        renderRecruiterPool();
    }
}

function clearRecruiterPool() {
    recruiterCandidatePool = [];
    renderRecruiterPool();
    showToast("Screening pool cleared.");
}

// 3. Stepped Slider Priority Management
const STEP_LABELS = {
    1: { text: "Low Priority", class: "p-low", weight: 1 },
    2: { text: "Balanced", class: "p-med", weight: 2 },
    3: { text: "High Priority", class: "p-high", weight: 3 },
    4: { text: "Critical", class: "p-crit", weight: 4 }
};

function onSteppedSliderInput(metric) {
    updateSteppedSliderUI(metric);
}

function updateSteppedSliderUI(metric) {
    const slider = document.getElementById(`slider-w-${metric}`);
    const label = document.getElementById(`label-w-${metric}`);
    if (!slider || !label) return;

    const val = parseInt(slider.value) || 2;
    const step = STEP_LABELS[val] || STEP_LABELS[2];

    label.innerText = step.text;
    label.className = `priority-badge ${step.class}`;
}

function getNormalizedWeights() {
    const vSem = STEP_LABELS[parseInt(document.getElementById("slider-w-semantic").value) || 2].weight;
    const vSkl = STEP_LABELS[parseInt(document.getElementById("slider-w-skills").value) || 3].weight;
    const vExp = STEP_LABELS[parseInt(document.getElementById("slider-w-exp").value) || 1].weight;
    const total = vSem + vSkl + vExp;

    return {
        w_semantic: parseFloat((vSem / total).toFixed(3)),
        w_skills: parseFloat((vSkl / total).toFixed(3)),
        w_experience: parseFloat((vExp / total).toFixed(3))
    };
}

// 4. Demographic Bias Mitigation Toggle
function onBiasToggleChange() {
    const isChecked = document.getElementById("toggle-bias-mitigation").checked;
    const pill = document.getElementById("bias-pill-state");
    const banner = document.getElementById("bias-banner-alert");

    if (isChecked) {
        pill.className = "bias-indicator on";
        pill.innerText = "ON";
        banner.classList.remove("hidden");
    } else {
        pill.className = "bias-indicator off";
        pill.innerText = "OFF";
        banner.classList.add("hidden");
    }

    if (recruiterResults.length > 0) {
        triggerRecruiterMatch();
    }
}

// 5. Trigger Recruiter Match
async function triggerRecruiterMatch() {
    const btn = document.getElementById("btn-run-match");
    const jdText = document.getElementById("recruiter-jd-text").value.trim();

    if (!jdText) {
        alert("Please paste a Job Description or upload a JD document.");
        return;
    }

    if (recruiterCandidatePool.length === 0) {
        alert("Please upload at least one candidate resume into the screening pool.");
        return;
    }

    const weights = getNormalizedWeights();
    const biasActive = document.getElementById("toggle-bias-mitigation").checked;

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Screening &amp; Ranking...';

    try {
        const res = await fetch("/api/match/recruiter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                custom_jd_text: jdText,
                candidates: recruiterCandidatePool,
                weights: weights,
                filter_mode: "soft",
                apply_bias_mitigation: biasActive
            })
        });

        const data = await res.json();
        if (data.status !== "success") {
            showToast("Error: " + (data.message || "Matching failed"));
            return;
        }

        recruiterResults = data.results || [];
        expandedRecruiterRowId = null;
        renderRecruiterTable(recruiterResults, biasActive);

        document.getElementById("results-sub-text").innerText = 
            `Evaluated ${recruiterResults.length} candidates. Click any candidate to view explainability breakdown & verified resume evidence.`;

    } catch (e) {
        showToast("Matching error: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Match &amp; Rank Candidates';
    }
}

function renderRecruiterTable(candidates, biasActive) {
    const tbody = document.getElementById("recruiter-table-body");
    if (!candidates || candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No candidates evaluated.</td></tr>';
        return;
    }

    tbody.innerHTML = candidates.map((c, idx) => {
        const rank = c.rank || (idx + 1);
        const scorePct = Math.round((c.final_score || 0) * 100);

        let scoreClass = "low";
        if (scorePct >= 75) scoreClass = "high";
        else if (scorePct >= 50) scoreClass = "mid";

        let rankShiftHtml = "";
        if (biasActive && typeof c.rank_delta !== 'undefined') {
            if (c.rank_delta > 0) {
                rankShiftHtml = `<span class="rank-shift up" title="Moved up ${c.rank_delta} positions after demographic stripping">▲ +${c.rank_delta}</span>`;
            } else if (c.rank_delta < 0) {
                rankShiftHtml = `<span class="rank-shift down" title="Moved down ${Math.abs(c.rank_delta)} positions after demographic stripping">▼ ${c.rank_delta}</span>`;
            } else {
                rankShiftHtml = `<span class="rank-shift same" title="No change in rank">=</span>`;
            }
        }

        const matchedSkills = c.top_matched_skills && c.top_matched_skills.length > 0
            ? c.top_matched_skills.map(s => `<span class="badge-skill matched">${escapeHtml(s)}</span>`).join("")
            : '<span class="badge-skill none">None identified</span>';

        const missingSkills = c.top_missing_skills && c.top_missing_skills.length > 0
            ? c.top_missing_skills.map(s => `<span class="badge-skill missing">${escapeHtml(s)}</span>`).join("")
            : '<span class="badge-skill none">None (Full match)</span>';

        const isConfident = c.is_confident !== false;
        const confidenceBadge = isConfident
            ? `<span class="confidence-badge confident"><i class="fa-solid fa-check"></i> Confident</span>`
            : `<span class="confidence-badge sparse" title="${escapeHtml(c.confidence_reason || 'Data too sparse')}"><i class="fa-solid fa-triangle-exclamation"></i> Too Sparse</span>`;

        const isExpanded = (expandedRecruiterRowId === c.id);

        return `
            <tr class="clickable-row ${isExpanded ? 'expanded' : ''}" onclick="toggleRecruiterDetail('${c.id}')">
                <td>
                    <div class="rank-box">
                        <span class="rank-num">#${rank}</span>
                        ${rankShiftHtml}
                    </div>
                </td>
                <td>
                    <div class="cand-name-text">${escapeHtml(c.candidate_name)}</div>
                    <div class="cand-exp-sub">${c.years_experience || 0} yrs exp • ${escapeHtml(c.degree || 'Bachelor')}</div>
                </td>
                <td>
                    <div class="score-cell">
                        <span class="score-badge ${scoreClass}">${scorePct}%</span>
                        <div class="score-progress">
                            <div class="score-fill" style="width: ${scorePct}%;"></div>
                        </div>
                    </div>
                </td>
                <td><div class="skills-cell">${matchedSkills}</div></td>
                <td><div class="skills-cell">${missingSkills}</div></td>
                <td>${confidenceBadge}</td>
                <td style="text-align: center;">
                    <i class="fa-solid fa-chevron-down expand-icon"></i>
                </td>
            </tr>
            ${isExpanded ? renderRecruiterDetailRow(c) : ''}
        `;
    }).join("");
}

function toggleRecruiterDetail(candId) {
    expandedRecruiterRowId = (expandedRecruiterRowId === candId) ? null : candId;
    renderRecruiterTable(recruiterResults, document.getElementById("toggle-bias-mitigation").checked);
}

function renderRecruiterDetailRow(c) {
    const isConfident = c.is_confident !== false;
    let warningCallout = "";
    if (!isConfident) {
        warningCallout = `
            <div class="sparse-warning-callout">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <strong>Notice:</strong> ${escapeHtml(c.confidence_reason || 'Source resume or JD is too brief to make a high-confidence evaluation.')}
            </div>
        `;
    }

    return `
        <tr class="detail-row">
            <td colspan="7">
                <div class="detail-card">
                    ${warningCallout}
                    <div class="detail-section">
                        <span class="detail-section-title"><i class="fa-solid fa-comment-dots"></i> Why They Fit / Don't Fit (AI Plain-English Explanation)</span>
                        <div class="detail-explanation-box">
                            ${escapeHtml(c.explanation || 'No detailed explanation generated.')}
                        </div>
                    </div>
                    <div class="detail-section">
                        <span class="detail-section-title"><i class="fa-solid fa-quote-left"></i> Verified Resume Excerpt (Evidence Snippet)</span>
                        <div class="detail-snippet-box">
                            "${escapeHtml(c.resume_snippet || 'No excerpt available.')}"
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

// ============================================================
// CANDIDATE MODE HANDLERS
// ============================================================

// 1. Candidate Resume File Upload (Extracts clean text via server pdfplumber - NO GIBBERISH)
async function handleCandidateResumeFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    showToast(`Extracting clean text from "${file.name}"...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/extract-text", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.status === "success") {
            document.getElementById("candidate-resume-text").value = data.text;
            showToast(`Resume text loaded cleanly from "${file.name}"!`);
        } else {
            showToast("Extraction error: " + (data.message || "Failed to extract text from resume"));
        }
    } catch (e) {
        showToast("Upload error: " + e.message);
    } finally {
        event.target.value = "";
    }
}

// 2. User-Controlled Target Jobs Pool Management
async function handleCandidateJobFilesUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    showToast(`Uploading ${files.length} job description(s)...`);

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/extract-text", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (data.status === "success") {
                const title = file.name.replace(/\.(txt|pdf)$/i, "").replace(/[_-]/g, " ").trim();
                candidateTargetJobs.push({
                    id: `job_up_${Date.now()}_${i}`,
                    title: title || "Target Role",
                    company: "Target Company",
                    description: data.text
                });
            }
        } catch (e) {
            console.error("Error processing job file:", file.name, e);
        }
    }

    renderCandidateJobsList();
    showToast(`Target jobs pool updated! (${candidateTargetJobs.length} jobs total)`);
    event.target.value = "";
}

function addCandidateJobFromPaste() {
    const titleInput = document.getElementById("cand-job-title-input");
    const descInput = document.getElementById("cand-job-desc-input");
    const title = titleInput.value.trim();
    const desc = descInput.value.trim();

    if (!desc) {
        alert("Please paste the job description text.");
        return;
    }

    candidateTargetJobs.push({
        id: `job_paste_${Date.now()}`,
        title: title || "Target Position",
        company: "Target Company",
        description: desc
    });

    titleInput.value = "";
    descInput.value = "";
    renderCandidateJobsList();
    showToast("Job added to comparison pool!");
}

async function loadSampleTechJobs() {
    try {
        const res = await fetch("/api/jobs");
        const jobs = await res.json();
        // Load first 4 diverse jobs
        const samples = jobs.slice(0, 4).map(j => ({
            id: j.id,
            title: j.title,
            company: j.company || "TechCorp",
            description: j.description
        }));

        candidateTargetJobs.push(...samples);
        renderCandidateJobsList();
        showToast("Loaded 4 sample tech jobs into your comparison pool!");
    } catch (e) {
        showToast("Error loading sample jobs: " + e.message);
    }
}

function renderCandidateJobsList() {
    const listEl = document.getElementById("candidate-jobs-list");
    const countEl = document.getElementById("candidate-jobs-count");
    const clearBtn = document.getElementById("btn-clear-candidate-jobs");

    if (!listEl) return;

    const count = candidateTargetJobs.length;
    countEl.innerText = `${count} job description${count === 1 ? '' : 's'} added to pool`;
    if (clearBtn) {
        clearBtn.style.display = count > 0 ? "inline-flex" : "none";
    }

    if (count === 0) {
        listEl.innerHTML = '<span style="font-size: 12px; color: var(--text-light); font-style: italic;">No jobs added yet. Upload files, paste below, or quick-load sample tech jobs.</span>';
        return;
    }

    listEl.innerHTML = candidateTargetJobs.map((j, idx) => `
        <div class="file-pill">
            <i class="fa-solid fa-briefcase" style="color: var(--primary);"></i>
            <span class="file-name" title="${escapeHtml(j.title)}">${escapeHtml(j.title)}</span>
            <button class="file-remove" onclick="removeCandidateJob(${idx})" title="Remove job">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `).join("");
}

function removeCandidateJob(idx) {
    if (idx >= 0 && idx < candidateTargetJobs.length) {
        candidateTargetJobs.splice(idx, 1);
        renderCandidateJobsList();
    }
}

function clearCandidateJobs() {
    candidateTargetJobs = [];
    renderCandidateJobsList();
    showToast("Job comparison pool cleared.");
}

// 3. Trigger Candidate Match
async function triggerCandidateMatch() {
    const btn = document.getElementById("btn-run-candidate-match");
    const resumeText = document.getElementById("candidate-resume-text").value.trim();

    if (!resumeText) {
        alert("Please paste your resume text or upload your resume document.");
        return;
    }

    if (candidateTargetJobs.length === 0) {
        alert("Please add at least one job description into your comparison pool.");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Matching Against Target Jobs...';

    try {
        const res = await fetch("/api/match/candidate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                custom_resume_text: resumeText,
                jobs: candidateTargetJobs
            })
        });

        const data = await res.json();
        if (data.status !== "success") {
            showToast("Error: " + (data.message || "Matching failed"));
            return;
        }

        candidateResults = data.results || [];
        expandedCandidateRowId = null;
        renderCandidateTable(candidateResults);

        document.getElementById("candidate-results-sub-text").innerText = 
            `Compared your profile against ${candidateResults.length} target positions. Click any job row to view your skill gaps & step-by-step roadmap.`;

    } catch (e) {
        showToast("Candidate matching error: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Match Against Target Jobs';
    }
}

function renderCandidateTable(jobs) {
    const tbody = document.getElementById("candidate-table-body");
    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No matching positions found.</td></tr>';
        return;
    }

    tbody.innerHTML = jobs.map((job, idx) => {
        const rank = job.rank || (idx + 1);
        const scorePct = Math.round((job.final_score || 0) * 100);

        let scoreClass = "low";
        if (scorePct >= 75) scoreClass = "high";
        else if (scorePct >= 50) scoreClass = "mid";

        const matchedSkills = job.top_matched_skills && job.top_matched_skills.length > 0
            ? job.top_matched_skills.map(s => `<span class="badge-skill matched">${escapeHtml(s)}</span>`).join("")
            : '<span class="badge-skill none">None</span>';

        const missingSkills = job.top_missing_skills && job.top_missing_skills.length > 0
            ? job.top_missing_skills.map(s => `<span class="badge-skill missing">${escapeHtml(s)}</span>`).join("")
            : '<span class="badge-skill none">None (Strong fit)</span>';

        const isConfident = job.is_confident !== false;
        const confidenceBadge = isConfident
            ? `<span class="confidence-badge confident"><i class="fa-solid fa-check"></i> Confident</span>`
            : `<span class="confidence-badge sparse" title="${escapeHtml(job.confidence_reason || 'Resume is sparse')}"><i class="fa-solid fa-triangle-exclamation"></i> Too Sparse</span>`;

        const isExpanded = (expandedCandidateRowId === job.job_id);

        return `
            <tr class="clickable-row ${isExpanded ? 'expanded' : ''}" onclick="toggleCandidateDetail('${job.job_id}')">
                <td><span class="rank-num">#${rank}</span></td>
                <td>
                    <div class="cand-name-text">${escapeHtml(job.job_title)}</div>
                    <div class="cand-exp-sub">${escapeHtml(job.company || 'Target Company')}</div>
                </td>
                <td>
                    <div class="score-cell">
                        <span class="score-badge ${scoreClass}">${scorePct}%</span>
                        <div class="score-progress">
                            <div class="score-fill" style="width: ${scorePct}%;"></div>
                        </div>
                    </div>
                </td>
                <td><div class="skills-cell">${matchedSkills}</div></td>
                <td><div class="skills-cell">${missingSkills}</div></td>
                <td>${confidenceBadge}</td>
                <td style="text-align: center;">
                    <i class="fa-solid fa-chevron-down expand-icon"></i>
                </td>
            </tr>
            ${isExpanded ? renderCandidateDetailRow(job) : ''}
        `;
    }).join("");
}

function toggleCandidateDetail(jobId) {
    expandedCandidateRowId = (expandedCandidateRowId === jobId) ? null : jobId;
    renderCandidateTable(candidateResults);
}

function renderCandidateDetailRow(job) {
    const isConfident = job.is_confident !== false;
    let warningCallout = "";
    if (!isConfident) {
        warningCallout = `
            <div class="sparse-warning-callout">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <strong>Notice:</strong> ${escapeHtml(job.confidence_reason || 'Resume text is too brief to make a high-confidence judgment.')}
            </div>
        `;
    }

    const roadmaps = (job.improvement_suggestions || []).map(step => `<li>${escapeHtml(step)}</li>`).join("");

    return `
        <tr class="detail-row">
            <td colspan="7">
                <div class="detail-card">
                    ${warningCallout}

                    <div class="detail-section">
                        <span class="detail-section-title"><i class="fa-solid fa-bullseye"></i> Match Fit Assessment</span>
                        <div class="detail-explanation-box">
                            ${escapeHtml(job.fit_summary || 'Fit analysis complete.')}
                        </div>
                    </div>

                    ${roadmaps ? `
                        <div class="detail-section">
                            <span class="detail-section-title"><i class="fa-solid fa-road"></i> Actionable Roadmap to Increase Your Match</span>
                            <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 12px 18px; border-radius: var(--radius-sm);">
                                <ul class="improvement-list">
                                    ${roadmaps}
                                </ul>
                            </div>
                        </div>
                    ` : ''}

                    <div class="detail-section">
                        <span class="detail-section-title"><i class="fa-solid fa-file-lines"></i> Job Description Snippet</span>
                        <div class="detail-snippet-box">
                            "${escapeHtml(job.jd_snippet || 'No job snippet available.')}"
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

// ============================================================
// UTILITIES
// ============================================================
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.remove("hidden");
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 3200);
}
