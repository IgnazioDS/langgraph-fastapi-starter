from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection
from psycopg2.pool import ThreadedConnectionPool

from app.config import config

_pool: ThreadedConnectionPool | None = None


def init_pool() -> None:
    """Initialize the connection pool. Called once at application startup."""
    global _pool
    _pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=config.database_pool_size,
        dsn=config.database_url,
    )


def close_pool() -> None:
    """Close all connections. Called once at application shutdown."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def get_conn() -> connection:
    """Borrow a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() at startup.")
    return _pool.getconn()


def release_conn(conn: connection) -> None:
    """Return a connection to the pool."""
    if _pool is not None:
        _pool.putconn(conn)


@contextmanager
def db_conn() -> Generator[connection, None, None]:
    """Context manager for database connections.

    Commits on clean exit, rolls back on exception, always releases the connection.
    This is the only way database connections are used in the rest of the codebase.

    Usage:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(SOME_QUERY, {"param": value})
                result = cur.fetchone()
    """
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_conn(conn)
