"""Servicio de chat: compone contexto de cartera, llama al LLM y ejecuta su plan.

El módulo LLM es puro (no toca la BD); aquí ejecutamos los trades y cambios de
watchlist que devuelve, con la misma validación que las operaciones manuales.
"""

from app import db
from app.llm import generate_chat_response
from app.market_data import MarketDataProvider
from app.services import portfolio


def _build_context() -> dict:
    """Contexto de cartera para el LLM (forma definida en el contrato §LLM)."""
    state = portfolio.portfolio_state()
    watchlist = [
        {"ticker": t, "price": portfolio.current_price(t)} for t in db.list_watchlist()
    ]
    return {
        "cash_balance": state["cash_balance"],
        "total_value": state["total_value"],
        "positions": state["positions"],
        "watchlist": watchlist,
    }


def handle_message(message: str, provider: MarketDataProvider | None = None) -> dict:
    """Procesa un mensaje de chat: LLM -> ejecuta acciones -> persiste -> responde.

    Devuelve `{message, actions: {trades, watchlist_changes, errors}}`.
    Los errores de validación se acumulan en vez de abortar el resto del plan.
    """
    history = [
        {"role": m["role"], "content": m["content"]} for m in db.recent_chat_messages()
    ]
    result = generate_chat_response(message, _build_context(), history)

    executed_trades: list[dict] = []
    watchlist_changes: list[dict] = []
    errors: list[str] = []

    for trade in result.trades:
        try:
            portfolio.execute_trade(trade.ticker, trade.quantity, trade.side)
            executed_trades.append(
                {"ticker": trade.ticker.upper(), "side": trade.side, "quantity": trade.quantity}
            )
        except portfolio.TradeError as exc:
            errors.append(str(exc))

    for change in result.watchlist_changes:
        ticker = change.ticker.upper()
        if change.action == "add":
            if db.add_to_watchlist(ticker):
                if provider is not None:
                    provider.add_ticker(ticker)
                watchlist_changes.append({"ticker": ticker, "action": "add"})
        elif change.action == "remove":
            if db.remove_from_watchlist(ticker):
                if provider is not None and ticker not in portfolio.active_tickers():
                    provider.remove_ticker(ticker)
                watchlist_changes.append({"ticker": ticker, "action": "remove"})
        else:
            errors.append(f"Acción de watchlist desconocida: {change.action}")

    actions = {
        "trades": executed_trades,
        "watchlist_changes": watchlist_changes,
        "errors": errors,
    }
    db.add_chat_message("user", message)
    db.add_chat_message("assistant", result.message, actions)
    return {"message": result.message, "actions": actions}
