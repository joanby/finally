import os

from .base import MarketDataProvider, TickCallback
from .massive_client import MassiveMarketDataProvider
from .simulator import MarketSimulator


def build_market_data_provider(on_tick: TickCallback) -> MarketDataProvider:
    """Selecciona la implementación de MarketDataProvider según el entorno.

    Si MASSIVE_API_KEY está definida y no está vacía, usa la API de Massive;
    en caso contrario, usa el simulador integrado (ver planning/PLAN.md §5-6).
    """
    massive_key = os.environ.get("MASSIVE_API_KEY", "").strip()
    if massive_key:
        return MassiveMarketDataProvider(on_tick)
    return MarketSimulator(on_tick)
