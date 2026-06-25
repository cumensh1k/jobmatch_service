from pathlib import Path
from getpass import getpass

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DB_NAME = "job_db"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432


TABLES = [
    (
        "sources",
        "sources.csv",
        ["source_id", "name", "source_type", "base_url"],
    ),
    (
        "companies",
        "companies.csv",
        ["company_id", "name", "website", "industry"],
    ),
    (
        "locations",
        "locations.csv",
        ["location_id", "country", "city", "is_remote_available"],
    ),
    (
        "professional_categories",
        "professional_categories.csv",
        ["category_id", "name", "description"],
    ),
    (
        "seniority_levels",
        "seniority_levels.csv",
        ["seniority_id", "name", "rank_value"],
    ),
    (
        "skills",
        "skills.csv",
        ["skill_id", "name", "skill_type"],
    ),
    (
        "vacancies",
        "vacancies.csv",
        [
            "vacancy_id",
            "source_id",
            "external_id",
            "company_id",
            "location_id",
            "category_id",
            "seniority_id",
            "title",
            "description_clean",
            "employment_type",
            "work_format",
            "salary_min",
            "salary_max",
            "salary_currency",
            "published_at",
            "is_active",
            "job_posting_url",
        ],
    ),
    (
        "vacancy_skills",
        "vacancy_skills.csv",
        ["vacancy_id", "skill_id", "confidence", "extraction_method"],
    ),
    (
        "import_batches",
        "import_batches.csv",
        [
            "batch_id",
            "source_id",
            "file_name",
            "status",
            "rows_total",
            "rows_success",
            "rows_failed",
        ],
    ),
]


def copy_csv(conn: psycopg.Connection, table_name: str, file_name: str, columns: list[str]) -> None:
    path = PROCESSED_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Не найден файл: {path}")

    columns_sql = ", ".join(columns)

    copy_sql = f"""
        COPY job_service.{table_name} ({columns_sql})
        FROM STDIN
        WITH (FORMAT CSV, HEADER TRUE, NULL '');
    """

    with path.open("r", encoding="utf-8", newline="") as file:
        with conn.cursor() as cur:
            with cur.copy(copy_sql) as copy:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)

    print(f"Loaded: {file_name} -> job_service.{table_name}")


def reset_sequences(conn: psycopg.Connection) -> None:
    sequence_queries = [
        ("sources_source_id_seq", "sources", "source_id"),
        ("companies_company_id_seq", "companies", "company_id"),
        ("locations_location_id_seq", "locations", "location_id"),
        ("professional_categories_category_id_seq", "professional_categories", "category_id"),
        ("seniority_levels_seniority_id_seq", "seniority_levels", "seniority_id"),
        ("skills_skill_id_seq", "skills", "skill_id"),
        ("vacancies_vacancy_id_seq", "vacancies", "vacancy_id"),
        ("import_batches_batch_id_seq", "import_batches", "batch_id"),
    ]

    with conn.cursor() as cur:
        for sequence_name, table_name, id_column in sequence_queries:
            cur.execute(
                f"""
                SELECT setval(
                    'job_service.{sequence_name}',
                    COALESCE((SELECT MAX({id_column}) FROM job_service.{table_name}), 1),
                    true
                );
                """
            )

    print("Sequences reset.")


def refresh_search_vector(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            ALTER TABLE job_service.vacancies
            ADD COLUMN IF NOT EXISTS search_vector tsvector;
            """
        )

        cur.execute(
            """
            UPDATE job_service.vacancies
            SET search_vector =
                to_tsvector(
                    'english',
                    coalesce(title, '') || ' ' || coalesce(description_clean, '')
                );
            """
        )

    print("Search vectors refreshed.")


def print_counts(conn: psycopg.Connection) -> None:
    tables = [
        "sources",
        "companies",
        "locations",
        "professional_categories",
        "seniority_levels",
        "skills",
        "vacancies",
        "vacancy_skills",
        "import_batches",
    ]

    print("\nRow counts:")

    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM job_service.{table};")
            count = cur.fetchone()[0]
            print(f"job_service.{table}: {count}")


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Processed dir: {PROCESSED_DIR}")

    password = getpass("PostgreSQL password: ")

    conninfo = (
        f"dbname={DB_NAME} "
        f"user={DB_USER} "
        f"password={password} "
        f"host={DB_HOST} "
        f"port={DB_PORT}"
    )

    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO job_service;")

            cur.execute(
                """
                TRUNCATE TABLE
                    job_service.vacancy_audit,
                    job_service.vacancy_views,
                    job_service.favorite_vacancies,
                    job_service.user_skills,
                    job_service.users,
                    job_service.vacancy_skills,
                    job_service.vacancies,
                    job_service.import_batches,
                    job_service.skills,
                    job_service.seniority_levels,
                    job_service.professional_categories,
                    job_service.locations,
                    job_service.companies,
                    job_service.sources
                RESTART IDENTITY CASCADE;
                """
            )

        for table_name, file_name, columns in TABLES:
            copy_csv(conn, table_name, file_name, columns)

        reset_sequences(conn)
        refresh_search_vector(conn)
        print_counts(conn)

        conn.commit()

    print("\nImport completed successfully.")


if __name__ == "__main__":
    main()