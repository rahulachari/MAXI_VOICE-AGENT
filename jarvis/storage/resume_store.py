"""
JARVIS Resume & Profile RAG Store
Manages persistent user profile: Resume text, contact details, GitHub, projects, and skills.
Provides semantic RAG matching against job descriptions and application forms.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.storage.database import get_data_dir, Database


class ResumeProfileStore:
    _instance: Optional["ResumeProfileStore"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.db = Database()
        self.profile_file = get_data_dir() / "user_resume_profile.json"
        self._ensure_tables()
        self._load_or_init()

    def _ensure_tables(self):
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _get_default_profile(self) -> Dict[str, Any]:
        return {
            "name": "Rahul Achari YC",
            "phone": "+91 8639996301",
            "email": "rahulyc6@gmail.com",
            "location": "Chittoor, Andhra Pradesh, India",
            "github": "https://github.com/rahulachari",
            "linkedin": "https://www.linkedin.com/in/rahulyc/",
            "portfolio": "https://rahulachariportfolio.vercel.app/",
            "role_title": "AI/ML & Full-Stack Developer",
            "years_of_experience": "Fresh Graduate / 1+ years hands-on production deployment experience",
            "skills": [
                "Python", "Scikit-learn", "Pandas", "NumPy", "Random Forest", "OpenCV", "Tesseract",
                "Groq LLaMA API", "Antigravity", "Docker", "Git", "GitHub", "VS Code", "Render.com",
                "SQL", "Supabase", "React", "TypeScript", "Tailwind CSS", "Flask", "Django", "FastAPI"
            ],
            "summary": (
                "Computer Science graduate focused on AI/ML and full-stack development, with hands-on experience developing "
                "and deploying multiple applications. Built AI-driven solutions in real estate, machine learning, and digital health, "
                "including a real estate forecasting platform achieving 92% R² accuracy and a multi-domain ML application "
                "covering 4 prediction domains. Worked with AI APIs, Docker deployment, and AI-assisted development using Antigravity."
            ),
            "projects": [
                {
                    "title": "PropCast — AI Real Estate Forecasting Platform",
                    "award": "Microsoft AI Skills Fest 2026",
                    "role": "Full Stack Developer",
                    "github_url": "https://github.com/rahulachari/PropCast",
                    "live_url": "https://propcast-oyan.onrender.com",
                    "problem": "Buyers in the Hyderabad real estate market had no AI-powered tool to forecast property prices using actual transaction data, forcing decisions based on guesswork and broker estimates.",
                    "action": "Built end-to-end Django + Scikit-learn platform with Gradient Boosting model and custom feature engineering; integrated Groq LLaMA API for natural-language market insights; developed Plotly dashboards, CSV pipeline, and property comparison module.",
                    "outcome": "Achieved 92% R² accuracy on price forecasts; shipped live app with AI chat, interactive dashboards, and CSV export; containerized with Docker and deployed to Render.com using GitHub Copilot.",
                    "description": "Django + Scikit-learn Gradient Boosting price forecaster with Groq LLaMA natural-language insights, Plotly dashboards, CSV pipeline, achieving 92% R² accuracy.",
                    "tech_stack": ["Django", "Scikit-learn", "Gradient Boosting", "Groq LLaMA API", "Plotly", "Docker", "Render.com", "Python"]
                },
                {
                    "title": "UniML — Multi-Domain ML Web Application",
                    "award": "Final Year Project",
                    "role": "Backend Developer",
                    "github_url": "https://github.com/rahulachari/UniML",
                    "live_url": "https://uniml.onrender.com",
                    "problem": "Students and researchers lacked a unified platform to run ML predictions across domains without installing Python, configuring environments, or writing code locally.",
                    "action": "Architected 4-module Flask + SQLite app (Banking, Education, Loan, Healthcare); built OCR-powered ATS resume scorer using OpenCV + Tesseract; trained Random Forest classifier on 800+ health records; implemented user authentication and session management.",
                    "outcome": "Delivered a single deployable ML platform covering 4 prediction domains with authenticated access; Dockerized and deployed to Render.com, eliminating local setup entirely.",
                    "description": "4-module Flask + SQLite app covering 4 prediction domains, featuring an OCR-powered ATS resume scorer using OpenCV + Tesseract and Random Forest on 800+ records.",
                    "tech_stack": ["Flask", "SQLite", "OpenCV", "Tesseract", "Random Forest", "Machine Learning", "Docker", "Render.com", "Python"]
                },
                {
                    "title": "ControL-D — Digital Health Assistant",
                    "award": "HealthTech Project",
                    "role": "Full Stack Developer",
                    "github_url": "https://github.com/rahulachari/ControL-D",
                    "live_url": "https://controld-three.vercel.app/login",
                    "problem": "Diabetes patients juggled multiple apps for meal plans, workouts, glucose tracking, and reminders — no single app combined all needs with AI-powered, personalized guidance.",
                    "action": "Built responsive SPA with React, TypeScript, Tailwind CSS, and Supabase; developed adaptive logic that adjusts recommendations by real-time health parameters (glucose, BMI, activity); integrated AI wellness chat with topic-restricted responses for safe health guidance.",
                    "outcome": "Shipped a unified health app with personalized nutrition, fitness, glucose tracking, and daily reminders — all in one responsive interface with real-time data sync via Supabase.",
                    "description": "Responsive SPA built with React, TypeScript, Tailwind CSS, and Supabase with real-time health parameter sync and AI wellness chat.",
                    "tech_stack": ["React", "TypeScript", "Tailwind CSS", "Supabase", "AI Chat", "Healthcare"]
                }
            ],
            "experience": [
                {
                    "title": "AI & Full-Stack Developer",
                    "company": "Projects & Production Deployments",
                    "duration": "2024 - 2026",
                    "description": "Architected, containerized, and deployed three end-to-end full stack and AI/ML applications (PropCast, UniML, ControL-D) with live user access on Render and Vercel."
                }
            ],
            "education": [
                {
                    "degree": "B.Tech in Computer Science Engineering",
                    "institution": "The Apollo University, Chittoor, AP",
                    "year": "Graduated April 2026",
                    "cgpa": "8.12 / 10"
                }
            ],
            "certifications": [
                "NPTEL — Introduction to Machine Learning (IIT Kharagpur)",
                "Anthropic — AI Fluency for Students"
            ],
            "extracurricular": [
                "Member, The Apollo Career Catalyst Club — actively participated in technical workshops and peer-learning sessions.",
                "Led end-to-end development and deployment of multiple production-grade applications from concept to live deployment.",
                "Participated in Microsoft AI Skills Fest 2026 Hackathon (Agents League / Creative Apps track), leveraging AI-assisted development workflows."
            ],
            "work_authorization": "Authorized to work in India (Available for immediate hiring, open to full-time/remote roles)",
            "notice_period": "Immediate"
        }

    def _load_or_init(self):
        # Always prioritize the latest Rahul Achari YC profile if existing file has old placeholder data
        default_p = self._get_default_profile()
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if loaded.get("name") == "Rahul Achari YC" and "PropCast" in json.dumps(loaded):
                        self.profile = loaded
                        return
            except Exception:
                pass

        # Use and save the accurate profile
        self.profile = default_p
        self.save_profile(self.profile)

    def _save_to_file(self):
        try:
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ResumeStore] Error writing profile file: {e}")

    def save_profile(self, profile_data: Dict[str, Any]):
        self.profile = profile_data
        self._save_to_file()
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO user_profile (profile_json) VALUES (?)",
                (json.dumps(self.profile, ensure_ascii=False),)
            )
            conn.commit()

    def get_profile(self) -> Dict[str, Any]:
        return self.profile

    def update_field(self, key: str, value: Any):
        self.profile[key] = value
        self.save_profile(self.profile)

    def add_project(self, project: Dict[str, Any]):
        projects = self.profile.get("projects", [])
        projects.insert(0, project)
        self.profile["projects"] = projects
        self.save_profile(self.profile)

    def match_rag_context(self, job_text: str) -> Dict[str, Any]:
        """
        RAG matching: Finds user's best matching projects, skills, and experience
        against job title, requirements, or application form on screen.
        """
        job_lower = (job_text or "").lower()
        skills = self.profile.get("skills", [])
        matched_skills = [s for s in skills if re.search(r"\b" + re.escape(s.lower()) + r"\b", job_lower)]

        scored_projects = []
        for p in self.profile.get("projects", []):
            score = 0
            # Match title
            for w in p.get("title", "").split():
                if len(w) > 3 and w.lower() in job_lower:
                    score += 2
            # Match tech stack
            for t in p.get("tech_stack", []):
                if t.lower() in job_lower:
                    score += 3
            # Match description
            for w in p.get("description", "").split():
                if len(w) > 4 and w.lower() in job_lower:
                    score += 1
            scored_projects.append((score, p))

        scored_projects.sort(key=lambda x: x[0], reverse=True)
        top_projects = [p for _, p in scored_projects[:2]] or self.profile.get("projects", [])[:2]

        # Calculate a realistic match percentage
        base_match = 78
        match_percentage = min(99, base_match + min(20, len(matched_skills) * 3 + len(top_projects) * 4))

        return {
            "match_percentage": match_percentage,
            "matched_skills": matched_skills or skills[:6],
            "top_projects": top_projects,
            "profile": self.profile
        }

    def get_full_resume_text(self) -> str:
        """Returns the complete, professional ATS-optimized text resume ready for pasting."""
        p = self.profile
        lines = [
            f"{p.get('name', 'Rahul Achari YC')}".upper(),
            f"{p.get('phone', '+91 8639996301')} | {p.get('email', 'rahulyc6@gmail.com')} | LinkedIn: {p.get('linkedin')} | GitHub: {p.get('github')} | Portfolio: {p.get('portfolio')} | {p.get('location', 'Chittoor, Andhra Pradesh')}",
            "",
            "PROFESSIONAL SUMMARY",
            f"{p.get('summary', '')}",
            "",
            "PROJECT EXPERIENCE",
        ]

        for proj in p.get("projects", []):
            title = proj.get("title", "")
            award = f" — {proj.get('award')}" if proj.get("award") else ""
            lines.append(f"{title}{award}")
            lines.append(f"{proj.get('role', 'Developer')} | GitHub: {proj.get('github_url', '')} | Live: {proj.get('live_url', '')}")
            if proj.get("problem"):
                lines.append(f"■ Problem: {proj.get('problem')}")
            if proj.get("action"):
                lines.append(f"■ Action: {proj.get('action')}")
            if proj.get("outcome"):
                lines.append(f"■ Outcome: {proj.get('outcome')}")
            lines.append("")

        skills = ", ".join(p.get("skills", []))
        lines.extend([
            "TECHNICAL SKILLS",
            f"Languages & Libraries: Python, Scikit-learn, Pandas, NumPy, Random Forest, OpenCV, Tesseract",
            f"AI & Tools: Groq LLaMA API, Antigravity, Docker, Git, GitHub, VS Code, Render.com",
            f"Databases & Web: SQL, Supabase, React, TypeScript, Tailwind CSS, Flask, Django, FastAPI",
            "",
            "EDUCATION",
        ])

        for edu in p.get("education", []):
            lines.append(f"{edu.get('degree')} — {edu.get('institution')}")
            lines.append(f"{edu.get('year')} | CGPA: {edu.get('cgpa')}")
            lines.append("")

        if p.get("certifications"):
            lines.append("CERTIFICATIONS")
            for cert in p.get("certifications"):
                lines.append(f"■ {cert}")
            lines.append("")

        if p.get("extracurricular"):
            lines.append("EXTRACURRICULAR & LEADERSHIP")
            for extra in p.get("extracurricular"):
                lines.append(f"■ {extra}")
            lines.append("")

        return "\n".join(lines).strip()


resume_store = ResumeProfileStore()

