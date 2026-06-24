def test_default_watchlist(client):
    data = client.get("/api/watchlist").json()
    tickers = [t["ticker"] for t in data["tickers"]]
    assert tickers == ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]
    # precios sembrados aparecen; los no sembrados son null
    by_ticker = {t["ticker"]: t["price"] for t in data["tickers"]}
    assert by_ticker["AAPL"] == 190.0
    assert by_ticker["AMZN"] is None


def test_add_watchlist_normalizes_and_notifies_provider(client):
    resp = client.post("/api/watchlist", json={"ticker": "pypl"})
    assert resp.status_code == 200
    assert resp.json() == {"ticker": "PYPL", "added": True}

    tickers = [t["ticker"] for t in client.get("/api/watchlist").json()["tickers"]]
    assert "PYPL" in tickers
    assert "PYPL" in client.app.state.provider.added


def test_add_duplicate_returns_added_false(client):
    resp = client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert resp.json() == {"ticker": "AAPL", "added": False}


def test_remove_watchlist(client):
    resp = client.delete("/api/watchlist/NFLX")
    assert resp.status_code == 200
    assert resp.json() == {"ticker": "NFLX", "removed": True}
    tickers = [t["ticker"] for t in client.get("/api/watchlist").json()["tickers"]]
    assert "NFLX" not in tickers
    assert "NFLX" in client.app.state.provider.removed


def test_remove_keeps_ticker_with_open_position(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
    client.delete("/api/watchlist/AAPL")
    # AAPL sigue con posición abierta: no se debe pedir al proveedor que lo quite
    assert "AAPL" not in client.app.state.provider.removed
