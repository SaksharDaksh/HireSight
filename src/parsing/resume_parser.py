import os
import re
from typing import Dict, List, Any
import PyPDF2

class ResumeParser:
    """
    Parses resume files (PDF, TXT, JSON) and chunks them for semantic RAG indexing.
    """

    def __init__(self):
        self.section_patterns = {
            "summary": re.compile(r"(summary|objective|profile|about\s+me)", re.IGNORECASE),
            "experience": re.compile(r"(experience|work\s+history|employment|career)", re.IGNORECASE),
            "skills": re.compile(r"(skills|technical\s+skills|core\s+competencies|technologies)", re.IGNORECASE),
            "education": re.compile(r"(education|academic\s+background|degrees|qualification)", re.IGNORECASE),
            "projects": re.compile(r"(projects|portfolio|personal\s+projects)", re.IGNORECASE)
        }

    def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pdfplumber with PyPDF2 fallback."""
        import logging
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        logging.getLogger("pdfplumber").setLevel(logging.ERROR)
        text_content = []
        # Try pdfplumber first
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        text_content.append(txt)
            if text_content:
                return "\n\n".join(text_content)
        except Exception:
            pass

        # Fallback to PyPDF2
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_content.append(extracted)
            return "\n\n".join(text_content)
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"

    def parse_text(self, file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def parse_file(self, file_path: str) -> str:
        """Dispatch to appropriate parser by file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self.parse_pdf(file_path)
        elif ext in [".txt", ".md", ".json"]:
            return self.parse_text(file_path)
        else:
            return self.parse_text(file_path)

    def clean_text(self, text: str) -> str:
        """Normalize whitespace, remove non-printable characters."""
        text = re.sub(r"[\r\t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    def chunk_resume(self, text: str) -> List[Dict[str, str]]:
        """
        Split resume into semantic sections/chunks for RAG retrieval.
        Returns a list of chunks with metadata: {'section': ..., 'content': ...}
        """
        lines = text.split("\n")
        chunks = []
        current_section = "general"
        current_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            detected_section = None
            if len(line_str) < 50 and (":" in line_str or line_str.isupper() or line_str.istitle()):
                for sec_name, pattern in self.section_patterns.items():
                    if pattern.search(line_str):
                        detected_section = sec_name
                        break

            if detected_section and detected_section != current_section:
                if current_lines:
                    chunks.append({
                        "section": current_section,
                        "content": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                current_section = detected_section

            current_lines.append(line_str)

        if current_lines:
            chunks.append({
                "section": current_section,
                "content": "\n".join(current_lines).strip()
            })

        # Fallback if no sections detected
        if not chunks:
            chunks.append({"section": "full", "content": text})

        return chunks
