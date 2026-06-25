from __future__ import annotations

import hashlib
import json
from getpass import getpass
from pathlib import Path
from typing import Any

import psycopg
import redis


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_NAME = "job_db"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432

REDIS_HOST = "localhost"
REDIS_PORT = 6379

KEY_PREFIX = "jobmatch"


def make_pg_conn() -> psycopg.Connection:
    password = getpass("PostgreSQL password: ")

    conninfo = (
        f"dbname={DB_NAME} "
        f"user={DB_USER} "
        f"password={password} "
        f"host={DB_HOST} "
        f"port={DB_PORT}"
    )

    return psycopg.connect(conninfo)


def make_redis_client() -> redis.Redis:
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )
    client.ping()
    return client


def make_search_cache_key(filters: dict[str, Any]) -> str:
    raw = json.dumps(filters, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{KEY_PREFIX}:search_cache:{digest}"


def cache_search_results(
    pg_conn: psycopg.Connection,
    redis_client: redis.Redis,
    query_text: str,
    limit: int = 20,
) -> list[int]:
    filters = {
        "query_text": query_text,
        "limit": limit,
    }

    cache_key = make_search_cache_key(filters)

    cached = redis_client.get(cache_key)

    if cached is not None:
        print(f"[CACHE HIT] {cache_key}")
        return json.loads(cached)

    print(f"[CACHE MISS] {cache_key}")

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT vacancy_id
            FROM job_service.vacancies
            WHERE search_vector @@ plainto_tsquery('english', %s)
              AND is_active = TRUE
            LIMIT %s;
            """,
            (query_text, limit),
        )
        vacancy_ids = [row[0] for row in cur.fetchall()]

    redis_client.set(
        cache_key,
        json.dumps(vacancy_ids, ensure_ascii=False),
        ex=600,
    )

    redis_client.zincrby(
        f"{KEY_PREFIX}:popular_queries",
        1,
        query_text,
    )

    return vacancy_ids


def cache_vacancy_card(
    pg_conn: psycopg.Connection,
    redis_client: redis.Redis,
    vacancy_id: int,
) -> None:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
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
            WHERE vacancy_id = %s;
            """,
            (vacancy_id,),
        )
        row = cur.fetchone()

    if row is None:
        print(f"Vacancy {vacancy_id} not found.")
        return

    card = {
        "vacancy_id": row[0],
        "title": row[1],
        "company_name": row[2],
        "location_city": row[3],
        "category_name": row[4],
        "seniority_name": row[5],
        "work_format": row[6],
        "salary_min": str(row[7]) if row[7] is not None else "",
        "salary_max": str(row[8]) if row[8] is not None else "",
        "salary_currency": row[9] or "",
        "skills": row[10] or "",
    }

    key = f"{KEY_PREFIX}:vacancy_card:{vacancy_id}"

    redis_client.hset(key, mapping=card)
    redis_client.expire(key, 1800)

    print(f"Cached vacancy card: {key}")


def add_recent_search(
    redis_client: redis.Redis,
    user_id: int,
    query_text: str,
) -> None:
    key = f"{KEY_PREFIX}:user:{user_id}:recent_searches"

    redis_client.lpush(key, query_text)
    redis_client.ltrim(key, 0, 9)
    redis_client.expire(key, 7 * 24 * 60 * 60)

    print(f"Added recent search for user {user_id}: {query_text}")


def update_popular_skills(
    pg_conn: psycopg.Connection,
    redis_client: redis.Redis,
    limit: int = 30,
) -> None:
    key = f"{KEY_PREFIX}:popular_skills"

    redis_client.delete(key)

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT skill_name, vacancy_count
            FROM job_service.v_skill_demand
            ORDER BY vacancy_count DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()

    if not rows:
        print("No skills found.")
        return

    mapping = {
        skill_name: vacancy_count
        for skill_name, vacancy_count in rows
    }

    redis_client.zadd(key, mapping)

    print(f"Updated popular skills: {key}")


def demo_rate_limit(redis_client: redis.Redis, user_id: int) -> None:
    key = f"{KEY_PREFIX}:rate_limit:user:{user_id}"

    current = redis_client.incr(key)

    if current == 1:
        redis_client.expire(key, 60)

    print(f"Rate limit counter for user {user_id}: {current}/60 requests per minute")


def add_import_stream_tasks(redis_client: redis.Redis) -> None:
    key = f"{KEY_PREFIX}:stream:vacancy_import"

    task_ids = []

    for raw_id in range(1, 4):
        task_id = redis_client.xadd(
            key,
            {
                "batch_id": "1",
                "external_id": f"demo_external_{raw_id}",
                "title": f"Demo vacancy {raw_id}",
                "status": "new",
            },
        )
        task_ids.append(task_id)

    print(f"Added stream tasks to {key}:")
    for task_id in task_ids:
        print(f"  {task_id}")


def print_redis_state(redis_client: redis.Redis) -> None:
    print("\nRedis keys:")

    for key in sorted(redis_client.keys(f"{KEY_PREFIX}:*")):
        key_type = redis_client.type(key)
        ttl = redis_client.ttl(key)
        print(f"{key} | type={key_type} | ttl={ttl}")


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")

    redis_client = make_redis_client()
    print("Redis connection: OK")

    with make_pg_conn() as pg_conn:
        print("PostgreSQL connection: OK")

        for key in redis_client.keys(f"{KEY_PREFIX}:*"):
            redis_client.delete(key)

        first_result = cache_search_results(pg_conn, redis_client, "python developer", limit=20)
        print(f"Search result ids: {first_result[:10]}")

        second_result = cache_search_results(pg_conn, redis_client, "python developer", limit=20)
        print(f"Search result ids from cache: {second_result[:10]}")

        if first_result:
            cache_vacancy_card(pg_conn, redis_client, first_result[0])

        add_recent_search(redis_client, user_id=1, query_text="python developer")
        add_recent_search(redis_client, user_id=1, query_text="sql remote")
        add_recent_search(redis_client, user_id=1, query_text="backend junior")

        update_popular_skills(pg_conn, redis_client, limit=30)

        demo_rate_limit(redis_client, user_id=1)
        demo_rate_limit(redis_client, user_id=1)

        add_import_stream_tasks(redis_client)

        print_redis_state(redis_client)

    print("\nRedis demo completed successfully.")


if __name__ == "__main__":
    main()