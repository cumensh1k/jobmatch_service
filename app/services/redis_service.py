import hashlib
import json
from typing import Any

import redis


KEY_PREFIX = "jobmatch"


def make_search_cache_key(filters: dict[str, Any]) -> str:
    raw = json.dumps(filters, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{KEY_PREFIX}:search_cache:{digest}"


def get_json_cache(redis_client: redis.Redis, key: str):
    value = redis_client.get(key)
    if value is None:
        return None
    return json.loads(value)


def set_json_cache(redis_client: redis.Redis, key: str, value, ttl_seconds: int) -> None:
    redis_client.set(
        key,
        json.dumps(value, ensure_ascii=False, default=str),
        ex=ttl_seconds,
    )


def increment_popular_query(redis_client: redis.Redis, query_text: str) -> None:
    if query_text:
        redis_client.zincrby(f"{KEY_PREFIX}:popular_queries", 1, query_text)


def add_recent_search(redis_client: redis.Redis, user_id: int, query_text: str) -> None:
    if not query_text:
        return

    key = f"{KEY_PREFIX}:user:{user_id}:recent_searches"

    redis_client.lpush(key, query_text)
    redis_client.ltrim(key, 0, 9)
    redis_client.expire(key, 7 * 24 * 60 * 60)


def get_recent_searches(redis_client: redis.Redis, user_id: int) -> list[str]:
    key = f"{KEY_PREFIX}:user:{user_id}:recent_searches"
    return redis_client.lrange(key, 0, -1)


def check_rate_limit(
    redis_client: redis.Redis,
    user_id: int,
    limit: int = 60,
    window_seconds: int = 60,
) -> dict:
    key = f"{KEY_PREFIX}:rate_limit:user:{user_id}"

    current = redis_client.incr(key)

    if current == 1:
        redis_client.expire(key, window_seconds)

    ttl = redis_client.ttl(key)

    return {
        "allowed": current <= limit,
        "current": current,
        "limit": limit,
        "ttl": ttl,
    }


def cache_vacancy_card(redis_client: redis.Redis, vacancy_id: int, card: dict) -> None:
    key = f"{KEY_PREFIX}:vacancy_card:{vacancy_id}"
    mapping = {
        field: "" if value is None else str(value)
        for field, value in card.items()
    }

    redis_client.hset(key, mapping=mapping)
    redis_client.expire(key, 1800)


def get_cached_vacancy_card(redis_client: redis.Redis, vacancy_id: int) -> dict | None:
    key = f"{KEY_PREFIX}:vacancy_card:{vacancy_id}"
    data = redis_client.hgetall(key)

    if not data:
        return None

    return data