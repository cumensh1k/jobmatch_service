import psycopg
from psycopg.rows import dict_row

from app.config import settings


def get_connection() -> psycopg.Connection:
    return psycopg.connect(
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        row_factory=dict_row,
    )