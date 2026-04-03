import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import DB_PATH


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                task        TEXT    NOT NULL,
                status      TEXT    NOT NULL,
                iterations  INTEGER NOT NULL,
                input_tokens  INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd    REAL    NOT NULL
            )
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def record_run(
    task: str,
    status: str,
    iterations: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO runs (created_at, task, status, iterations, input_tokens, output_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                task,
                status,
                iterations,
                input_tokens,
                output_tokens,
                cost_usd,
            ),
        )


def get_stats() -> dict:
    with _conn() as conn:
        totals = conn.execute("""
            SELECT
                COUNT(*)            AS total_runs,
                SUM(input_tokens)   AS total_input_tokens,
                SUM(output_tokens)  AS total_output_tokens,
                SUM(cost_usd)       AS total_cost_usd
            FROM runs
        """).fetchone()

        recent = conn.execute("""
            SELECT id, created_at, task, status, iterations, input_tokens, output_tokens, cost_usd
            FROM runs
            ORDER BY id DESC
            LIMIT 20
        """).fetchall()

    return {
        "total_runs": totals["total_runs"] or 0,
        "total_input_tokens": totals["total_input_tokens"] or 0,
        "total_output_tokens": totals["total_output_tokens"] or 0,
        "total_cost_usd": round(totals["total_cost_usd"] or 0.0, 6),
        "recent_runs": [dict(row) for row in recent],
    }
