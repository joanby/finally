"""Tests del stream SSE.

El TestClient de Starlette+httpx de este entorno se cuelga al abrir una respuesta
streaming infinita, así que ejercitamos el generador real directamente y verificamos
el cableado de la ruta sobre la app (pytest-asyncio en modo auto).
"""

import json

from app.api import stream


class _FakeRequest:
    """Request mínima: nunca desconectada, para drenar el snapshot inicial."""

    async def is_disconnected(self) -> bool:
        return False


async def test_event_source_emits_initial_snapshot(seed_prices):
    gen = stream._event_source(_FakeRequest())
    first = await gen.__anext__()
    await gen.aclose()

    assert first.startswith("data: ")
    payload = json.loads(first[len("data: "):].strip())
    assert set(payload) == {"ticker", "price", "prev_price", "timestamp", "direction"}
    assert payload["ticker"] in seed_prices


def test_stream_route_registered(client):
    paths = client.app.openapi()["paths"]
    assert "get" in paths["/api/stream/prices"]
