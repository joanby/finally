import re

from .models import ChatResult, TradeAction, WatchlistChange

_BUY_RE = re.compile(r"\bbuy\s+(\d+(?:\.\d+)?)\s+([a-zA-Z]+)\b", re.IGNORECASE)
_SELL_RE = re.compile(r"\bsell\s+(\d+(?:\.\d+)?)\s+([a-zA-Z]+)\b", re.IGNORECASE)
_ADD_RE = re.compile(r"\badd\s+([a-zA-Z]+)\b", re.IGNORECASE)
_REMOVE_RE = re.compile(r"\bremove\s+([a-zA-Z]+)\b", re.IGNORECASE)


def mock_chat_response(user_message: str) -> ChatResult:
    """Respuesta determinista para LLM_MOCK=true, sin red.

    Reglas (aplicadas todas sobre `user_message`, sin distinguir mayúsculas):
    - `buy <n> <TICKER>`    -> trades += [{ticker: TICKER, side: "buy", quantity: n}]
    - `sell <n> <TICKER>`   -> trades += [{ticker: TICKER, side: "sell", quantity: n}]
    - `add <TICKER>`        -> watchlist_changes += [{ticker: TICKER, action: "add"}]
    - `remove <TICKER>`     -> watchlist_changes += [{ticker: TICKER, action: "remove"}]
    Pueden coincidir varias reglas en el mismo mensaje. `message` siempre es no
    vacío y resume lo entendido (o indica que no se reconoció ninguna instrucción).
    """
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistChange] = []
    understood: list[str] = []

    for quantity, ticker in _BUY_RE.findall(user_message):
        ticker = ticker.upper()
        trades.append(TradeAction(ticker=ticker, side="buy", quantity=float(quantity)))
        understood.append(f"comprar {quantity} {ticker}")

    for quantity, ticker in _SELL_RE.findall(user_message):
        ticker = ticker.upper()
        trades.append(TradeAction(ticker=ticker, side="sell", quantity=float(quantity)))
        understood.append(f"vender {quantity} {ticker}")

    for ticker in _ADD_RE.findall(user_message):
        ticker = ticker.upper()
        watchlist_changes.append(WatchlistChange(ticker=ticker, action="add"))
        understood.append(f"añadir {ticker} a la watchlist")

    for ticker in _REMOVE_RE.findall(user_message):
        ticker = ticker.upper()
        watchlist_changes.append(WatchlistChange(ticker=ticker, action="remove"))
        understood.append(f"eliminar {ticker} de la watchlist")

    if understood:
        message = "Entendido: " + "; ".join(understood) + "."
    else:
        message = "No he detectado ninguna instrucción de operación o watchlist en tu mensaje."

    return ChatResult(message=message, trades=trades, watchlist_changes=watchlist_changes)
