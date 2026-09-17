import os
import json

def generate_sample_data():
    os.makedirs("data/job_descriptions", exist_ok=True)
    os.makedirs("data/resumes", exist_ok=True)

    # 1. Curate 10 Job Descriptions
    jds = [
        {
            "id": "jd_01_ml_engineer",
            "title": "Machine Learning Engineer",
            "company": "Nexus AI Labs",
            "department": "AI & Data",
            "min_years_experience": 3,
            "degree_required": "Bachelor",
            "required_skills": ["Python", "PyTorch", "Scikit-Learn", "Docker", "Machine Learning", "SQL"],
            "preferred_skills": ["MLOps", "Kubernetes", "AWS", "XGBoost", "FastAPI"],
            "description": (
                "We are seeking an experienced Machine Learning Engineer to design, build, and deploy production ML systems. "
                "The ideal candidate must have at least 3 years of hands-on experience developing ML models using Python, PyTorch, "
                "and Scikit-Learn, with strong SQL skills and containerization using Docker. Experience with MLOps pipelines and AWS is a plus."
            )
        },
        {
            "id": "jd_02_backend_lead",
            "title": "Senior Backend Developer",
            "company": "FinTech Prime",
            "department": "Core Platform",
            "min_years_experience": 5,
            "degree_required": "Bachelor",
            "required_skills": ["Python", "Flask", "PostgreSQL", "Redis", "Microservices", "REST APIs"],
            "preferred_skills": ["Go", "Kubernetes", "Kafka", "AWS", "System Design"],
            "description": (
                "FinTech Prime is hiring a Senior Backend Developer with 5+ years of experience in architecting high-throughput distributed systems. "
                "Must be proficient in Python, Flask or FastAPI, PostgreSQL database design, Redis caching, and microservices architecture. "
                "Experience with message brokers like Kafka and cloud infrastructure on AWS is highly desirable."
            )
        },
        {
            "id": "jd_03_data_analyst",
            "title": "Data Analyst (BI & Analytics)",
            "company": "RetailPulse Global",
            "department": "Business Intelligence",
            "min_years_experience": 2,
            "degree_required": "Bachelor",
            "required_skills": ["SQL", "Power BI", "Excel", "Python", "Data Visualization", "EDA"],
            "preferred_skills": ["Tableau", "DAX", "Pandas", "Statistical Testing", "ETL"],
            "description": (
                "RetailPulse is seeking a detail-oriented Data Analyst to uncover actionable business insights. "
                "Requirements include at least 2 years of experience with advanced SQL queries, Power BI dashboard development, "
                "Excel financial modeling, and Python for exploratory data analysis (EDA). Strong communication and visualization skills required."
            )
        },
        {
            "id": "jd_04_fullstack_dev",
            "title": "Full Stack Engineer",
            "company": "CloudSprint Tech",
            "department": "Product Engineering",
            "min_years_experience": 3,
            "degree_required": "Bachelor",
            "required_skills": ["JavaScript", "React", "Python", "HTML", "CSS", "REST APIs", "MySQL"],
            "preferred_skills": ["TypeScript", "Docker", "Next.js", "Node.js", "GraphQL"],
            "description": (
                "Looking for a dynamic Full Stack Engineer capable of working across responsive frontend interfaces and scalable backend services. "
                "Must possess 3+ years of experience with React, HTML5, CSS3, JavaScript, Python backend APIs, and MySQL relational databases."
            )
        },
        {
            "id": "jd_05_nlp_engineer",
            "title": "NLP / LLM Research Engineer",
            "company": "CognitiveGen AI",
            "department": "Applied Research",
            "min_years_experience": 4,
            "degree_required": "Master",
            "required_skills": ["Python", "PyTorch", "Transformers", "NLP", "HuggingFace", "RAG"],
            "preferred_skills": ["LangChain", "Vector Databases", "Fine-Tuning", "C++", "FastAPI"],
            "description": (
                "CognitiveGen AI is pioneering domain-specific generative AI solutions. We need an NLP Engineer with a Master's degree "
                "and 4+ years of experience in transformer models, HuggingFace libraries, retrieval-augmented generation (RAG), "
                "vector databases, and fine-tuning open-source LLMs."
            )
        },
        {
            "id": "jd_06_devops_engineer",
            "title": "DevOps & Cloud Engineer",
            "company": "HyperScale Cloud",
            "department": "Infrastructure",
            "min_years_experience": 3,
            "degree_required": "Bachelor",
            "required_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux"],
            "preferred_skills": ["Ansible", "Prometheus", "Python", "Bash", "Security"],
            "description": (
                "Seeking an infrastructure specialist to automate deployment pipelines, manage Kubernetes clusters, "
                "and enforce cloud security standards across AWS. At least 3 years experience with Terraform, Docker, and CI/CD pipelines."
            )
        },
        {
            "id": "jd_07_data_scientist",
            "title": "Lead Data Scientist",
            "company": "Predictive Health Systems",
            "department": "Data Science",
            "min_years_experience": 5,
            "degree_required": "Master",
            "required_skills": ["Python", "Machine Learning", "Scikit-Learn", "XGBoost", "SHAP", "Pandas", "SQL"],
            "preferred_skills": ["SMOTE", "Healthcare Domain", "Deep Learning", "A/B Testing", "Feature Store"],
            "description": (
                "Seeking a Lead Data Scientist to build predictive models for patient diagnostics. Minimum 5 years of experience "
                "in supervised learning, tree-based models (XGBoost, LightGBM), model explainability using SHAP, handling imbalanced datasets "
                "using SMOTE, and scientific Python stack."
            )
        },
        {
            "id": "jd_08_frontend_dev",
            "title": "Frontend UI/UX Developer",
            "company": "PixelCraft Studio",
            "department": "Design & UI",
            "min_years_experience": 2,
            "degree_required": "Bachelor",
            "required_skills": ["JavaScript", "HTML", "CSS", "React", "Responsive Design"],
            "preferred_skills": ["Figma", "Tailwind CSS", "TypeScript", "Web Performance", "Accessibility"],
            "description": (
                "Join PixelCraft to build beautiful, accessible, and responsive user experiences. Requires 2+ years of experience "
                "writing modular JavaScript, semantic HTML5, modern CSS styling, and component architectures in React."
            )
        },
        {
            "id": "jd_09_database_admin",
            "title": "Database Engineer / MySQL Administrator",
            "company": "Enterprise Data Hub",
            "department": "Database Systems",
            "min_years_experience": 4,
            "degree_required": "Bachelor",
            "required_skills": ["MySQL", "SQL", "Database Optimization", "Indexing", "Backup & Recovery"],
            "preferred_skills": ["PostgreSQL", "Replication", "Python", "Linux", "Performance Tuning"],
            "description": (
                "Responsible for managing, tuning, and securing mission-critical enterprise MySQL clusters. "
                "Requires 4+ years of hands-on database administration, schema design, query optimization, and high availability replication."
            )
        },
        {
            "id": "jd_10_cpp_systems_dev",
            "title": "C++ High Performance Systems Engineer",
            "company": "UltraLatency Trading",
            "department": "Low Latency Core",
            "min_years_experience": 3,
            "degree_required": "Bachelor",
            "required_skills": ["C++", "Data Structures", "Algorithms", "Multithreading", "Linux"],
            "preferred_skills": ["Network Programming", "Memory Management", "C++20", "Python", "CMake"],
            "description": (
                "Seeking a C++ engineer for low-latency, multi-threaded algorithm acceleration and core matching engines. "
                "Must demonstrate deep knowledge of C++ modern standards, memory layout, cache optimization, and concurrent programming."
            )
        }
    ]

    for jd in jds:
        path = os.path.join("data/job_descriptions", f"{jd['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(jd, f, indent=2)

    # 2. Curate 35 Resumes (Covering varied experience, skills, degrees, demographic names, schools)
    # We deliberately include candidates with prestige names/schools and standard ones to test bias mitigation!
    resumes = [
        {
            "id": "res_01",
            "candidate_name": "Aarav Sharma",
            "gender_indicator": "he/him",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "Stanford University",
            "email": "aarav.sharma@example.com",
            "skills": ["Python", "PyTorch", "Scikit-Learn", "Machine Learning", "Docker", "SQL", "FastAPI", "Pandas", "XGBoost"],
            "summary": "Experienced ML Engineer with 4 years building deep learning and classical ML models. He graduated from Stanford University.",
            "past_roles": [{"title": "ML Engineer", "company": "AlphaAI", "duration_years": 4}],
            "target_role": "Machine Learning Engineer"
        },
        {
            "id": "res_02",
            "candidate_name": "Priya Patel",
            "gender_indicator": "she/her",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "State University of Technology",
            "email": "priya.patel@example.com",
            "skills": ["Python", "PyTorch", "Scikit-Learn", "Docker", "Machine Learning", "SQL", "AWS", "MLOps"],
            "summary": "Machine Learning practitioner with 4 years deploying computer vision and predictive models. She specialized in Docker containerization and MLOps.",
            "past_roles": [{"title": "Data Scientist", "company": "InnoTech", "duration_years": 4}],
            "target_role": "Machine Learning Engineer"
        },
        {
            "id": "res_03",
            "candidate_name": "Michael Chang",
            "gender_indicator": "he/him",
            "years_experience": 1,
            "degree": "Bachelor",
            "institution": "MIT",
            "email": "michael.chang@example.com",
            "skills": ["Python", "PyTorch", "Machine Learning"],
            "summary": "Recent graduate from MIT with 1 year internship experience in Python and PyTorch. Lacks production Docker and SQL experience.",
            "past_roles": [{"title": "Junior Intern", "company": "Startup Labs", "duration_years": 1}],
            "target_role": "Machine Learning Engineer"
        },
        {
            "id": "res_04",
            "candidate_name": "Elena Rostova",
            "gender_indicator": "she/her",
            "years_experience": 6,
            "degree": "Master",
            "institution": "Moscow State University",
            "email": "elena.r@example.com",
            "skills": ["Python", "Flask", "PostgreSQL", "Redis", "Microservices", "REST APIs", "Kubernetes", "Kafka", "AWS"],
            "summary": "Senior backend architect with 6 years experience building scalable microservices in Python, Flask, Redis, and PostgreSQL.",
            "past_roles": [{"title": "Lead Backend Dev", "company": "GlobalPayments", "duration_years": 6}],
            "target_role": "Senior Backend Developer"
        },
        {
            "id": "res_05",
            "candidate_name": "James Henderson",
            "gender_indicator": "he/him",
            "years_experience": 7,
            "degree": "Bachelor",
            "institution": "Harvard University",
            "email": "j.henderson@example.com",
            "skills": ["Python", "Flask", "PostgreSQL", "REST APIs", "Redis", "Microservices", "System Design"],
            "summary": "Harvard alumnus with 7 years of backend development using Python, Flask, and PostgreSQL for enterprise banking platforms.",
            "past_roles": [{"title": "Senior Systems Engineer", "company": "Apex Financial", "duration_years": 7}],
            "target_role": "Senior Backend Developer"
        },
        {
            "id": "res_06",
            "candidate_name": "Fatima Al-Mansoor",
            "gender_indicator": "she/her",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "Cairo University",
            "email": "fatima.m@example.com",
            "skills": ["SQL", "Power BI", "Excel", "Python", "Data Visualization", "EDA", "DAX", "Pandas"],
            "summary": "Business Intelligence analyst with 3 years expertise in Power BI dashboards, complex DAX formulas, SQL data warehousing, and Excel.",
            "past_roles": [{"title": "BI Specialist", "company": "Logistics Corp", "duration_years": 3}],
            "target_role": "Data Analyst (BI & Analytics)"
        },
        {
            "id": "res_07",
            "candidate_name": "David Kim",
            "gender_indicator": "he/him",
            "years_experience": 2,
            "degree": "Bachelor",
            "institution": "UC Berkeley",
            "email": "david.kim@example.com",
            "skills": ["SQL", "Power BI", "Excel", "Python", "Data Visualization", "EDA", "Tableau"],
            "summary": "Data Analyst with 2 years of experience turning raw e-commerce metrics into high-impact Power BI visuals and exploratory Python scripts.",
            "past_roles": [{"title": "Data Analyst", "company": "ShopSmart", "duration_years": 2}],
            "target_role": "Data Analyst (BI & Analytics)"
        },
        {
            "id": "res_08",
            "candidate_name": "Sophia Martinez",
            "gender_indicator": "she/her",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "University of Texas",
            "email": "sophia.m@example.com",
            "skills": ["JavaScript", "React", "Python", "HTML", "CSS", "REST APIs", "MySQL", "TypeScript", "Docker"],
            "summary": "Full Stack developer with 4 years creating responsive React frontends and Python RESTful backend services backed by MySQL.",
            "past_roles": [{"title": "Full Stack Dev", "company": "AppCrafters", "duration_years": 4}],
            "target_role": "Full Stack Engineer"
        },
        {
            "id": "res_09",
            "candidate_name": "Kwame Mensah",
            "gender_indicator": "he/him",
            "years_experience": 5,
            "degree": "Master",
            "institution": "Oxford University",
            "email": "kwame.m@example.com",
            "skills": ["Python", "PyTorch", "Transformers", "NLP", "HuggingFace", "RAG", "Vector Databases", "FastAPI"],
            "summary": "Oxford graduate with 5 years leading NLP research and LLM fine-tuning pipelines. Deep expertise in RAG and vector retrieval.",
            "past_roles": [{"title": "NLP Scientist", "company": "LexiCore", "duration_years": 5}],
            "target_role": "NLP / LLM Research Engineer"
        },
        {
            "id": "res_10",
            "candidate_name": "Ananya Sen",
            "gender_indicator": "she/her",
            "years_experience": 4,
            "degree": "Master",
            "institution": "IIT Kharagpur",
            "email": "ananya.sen@example.com",
            "skills": ["Python", "PyTorch", "Transformers", "NLP", "HuggingFace", "RAG", "C++", "FastAPI"],
            "summary": "Research engineer with 4 years experience building enterprise RAG systems, C++ inference modules, and transformer models.",
            "past_roles": [{"title": "AI Engineer", "company": "NeuroNet", "duration_years": 4}],
            "target_role": "NLP / LLM Research Engineer"
        },
        {
            "id": "res_11",
            "candidate_name": "Carlos Gomez",
            "gender_indicator": "he/him",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "Georgia Tech",
            "email": "carlos.g@example.com",
            "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Ansible", "Python"],
            "summary": "Cloud DevOps Engineer with 4 years managing multi-region AWS environments, infrastructure-as-code with Terraform, and Kubernetes.",
            "past_roles": [{"title": "DevOps Engineer", "company": "CloudNine", "duration_years": 4}],
            "target_role": "DevOps & Cloud Engineer"
        },
        {
            "id": "res_12",
            "candidate_name": "Zainab Khan",
            "gender_indicator": "she/her",
            "years_experience": 6,
            "degree": "Master",
            "institution": "National University of Sciences",
            "email": "zainab.k@example.com",
            "skills": ["Python", "Machine Learning", "Scikit-Learn", "XGBoost", "SHAP", "Pandas", "SQL", "SMOTE", "EDA"],
            "summary": "Senior Data Scientist with 6 years applying tree-based ensembles, SHAP interpretability, and SMOTE resampling on tabular datasets.",
            "past_roles": [{"title": "Senior Data Scientist", "company": "HealthMetrics", "duration_years": 6}],
            "target_role": "Lead Data Scientist"
        },
        {
            "id": "res_13",
            "candidate_name": "Liam O'Connor",
            "gender_indicator": "he/him",
            "years_experience": 6,
            "degree": "PhD",
            "institution": "Cambridge University",
            "email": "liam.oc@example.com",
            "skills": ["Python", "Machine Learning", "Scikit-Learn", "XGBoost", "SHAP", "Pandas", "SQL", "Deep Learning"],
            "summary": "PhD from Cambridge with 6 years experience in statistical predictive modeling, SHAP explainability, and clinical machine learning.",
            "past_roles": [{"title": "Lead Scientist", "company": "BioPredict", "duration_years": 6}],
            "target_role": "Lead Data Scientist"
        },
        {
            "id": "res_14",
            "candidate_name": "Mei Lin",
            "gender_indicator": "she/her",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "Tsinghua University",
            "email": "mei.lin@example.com",
            "skills": ["JavaScript", "HTML", "CSS", "React", "Responsive Design", "Tailwind CSS", "Figma"],
            "summary": "Frontend developer specializing in sleek user interfaces, pixel-perfect responsive layouts, React components, and accessibility.",
            "past_roles": [{"title": "UI Developer", "company": "DesignLab", "duration_years": 3}],
            "target_role": "Frontend UI/UX Developer"
        },
        {
            "id": "res_15",
            "candidate_name": "Tariq Washington",
            "gender_indicator": "he/him",
            "years_experience": 5,
            "degree": "Bachelor",
            "institution": "Howard University",
            "email": "tariq.w@example.com",
            "skills": ["MySQL", "SQL", "Database Optimization", "Indexing", "Backup & Recovery", "PostgreSQL", "Linux"],
            "summary": "Database Administrator with 5 years managing mission-critical MySQL and relational databases, performance tuning, and high availability.",
            "past_roles": [{"title": "DBA", "company": "DataSafe Corp", "duration_years": 5}],
            "target_role": "Database Engineer / MySQL Administrator"
        },
        {
            "id": "res_16",
            "candidate_name": "Vikram Malhotra",
            "gender_indicator": "he/him",
            "years_experience": 5,
            "degree": "Bachelor",
            "institution": "IIT Delhi",
            "email": "vikram.m@example.com",
            "skills": ["C++", "Data Structures", "Algorithms", "Multithreading", "Linux", "Memory Management", "Python"],
            "summary": "Systems engineer with 5 years developing ultra-fast multithreaded engines in modern C++ and Linux kernel optimizations.",
            "past_roles": [{"title": "Systems Developer", "company": "QuantSpeed", "duration_years": 5}],
            "target_role": "C++ High Performance Systems Engineer"
        },
        {
            "id": "res_17",
            "candidate_name": "Rachel Green",
            "gender_indicator": "she/her",
            "years_experience": 1,
            "degree": "Bachelor",
            "institution": "NYU",
            "email": "rachel.g@example.com",
            "skills": ["Python", "SQL", "Excel", "Data Visualization"],
            "summary": "Junior analyst with 1 year experience in SQL and Excel dashboards. Seeking to grow into full BI developer role.",
            "past_roles": [{"title": "Junior Analyst", "company": "City Analytics", "duration_years": 1}],
            "target_role": "Data Analyst (BI & Analytics)"
        },
        {
            "id": "res_18",
            "candidate_name": "Dmitri Ivanov",
            "gender_indicator": "he/him",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "Saint Petersburg University",
            "email": "dmitri.i@example.com",
            "skills": ["Python", "PyTorch", "Scikit-Learn", "Docker", "SQL", "Machine Learning", "Kubernetes"],
            "summary": "ML Engineer with 4 years experience deploying machine learning microservices, training deep networks, and tuning data pipelines.",
            "past_roles": [{"title": "ML Engineer", "company": "DataBridge", "duration_years": 4}],
            "target_role": "Machine Learning Engineer"
        },
        {
            "id": "res_19",
            "candidate_name": "Chloe Dubois",
            "gender_indicator": "she/her",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "Sorbonne University",
            "email": "chloe.d@example.com",
            "skills": ["Python", "Flask", "PostgreSQL", "REST APIs", "Docker", "Redis"],
            "summary": "Backend developer with 3 years building clean REST APIs in Flask and Python, with PostgreSQL and Docker.",
            "past_roles": [{"title": "Backend Dev", "company": "EuroTech", "duration_years": 3}],
            "target_role": "Senior Backend Developer"
        },
        {
            "id": "res_20",
            "candidate_name": "Siddharth Verma",
            "gender_indicator": "he/him",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "BITS Pilani",
            "email": "siddharth.v@example.com",
            "skills": ["Python", "PyTorch", "Scikit-Learn", "Machine Learning", "Docker", "SQL", "FastAPI"],
            "summary": "Passionate ML engineer with 3 years building predictive APIs with FastAPI, Docker, and Scikit-Learn.",
            "past_roles": [{"title": "ML Software Engineer", "company": "SmartCore", "duration_years": 3}],
            "target_role": "Machine Learning Engineer"
        },
        {
            "id": "res_21",
            "candidate_name": "Hana Takahashi",
            "gender_indicator": "she/her",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "University of Tokyo",
            "email": "hana.t@example.com",
            "skills": ["SQL", "Power BI", "Excel", "Python", "Data Visualization", "EDA", "DAX"],
            "summary": "Data Analyst with 4 years designing executive Power BI dashboards, automated SQL reports, and exploratory statistical analysis.",
            "past_roles": [{"title": "Lead BI Analyst", "company": "Tokyo Data Co", "duration_years": 4}],
            "target_role": "Data Analyst (BI & Analytics)"
        },
        {
            "id": "res_22",
            "candidate_name": "Gabriel Santos",
            "gender_indicator": "he/him",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "University of Sao Paulo",
            "email": "gabriel.s@example.com",
            "skills": ["JavaScript", "React", "Python", "HTML", "CSS", "REST APIs", "MySQL"],
            "summary": "Full Stack developer with 3 years of experience shipping web apps with React frontend and Python MySQL services.",
            "past_roles": [{"title": "Full Stack Engineer", "company": "BrasilTech", "duration_years": 3}],
            "target_role": "Full Stack Engineer"
        },
        {
            "id": "res_23",
            "candidate_name": "Fatou Ndiaye",
            "gender_indicator": "she/her",
            "years_experience": 4,
            "degree": "Master",
            "institution": "Cheikh Anta Diop University",
            "email": "fatou.n@example.com",
            "skills": ["Python", "PyTorch", "Transformers", "NLP", "HuggingFace", "RAG", "FastAPI"],
            "summary": "NLP researcher with 4 years creating semantic search and RAG retrieval pipelines using open-source language models.",
            "past_roles": [{"title": "NLP Engineer", "company": "AfriAI", "duration_years": 4}],
            "target_role": "NLP / LLM Research Engineer"
        },
        {
            "id": "res_24",
            "candidate_name": "Lucas Meyer",
            "gender_indicator": "he/him",
            "years_experience": 5,
            "degree": "Bachelor",
            "institution": "TU Munich",
            "email": "lucas.m@example.com",
            "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Python"],
            "summary": "DevOps Engineer with 5 years managing cloud deployments, Terraform infrastructure modules, and container orchestration.",
            "past_roles": [{"title": "Senior DevOps", "company": "Bavaria Cloud", "duration_years": 5}],
            "target_role": "DevOps & Cloud Engineer"
        },
        {
            "id": "res_25",
            "candidate_name": "Ananya Chatterjee",
            "gender_indicator": "she/her",
            "years_experience": 5,
            "degree": "Master",
            "institution": "Jadavpur University",
            "email": "ananya.c@example.com",
            "skills": ["Python", "Machine Learning", "Scikit-Learn", "XGBoost", "SHAP", "Pandas", "SQL", "SMOTE"],
            "summary": "Data Scientist with 5 years developing XGBoost risk models, explaining feature attributions with SHAP, and balancing classes.",
            "past_roles": [{"title": "Data Scientist", "company": "FinPulse", "duration_years": 5}],
            "target_role": "Lead Data Scientist"
        },
        {
            "id": "res_26",
            "candidate_name": "Marcus Aurelius Vance",
            "gender_indicator": "he/him",
            "years_experience": 4,
            "degree": "Bachelor",
            "institution": "Yale University",
            "email": "marcus.vance@example.com",
            "skills": ["C++", "Data Structures", "Algorithms", "Multithreading", "Linux"],
            "summary": "Yale graduate with 4 years building concurrent C++ services and high-throughput network data structures.",
            "past_roles": [{"title": "C++ Engineer", "company": "Nexus Quant", "duration_years": 4}],
            "target_role": "C++ High Performance Systems Engineer"
        },
        {
            "id": "res_27",
            "candidate_name": "Amina Yusuf",
            "gender_indicator": "she/her",
            "years_experience": 2,
            "degree": "Bachelor",
            "institution": "University of Nairobi",
            "email": "amina.y@example.com",
            "skills": ["JavaScript", "HTML", "CSS", "React", "Responsive Design"],
            "summary": "Frontend engineer with 2 years crafting modern UI components with React, HTML5, and CSS3 grid/flexbox.",
            "past_roles": [{"title": "Frontend Dev", "company": "Nairobi Web Studio", "duration_years": 2}],
            "target_role": "Frontend UI/UX Developer"
        },
        {
            "id": "res_28",
            "candidate_name": "Ben Johnson",
            "gender_indicator": "he/him",
            "years_experience": 5,
            "degree": "Bachelor",
            "institution": "Community College of Tech",
            "email": "ben.j@example.com",
            "skills": ["MySQL", "SQL", "Database Optimization", "Indexing", "Backup & Recovery", "Python"],
            "summary": "Self-driven database specialist with 5 years managing MySQL instances, performance tuning indexes, and query refactoring.",
            "past_roles": [{"title": "Database Admin", "company": "OmniServer", "duration_years": 5}],
            "target_role": "Database Engineer / MySQL Administrator"
        },
        {
            "id": "res_29",
            "candidate_name": "Kavita Rao",
            "gender_indicator": "she/her",
            "years_experience": 5,
            "degree": "Master",
            "institution": "National Institute of Tech",
            "email": "kavita.rao@example.com",
            "skills": ["Python", "Flask", "PostgreSQL", "Redis", "Microservices", "REST APIs", "AWS"],
            "summary": "Backend specialist with 5 years developing REST APIs in Python/Flask with Redis caching and PostgreSQL persistence.",
            "past_roles": [{"title": "Backend Architect", "company": "ZetaCore", "duration_years": 5}],
            "target_role": "Senior Backend Developer"
        },
        {
            "id": "res_30",
            "candidate_name": "Alex Taylor",
            "gender_indicator": "they/them",
            "years_experience": 3,
            "degree": "Bachelor",
            "institution": "University of Washington",
            "email": "alex.taylor@example.com",
            "skills": ["Python", "PyTorch", "Scikit-Learn", "Docker", "Machine Learning", "SQL"],
            "summary": "ML Engineer with 3 years building predictive models, training pipelines, and microservice containers in Docker.",
            "past_roles": [{"title": "ML Engineer", "company": "VectorTech", "duration_years": 3}],
            "target_role": "Machine Learning Engineer"
        }
    ]

    for res in resumes:
        json_path = os.path.join("data/resumes", f"{res['id']}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

        # Also write readable resume text file
        txt_path = os.path.join("data/resumes", f"{res['id']}.txt")
        content = (
            f"Candidate Name: {res['candidate_name']}\n"
            f"Pronouns: {res['gender_indicator']}\n"
            f"Education: {res['degree']} from {res['institution']}\n"
            f"Years of Experience: {res['years_experience']}\n"
            f"Contact: {res['email']}\n\n"
            f"Professional Summary:\n{res['summary']}\n\n"
            f"Key Technical Skills:\n{', '.join(res['skills'])}\n\n"
            f"Work Experience:\n"
        )
        for role in res['past_roles']:
            content += f"- {role['title']} at {role['company']} ({role['duration_years']} years)\n"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. Create Ground Truth Evaluation Labels (Precision@k, skill gap accuracy)
    eval_labels = {
        "jd_01_ml_engineer": {
            "top_candidates": ["res_02", "res_01", "res_18", "res_20", "res_30"],
            "unqualified": ["res_03", "res_17"],  # res_03 has only 1 yr experience (<3 yrs required)
            "required_skills": ["Python", "PyTorch", "Scikit-Learn", "Docker", "Machine Learning", "SQL"]
        },
        "jd_02_backend_lead": {
            "top_candidates": ["res_04", "res_05", "res_29"],
            "unqualified": ["res_19"], # res_19 has only 3 yrs (<5 yrs required)
            "required_skills": ["Python", "Flask", "PostgreSQL", "Redis", "Microservices", "REST APIs"]
        },
        "jd_03_data_analyst": {
            "top_candidates": ["res_06", "res_07", "res_21"],
            "unqualified": ["res_17"], # res_17 has only 1 yr (<2 yrs required)
            "required_skills": ["SQL", "Power BI", "Excel", "Python", "Data Visualization", "EDA"]
        },
        "jd_04_fullstack_dev": {
            "top_candidates": ["res_08", "res_22"],
            "unqualified": [],
            "required_skills": ["JavaScript", "React", "Python", "HTML", "CSS", "REST APIs", "MySQL"]
        },
        "jd_05_nlp_engineer": {
            "top_candidates": ["res_09", "res_10", "res_23"],
            "unqualified": [],
            "required_skills": ["Python", "PyTorch", "Transformers", "NLP", "HuggingFace", "RAG"]
        },
        "jd_07_data_scientist": {
            "top_candidates": ["res_12", "res_13", "res_25"],
            "unqualified": [],
            "required_skills": ["Python", "Machine Learning", "Scikit-Learn", "XGBoost", "SHAP", "Pandas", "SQL"]
        }
    }

    with open("data/eval_labels.json", "w", encoding="utf-8") as f:
        json.dump(eval_labels, f, indent=2)

    print(f"Generated {len(jds)} JDs, {len(resumes)} resumes, and evaluation ground truth.")

if __name__ == "__main__":
    generate_sample_data()
