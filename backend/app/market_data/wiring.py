from .cache import price_cache
from .types import PriceTick


async def on_tick(tick: PriceTick) -> None:
    """Callback por defecto que conecta cualquier proveedor con la caché de precios."""
    await price_cache.update(tick)
