# Tests E2E — FinAlly

Suite Playwright que cubre los escenarios de `planning/PLAN.md` §12 contra el
contenedor en marcha con `LLM_MOCK=true`.

## Ejecutar contra un contenedor local

```bash
# 1. Levantar la app (puerto host alternativo; el 8000 puede estar ocupado)
docker run -d --name finally_e2e -e LLM_MOCK=true \
  -v "$(mktemp -d)":/app/db -p 8012:8000 finally:latest
# esperar al health
curl -fsS http://localhost:8012/api/health

# 2. Instalar y ejecutar
cd test
npm install
BASE_URL=http://localhost:8012 npx playwright test

# 3. Limpiar
docker rm -f finally_e2e
```

## Ejecutar con docker-compose (red interna)

`docker compose -f docker-compose.test.yml up --build` levanta la app y el runner
de Playwright (`BASE_URL=http://app:8000`).

## Escenarios

| Spec | Cubre |
|---|---|
| `01-startup` | Watchlist por defecto (10 tickers), saldo $10k, LIVE, precios en vivo (SSE) |
| `02-watchlist` | Añadir y eliminar tickers vía UI |
| `03-trade` | Comprar (efectivo baja, posición aparece) y vender (revierte) |
| `04-portfolio-viz` | Treemap con posiciones y gráfico de P&L con puntos |
| `05-chat` | Chat mock `buy 1 AAPL` → respuesta + ejecución inline del trade |
