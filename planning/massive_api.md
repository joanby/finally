# Investigación: API de Datos de Mercado de Massive (antes Polygon.io)

## 1. Contexto

[Polygon.io se renombró a Massive.com](https://massive.com/blog/polygon-is-now-massive) el 30 de octubre de 2025. El cambio es solo de marca: las claves de API, las cuentas, los endpoints y la calidad de los datos existentes siguen funcionando exactamente igual, sin necesidad de actualizar código. El dominio legacy `api.polygon.io` sigue soportado; el nuevo dominio es `api.massive.com`. El cliente Python oficial se renombró de `polygon-api-client` a `massive`.

La documentación completa vive en [massive.com/docs](https://massive.com/docs) (interfaz JavaScript renderizada en cliente, por lo que no es trivial *scrapear*; conviene consultar vía navegador o el índice en texto plano [massive.com/docs/llms.txt](https://massive.com/docs/llms.txt)).

## 2. Qué necesitamos de esta API para FinAlly

Según `planning/PLAN.md`, solo necesitamos **datos de acciones (stocks)** vía **REST con sondeo (polling)**, no WebSocket — el PLAN ya descarta WebSocket a favor de un poller REST simple compatible con el nivel gratuito. Los casos de uso concretos son:

1. Precio actual de cada ticker en la watchlist + posiciones abiertas (para el caché de precios y el stream SSE).
2. Precio de cierre anterior (para calcular el % de cambio diario).
3. Historial de precios para el gráfico principal cuando el usuario selecciona un ticker.
4. Precio semilla razonable cuando se añade un ticker nuevo no visto antes.

## 3. Autenticación

- Autenticación por API key simple, pasada como query param `apiKey=...` o cabecera `Authorization: Bearer <API_KEY>`.
- Con el cliente oficial Python:

```python
from massive import RESTClient
client = RESTClient(api_key="<API_KEY>")
```

- En FinAlly, la clave se lee de `MASSIVE_API_KEY` en `.env` (ver `planning/PLAN.md` sección 5). Si está vacía, no se usa Massive y se cae al simulador.

## 4. Endpoints relevantes

| Propósito | Endpoint REST | Notas |
|---|---|---|
| Snapshot de un ticker | `GET /v2/snapshot/locale/us/markets/stocks/tickers/{ticker}` | Precio actual, OHLC del día, cierre anterior, último trade/quote — todo en una llamada |
| **Snapshot de varios tickers a la vez** | `GET /v2/snapshot/locale/us/markets/stocks/tickers?tickers=AAPL,MSFT,GOOGL` | **Clave para nosotros**: una sola llamada cubre toda la watchlist |
| Cierre anterior | `GET /v2/aggs/ticker/{ticker}/prev` | Para el % de cambio diario si no se usa el snapshot |
| Barras agregadas (velas) | `GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}` | Para el gráfico histórico al seleccionar un ticker (p. ej. velas de 1 día de los últimos 3 meses) |
| Barras diarias agrupadas (todo el mercado) | `GET /v2/aggs/grouped/locale/us/market/stocks/{date}` | No la necesitamos en el alcance actual |
| Último trade / última quote | `GET /v2/last/trade/{ticker}`, `/v2/last/nbbo/{ticker}` | Cubierto ya por el snapshot, no hace falta llamarlos por separado |
| Detalles de ticker | `GET /v3/reference/tickers/{ticker}` | Útil si se quiere validar que un ticker nuevo existe antes de simularlo/seguirlo |

El cliente Python oficial expone equivalentes directos: `client.get_snapshot_all(market_type="stocks", tickers=[...])`, `client.get_previous_close_agg(ticker)`, `client.list_aggs(ticker, multiplier, timespan, from_, to)`.

## 5. Límites de uso y niveles (tiers)

- **Nivel gratuito**: 5 llamadas/minuto, datos con retraso (no en tiempo real). Esto coincide con lo ya asumido en `planning/PLAN.md` sección 6.
- **Niveles de pago**: desde $199/mes, llamadas prácticamente ilimitadas y datos en tiempo real. Massive recomienda no superar ~100 req/s incluso en planes sin límite explícito, para evitar *throttling*.
- Hay suscripciones separadas por clase de activo (Stocks, Options, Indices, Forex+Crypto, Futures); a nosotros solo nos concierne **Stocks**.

### Implicación de diseño importante

Con **5 llamadas/min** en el nivel gratuito, sondear cada ticker individualmente (10 tickers × 1 llamada cada uno) agotaría la cuota en una sola pasada. La solución es usar el **endpoint de snapshot por lotes** (`tickers=AAPL,MSFT,...`), que devuelve la unión completa de tickers vigilados en **una sola llamada**. Esto permite sondear cada ~15 segundos (4 llamadas/min, dejando margen) sin exceder el límite, tal como ya prevé el PLAN (sección 6: "Nivel gratuito (5 llamadas/min): sondeo cada 15 segundos").

## 6. Formato de respuesta (snapshot, resumido)

```json
{
  "status": "OK",
  "tickers": [
    {
      "ticker": "AAPL",
      "day": { "o": 188.2, "h": 191.0, "l": 187.5, "c": 189.7, "v": 52000000 },
      "prevDay": { "c": 187.9 },
      "lastTrade": { "p": 189.72, "t": 1735000000000 },
      "lastQuote": { "P": 189.75, "p": 189.70 },
      "todaysChange": 1.82,
      "todaysChangePerc": 0.97
    }
  ]
}
```

Mapeo directo a nuestro modelo interno: `price = lastTrade.p`, `previous_price` se deriva del último valor cacheado (o `prevDay.c` en el primer arranque), `timestamp = lastTrade.t`.

## 7. Cliente oficial vs llamadas HTTP directas

- Cliente Python oficial: `uv add massive` (paquete `massive`, antes `polygon-api-client`). Da tipado y paginación automática, pero es una dependencia más.
- Alternativa: usar `httpx` directamente contra `https://api.massive.com/...` — más control, menos abstracción, coherente con "no sobre-ingenierices". Dado que solo necesitamos 1-2 endpoints (snapshot por lotes + aggregates para el histórico), **llamadas HTTP directas con `httpx` son suficientes** y evitan atar el proyecto a un SDK completo para dos llamadas.

## 8. Recomendación para el backend

1. Implementar `MassiveProvider` que cumple la misma interfaz que el simulador (ver `planning/market_data_interface.md`).
2. Un único poller en segundo plano llama a `GET /v2/snapshot/locale/us/markets/stocks/tickers?tickers=...` con la unión de watchlist + posiciones abiertas, cada 15s (configurable según el plan/tier).
3. Al añadir un ticker nuevo a la watchlist, se incluye automáticamente en la siguiente llamada por lotes (no hace falta una llamada extra de "seed", a diferencia del simulador).
4. Si `MASSIVE_API_KEY` no está definida o está vacía → se usa el simulador (`planning/market_simulator.md`), sin tocar este código.

## Fuentes

- [Polygon.io is Now Massive](https://massive.com/blog/polygon-is-now-massive)
- [Massive — Stock Market API](https://massive.com/)
- [Massive API Docs](https://massive.com/docs)
- [Stocks REST API Overview](https://massive.com/docs/rest/stocks/overview)
- [REST API Quickstart](https://massive.com/docs/rest/quickstart)
- [Pricing | Massive](https://massive.com/pricing)
- [What is the request limit for Massive's RESTful APIs?](https://massive.com/knowledge-base/article/what-is-the-request-limit-for-massives-restful-apis)
- [What are the different Massive subscriptions I can use?](https://massive.com/knowledge-base/article/what-are-the-different-massive-subscriptions-i-can-use)
- [github.com/massive-com/client-python](https://github.com/massive-com/client-python)
- [Polygon (legacy) Stocks library reference](https://polygon.readthedocs.io/en/latest/Stocks.html)
