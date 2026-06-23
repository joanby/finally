from app.market_data.cache import price_cache
from app.market_data.types import PriceTick
from app.market_data.wiring import on_tick


async def test_on_tick_writes_through_to_the_shared_price_cache():
    tick = PriceTick.create("WIRE", 10.0, 9.0)
    await on_tick(tick)

    assert price_cache.get("WIRE").price == 10.0
