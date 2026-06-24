from pydantic import BaseModel


class TradeAction(BaseModel):
    ticker: str
    side: str  # "buy" | "sell"
    quantity: float


class WatchlistChange(BaseModel):
    ticker: str
    action: str  # "add" | "remove"


class ChatResult(BaseModel):
    message: str
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistChange] = []
