from app.db.postgres import get_connection


def get_user_recommendations(user_id: int, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    v.vacancy_id,
                    v.title,
                    c.name AS company_name,
                    pc.name AS category_name,
                    sl.name AS seniority_name,
                    job_service.fn_matched_skills_count(%s, v.vacancy_id) AS matched_skills,
                    job_service.fn_skill_match_ratio(%s, v.vacancy_id) AS skill_ratio,
                    job_service.fn_vacancy_match_score(%s, v.vacancy_id) AS match_score
                FROM job_service.vacancies v
                JOIN job_service.companies c ON c.company_id = v.company_id
                JOIN job_service.professional_categories pc ON pc.category_id = v.category_id
                JOIN job_service.seniority_levels sl ON sl.seniority_id = v.seniority_id
                WHERE v.is_active = TRUE
                ORDER BY match_score DESC, matched_skills DESC
                LIMIT %s;
                """,
                (user_id, user_id, user_id, limit),
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]