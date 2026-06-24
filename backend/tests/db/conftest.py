import pytest

from app import db as db_module


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Apunta el módulo db a un SQLite temporal nuevo e inicializado para cada test."""
    monkeypatch.setenv("FINALLY_DB_PATH", str(tmp_path / "finally.db"))
    db_module.init_db()
    return db_module
