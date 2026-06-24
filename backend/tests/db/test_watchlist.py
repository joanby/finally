def test_add_to_watchlist_new_ticker(db):
    assert db.add_to_watchlist("PYPL") is True
    assert "PYPL" in db.list_watchlist()


def test_add_to_watchlist_existing_ticker_returns_false(db):
    assert db.add_to_watchlist("AAPL") is False


def test_list_watchlist_preserves_insertion_order(db):
    db.add_to_watchlist("PYPL")
    db.add_to_watchlist("SHOP")

    tickers = db.list_watchlist()
    assert tickers[-2:] == ["PYPL", "SHOP"]


def test_remove_from_watchlist_existing_ticker(db):
    assert db.remove_from_watchlist("AAPL") is True
    assert "AAPL" not in db.list_watchlist()


def test_remove_from_watchlist_missing_ticker_returns_false(db):
    assert db.remove_from_watchlist("DOESNOTEXIST") is False
