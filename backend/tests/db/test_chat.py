def test_add_chat_message_without_actions(db):
    message = db.add_chat_message("user", "hola")

    assert message["role"] == "user"
    assert message["content"] == "hola"
    assert message["actions"] is None


def test_add_chat_message_serializes_actions_as_json(db):
    actions = {"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}]}

    db.add_chat_message("assistant", "comprado", actions)

    [message] = db.recent_chat_messages()
    assert message["actions"] == actions


def test_recent_chat_messages_returns_chronological_order(db):
    db.add_chat_message("user", "primero")
    db.add_chat_message("assistant", "segundo")

    messages = db.recent_chat_messages()
    assert [m["content"] for m in messages] == ["primero", "segundo"]


def test_recent_chat_messages_respects_limit(db):
    for i in range(5):
        db.add_chat_message("user", f"mensaje {i}")

    messages = db.recent_chat_messages(limit=2)
    assert [m["content"] for m in messages] == ["mensaje 3", "mensaje 4"]
