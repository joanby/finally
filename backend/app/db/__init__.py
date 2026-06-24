"""Persistencia SQLite para FinAlly. API pública síncrona, dicts planos.

Inicialización diferida: llama a `init_db()` antes de usar cualquier otra función
(crea el esquema y siembra los datos por defecto si la base está vacía; es idempotente).
"""

from .queries import (
    add_chat_message,
    add_to_watchlist,
    delete_position,
    get_position,
    get_profile,
    list_positions,
    list_snapshots,
    list_trades,
    list_watchlist,
    record_snapshot,
    record_trade,
    recent_chat_messages,
    remove_from_watchlist,
    set_cash_balance,
    upsert_position,
)
from .schema import init_db

__all__ = [
    "init_db",
    "get_profile",
    "set_cash_balance",
    "list_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "list_positions",
    "get_position",
    "upsert_position",
    "delete_position",
    "record_trade",
    "list_trades",
    "record_snapshot",
    "list_snapshots",
    "add_chat_message",
    "recent_chat_messages",
]
