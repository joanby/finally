from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import db
from app.services import portfolio

router = APIRouter(prefix="/api/watchlist")


class WatchlistRequest(BaseModel):
    ticker: str


@router.get("")
def get_watchlist() -> dict:
    tickers = [
        {"ticker": t, "price": portfolio.current_price(t)} for t in db.list_watchlist()
    ]
    return {"tickers": tickers}


@router.post("")
def add(req: WatchlistRequest, request: Request) -> dict:
    ticker = req.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker vacío")
    added = db.add_to_watchlist(ticker)
    if added:
        provider = request.app.state.provider
        if provider is not None:
            provider.add_ticker(ticker)
    return {"ticker": ticker, "added": added}


@router.delete("/{ticker}")
def remove(ticker: str, request: Request) -> dict:
    ticker = ticker.upper()
    removed = db.remove_from_watchlist(ticker)
    # No dejamos de seguir un ticker que aún tiene posición abierta.
    if removed and ticker not in portfolio.active_tickers():
        provider = request.app.state.provider
        if provider is not None:
            provider.remove_ticker(ticker)
    return {"ticker": ticker, "removed": removed}
