-- ==========================================================
-- Fairness-Aware Resume <-> Job Description Matcher
-- Relational Database Schema (MySQL 8.x & SQLite compatible)
-- ==========================================================

-- 1. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) DEFAULT 'TechCorp Solutions',
    department VARCHAR(128) DEFAULT 'Engineering',
    min_years_experience INT DEFAULT 0,
    required_skills TEXT NOT NULL,         -- JSON array or comma-separated list
    preferred_skills TEXT,                 -- JSON array or comma-separated list
    degree_required VARCHAR(128) DEFAULT 'Bachelor',
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Resumes Table
CREATE TABLE IF NOT EXISTS resumes (
    id VARCHAR(64) PRIMARY KEY,
    candidate_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(64),
    years_experience INT DEFAULT 0,
    degree VARCHAR(128),
    institution VARCHAR(255),              -- May be stripped during bias mitigation
    skills TEXT NOT NULL,                  -- JSON array or comma-separated list
    summary TEXT,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Matches & Scoring Table
CREATE TABLE IF NOT EXISTS matches (
    id INT AUTO_INCREMENT PRIMARY KEY,     -- In SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
    job_id VARCHAR(64) NOT NULL,
    resume_id VARCHAR(64) NOT NULL,
    semantic_score FLOAT DEFAULT 0.0,
    skill_overlap_score FLOAT DEFAULT 0.0,
    experience_score FLOAT DEFAULT 0.0,
    final_score FLOAT DEFAULT 0.0,
    xgb_probability FLOAT DEFAULT 0.0,
    hard_constraint_passed BOOLEAN DEFAULT TRUE,
    rank_position INT DEFAULT 0,
    is_bias_mitigated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

-- 4. Bias & Fairness Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    resume_id VARCHAR(64) NOT NULL,
    original_rank INT NOT NULL,
    mitigated_rank INT NOT NULL,
    rank_delta INT NOT NULL,               -- (original_rank - mitigated_rank)
    original_score FLOAT NOT NULL,
    mitigated_score FLOAT NOT NULL,
    score_delta FLOAT NOT NULL,
    stripped_signals TEXT,                 -- JSON of masked demographic attributes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Recruiter Feedback & Active Learning Table
CREATE TABLE IF NOT EXISTS recruiter_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    resume_id VARCHAR(64) NOT NULL,
    decision VARCHAR(32) NOT NULL,         -- 'accept', 'reject', 'interview'
    fit_rating INT DEFAULT 3,              -- 1 to 5 scale
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
