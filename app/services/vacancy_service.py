import redis

from app.db.postgres import get_connection
from app.services.redis_service import cache_vacancy_card, get_cached_vacancy_card


def get_vacancy_by_id(redis_client: redis.Redis, vacancy_id: int) -> dict | None:
    cached = get_cached_vacancy_card(redis_client, vacancy_id)

    if cached is not None:
        cached["source"] = "redis_cache"
        return cached

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    vacancy_id,
                    title,
                    company_name,
                    location_city,
                    location_country,
                    category_name,
                    seniority_name,
                    work_format,
                    employment_type,
                    salary_min,
                    salary_max,
                    salary_currency,
                    is_active,
                    published_at,
                    job_posting_url,
                    skills
                FROM job_service.v_vacancy_cards
                WHERE vacancy_id = %s;
                """,
                (vacancy_id,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    card = dict(row)
    cache_vacancy_card(redis_client, vacancy_id, card)

    card["source"] = "postgres"
    return card