import uuid
from datetime import datetime, timezone

from .connection import USER_ID, get_connection

DEFAULT_CASH_BALANCE = 10000.0
DEFAULT_WATCHLIST = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY,
    cash_balance REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    executed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    actions TEXT,
    created_at TEXT NOT NULL
);
"""


def init_db() -> None:
    """Crea el esquema si falta y siembra los datos por defecto si está vacío. Idempotente."""
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA)

        if conn.execute("SELECT 1 FROM users_profile WHERE id = ?", (USER_ID,)).fetchone() is None:
            conn.execute(
                "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
                (USER_ID, DEFAULT_CASH_BALANCE, datetime.now(timezone.utc).isoformat()),
            )

        if conn.execute("SELECT 1 FROM watchlist WHERE user_id = ?", (USER_ID,)).fetchone() is None:
            now = datetime.now(timezone.utc).isoformat()
            conn.executemany(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                [(str(uuid.uuid4()), USER_ID, ticker, now) for ticker in DEFAULT_WATCHLIST],
            )

        conn.commit()
    finally:
        conn.close()
