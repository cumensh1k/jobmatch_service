from typing import Optional

import redis

from app.db.postgres import get_connection
from app.services.redis_service import (
    add_recent_search,
    check_rate_limit,
    get_json_cache,
    increment_popular_query,
    make_search_cache_key,
    set_json_cache,
)


def search_vacancies(
    redis_client: redis.Redis,
    query_text: str,
    user_id: int = 1,
    category: Optional[str] = None,
    seniority: Optional[str] = None,
    work_format: Optional[str] = None,
    min_salary: Optional[float] = None,
    limit: int = 20,
) -> dict:
    rate = check_rate_limit(redis_client, user_id=user_id)

    if not rate["allowed"]:
        return {
            "source": "rate_limited",
            "rate_limit": rate,
            "items": [],
        }

    filters = {
        "query_text": query_text,
        "user_id": user_id,
        "category": category,
        "seniority": seniority,
        "work_format": work_format,
        "min_salary": min_salary,
        "limit": limit,
    }

    cache_key = make_search_cache_key(filters)
    cached = get_json_cache(redis_client, cache_key)

    if cached is not None:
        add_recent_search(redis_client, user_id, query_text)
        increment_popular_query(redis_client, query_text)

        return {
            "source": "redis_cache",
            "cache_key": cache_key,
            "rate_limit": rate,
            "items": cached,
        }

    sql = """
        SELECT
            vacancy_id,
            title,
            company_name,
            location_city,
            category_name,
            seniority_name,
            work_format,
            salary_min,
            salary_max,
            salary_currency,
            skills
        FROM job_service.v_vacancy_cards
        WHERE is_active = TRUE
    """

    params = []

    if query_text:
        sql += """
            AND vacancy_id IN (
                SELECT vacancy_id
                FROM job_service.vacancies
                WHERE search_vector @@ plainto_tsquery('english', %s)
            )
        """
        params.append(query_text)

    if category:
        sql += " AND category_name = %s"
        params.append(category)

    if seniority:
        sql += " AND seniority_name = %s"
        params.append(seniority)

    if work_format:
        sql += " AND work_format = %s"
        params.append(work_format)

    if min_salary is not None:
        sql += " AND (salary_min IS NULL OR salary_min >= %s)"
        params.append(min_salary)

    sql += " ORDER BY vacancy_id LIMIT %s"
    params.append(limit)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    items = [dict(row) for row in rows]

    set_json_cache(redis_client, cache_key, items, ttl_seconds=600)
    add_recent_search(redis_client, user_id, query_text)
    increment_popular_query(redis_client, query_text)

    return {
        "source": "postgres",
        "cache_key": cache_key,
        "rate_limit": rate,
        "items": items,
    }