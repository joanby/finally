from app.llm import ChatResult, generate_chat_response


def test_mock_mode_used_when_env_true(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    result = generate_chat_response("buy 1 AAPL", {}, [])
    assert isinstance(result, ChatResult)
    assert result.trades[0].ticker == "AAPL"


def test_real_path_calls_llm_when_mock_disabled(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "false")
    captured = {}

    def fake_call_llm(messages):
        captured["messages"] = messages
        return ChatResult(message="ok")

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)
    result = generate_chat_response(
        "hola", {"cash_balance": 100.0}, [{"role": "user", "content": "hi"}]
    )
    assert result.message == "ok"
    assert captured["messages"][-1] == {"role": "user", "content": "hola"}
