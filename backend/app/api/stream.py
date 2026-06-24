import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.market_data import Direction, PriceTick, price_cache

router = APIRouter(prefix="/api/stream")

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
_HEARTBEAT_SECONDS = 15


async def _event_source(request: Request):
    """Genera el stream SSE: snapshot inicial + ticks en vivo de price_cache.

    Emite un keep-alive si no llegan ticks en _HEARTBEAT_SECONDS y se detiene
    en cuanto el cliente se desconecta, para no dejar la conexión parada.
    """
    queue = price_cache.subscribe()
    try:
        for ticker, cached in price_cache.snapshot().items():
            tick = PriceTick(
                ticker=ticker,
                price=cached.price,
                prev_price=cached.prev_price,
                timestamp=cached.timestamp,
                direction=Direction.FLAT,
            )
            yield f"data: {json.dumps(tick.to_sse_dict())}\n\n"
        while not await request.is_disconnected():
            try:
                tick = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield f"data: {json.dumps(tick.to_sse_dict())}\n\n"
    finally:
        price_cache.unsubscribe(queue)


@router.get("/prices")
async def stream_prices(request: Request) -> StreamingResponse:
    return StreamingResponse(
        _event_source(request), media_type="text/event-stream", headers=_SSE_HEADERS
    )
