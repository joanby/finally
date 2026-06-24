def test_record_trade_returns_inserted_row(db):
    trade = db.record_trade("AAPL", "buy", 10, 190.0)

    assert trade["ticker"] == "AAPL"
    assert trade["side"] == "buy"
    assert trade["quantity"] == 10
    assert trade["price"] == 190.0
    assert trade["executed_at"]


def test_list_trades_returns_in_chronological_order(db):
    db.record_trade("AAPL", "buy", 10, 190.0)
    db.record_trade("AAPL", "sell", 5, 195.0)

    trades = db.list_trades()
    assert [t["side"] for t in trades] == ["buy", "sell"]
