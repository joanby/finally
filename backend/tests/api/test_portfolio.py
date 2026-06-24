def test_portfolio_initial_shape(client):
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cash_balance"] == 10000.0
    assert data["positions"] == []
    assert data["total_value"] == 10000.0
    assert data["total_unrealized_pnl"] == 0.0


def test_buy_decreases_cash_and_creates_position(client):
    resp = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
    assert resp.status_code == 200

    data = client.get("/api/portfolio").json()
    assert data["cash_balance"] == 10000.0 - 190.0 * 10
    assert len(data["positions"]) == 1
    pos = data["positions"][0]
    assert pos["ticker"] == "AAPL"
    assert pos["quantity"] == 10
    assert pos["avg_cost"] == 190.0
    assert pos["current_price"] == 190.0
    assert pos["unrealized_pnl"] == 0.0


def test_buy_weighted_average_cost(client):
    # 10 @ 190 con precio 190, luego subimos el precio a 210 y compramos 10 más.
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})

    from app.market_data import price_cache
    from app.market_data.cache import CachedPrice

    price_cache._latest["AAPL"] = CachedPrice(price=210.0, prev_price=190.0, timestamp="t")
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})

    pos = client.get("/api/portfolio").json()["positions"][0]
    assert pos["quantity"] == 20
    assert pos["avg_cost"] == 200.0  # (190*10 + 210*10) / 20


def test_sell_increases_cash_and_reduces_position(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
    resp = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 4, "side": "sell"})
    assert resp.status_code == 200

    data = client.get("/api/portfolio").json()
    pos = data["positions"][0]
    assert pos["quantity"] == 6
    # gastó 1900 en compra, recuperó 760 en venta
    assert data["cash_balance"] == 10000.0 - 1900.0 + 760.0


def test_sell_all_removes_position(client):
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "buy"})
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 10, "side": "sell"})

    data = client.get("/api/portfolio").json()
    assert data["positions"] == []
    assert data["cash_balance"] == 10000.0


def test_buy_insufficient_cash_returns_400(client):
    resp = client.post("/api/portfolio/trade", json={"ticker": "NVDA", "quantity": 100, "side": "buy"})
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()


def test_sell_insufficient_quantity_returns_400(client):
    resp = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 5, "side": "sell"})
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()


def test_history_records_snapshot_on_trade(client):
    assert client.get("/api/portfolio/history").json()["snapshots"] == []
    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
    snapshots = client.get("/api/portfolio/history").json()["snapshots"]
    assert len(snapshots) == 1
    assert "total_value" in snapshots[0]
    assert "recorded_at" in snapshots[0]
