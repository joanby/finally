from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import db
from app.services import portfolio

router = APIRouter(prefix="/api/portfolio")


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str


@router.get("")
def get_portfolio() -> dict:
    return portfolio.portfolio_state()


@router.post("/trade")
def trade(req: TradeRequest, request: Request) -> dict:
    try:
        result = portfolio.execute_trade(req.ticker, req.quantity, req.side)
    except portfolio.TradeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # Una compra puede introducir un ticker nuevo que el stream debe seguir.
    provider = request.app.state.provider
    if provider is not None:
        provider.add_ticker(req.ticker.upper())
    return result


@router.get("/history")
def history() -> dict:
    return {"snapshots": db.list_snapshots()}
