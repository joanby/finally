from app.llm.mock import mock_chat_response


def test_buy_rule():
    result = mock_chat_response("buy 10 AAPL please")
    assert result.trades[0].ticker == "AAPL"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 10.0
    assert result.watchlist_changes == []
    assert result.message


def test_sell_rule():
    result = mock_chat_response("sell 2.5 TSLA now")
    assert result.trades[0].ticker == "TSLA"
    assert result.trades[0].side == "sell"
    assert result.trades[0].quantity == 2.5


def test_add_rule():
    result = mock_chat_response("add NVDA to my watchlist")
    assert result.watchlist_changes[0].ticker == "NVDA"
    assert result.watchlist_changes[0].action == "add"
    assert result.trades == []


def test_remove_rule():
    result = mock_chat_response("remove NFLX")
    assert result.watchlist_changes[0].ticker == "NFLX"
    assert result.watchlist_changes[0].action == "remove"


def test_case_insensitive():
    result = mock_chat_response("BUY 5 msft")
    assert result.trades[0].ticker == "MSFT"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 5.0


def test_multiple_rules_in_one_message():
    result = mock_chat_response("buy 10 AAPL and remove NFLX")
    assert result.trades[0].ticker == "AAPL"
    assert result.watchlist_changes[0].ticker == "NFLX"


def test_no_rule_matches_returns_nonempty_message():
    result = mock_chat_response("how is my portfolio doing?")
    assert result.trades == []
    assert result.watchlist_changes == []
    assert result.message
