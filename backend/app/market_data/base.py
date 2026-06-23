from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from .types import PriceTick

TickCallback = Callable[[PriceTick], Awaitable[None]]


class MarketDataProvider(ABC):
    """Interfaz unificada que deben implementar el simulador y el cliente de Massive.

    El contrato es deliberadamente mínimo: arrancar, detener, y notificar ticks vía
    callback — así el resto del sistema (caché de precios, SSE) es agnóstico a la
    fuente de datos concreta (ver planning/PLAN.md §6 y planning/market_data_interface.md).
    """

    def __init__(self, on_tick: TickCallback) -> None:
        self._on_tick = on_tick
        self._tickers: set[str] = set()

    @abstractmethod
    async def start(self) -> None:
        """Arranca la tarea en segundo plano que produce ticks."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Detiene limpiamente la tarea en segundo plano."""
        ...

    @abstractmethod
    def add_ticker(self, ticker: str) -> None:
        """Añade un ticker al conjunto vigilado."""
        ...

    @abstractmethod
    def remove_ticker(self, ticker: str) -> None:
        """Elimina un ticker del conjunto vigilado."""
        ...

    @property
    def tickers(self) -> frozenset[str]:
        return frozenset(self._tickers)

    async def _emit(self, tick: PriceTick) -> None:
        await self._on_tick(tick)
