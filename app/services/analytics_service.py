import redis

from app.db.postgres import get_connection


KEY_PREFIX = "jobmatch"


def get_top_skills(redis_client: redis.Redis, limit: int = 20) -> dict:
    key = f"{KEY_PREFIX}:popular_skills"

    cached = redis_client.zrevrange(key, 0, limit - 1, withscores=True)

    if cached:
        return {
            "source": "redis_cache",
            "items": [
                {"skill_name": skill, "vacancy_count": int(score)}
                for skill, score in cached
            ],
        }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT skill_name, vacancy_count, vacancy_share_percent
                FROM job_service.v_skill_demand
                ORDER BY vacancy_count DESC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    items = [dict(row) for row in rows]

    if items:
        redis_client.zadd(
            key,
            {
                item["skill_name"]: item["vacancy_count"]
                for item in items
            },
        )

    return {
        "source": "postgres",
        "items": items,
    }


def get_salary_stats() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM job_service.v_category_salary_stats;
                """
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_company_activity(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM job_service.v_company_activity
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_work_format_stats() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM job_service.v_work_format_stats;
                """
            )
            rows = cur.fetchall()

    return [dict(row) for row in rows]


def get_popular_queries(redis_client: redis.Redis, limit: int = 10) -> list[dict]:
    rows = redis_client.zrevrange(
        f"{KEY_PREFIX}:popular_queries",
        0,
        limit - 1,
        withscores=True,
    )

    return [
        {"query_text": query, "count": int(score)}
        for query, score in rows
    ]