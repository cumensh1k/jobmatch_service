import redis

from app.config import settings


def get_redis_client() -> redis.Redis:
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )
    client.ping()
    return client