import os

import pytest
from fastapi.testclient import TestClient

# LLM en modo mock para tests deterministas y sin red.
os.environ["LLM_MOCK"] = "true"


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "finally.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path


@pytest.fixture
def seed_prices(db_path):
    """Inyecta precios deterministas en price_cache para tests sin proveedor real."""
    from app.market_data import price_cache
    from app.market_data.cache import CachedPrice

    price_cache._latest.clear()
    prices = {"AAPL": 190.0, "GOOGL": 175.0, "MSFT": 400.0, "NVDA": 1200.0}
    for ticker, price in prices.items():
        price_cache._latest[ticker] = CachedPrice(price=price, prev_price=price, timestamp="t")
    return prices


class _FakeProvider:
    """Proveedor de mercado inerte: registra add/remove sin tocar price_cache."""

    def __init__(self) -> None:
        self.added: list[str] = []
        self.removed: list[str] = []

    def add_ticker(self, ticker: str) -> None:
        self.added.append(ticker)

    def remove_ticker(self, ticker: str) -> None:
        self.removed.append(ticker)

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


@pytest.fixture
def client(seed_prices, monkeypatch):
    """TestClient con BD temporal sembrada y proveedor inerte (precios estables)."""
    import app.main as main

    monkeypatch.setattr(main, "build_market_data_provider", lambda on_tick: _FakeProvider())
    with TestClient(main.app) as c:
        yield c
