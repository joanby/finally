def test_get_position_missing_returns_none(db):
    assert db.get_position("AAPL") is None


def test_upsert_position_creates_new_position(db):
    db.upsert_position("AAPL", 10, 190.0)

    position = db.get_position("AAPL")
    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 10
    assert position["avg_cost"] == 190.0


def test_upsert_position_updates_existing_position(db):
    db.upsert_position("AAPL", 10, 190.0)
    db.upsert_position("AAPL", 15, 191.0)

    position = db.get_position("AAPL")
    assert position["quantity"] == 15
    assert position["avg_cost"] == 191.0


def test_list_positions_returns_all(db):
    db.upsert_position("AAPL", 10, 190.0)
    db.upsert_position("GOOGL", 5, 175.0)

    tickers = {p["ticker"] for p in db.list_positions()}
    assert tickers == {"AAPL", "GOOGL"}


def test_delete_position_removes_it(db):
    db.upsert_position("AAPL", 10, 190.0)
    db.delete_position("AAPL")

    assert db.get_position("AAPL") is None
