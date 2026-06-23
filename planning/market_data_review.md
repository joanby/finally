# Revisión del Backend de Datos de Mercado

**Fecha:** 2026-06-23  
**Revisor:** Claude Sonnet 4.6  
**Resultado de tests:** 47/47 ✅ (tras corrección de 1 bug + cierre de 3 gaps de cobertura + alineación de precios semilla con el diseño)

---

## Resumen ejecutivo

La implementación cumple fielmente la especificación de `PLAN.md` §6 y los documentos de diseño de `planning/`. La arquitectura es limpia y desacoplada. Se encontró y corrigió un bug en `PriceCache.snapshot()`. No hay problemas de seguridad ni deuda técnica significativa.

---

## Archivos revisados

| Archivo | Estado |
|---|---|
| `app/market_data/types.py` | ✅ Correcto |
| `app/market_data/base.py` | ✅ Correcto |
| `app/market_data/cache.py` | ✅ Corregido (ver §Bug) |
| `app/market_data/simulator_config.py` | ✅ Correcto |
| `app/market_data/correlation.py` | ✅ Correcto |
| `app/market_data/simulator.py` | ✅ Correcto |
| `app/market_data/massive_config.py` | ✅ Correcto |
| `app/market_data/massive_client.py` | ✅ Correcto |
| `app/market_data/factory.py` | ✅ Correcto |
| `app/market_data/wiring.py` | ✅ Correcto |

---

## Bug encontrado y corregido

### `PriceCache.snapshot()` — copia superficial (shallow copy)

**Archivo:** `app/market_data/cache.py`  
**Severidad:** Media — no es un crash pero viola la garantía de aislamiento que el código promete.

**Problema:** `snapshot()` hacía `dict(self._latest)`, que copia el diccionario pero comparte los objetos `CachedPrice` internos. Cualquier código que mutera un `CachedPrice` obtenido del snapshot estaría modificando el estado real de la caché.

**Corrección aplicada:**
```python
# Antes
def snapshot(self) -> dict[str, CachedPrice]:
    return dict(self._latest)

# Después
def snapshot(self) -> dict[str, CachedPrice]:
    return {k: CachedPrice(v.price, v.prev_price, v.timestamp) for k, v in self._latest.items()}
```

Cada `CachedPrice` del snapshot es ahora una instancia independiente. El test `test_snapshot_returns_a_copy` que detectaba este problema pasa correctamente.

**Alternativa equivalente:** declarar `CachedPrice` como `@dataclass(frozen=True, slots=True)` impediría la mutación por construcción, pero requeriría actualizar el test.

---

## Análisis por módulo

### `types.py` — Modelo de datos

- `PriceTick.create()` centraliza correctamente el cálculo de `direction` y el redondeo a 4 decimales.
- `Direction` hereda de `str` y `Enum`, lo que permite serializar directamente a JSON sin conversión manual.
- El campo `timestamp` como ISO 8601 UTC string (no `float` epoch) es la elección correcta para SSE — el frontend puede parsear directamente con `new Date(ts)`.
- `to_sse_dict()` emite `direction.value` (string), no el objeto Enum — correcto para JSON.

### `base.py` — Interfaz abstracta

- La firma mínima (`start`, `stop`, `add_ticker`, `remove_ticker`, `_emit`) sigue la especificación exacta de `market_data_design.md`.
- La propiedad `tickers` devuelve un `frozenset`, lo que previene mutaciones accidentales desde fuera de la clase.
- El método `_emit` como método concreto en la base (no abstracto) es la decisión correcta: es puro andamiaje, no lógica específica de implementación.
- El convenio `TickCallback = Callable[[PriceTick], Awaitable[None]]` tipifica correctamente el contrato del callback.

### `cache.py` — Caché pub/sub

- El lock `asyncio.Lock` en `update()` protege correctamente contra escrituras concurrentes.
- El drop automático de suscriptores lentos (`QueueFull`) evita que un cliente lento bloquee al proveedor.
- El singleton `price_cache` a nivel de módulo es el patrón estándar de FastAPI para estado compartido.
- **Post-corrección:** `snapshot()` es ahora una copia profunda de valores, aislada del estado interno.

### `simulator_config.py` — Parámetros GBM

- Los precios semilla y parámetros por ticker (drift, volatility, sector) corresponden bien a los valores del documento `market_simulator.md`.
- `EFFECTIVE_DT_PER_TICK = 1.0 / 360` (un "día" simulado en ~3 min reales) es el valor correcto para movimiento visualmente dramático pero no absurdo.
- `EVENT_PROBABILITY = 0.0008` se traduce a ~1 evento cada ~20 min a 500ms/tick — consistente con la especificación.
- Los parámetros genéricos para tickers no pre-configurados (`GENERIC_TICKER_DRIFT`, `GENERIC_TICKER_VOLATILITY = 0.30`, `GENERIC_TICKER_SECTOR = "general"`) son valores razonables de fallback.

**Discrepancia menor con el diseño — corregida:** `market_simulator.md` especificaba precios semilla ligeramente diferentes para algunos tickers (META=$580, JPM=$215, V=$310, NVDA=$135), mientras que `simulator_config.py` usaba META=$500, JPM=$200, V=$280, NVDA=$130. Se alinearon los cuatro valores con el documento de diseño. Ningún test dependía de los valores anteriores, por lo que el cambio no rompió la suite.

### `correlation.py` — Shocks correlacionados

- El enfoque de tres factores (mercado global + sector + idiosincrático) implementa correctamente la especificación de `market_data_design.md §5.3`.
- La normalización por `norm = (w_market² + w_sector² + w_idio²)^0.5` mantiene la varianza total ~1, preservando la propiedad N(0,1) aproximada de los shocks.
- La función acepta `sectors_by_ticker: dict[str, str]` como parámetro en lugar de leer `DEFAULT_TICKERS` directamente — esto es correcto porque el simulador puede tener tickers dinámicos no en el config estático.
- El test `test_shocks_are_roughly_standard_normal` valida estadísticamente esta propiedad (media ≈ 0, stdev entre 0.85 y 1.15 sobre 500×20 muestras).
- El test `test_same_sector_tickers_move_more_alike_than_different_sectors` valida el efecto de correlación sectorial sobre 300 iteraciones.

### `simulator.py` — Bucle GBM

- El método `tick_once()` es **público** y retorna la lista de ticks — decisión clave de diseño: permite que los tests avancen la simulación de forma determinista sin temporizadores reales. Los tests lo aprovechan extensamente.
- El precio mínimo `max(new_price, 0.01)` previene precios negativos o cero, aunque GBM por construcción no puede llegar a cero; es una salvaguarda defensiva correcta.
- Los tickers dinámicos (no en `DEFAULT_TICKERS`) reciben precio log-uniforme entre 10 y 500 — implementa correctamente la especificación de `market_simulator.md §8`.
- El bucle `_run_loop` llama a `tick_once()` y luego `asyncio.sleep()` — el sleep va al *final* del tick, no al principio, lo que significa que el primer tick ocurre inmediatamente al arrancar. Comportamiento correcto para el snapshot inicial SSE.

### `massive_client.py` — Cliente Massive/Polygon

- El parámetro `client: httpx.AsyncClient | None = None` en el constructor permite inyectar un cliente mock en tests — patrón de inyección de dependencias correcto que los tests explotan completamente con `httpx.MockTransport`.
- `poll_once()` es público (como `tick_once()` en el simulador) — misma decisión de diseño, misma ventaja en testabilidad.
- La jerarquía de fallback en `_parse_response()`: `lastTrade.p` → `day.c` → `prevDay.c` es correcta y está cubierta por el test `test_poll_once_falls_back_to_day_close_then_prev_day_close`.
- El bucle `_run_loop` traga `httpx.HTTPError` con un log de warning y continúa — comportamiento correcto para resiliencia ante fallos transitorios de red. Cubierto por `test_run_loop_swallows_http_errors_and_keeps_polling`.
- `stop()` llama a `await self._client.aclose()` — limpieza correcta del cliente HTTP. Cubierto por `test_stop_closes_the_http_client`.

**Nota sobre la URL base:** `massive_config.py` usa `https://api.massive.com` como base URL, pero el endpoint de snapshot es `/v2/snapshot/locale/us/markets/stocks/tickers`. Esto es consistente con la documentación de Massive/Polygon investigada en `massive_api.md §4`.

### `factory.py` — Selección del proveedor

- Lógica mínima y correcta: `.strip()` en la clave antes de evaluar su presencia — esto maneja el caso de una clave que solo contiene espacios en blanco (cubierto por `test_uses_simulator_when_massive_key_blank`).

### `wiring.py` — Conexión proveedor↔caché

- Módulo de una función: conecta cualquier proveedor con el singleton `price_cache`. Correcto, sin lógica adicional innecesaria.

---

## Análisis de la suite de tests

### Cobertura por módulo

| Módulo | Tests | Calidad |
|---|---|---|
| `types.py` | 4 | Cubre los 3 directions, redondeo, timestamp UTC, forma SSE |
| `base.py` | 3 | ABC no instanciable, callback emit, propiedad tickers |
| `cache.py` | 8 | CRUD, snapshot aislado, sub/unsub, drop de cola llena, fan-out a múltiples suscriptores |
| `correlation.py` | 5 | Cobertura, normalidad estadística, correlación sectorial, determinismo, sector nuevo |
| `simulator.py` | 12 | Interfaz, tickers default, emisión, movimiento, add/remove, re-add genérico, seed, loop |
| `massive_client.py` | 10 | Interfaz, add/remove, request URL, parseo, fallbacks, errores, loop, cleanup |
| `factory.py` | 3 | Sin clave, clave en blanco, clave presente |
| `wiring.py` | 1 | Escritura al cache compartido |

**Total: 47 tests** — cobertura completa del happy path, los casos de error más importantes, y los gaps previamente identificados.

### Puntos fuertes de la suite

1. **Determinismo:** el uso de `seed` fijo en simulador y `MockTransport` en Massive Client permite tests reproducibles sin timers reales.
2. **`tick_once()` y `poll_once()` como métodos públicos** permiten avanzar el estado sin `asyncio.sleep()`, haciendo los tests rápidos y sin flakiness.
3. **Tests estadísticos en correlation:** `test_shocks_are_roughly_standard_normal` y `test_same_sector_tickers_move_more_alike_than_different_sectors` validan propiedades matemáticas reales, no solo que "no falla".
4. **Test de comportamiento de lifecycle:** `test_start_and_stop_runs_background_loop` y `test_run_loop_swallows_http_errors_and_keeps_polling` validan comportamiento asíncrono real.

### Gaps de cobertura — cerrados

Los tres gaps identificados en la primera pasada de revisión ya están cubiertos:

- **`correlated_shocks` con sector no visto** → `test_handles_a_brand_new_sector_not_seen_before` en `test_correlation.py`.
- **`PriceCache` con múltiples suscriptores simultáneos** → `test_multiple_subscribers_all_receive_the_same_tick` y `test_unsubscribing_one_does_not_affect_others` en `test_cache.py`.
- **`MarketSimulator.add_ticker` re-añadiendo un ticker genérico ya visto** → `test_readding_a_previously_seen_generic_ticker_preserves_its_price` en `test_simulator.py`, que confirma que el precio se conserva (no se regenera) al re-añadir.

---

## Conformidad con el diseño documentado

| Requisito de PLAN.md / documentos de diseño | Implementado |
|---|---|
| Dos implementaciones con interfaz común | ✅ |
| Simulador usa GBM con `exp((μ - σ²/2)dt + σ√dt·Z)` | ✅ |
| Shocks correlacionados por sector | ✅ |
| Eventos de salto idiosincrático ocasionales | ✅ |
| Tickers dinámicos con precio log-uniforme | ✅ |
| `dt` efectivo acelerado para efecto visual | ✅ |
| Massive usa polling REST por lotes | ✅ |
| Fallback a simulador si no hay `MASSIVE_API_KEY` | ✅ |
| Caché con fan-out pub/sub por `asyncio.Queue` | ✅ |
| Drop automático de suscriptores lentos | ✅ |
| `snapshot()` para snapshot inicial SSE | ✅ |
| Seed determinista para tests | ✅ |

---

## Conclusión

La implementación es sólida, bien estructurada y fiel a la especificación. El bug real (shallow copy en `snapshot()`) está corregido, los precios semilla están alineados con `market_simulator.md`, y los tres gaps de cobertura identificados se cerraron con nuevos tests. La suite de 47 tests pasa en su totalidad. El módulo está listo para integrarse con el resto del backend (rutas SSE, watchlist, portfolio).
