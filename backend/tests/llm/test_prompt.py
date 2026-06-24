from app.llm.prompt import build_messages


def test_build_messages_shape():
    history = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "hey"}]
    messages = build_messages("¿cómo va mi cartera?", {"cash_balance": 100.0}, history)

    assert messages[0]["role"] == "system"
    assert "FinAlly" in messages[0]["content"]
    assert messages[1]["role"] == "system"
    assert "cash_balance" in messages[1]["content"]
    assert messages[2:4] == history
    assert messages[-1] == {"role": "user", "content": "¿cómo va mi cartera?"}
