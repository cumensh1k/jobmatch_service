from pathlib import Path
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "linkedin"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_ID = 1
SOURCE_NAME = "LinkedIn Job Postings"

TECH_KEYWORDS = [
    "software engineer", "software developer", "backend", "back-end", "frontend", "front-end",
    "full stack", "full-stack", "python developer", "java developer", "javascript developer",
    "typescript", "react", "vue", "angular", "node.js", "django", "fastapi", "flask",
    "data analyst", "data scientist", "machine learning", "ml engineer", "ai engineer",
    "business intelligence", "bi analyst", "power bi", "tableau",
    "devops", "sre", "site reliability", "cloud engineer", "kubernetes", "docker",
    "database administrator", "dba", "sql developer", "data engineer",
    "qa engineer", "automation tester", "test automation"
]

CATEGORY_RULES = [
    ("Data Analyst", ["data analyst", "business analyst", "bi analyst", "power bi", "tableau"]),
    ("Data Scientist", ["data scientist", "statistics", "statistical", "modeling"]),
    ("ML Engineer", ["machine learning", "ml engineer", "deep learning", "pytorch", "tensorflow", "artificial intelligence"]),
    ("Backend Developer", ["backend", "back-end", "python developer", "java developer", "django", "fastapi", "api developer"]),
    ("Frontend Developer", ["frontend", "front-end", "react", "vue", "angular", "javascript developer", "typescript"]),
    ("DevOps Engineer", ["devops", "sre", "site reliability", "kubernetes", "ci/cd", "docker"]),
    ("QA Engineer", ["qa engineer", "quality assurance", "test engineer", "automation tester"]),
    ("Product Manager", ["product manager", "product owner"]),
]

SENIORITY_RULES = [
    ("Intern", ["intern", "internship", "trainee"]),
    ("Junior", ["junior", "jr.", "entry level", "entry-level"]),
    ("Middle", ["middle", "mid-level", "mid level"]),
    ("Senior", ["senior", "sr."]),
    ("Lead", ["lead", "principal", "staff", "head of"]),
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in keywords)


def detect_category(title: str, description: str, skills_desc: str) -> str:
    text = f"{title} {description} {skills_desc}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def detect_seniority(title: str, description: str, formatted_experience_level: str) -> str:
    text = f"{title} {description} {formatted_experience_level}".lower()

    for seniority, keywords in SENIORITY_RULES:
        if any(keyword in text for keyword in keywords):
            return seniority

    if "associate" in text:
        return "Junior"
    if "director" in text or "executive" in text:
        return "Lead"

    return "Unknown"


def detect_work_format(row: pd.Series) -> str:
    remote_allowed = row.get("remote_allowed")

    if not pd.isna(remote_allowed):
        try:
            if int(remote_allowed) == 1:
                return "remote"
        except ValueError:
            pass

    text = " ".join(
        str(row.get(col, "")).lower()
        for col in ["formatted_work_type", "work_type", "location", "title"]
        if col in row.index
    )

    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "on-site" in text or "onsite" in text or "office" in text:
        return "office"

    return "unknown"


def parse_location_city(location: object) -> str:
    if pd.isna(location):
        return "Unknown"
    text = str(location).strip()
    if not text:
        return "Unknown"
    return text


def unix_ms_to_datetime(value: object):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(float(value), unit="ms")
    except Exception:
        return None


def extract_skills_from_skills_desc(skills_desc: str) -> list[str]:
    text = normalize_text(skills_desc)
    if not text:
        return []

    skill_dictionary = [
        "Python", "Java", "JavaScript", "TypeScript", "SQL", "PostgreSQL", "MySQL",
        "MongoDB", "Redis", "Docker", "Kubernetes", "Git", "Linux", "AWS", "Azure",
        "GCP", "Django", "FastAPI", "Flask", "React", "Vue", "Angular", "Node.js",
        "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Excel",
        "Power BI", "Tableau", "Spark", "Airflow", "CI/CD", "REST", "GraphQL",
        "C++", "C#", "Go", "Golang", "PHP", "Ruby", "Swift", "Kotlin",
        "Spring", "Spring Boot", "Laravel", ".NET", "ASP.NET",
        "HTML", "CSS", "Sass", "Redux", "Next.js",
        "Oracle", "SQLite", "MS SQL", "SQL Server", "Elasticsearch",
        "Snowflake", "BigQuery", "Databricks",
        "Jenkins", "GitLab CI", "GitHub Actions", "Terraform", "Ansible",
        "Prometheus", "Grafana",
        "REST API", "Microservices",
        "R", "SAS", "SPSS",
        "Jupyter", "Matplotlib", "Seaborn",
        "NLP", "Computer Vision", "LLM"
    ]

    found = []
    lower_text = text.lower()

    for skill in skill_dictionary:
        pattern = re.escape(skill.lower())
        if re.search(rf"(?<![a-zA-Z0-9]){pattern}(?![a-zA-Z0-9])", lower_text):
            found.append(skill)

    return found


def main() -> None:
    jobs_path = RAW_DIR / "postings.csv"

    if not jobs_path.exists():
        raise FileNotFoundError(f"Не найден файл: {jobs_path}")

    jobs = pd.read_csv(jobs_path, low_memory=False)

    print(f"Initial rows: {len(jobs)}")
    print(f"Columns: {list(jobs.columns)}")

    required_columns = ["job_id", "title", "description", "location"]
    missing = [col for col in required_columns if col not in jobs.columns]

    if missing:
        raise ValueError(f"Не хватает обязательных колонок: {missing}")

    jobs["title_clean"] = jobs["title"].apply(normalize_text)
    jobs["description_clean"] = jobs["description"].apply(normalize_text)
    jobs["skills_desc_clean"] = jobs["skills_desc"].apply(normalize_text) if "skills_desc" in jobs.columns else ""

    filter_text = (
        jobs["title_clean"].fillna("") + " "
        + jobs["description_clean"].fillna("") + " "
        + jobs["skills_desc_clean"].fillna("")
    )

    jobs = jobs[filter_text.apply(lambda x: contains_any(x, TECH_KEYWORDS))].copy()
    print(f"After IT filter: {len(jobs)}")

    jobs = jobs.sample(n=min(30_000, len(jobs)), random_state=42).copy()
    print(f"Final selected rows: {len(jobs)}")

    sources = pd.DataFrame([{
        "source_id": SOURCE_ID,
        "name": SOURCE_NAME,
        "source_type": "dataset",
        "base_url": "https://www.kaggle.com/datasets/arshkon/linkedin-job-postings"
    }])
    sources.to_csv(PROCESSED_DIR / "sources.csv", index=False)

    category_names = [item[0] for item in CATEGORY_RULES] + ["Other"]
    categories = pd.DataFrame({
        "category_id": range(1, len(category_names) + 1),
        "name": category_names,
        "description": category_names
    })
    categories.to_csv(PROCESSED_DIR / "professional_categories.csv", index=False)
    category_map = dict(zip(categories["name"], categories["category_id"]))

    seniority_names = [item[0] for item in SENIORITY_RULES] + ["Unknown"]
    seniority = pd.DataFrame({
        "seniority_id": range(1, len(seniority_names) + 1),
        "name": seniority_names,
        "rank_value": range(1, len(seniority_names) + 1)
    })
    seniority.to_csv(PROCESSED_DIR / "seniority_levels.csv", index=False)
    seniority_map = dict(zip(seniority["name"], seniority["seniority_id"]))

    company_names = jobs["company_name"].fillna("Unknown company").astype(str)
    companies = (
        pd.DataFrame({"name": company_names})
        .drop_duplicates()
        .reset_index(drop=True)
    )
    companies["company_id"] = companies.index + 1
    companies["website"] = None
    companies["industry"] = None
    companies = companies[["company_id", "name", "website", "industry"]]
    companies.to_csv(PROCESSED_DIR / "companies.csv", index=False)
    company_map = dict(zip(companies["name"], companies["company_id"]))

    location_names = jobs["location"].apply(parse_location_city)
    locations = (
        pd.DataFrame({"city": location_names})
        .drop_duplicates()
        .reset_index(drop=True)
    )
    locations["location_id"] = locations.index + 1
    locations["country"] = "Unknown"
    locations["is_remote_available"] = locations["city"].str.lower().str.contains("remote")
    locations = locations[["location_id", "country", "city", "is_remote_available"]]
    locations.to_csv(PROCESSED_DIR / "locations.csv", index=False)
    location_map = dict(zip(locations["city"], locations["location_id"]))

    detected_categories = [
        detect_category(title, desc, skills)
        for title, desc, skills in zip(
            jobs["title_clean"],
            jobs["description_clean"],
            jobs["skills_desc_clean"]
        )
    ]

    detected_seniority = [
        detect_seniority(title, desc, exp)
        for title, desc, exp in zip(
            jobs["title_clean"],
            jobs["description_clean"],
            jobs["formatted_experience_level"].fillna("") if "formatted_experience_level" in jobs.columns else [""] * len(jobs)
        )
    ]

    vacancies = pd.DataFrame()
    vacancies["vacancy_id"] = range(1, len(jobs) + 1)
    vacancies["source_id"] = SOURCE_ID
    vacancies["external_id"] = jobs["job_id"].astype(str).values
    vacancies["company_id"] = company_names.map(company_map).values
    vacancies["location_id"] = location_names.map(location_map).values
    vacancies["category_id"] = [category_map[name] for name in detected_categories]
    vacancies["seniority_id"] = [seniority_map[name] for name in detected_seniority]
    vacancies["title"] = jobs["title_clean"].values
    vacancies["description_clean"] = jobs["description_clean"].values
    vacancies["employment_type"] = jobs["work_type"].fillna("unknown").astype(str).str.lower().values if "work_type" in jobs.columns else "unknown"
    vacancies["work_format"] = jobs.apply(detect_work_format, axis=1).values
    vacancies["salary_min"] = pd.to_numeric(jobs["min_salary"], errors="coerce") if "min_salary" in jobs.columns else None
    vacancies["salary_max"] = pd.to_numeric(jobs["max_salary"], errors="coerce") if "max_salary" in jobs.columns else None
    vacancies["salary_currency"] = jobs["currency"].fillna("USD").values if "currency" in jobs.columns else "USD"
    vacancies["published_at"] = jobs["listed_time"].apply(unix_ms_to_datetime) if "listed_time" in jobs.columns else None
    vacancies["is_active"] = True
    vacancies["job_posting_url"] = jobs["job_posting_url"].fillna("").values if "job_posting_url" in jobs.columns else ""

    vacancies.to_csv(PROCESSED_DIR / "vacancies.csv", index=False)

    skill_rows = []
    vacancy_skill_rows = []
    skill_name_to_id = {}

    for vacancy_id, skills_desc in zip(vacancies["vacancy_id"], jobs["skills_desc_clean"]):
        found_skills = extract_skills_from_skills_desc(skills_desc)

        if not found_skills:
            row_text = (
                jobs.iloc[vacancy_id - 1]["title_clean"] + " "
                + jobs.iloc[vacancy_id - 1]["description_clean"]
            )
            found_skills = extract_skills_from_skills_desc(row_text)

        for skill_name in found_skills:
            if skill_name not in skill_name_to_id:
                skill_id = len(skill_name_to_id) + 1
                skill_name_to_id[skill_name] = skill_id
                skill_rows.append({
                    "skill_id": skill_id,
                    "name": skill_name,
                    "skill_type": "technical"
                })

            vacancy_skill_rows.append({
                "vacancy_id": vacancy_id,
                "skill_id": skill_name_to_id[skill_name],
                "confidence": 1.0,
                "extraction_method": "dictionary"
            })

    skills = pd.DataFrame(skill_rows)
    vacancy_skills = pd.DataFrame(vacancy_skill_rows).drop_duplicates(
        subset=["vacancy_id", "skill_id"]
    )

    skills.to_csv(PROCESSED_DIR / "skills.csv", index=False)
    vacancy_skills.to_csv(PROCESSED_DIR / "vacancy_skills.csv", index=False)

    import_batches = pd.DataFrame([{
        "batch_id": 1,
        "source_id": SOURCE_ID,
        "file_name": "postings.csv",
        "status": "prepared",
        "rows_total": len(jobs),
        "rows_success": len(jobs),
        "rows_failed": 0
    }])
    import_batches.to_csv(PROCESSED_DIR / "import_batches.csv", index=False)

    vacancies.head(500).to_csv(SAMPLE_DIR / "vacancies_sample.csv", index=False)

    print("\nPrepared files:")
    for path in sorted(PROCESSED_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        print(f"{path.relative_to(PROJECT_ROOT)}: {len(df)} rows")

    print(f"\nSample written to: {(SAMPLE_DIR / 'vacancies_sample.csv').relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()