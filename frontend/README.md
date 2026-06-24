# FinAlly — Frontend

Terminal de trading (Next.js 14 + TypeScript, export estático) servida por el backend FastAPI en el mismo origen.

## Scripts

```bash
npm ci          # instala dependencias
npm run dev     # desarrollo en http://localhost:3000
npm run build   # export estático en out/
npm test        # tests unitarios (Vitest + Testing Library)
```

`npm run build` produce `out/` (HTML/JS/CSS estático); el backend lo sirve desde `app/static/`.

## Configuración

- Las llamadas API usan rutas relativas `/api/*` (mismo origen).
- Para desarrollo aislado contra un backend en otro puerto:
  `NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev`.

## Estructura

- `app/` — layout, página única y estilos globales (Tailwind, tema oscuro).
- `components/` — Header, Watchlist, MainChart, Treemap, PnLChart, PositionsTable, TradeBar, ChatPanel, y primitivas (PriceFlash, Sparkline).
- `lib/` — cliente API, tipos del contrato, hook SSE (`usePriceStream`), helpers de formato y cálculo de cartera.
- `tests/` — pruebas de componentes y helpers.

## Datos en vivo

`usePriceStream` abre un `EventSource` a `/api/stream/prices`, acumula precios y
sparklines en cliente, y expone el estado de conexión para el indicador del header.
La UI degrada con elegancia (indicador en rojo) si el backend no responde.
