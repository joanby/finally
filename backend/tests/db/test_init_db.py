from app.db.schema import DEFAULT_CASH_BALANCE, DEFAULT_WATCHLIST


def test_init_db_seeds_default_profile_and_watchlist(db):
    profile = db.get_profile()
    assert profile["cash_balance"] == DEFAULT_CASH_BALANCE

    assert db.list_watchlist() == DEFAULT_WATCHLIST


def test_init_db_is_idempotent(db):
    db.set_cash_balance(123.0)
    db.add_to_watchlist("PYPL")

    db.init_db()
    db.init_db()

    assert db.get_profile()["cash_balance"] == 123.0
    assert "PYPL" in db.list_watchlist()
    assert len(db.list_watchlist()) == len(DEFAULT_WATCHLIST) + 1
