import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import sqlite3
import json
from typing import Dict, List, Any, Optional

class DatabaseManager:
    """
    Manages persistence with MySQL support and transparent automatic SQLite fallback.
    """

    def __init__(self, sqlite_path: str = "data/app_database.db"):
        self.sqlite_path = sqlite_path
        self.backend = "sqlite"
        self.mysql_conn = None
        self.init_database()

    def get_connection(self):
        """Attempts MySQL first if credentials provided, falls back to SQLite."""
        mysql_host = os.getenv("MYSQL_HOST")
        if mysql_host:
            try:
                import pymysql
                conn = pymysql.connect(
                    host=mysql_host,
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", ""),
                    database=os.getenv("MYSQL_DB", "resume_matcher"),
                    cursorclass=pymysql.cursors.DictCursor
                )
                self.backend = "mysql"
                return conn
            except Exception as e:
                print(f"[DB] MySQL connection failed ({str(e)}). Falling back to SQLite.")

        # SQLite Fallback
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        self.backend = "sqlite"
        return conn

    def init_database(self):
        """Initializes tables using schema.sql."""
        conn = self.get_connection()
        schema_path = "data/schema.sql"
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                ddl = f.read()

            # Adapt MySQL DDL for SQLite if in SQLite mode
            if self.backend == "sqlite":
                ddl = ddl.replace("INT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                ddl = ddl.replace("AUTO_INCREMENT", "AUTOINCREMENT")
                ddl = ddl.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
                ddl = ddl.replace("BOOLEAN DEFAULT TRUE", "INTEGER DEFAULT 1")
                ddl = ddl.replace("BOOLEAN DEFAULT FALSE", "INTEGER DEFAULT 0")

            cursor = conn.cursor()
            for statement in ddl.split(";"):
                stmt = statement.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as ex:
                        print(f"[DB Init Stmt Error]: {ex} in: {stmt[:60]}")
            conn.commit()
        conn.close()

    def save_job(self, jd: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
            INSERT OR REPLACE INTO jobs 
            (id, title, company, department, min_years_experience, required_skills, preferred_skills, degree_required, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.backend == "sqlite" else """
            REPLACE INTO jobs 
            (id, title, company, department, min_years_experience, required_skills, preferred_skills, degree_required, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            jd.get("id"),
            jd.get("title"),
            jd.get("company", "TechCorp"),
            jd.get("department", "Engineering"),
            int(jd.get("min_years_experience", 0)),
            json.dumps(jd.get("required_skills", [])),
            json.dumps(jd.get("preferred_skills", [])),
            jd.get("degree_required", "Bachelor"),
            jd.get("description", "")
        )
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def save_resume(self, res: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
            INSERT OR REPLACE INTO resumes 
            (id, candidate_name, email, phone, years_experience, degree, institution, skills, summary, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.backend == "sqlite" else """
            REPLACE INTO resumes 
            (id, candidate_name, email, phone, years_experience, degree, institution, skills, summary, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            res.get("id"),
            res.get("candidate_name", "Candidate"),
            res.get("email", ""),
            res.get("phone", ""),
            int(res.get("years_experience", res.get("years_of_experience", 0))),
            res.get("degree", res.get("education", {}).get("degree", "Bachelor")),
            res.get("institution", res.get("education", {}).get("institution", "")),
            json.dumps(res.get("skills", [])),
            res.get("summary", ""),
            res.get("raw_text", "")
        )
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def record_feedback(self, job_id: str, resume_id: str, decision: str, rating: int, notes: str = ""):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO recruiter_feedback (job_id, resume_id, decision, fit_rating, notes)
            VALUES (?, ?, ?, ?, ?)
        """ if self.backend == "sqlite" else """
            INSERT INTO recruiter_feedback (job_id, resume_id, decision, fit_rating, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (job_id, resume_id, decision, rating, notes))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    db = DatabaseManager()
    print(f"Database initialized successfully using backend: {db.backend}")
