import os
import sqlite3
from pathlib import Path

# backend/app/db/connection.py -> repo root is 3 levels up
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = _REPO_ROOT / "db" / "finally.db"

USER_ID = "default"


def db_path() -> Path:
    """Resuelve la ruta del archivo SQLite, respetando FINALLY_DB_PATH si está definida."""
    override = os.environ.get("FINALLY_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Abre una conexión nueva con row factory de dict y claves foráneas activas."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
