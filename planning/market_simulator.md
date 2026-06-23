# Diseño: Simulador de Datos de Mercado

## 1. Objetivo

Generar precios de acciones falsos pero visualmente convincentes, sin depender de ninguna API externa: movimiento continuo realista, tickers correlacionados entre sí (p. ej. tecnológicas moviéndose juntas) y "eventos" ocasionales de saltos bruscos del 2-5%. Es la implementación por defecto (`MASSIVE_API_KEY` vacía) según `planning/PLAN.md` sección 6, e implementa la interfaz `MarketDataProvider` de `planning/market_data_interface.md`.

## 2. Modelo matemático: Movimiento Browniano Geométrico (GBM)

Cada precio sigue:

```
dS = μ S dt + σ S dW
```

Discretizado para avanzar un paso de tiempo `dt`:

```
S(t+dt) = S(t) · exp[(μ − σ²/2) dt + σ √dt · Z]
```

donde `Z ~ N(0, 1)`. Es el modelo estándar para simular trayectorias de precios de acciones — sencillo, controlable por dos parámetros (deriva `μ`, volatilidad `σ`) y produce trayectorias que "se ven" como precios reales.

## 3. Correlación entre tickers (Cholesky)

Para que las tecnológicas se muevan juntas (y no de forma independiente), no generamos un `Z` independiente por ticker: generamos un vector de `Z` **correlacionados**.

1. Definir una matriz de correlación `Σ` (n×n, n = número de tickers) — alta correlación dentro del mismo "clúster" sectorial, baja entre clústeres.
2. Descomponer `Σ = L · Lᵗ` (descomposición de Cholesky; `Σ` debe ser simétrica y positiva-definida).
3. En cada tick: generar `Z_indep ~ N(0, I)` (vector de n normales independientes), y calcular `Z_correlado = L @ Z_indep`.
4. Usar `Z_correlado[i]` en la fórmula GBM del ticker `i`.

```python
import numpy as np

class CorrelatedShockGenerator:
    def __init__(self, correlation_matrix: np.ndarray) -> None:
        self._L = np.linalg.cholesky(correlation_matrix)

    def next_shocks(self, rng: np.random.Generator) -> np.ndarray:
        z = rng.standard_normal(self._L.shape[0])
        return self._L @ z
```

Si la matriz no es positiva-definida (puede pasar al añadir tickers dinámicamente con correlaciones inventadas a mano), se regulariza con un pequeño "jitter" en la diagonal (`Σ + ε·I`) antes de descomponer.

### Clústeres sugeridos para los 10 tickers semilla

| Clúster | Tickers | Correlación intra-clúster |
|---|---|---|
| Tech / growth | AAPL, GOOGL, MSFT, NVDA, META | ~0.6 |
| Consumo / EV | AMZN, TSLA | ~0.4 |
| Financiero | JPM, V | ~0.5 |
| Streaming | NFLX | correlación moderada (~0.3) con tech, baja con financiero |

Correlación entre clústeres distintos: ~0.15 (el mercado en general tiende a moverse algo junto, pero menos que dentro del mismo sector). Estos números son de partida razonable para el efecto visual buscado, no estimaciones estadísticas reales.

## 4. Parámetros por ticker (semilla)

| Ticker | Precio semilla | Volatilidad anualizada (σ) aprox. |
|---|---|---|
| AAPL | $190 | 25% |
| GOOGL | $175 | 28% |
| MSFT | $420 | 22% |
| AMZN | $185 | 30% |
| TSLA | $250 | 55% |
| NVDA | $135 | 50% |
| META | $580 | 32% |
| JPM | $215 | 20% |
| V | $310 | 18% |
| NFLX | $700 | 35% |

Deriva (`μ`) por defecto: ligeramente positiva (~5-8% anualizada) para todos, para que la cartera tienda a subir a largo plazo sin que cada ticker se comporte igual.

## 5. Escala de tiempo del tick

El sistema actualiza cada ~500ms (`planning/PLAN.md`), pero **no** se debe usar `dt = 0.5 segundos / segundos por año`, porque eso produce movimientos microscópicos e imperceptibles. En su lugar, se trata cada tick como una fracción visualmente significativa de un "día de trading simulado":

```
dt_efectivo = 1 / N_ticks_por_dia_simulado
```

Con `N_ticks_por_dia_simulado ≈ 360` (un "día" se simula en 3 minutos reales a 500ms/tick), cada tick produce movimientos del orden de `σ · √(1/360)` — para AAPL (σ=25%) eso es ~1.3% de desviación estándar por tick, suficiente para que se vea vivo sin ser absurdo. Este número es un parámetro de ajuste visual, documentado como tal y configurable.

## 6. Eventos de salto (jump diffusion ligero)

Para el "dramatismo" ocasional que pide el PLAN (movimientos súbitos del 2-5%), se superpone un proceso de saltos simple tipo Poisson, independiente de la correlación:

```python
JUMP_PROBABILITY_PER_TICK = 0.003  # ~0.3% de probabilidad por ticker por tick

def maybe_apply_jump(rng: np.random.Generator) -> float:
    if rng.random() < JUMP_PROBABILITY_PER_TICK:
        magnitude = rng.uniform(0.02, 0.05)
        direction = rng.choice([-1, 1])
        return 1 + direction * magnitude
    return 1.0
```

El salto se aplica como multiplicador extra sobre el precio GBM del tick, solo al ticker afectado (no correlacionado con los demás — es un evento idiosincrático, como una noticia de earnings).

## 7. Paso completo del simulador (vectorizado)

```python
class SimulatedProvider(BaseMarketDataProvider):
    interval_seconds = 0.5

    def __init__(self, cache: PriceCache, broadcaster: Broadcaster, rng_seed: int | None = None) -> None:
        super().__init__(cache, broadcaster)
        self._rng = np.random.default_rng(rng_seed)
        self._prices: dict[str, float] = dict(SEED_PRICES)
        self._params: dict[str, TickerParams] = dict(DEFAULT_PARAMS)
        self._shocks = CorrelatedShockGenerator(DEFAULT_CORRELATION_MATRIX)

    async def _fetch_ticks(self, tickers: set[str]) -> list[PriceTick]:
        ordered = sorted(tickers)
        z = self._shocks.next_shocks(self._rng)  # alineado con el orden de tickers conocidos
        ticks = []
        for i, ticker in enumerate(ordered):
            params = self._params[ticker]
            prev = self._prices[ticker]
            drift = (params.mu - 0.5 * params.sigma**2) * DT
            diffusion = params.sigma * sqrt(DT) * z[i]
            jump = maybe_apply_jump(self._rng)
            new_price = prev * exp(drift + diffusion) * jump
            self._prices[ticker] = new_price
            ticks.append(PriceTick(
                ticker=ticker, price=new_price, previous_price=prev,
                timestamp=time.time(),
                direction="up" if new_price > prev else "down" if new_price < prev else "flat",
            ))
        return ticks
```

Es `O(n)` por tick (n = nº de tickers vigilados, típicamente 10-30), trivial en coste para `numpy`.

## 8. Añadir un ticker nuevo en caliente

Cuando se añade un ticker no pre-configurado (vía watchlist manual o acción del LLM):

1. Generar un precio semilla plausible: `rng.uniform(10, 500)` con un sesgo log-uniforme (para que sea igualmente probable un precio de $20 que de $200) en lugar de uniforme lineal.
2. Asignar parámetros por defecto de un clúster "general" (σ ≈ 30%, μ ≈ 6% anual, correlación baja con el resto).
3. Ampliar la matriz de correlación y recalcular su descomposición de Cholesky (operación barata para matrices de este tamaño).
4. Incluirlo en el siguiente tick con normalidad.

```python
async def add_ticker(self, ticker: str) -> None:
    if ticker not in self._prices:
        self._prices[ticker] = lognormal_seed_price(self._rng)
        self._params[ticker] = GENERIC_CLUSTER_PARAMS
        self._shocks = self._shocks.expanded_with(ticker, correlation=0.1)
    await super().add_ticker(ticker)
```

## 9. Determinismo para tests

`SimulatedProvider` acepta `rng_seed` opcional. Los tests unitarios y E2E (`LLM_MOCK=true`) instancian el simulador con una semilla fija para obtener trayectorias reproducibles y aserciones estables (p. ej. "el precio tras N ticks está dentro de tal rango"), sin necesidad de mockear la lógica matemática.

## 10. Por qué este diseño y no otro

| Alternativa descartada | Motivo |
|---|---|
| Random walk simple (sin GBM) | Permite precios negativos y no refleja cómo se comportan acciones reales (retornos porcentuales, no absolutos). GBM evita precios negativos por construcción (`exp(...)` siempre positivo). |
| Volatilidad/deriva idénticas para todos los tickers | Aburrido visualmente — TSLA y NVDA deben "moverse" notablemente más que JPM o V, como en la realidad. |
| Sin correlación entre tickers | El PLAN pide explícitamente "movimientos correlacionados entre tickers (p. ej. las acciones tecnológicas se mueven juntas)" — es un requisito, no un extra. |
| Saltos correlacionados con el GBM | Los eventos de salto deben ser idiosincráticos (una sola acción reacciona a "noticias"), no sistémicos; mezclarlos con el shock correlacionado eliminaría el efecto dramático aislado que se busca. |
| Recalibrar `dt` para ser "anualizado correctamente" | El objetivo es el efecto visual de una terminal de trading viva, no precisión cuantitativa real; un `dt` ajustado a mano para que el movimiento por tick "se vea bien" es la elección correcta y más simple. |

## Fuentes

- [Geometric Brownian Motion Simulation with Python — QuantStart](https://www.quantstart.com/articles/geometric-brownian-motion-simulation-with-python/)
- [Simulate Multi-Asset Baskets With Correlated Price Paths Using Python](https://medium.com/codex/simulate-multi-asset-baskets-with-correlated-price-paths-using-python-472cbec4e379)
- [Simulation of correlated random walks for a basket of stocks using Python](https://abhyankar-ameya.medium.com/simulation-of-correlated-random-walks-for-a-basket-of-stocks-using-python-2f1a909ba089)
- [Generating Synthetic Equity Data with Realistic Correlation Structure — QuantStart](https://www.quantstart.com/articles/generating-synthetic-equity-data-with-realistic-correlation-structure/)
