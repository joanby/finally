"""Lógica de trading y P&L de la cartera.

Funciones puras de negocio (sin FastAPI): leen el precio actual de `price_cache`,
validan y ejecutan órdenes de mercado, y calculan el estado de la cartera.
"""

from app import db
from app.market_data import price_cache


class TradeError(Exception):
    """Operación inválida (efectivo o cantidad insuficiente, precio no disponible)."""


def current_price(ticker: str) -> float | None:
    """Último precio conocido del ticker, o None si aún no hay tick."""
    cached = price_cache.get(ticker)
    return cached.price if cached is not None else None


def execute_trade(ticker: str, quantity: float, side: str) -> dict:
    """Ejecuta una orden de mercado al precio actual y persiste el resultado.

    Compra: valida efectivo, actualiza posición con coste medio ponderado.
    Venta: valida cantidad poseída; al vender todo borra la posición.
    Registra el trade y un snapshot inmediato. Lanza TradeError si no es válida.
    """
    ticker = ticker.upper()
    side = side.lower()
    if side not in ("buy", "sell"):
        raise TradeError(f"Lado inválido: {side}")
    if quantity <= 0:
        raise TradeError("La cantidad debe ser positiva")

    price = current_price(ticker)
    if price is None:
        raise TradeError(f"No hay precio disponible para {ticker}")

    profile = db.get_profile()
    cash = profile["cash_balance"]
    position = db.get_position(ticker)

    if side == "buy":
        cost = price * quantity
        if cost > cash:
            raise TradeError(
                f"Efectivo insuficiente: necesitas {cost:.2f} y tienes {cash:.2f}"
            )
        if position is None:
            new_qty, new_avg = quantity, price
        else:
            total_qty = position["quantity"] + quantity
            new_avg = (
                position["avg_cost"] * position["quantity"] + price * quantity
            ) / total_qty
            new_qty = total_qty
        db.upsert_position(ticker, new_qty, new_avg)
        db.set_cash_balance(cash - cost)
    else:  # sell
        owned = position["quantity"] if position is not None else 0.0
        if quantity > owned:
            raise TradeError(
                f"Cantidad insuficiente: tienes {owned} de {ticker}, intentas vender {quantity}"
            )
        proceeds = price * quantity
        remaining = owned - quantity
        if remaining == 0:
            db.delete_position(ticker)
        else:
            db.upsert_position(ticker, remaining, position["avg_cost"])
        db.set_cash_balance(cash + proceeds)

    trade = db.record_trade(ticker, side, quantity, price)
    db.record_snapshot(portfolio_value())
    return trade


def portfolio_state() -> dict:
    """Estado completo de la cartera con precios en vivo y P&L no realizado."""
    profile = db.get_profile()
    cash = profile["cash_balance"]
    positions = []
    positions_value = 0.0
    total_pnl = 0.0
    for pos in db.list_positions():
        price = current_price(pos["ticker"])
        price = price if price is not None else pos["avg_cost"]
        market_value = price * pos["quantity"]
        cost_basis = pos["avg_cost"] * pos["quantity"]
        pnl = market_value - cost_basis
        pct = (price / pos["avg_cost"] - 1) * 100 if pos["avg_cost"] else 0.0
        positions_value += market_value
        total_pnl += pnl
        positions.append(
            {
                "ticker": pos["ticker"],
                "quantity": pos["quantity"],
                "avg_cost": pos["avg_cost"],
                "current_price": price,
                "unrealized_pnl": pnl,
                "pct_change": pct,
            }
        )
    return {
        "cash_balance": cash,
        "positions": positions,
        "total_value": cash + positions_value,
        "total_unrealized_pnl": total_pnl,
    }


def portfolio_value() -> float:
    """Valor total de la cartera (efectivo + valor de mercado de las posiciones)."""
    return portfolio_state()["total_value"]


def active_tickers() -> set[str]:
    """Unión de watchlist y tickers con posición abierta (los que el stream debe seguir)."""
    return set(db.list_watchlist()) | {p["ticker"] for p in db.list_positions()}
