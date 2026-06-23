# Diseño: Interfaz de Datos de Mercado

## 1. Objetivo

`planning/PLAN.md` (sección 6) exige que el simulador y el cliente de Massive implementen **la misma interfaz abstracta**, de forma que el resto del backend (caché de precios, streaming SSE, watchlist) sea agnóstico a la fuente de datos. Este documento concreta cómo construir esa interfaz.

## 2. Patrón: Protocol (contrato público) + ABC (base interna compartida)

La investigación sobre diseño de interfaces en Python moderno apunta a un patrón híbrido:

- Un **`Protocol`** define el contrato público que consume el resto de la app (tipado estructural — cualquier clase con los métodos correctos lo cumple, sin herencia obligatoria).
- Una **`ABC`** interna (`BaseMarketDataProvider`) implementa el código compartido entre `SimulatedProvider` y `MassiveProvider` (gestión del caché, lifecycle de la tarea en background, lógica de "añadir ticker en caliente").

Esto evita over-engineering: no necesitamos un framework de plugins, solo dos implementaciones concretas que comparten bastante lógica de orquestación.

```python
from typing import Protocol, AsyncIterator

class MarketDataProvider(Protocol):
    async def start(self, tickers: set[str]) -> None: ...
    async def add_ticker(self, ticker: str) -> None: ...
    def get_latest(self, ticker: str) -> PriceTick | None: ...
    def subscribe(self) -> AsyncIterator[PriceTick]: ...
```

## 3. Modelo de datos

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PriceTick:
    ticker: str
    price: float
    previous_price: float
    timestamp: float  # epoch seconds
    direction: str     # "up" | "down" | "flat"
```

`direction` se deriva de `price` vs `previous_price` y es lo que el frontend usa para el destello verde/rojo. Se calcula una sola vez en el provider, no en cada consumidor.

## 4. Caché de precios compartida

Un único objeto en memoria, propiedad del provider activo:

```python
class PriceCache:
    def __init__(self) -> None:
        self._latest: dict[str, PriceTick] = {}
        self._lock = asyncio.Lock()

    async def set(self, tick: PriceTick) -> None:
        async with self._lock:
            self._latest[tick.ticker] = tick

    def get(self, ticker: str) -> PriceTick | None:
        return self._latest.get(ticker)
```

- Lectura sin lock (dict.get es seguro en CPython para este caso de uso de un solo escritor).
- Escritura con lock para evitar carreras si en el futuro hay múltiples escritores.
- Vive como singleton a nivel de app (`app.state.price_cache`), inicializado en el `lifespan` de FastAPI.

## 5. Distribución a consumidores: caché + cola de difusión (broadcast)

El SSE necesita "empujar" eventos a clientes conectados, no solo leer el último valor. Patrón productor/consumidores con `asyncio.Queue` por cliente conectado:

```python
class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[PriceTick]] = []

    def subscribe(self) -> asyncio.Queue[PriceTick]:
        q: asyncio.Queue[PriceTick] = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    async def publish(self, tick: PriceTick) -> None:
        for q in self._subscribers:
            q.put_nowait(tick)  # descarta si el cliente va lento; no bloquea el productor
```

Cada conexión SSE (`GET /api/stream/prices`) llama a `subscribe()`, filtra por la unión de watchlist + posiciones abiertas de esa sesión, y hace `yield` de cada tick como evento SSE hasta que el cliente se desconecta (momento en que se elimina su cola).

## 6. La tarea en segundo plano (background task)

Tanto `SimulatedProvider` como `MassiveProvider` corren **una única tarea `asyncio`** lanzada en el `lifespan` de FastAPI, que en cada tick:

1. Calcula/obtiene los nuevos precios para todos los tickers vigilados.
2. Escribe cada uno en `PriceCache`.
3. Publica cada uno en `Broadcaster`.
4. Duerme hasta el siguiente intervalo (`~500ms` simulador, `~15s` Massive nivel gratuito).

```python
class BaseMarketDataProvider(ABC):
    def __init__(self, cache: PriceCache, broadcaster: Broadcaster) -> None:
        self._cache = cache
        self._broadcaster = broadcaster
        self._tickers: set[str] = set()
        self._task: asyncio.Task | None = None

    async def start(self, tickers: set[str]) -> None:
        self._tickers = set(tickers)
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            ticks = await self._fetch_ticks(self._tickers)
            for tick in ticks:
                await self._cache.set(tick)
                await self._broadcaster.publish(tick)
            await asyncio.sleep(self.interval_seconds)

    @abstractmethod
    async def _fetch_ticks(self, tickers: set[str]) -> list[PriceTick]: ...

    @property
    @abstractmethod
    def interval_seconds(self) -> float: ...

    async def add_ticker(self, ticker: str) -> None:
        self._tickers.add(ticker)
```

`SimulatedProvider._fetch_ticks` calcula el siguiente paso GBM (ver `planning/market_simulator.md`). `MassiveProvider._fetch_ticks` hace la llamada HTTP de snapshot por lotes (ver `planning/massive_api.md`).

## 7. Añadir un ticker en caliente

`add_ticker(ticker)` se invoca desde el endpoint `POST /api/watchlist` y desde las acciones de watchlist del LLM. El comportamiento difiere por implementación pero el contrato es idéntico:

- `SimulatedProvider`: genera un precio semilla plausible y empieza a simular ese ticker en el siguiente tick.
- `MassiveProvider`: simplemente añade el ticker al conjunto; ya se incluirá en la próxima llamada de snapshot por lotes (no requiere lógica especial de "seed").

Esto es exactamente el tipo de comportamiento que justifica tener una interfaz común: la lógica de la ruta de la API no necesita saber cuál de las dos implementaciones está activa.

## 8. Selección de implementación (factory)

```python
def build_market_data_provider(cache: PriceCache, broadcaster: Broadcaster) -> MarketDataProvider:
    if api_key := os.environ.get("MASSIVE_API_KEY"):
        return MassiveProvider(cache, broadcaster, api_key=api_key)
    return SimulatedProvider(cache, broadcaster)
```

Se llama una sola vez, en el `lifespan` de la app. El resto del código nunca importa `SimulatedProvider` ni `MassiveProvider` directamente — solo conoce `MarketDataProvider` (el `Protocol`) y `PriceCache`/`Broadcaster`.

## 9. Por qué esta forma y no otra

| Alternativa descartada | Motivo |
|---|---|
| Una clase `ABC` pura sin `Protocol` | Funciona igual de bien aquí; se documenta el híbrido porque es el estándar moderno, pero si se prefiere simplicidad, una sola `ABC` abstracta es una simplificación válida y razonable — no es una elección incorrecta dado que solo hay dos implementaciones. |
| WebSockets internos en lugar de SSE | Ya descartado en el PLAN; no aporta nada dado que el flujo es unidireccional servidor→cliente. |
| Cada conexión SSE haciendo su propio polling a Massive/simulador | Multiplicaría las llamadas a la API externa por cada pestaña de navegador abierta; rompe el límite de 5 llamadas/min del nivel gratuito. El caché + broadcaster centralizado garantiza **una sola fuente de verdad y una sola tarea de fondo**, sin importar cuántos clientes SSE estén conectados. |
| Pub/sub con Redis u otro broker externo | Innecesario para un solo proceso, un solo usuario, sin necesidad de escalar horizontalmente (ver PLAN.md sección 3: SQLite + contenedor único). `asyncio.Queue` en memoria es suficiente y no añade infraestructura. |

## Fuentes

- [Abstract Base Classes and Protocols: What Are They? When To Use Them?](https://jellis18.github.io/post/2022-01-11-abc-vs-protocol/)
- [Interfaces: abc vs. Protocols](https://sinavski.com/post/1_abc_vs_protocols/)
- [Modern Python Interfaces: ABC, Protocol, or Both?](https://tconsta.medium.com/python-interfaces-abc-protocol-or-both-3c5871ea6642)
- [Python Protocols: Leveraging Structural Subtyping – Real Python](https://realpython.com/python-protocol/)
