import json
from types import SimpleNamespace

from app.llm.client import call_llm


def _fake_response(content: dict):
    message = SimpleNamespace(content=json.dumps(content))
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def test_call_llm_parses_structured_output(monkeypatch):
    payload = {"message": "Hola", "trades": [], "watchlist_changes": []}
    monkeypatch.setattr(
        "app.llm.client.completion", lambda **kwargs: _fake_response(payload)
    )
    result = call_llm([{"role": "user", "content": "hola"}])
    assert result.message == "Hola"
    assert result.trades == []
    assert result.watchlist_changes == []


def test_call_llm_parses_trades_and_watchlist_changes(monkeypatch):
    payload = {
        "message": "Compro AAPL y añado NVDA",
        "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
        "watchlist_changes": [{"ticker": "NVDA", "action": "add"}],
    }
    monkeypatch.setattr(
        "app.llm.client.completion", lambda **kwargs: _fake_response(payload)
    )
    result = call_llm([{"role": "user", "content": "compra 10 AAPL y añade NVDA"}])
    assert result.trades[0].ticker == "AAPL"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 10.0
    assert result.watchlist_changes[0].ticker == "NVDA"
    assert result.watchlist_changes[0].action == "add"


def test_call_llm_passes_model_and_response_format(monkeypatch):
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _fake_response({"message": "ok", "trades": [], "watchlist_changes": []})

    monkeypatch.setattr("app.llm.client.completion", fake_completion)
    call_llm([{"role": "user", "content": "hola"}])
    assert captured["model"] == "openrouter/openai/gpt-oss-120b"
    assert captured["extra_body"] == {"provider": {"order": ["cerebras"]}}
