import random

from .simulator_config import MARKET_CORRELATION, SECTOR_CORRELATION


def correlated_shocks(rng: random.Random, sectors_by_ticker: dict[str, str]) -> dict[str, float]:
    """Devuelve un shock Z ~ N(0,1) correlacionado para cada ticker.

    Combina un factor de mercado global, un factor por sector y un factor
    idiosincrático por ticker (ver planning/market_data_design.md §5.3), de
    forma que tickers del mismo sector tiendan a moverse juntos.
    """
    z_market = rng.gauss(0, 1)
    sectors = set(sectors_by_ticker.values())
    z_sector = {s: rng.gauss(0, 1) for s in sectors}

    w_market = MARKET_CORRELATION
    w_sector = SECTOR_CORRELATION * (1 - MARKET_CORRELATION)
    w_idio = 1 - w_market - w_sector
    # normalizamos pesos al espacio de varianzas para mantener Var(Z) = 1
    norm = (w_market**2 + w_sector**2 + w_idio**2) ** 0.5

    shocks: dict[str, float] = {}
    for ticker, sector in sectors_by_ticker.items():
        z_idio = rng.gauss(0, 1)
        z = (w_market * z_market + w_sector * z_sector[sector] + w_idio * z_idio) / norm
        shocks[ticker] = z
    return shocks
