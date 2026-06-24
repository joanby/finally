# Contrato de Integración del Equipo — FinAlly

Este documento es el **contrato compartido** entre los agentes que construyen FinAlly.
El componente de **datos de mercado ya está terminado** (`backend/app/market_data/`).
Todo lo demás se construye contra los contratos definidos aquí. Si necesitas cambiar
un contrato, actualiza este archivo primero.

> Fuente de verdad de producto: `planning/PLAN.md`. Este documento solo fija las
> **fronteras técnicas entre equipos** para que el trabajo en paralelo no colisione.

---

## Reglas de oro para evitar colisiones

- Cada equipo **es dueño exclusivo** de su conjunto de archivos (ver tabla). No edites
  archivos de otro equipo; si necesitas algo de ellos, consúmelo vía el contrato.
- Las dependencias de Python **ya están instaladas** (`fastapi`, `uvicorn[standard]`,
  `litellm`, `pydantic`, `python-dotenv`, `httpx`, `pytest`, `pytest-asyncio`).
  **No ejecutes `uv add`** salvo que falte algo imprescindible; si lo haces, hazlo de
  uno en uno y avisa.
- Ejecuta siempre con `uv run` (nunca `python3`). Tests backend: `uv run pytest`.
- Estética y colores: ver `planning/PLAN.md` §2.

## Propiedad de archivos

| Equipo | Posee | No toca |
|---|---|---|
| Base de Datos | `backend/app/db/`, `backend/tests/db/` | `app/api`, `app/llm`, `app/main.py` |
| LLM | `backend/app/llm/`, `backend/tests/llm/` | `app/db`, `app/api`, `app/main.py` |
| Backend/API | `backend/app/api/`, `backend/app/services/`, `backend/app/main.py`, `backend/tests/api/` | internos de `app/db`, `app/llm`, `app/market_data` |
| Frontend | `frontend/` | todo lo de `backend/` |
| DevOps | `Dockerfile`, `.dockerignore`, `scripts/`, `test/docker-compose.test.yml` | código de app |
| Integración | `test/` (excepto compose) | código de app (solo reporta bugs) |

`app/market_data/` ya existe y es de solo lectura para todos.

---

## Contrato: módulo de Base de Datos — `backend/app/db/`

SQLite en `db/finally.db` (raíz del repo, no dentro de `backend/`). Resolver la ruta
relativa a la raíz del proyecto; permitir override con env `FINALLY_DB_PATH` (útil para tests).
Inicialización **diferida**: `init_db()` crea tablas y siembra datos si faltan. Esquema y
datos semilla exactos en `PLAN.md` §7.

Expón funciones **síncronas** (FastAPI las llamará en threadpool). Devuelve `dict`s planos.

```python
# backend/app/db/__init__.py  — API pública estable
init_db() -> None                       # idempotente; crea esquema + seed si vacío

# profile
get_profile() -> dict                   # {id, cash_balance, created_at}
set_cash_balance(amount: float) -> None

# watchlist
list_watchlist() -> list[str]           # tickers, orden de inserción
add_to_watchlist(ticker: str) -> bool   # False si ya existía
remove_from_watchlist(ticker: str) -> bool

# positions
list_positions() -> list[dict]          # [{ticker, quantity, avg_cost, updated_at}]
get_position(ticker: str) -> dict | None
upsert_position(ticker: str, quantity: float, avg_cost: float) -> None
delete_position(ticker: str) -> None

# trades
record_trade(ticker: str, side: str, quantity: float, price: float) -> dict  # fila insertada
list_trades() -> list[dict]

# portfolio snapshots
record_snapshot(total_value: float) -> None
list_snapshots() -> list[dict]          # [{total_value, recorded_at}] asc por tiempo

# chat
add_chat_message(role: str, content: str, actions: dict | list | None = None) -> dict
recent_chat_messages(limit: int = 20) -> list[dict]  # asc por created_at; actions ya parseado
```

Notas:
- `user_id="default"` fijo en todas las tablas; la API pública no lo expone.
- Timestamps ISO 8601 UTC.
- `actions` se serializa a JSON TEXT al guardar y se deserializa al leer.
- La **lógica de negocio de trading NO vive aquí** (la hace Backend/services). DB solo persiste.

---

## Contrato: módulo LLM — `backend/app/llm/`

Módulo **puro**: recibe contexto, devuelve un plan estructurado. **No toca la BD ni
ejecuta operaciones** (eso lo hace Backend). Usa la skill `cerebras` (LiteLLM →
OpenRouter, modelo `openrouter/openai/gpt-oss-120b`, provider Cerebras, salida
estructurada con Pydantic). Lee `OPENROUTER_API_KEY` del entorno.

```python
# backend/app/llm/__init__.py — API pública estable
from pydantic import BaseModel

class TradeAction(BaseModel):
    ticker: str
    side: str          # "buy" | "sell"
    quantity: float

class WatchlistChange(BaseModel):
    ticker: str
    action: str        # "add" | "remove"

class ChatResult(BaseModel):
    message: str
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistChange] = []

def generate_chat_response(
    user_message: str,
    portfolio_context: dict,     # forma definida abajo
    history: list[dict],         # [{role, content}], orden cronológico, <=20
) -> ChatResult: ...
```

`portfolio_context` (lo construye Backend y lo pasa tal cual):
```json
{
  "cash_balance": 8000.0,
  "total_value": 10250.0,
  "positions": [
    {"ticker":"AAPL","quantity":10,"avg_cost":190.0,"current_price":195.0,
     "unrealized_pnl":50.0,"pct_change":2.63}
  ],
  "watchlist": [{"ticker":"NVDA","price":1200.0}]
}
```

- **Modo mock**: si `LLM_MOCK=true`, devolver respuestas deterministas SIN llamar a la
  red. Reglas mock mínimas (para que los E2E sean predecibles): si el mensaje contiene
  `buy <n> <TICKER>` → `trades=[{TICKER,buy,n}]`; si contiene `sell <n> <TICKER>` →
  venta; si contiene `add <TICKER>` / `remove <TICKER>` → watchlist_changes; en
  cualquier caso `message` no vacío y eco del entendimiento. Documenta las reglas mock
  en un docstring para que Integración escriba asserts estables.
- El prompt de sistema sigue `PLAN.md` §9 ("FinAlly, asistente de trading con IA").
- `generate_chat_response` puede ser `def` síncrona; Backend la invoca en threadpool.
  (Si la implementas `async`, indícalo en el docstring.)

---

## Contrato: Backend/API — `backend/app/main.py`, `app/api/`, `app/services/`

Es el **integrador**. Monta FastAPI, registra routers, gestiona el ciclo de vida del
proveedor de datos de mercado y las tareas en segundo plano, y compone DB + LLM.

Arranque (`lifespan`):
1. `db.init_db()`
2. `provider = build_market_data_provider(on_tick)` (de `app.market_data.factory`;
   `on_tick` de `app.market_data.wiring`, que ya escribe en `price_cache`).
3. Añadir al proveedor la **unión** de watchlist + tickers con posición abierta.
4. `await provider.start()`
5. Tarea snapshots: cada 30 s `record_snapshot(total_value_actual)`.
6. Al apagar: `await provider.stop()`.

Cuando cambian watchlist o posiciones, actualizar el proveedor con
`provider.add_ticker()` / `remove_ticker()` (mantener la unión; no quitar un ticker que
aún tiene posición abierta).

Endpoints (formas y rutas exactas en `PLAN.md` §8):
- `GET /api/health` → `{"status":"ok"}`
- `GET /api/stream/prices` → SSE. Cada evento: `data: ` + JSON de `PriceTick.to_sse_dict()`
  (`{ticker, price, prev_price, timestamp, direction}`). Usar `StreamingResponse` con
  `media_type="text/event-stream"`, leer de `price_cache.subscribe()`, y al primer
  contacto emitir un snapshot inicial (`price_cache.snapshot()`) para poblar la UI.
  Cabeceras: `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
- `GET /api/portfolio` → `{cash_balance, positions:[{ticker,quantity,avg_cost,current_price,
  unrealized_pnl,pct_change}], total_value, total_unrealized_pnl}`. Precios de `price_cache`.
- `POST /api/portfolio/trade` body `{ticker, quantity, side}` → ejecuta orden de mercado al
  precio actual de `price_cache`. Valida efectivo (compra) / cantidad (venta). Actualiza
  posición (coste medio ponderado en compra; al vender todo, borra posición), efectivo,
  registra trade y un snapshot inmediato. Error claro (4xx) si validación falla.
- `GET /api/portfolio/history` → `{snapshots:[{total_value,recorded_at}]}`
- `GET /api/watchlist` → `{tickers:[{ticker, price}]}` (precio de `price_cache`, puede ser null si aún sin tick)
- `POST /api/watchlist` body `{ticker}` → añade (normaliza a mayúsculas); informa al proveedor.
- `DELETE /api/watchlist/{ticker}` → elimina.
- `POST /api/chat` body `{message}` → construye `portfolio_context` + `history`
  (`recent_chat_messages`), llama `llm.generate_chat_response`, **ejecuta** trades y
  watchlist_changes resultantes (misma validación que manual; errores se acumulan),
  persiste mensajes user+assistant (con `actions`), devuelve
  `{message, actions:{trades:[...], watchlist_changes:[...], errors:[...]}}`.

Lógica de trading/P&L vive en `app/services/portfolio.py` (testeable sin FastAPI).
Servir estáticos: si existe `app/static/` (o `static/`), montar el frontend exportado y
servir `index.html` como fallback SPA. En dev puede no existir; no fallar por ello.

**Comando de arranque (lo usa DevOps):**
`uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` (cwd `backend/`).

---

## Contrato: Frontend — `frontend/`

Next.js + TypeScript, **export estático** (`output: 'export'` en `next.config`), Tailwind
con tema oscuro (colores en `PLAN.md` §2). Componentes mínimos en `PLAN.md` §10. Build →
`frontend/out/` (Next 14+ exporta ahí con `next build`). Consume `/api/*` y SSE
`/api/stream/prices` vía `EventSource` (mismo origen). Sparklines acumulados en cliente
desde el SSE. Destello verde/rojo por cambio de precio. Indicador de conexión.

Para desarrollo, puede usar `NEXT_PUBLIC_API_BASE` (vacío en prod = mismo origen) para
apuntar al backend en `http://localhost:8000` mientras se prueba aislado.

Comando de build (lo usa DevOps): `npm ci && npm run build` (cwd `frontend/`), salida en
`frontend/out`.

---

## Contrato: DevOps — `Dockerfile`, `scripts/`, `test/docker-compose.test.yml`

Dockerfile multi-etapa (`PLAN.md` §11):
- Etapa 1 (node:20-slim): build de `frontend/` → `out/`.
- Etapa 2 (python:3.12-slim): instala `uv`, copia `backend/`, `uv sync`, copia el `out/`
  del frontend a `backend/app/static/` (donde el backend lo sirve), expone 8000,
  `CMD` uvicorn (ver comando arriba). DB en volumen `-v $(pwd)/db:/app/db`.
- Scripts idempotentes: `scripts/{start,stop}_mac.sh`, `scripts/{start,stop}_windows.ps1`.
- `test/docker-compose.test.yml`: app (con `LLM_MOCK=true`) + servicio Playwright.

> El backend monta los estáticos desde `app/static/`. Coordina esa ruta con Backend/API.

---

## Contrato: Integración (E2E) — `test/`

Playwright contra el contenedor en marcha con `LLM_MOCK=true`. Escenarios en `PLAN.md` §12.
Cuando algo falle, **reporta** en `planning/integration_report.md` (crea el archivo):
qué endpoint/UI, pasos de repro, esperado vs obtenido, y a qué equipo corresponde.
No arregles código de otros equipos; solo tests E2E e informe.
