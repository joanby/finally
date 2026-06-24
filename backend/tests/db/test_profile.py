def test_get_profile_returns_default_user(db):
    profile = db.get_profile()

    assert profile["id"] == "default"
    assert profile["cash_balance"] == 10000.0
    assert profile["created_at"]


def test_set_cash_balance_updates_value(db):
    db.set_cash_balance(8500.5)

    assert db.get_profile()["cash_balance"] == 8500.5
