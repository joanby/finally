def test_chat_executes_buy_trade(client):
    resp = client.post("/api/chat", json={"message": "buy 1 AAPL please"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]
    assert data["actions"]["trades"] == [{"ticker": "AAPL", "side": "buy", "quantity": 1.0}]
    assert data["actions"]["errors"] == []

    # el trade se ejecutó de verdad: aparece la posición
    positions = client.get("/api/portfolio").json()["positions"]
    assert any(p["ticker"] == "AAPL" and p["quantity"] == 1 for p in positions)


def test_chat_watchlist_add(client):
    resp = client.post("/api/chat", json={"message": "add PLTR"})
    data = resp.json()
    assert data["actions"]["watchlist_changes"] == [{"ticker": "PLTR", "action": "add"}]
    tickers = [t["ticker"] for t in client.get("/api/watchlist").json()["tickers"]]
    assert "PLTR" in tickers


def test_chat_invalid_trade_accumulates_error(client):
    resp = client.post("/api/chat", json={"message": "buy 1000 NVDA"})
    data = resp.json()
    assert data["actions"]["trades"] == []
    assert len(data["actions"]["errors"]) == 1
    assert "insuficiente" in data["actions"]["errors"][0].lower()


def test_chat_persists_messages(client):
    client.post("/api/chat", json={"message": "buy 1 AAPL"})
    from app import db

    history = db.recent_chat_messages()
    assert history[-2]["role"] == "user"
    assert history[-1]["role"] == "assistant"
    assert history[-1]["actions"]["trades"]
