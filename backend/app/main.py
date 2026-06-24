"""App FastAPI de FinAlly: integra BD, datos de mercado, cartera, watchlist y chat."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db
from app.api import chat, health, portfolio, stream, watchlist
from app.market_data import build_market_data_provider, on_tick
from app.services.portfolio import active_tickers, portfolio_value

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SNAPSHOT_INTERVAL_SECONDS = 30


async def _snapshot_loop() -> None:
    """Registra el valor de la cartera cada 30 s para el gráfico de P&L."""
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
        await asyncio.to_thread(db.record_snapshot, await asyncio.to_thread(portfolio_value))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    provider = build_market_data_provider(on_tick)
    for ticker in active_tickers():
        provider.add_ticker(ticker)
    await provider.start()
    app.state.provider = provider
    snapshot_task = asyncio.create_task(_snapshot_loop())
    try:
        yield
    finally:
        snapshot_task.cancel()
        await provider.stop()


app = FastAPI(title="FinAlly", lifespan=lifespan)
app.state.provider = None

app.include_router(health.router)
app.include_router(stream.router)
app.include_router(portfolio.router)
app.include_router(watchlist.router)
app.include_router(chat.router)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
