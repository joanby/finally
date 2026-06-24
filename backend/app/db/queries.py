import json
import uuid
from datetime import datetime, timezone

from .connection import USER_ID, get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# profile

def get_profile() -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users_profile WHERE id = ?", (USER_ID,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def set_cash_balance(amount: float) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE users_profile SET cash_balance = ? WHERE id = ?", (amount, USER_ID))
        conn.commit()
    finally:
        conn.close()


# watchlist

def list_watchlist() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY rowid", (USER_ID,)
        ).fetchall()
        return [row["ticker"] for row in rows]
    finally:
        conn.close()


def add_to_watchlist(ticker: str) -> bool:
    """Añade un ticker a la watchlist. Devuelve False si ya existía."""
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?", (USER_ID, ticker)
        ).fetchone()
        if existing is not None:
            return False
        conn.execute(
            "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), USER_ID, ticker, _now()),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def remove_from_watchlist(ticker: str) -> bool:
    """Elimina un ticker de la watchlist. Devuelve False si no existía."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (USER_ID, ticker)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# positions

def list_positions() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker, quantity, avg_cost, updated_at FROM positions WHERE user_id = ?",
            (USER_ID,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_position(ticker: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT ticker, quantity, avg_cost, updated_at FROM positions WHERE user_id = ? AND ticker = ?",
            (USER_ID, ticker),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()


def upsert_position(ticker: str, quantity: float, avg_cost: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, ticker)
            DO UPDATE SET quantity = excluded.quantity, avg_cost = excluded.avg_cost, updated_at = excluded.updated_at
            """,
            (str(uuid.uuid4()), USER_ID, ticker, quantity, avg_cost, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def delete_position(ticker: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM positions WHERE user_id = ? AND ticker = ?", (USER_ID, ticker))
        conn.commit()
    finally:
        conn.close()


# trades

def record_trade(ticker: str, side: str, quantity: float, price: float) -> dict:
    conn = get_connection()
    try:
        row = {
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "price": price,
            "executed_at": _now(),
        }
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (row["id"], USER_ID, ticker, side, quantity, price, row["executed_at"]),
        )
        conn.commit()
        return row
    finally:
        conn.close()


def list_trades() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, ticker, side, quantity, price, executed_at FROM trades WHERE user_id = ? ORDER BY executed_at",
            (USER_ID,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# portfolio snapshots

def record_snapshot(total_value: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), USER_ID, total_value, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def list_snapshots() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT total_value, recorded_at FROM portfolio_snapshots WHERE user_id = ? ORDER BY recorded_at",
            (USER_ID,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# chat

def add_chat_message(role: str, content: str, actions: dict | list | None = None) -> dict:
    conn = get_connection()
    try:
        row = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "actions": actions,
            "created_at": _now(),
        }
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (row["id"], USER_ID, role, content, json.dumps(actions) if actions is not None else None, row["created_at"]),
        )
        conn.commit()
        return row
    finally:
        conn.close()


def recent_chat_messages(limit: int = 20) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, role, content, actions, created_at FROM chat_messages
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
            """,
            (USER_ID, limit),
        ).fetchall()
        messages = [dict(row) for row in rows]
        messages.reverse()
        for message in messages:
            message["actions"] = json.loads(message["actions"]) if message["actions"] is not None else None
        return messages
    finally:
        conn.close()
