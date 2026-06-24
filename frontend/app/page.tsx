"use client";

import { useCallback, useEffect, useState } from "react";
import { usePriceStream } from "@/lib/usePriceStream";
import * as api from "@/lib/api";
import type { Portfolio, Snapshot, TradeSide } from "@/lib/types";
import { Header } from "@/components/Header";
import { Watchlist } from "@/components/Watchlist";
import { MainChart } from "@/components/MainChart";
import { Treemap } from "@/components/Treemap";
import { PnLChart } from "@/components/PnLChart";
import { PositionsTable } from "@/components/PositionsTable";
import { TradeBar } from "@/components/TradeBar";
import { ChatPanel } from "@/components/ChatPanel";

const EMPTY_PORTFOLIO: Portfolio = {
  cash_balance: 0,
  positions: [],
  total_value: 0,
  total_unrealized_pnl: 0,
};

export default function Page() {
  const { prices, status } = usePriceStream();
  const [tickers, setTickers] = useState<string[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio>(EMPTY_PORTFOLIO);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const loadWatchlist = useCallback(async () => {
    try {
      const { tickers } = await api.getWatchlist();
      const list = tickers.map((t) => t.ticker);
      setTickers(list);
      setSelected((s) => s ?? list[0] ?? null);
    } catch {
      /* backend no disponible: la UI degrada con el indicador de conexión */
    }
  }, []);

  const loadPortfolio = useCallback(async () => {
    try {
      const [p, h] = await Promise.all([api.getPortfolio(), api.getHistory()]);
      setPortfolio(p);
      setSnapshots(h.snapshots);
    } catch {
      /* idem */
    }
  }, []);

  useEffect(() => {
    loadWatchlist();
    loadPortfolio();
    const id = setInterval(loadPortfolio, 10_000);
    return () => clearInterval(id);
  }, [loadWatchlist, loadPortfolio]);

  const addTicker = async (t: string) => {
    await api.addWatchlist(t).catch(() => {});
    setSelected(t);
    loadWatchlist();
  };

  const removeTicker = async (t: string) => {
    await api.removeWatchlist(t).catch(() => {});
    loadWatchlist();
  };

  const doTrade = async (ticker: string, quantity: number, side: TradeSide) => {
    await api.trade(ticker, quantity, side);
    await Promise.all([loadPortfolio(), loadWatchlist()]);
  };

  const afterChat = () => {
    loadPortfolio();
    loadWatchlist();
  };

  return (
    <div className="flex h-screen flex-col">
      <Header
        totalValue={portfolio.total_value}
        cash={portfolio.cash_balance}
        pnl={portfolio.total_unrealized_pnl}
        status={status}
      />

      <main className="grid min-h-0 flex-1 gap-2 p-2 lg:grid-cols-[300px_1fr_340px]">
        {/* Columna izquierda: watchlist */}
        <div className="hidden min-h-0 lg:block">
          <Watchlist
            tickers={tickers}
            prices={prices}
            selected={selected}
            onSelect={setSelected}
            onAdd={addTicker}
            onRemove={removeTicker}
          />
        </div>

        {/* Columna central: gráfico + allocation/pnl + posiciones + trade */}
        <div className="grid min-h-0 grid-rows-[1.4fr_1fr_1.2fr_auto] gap-2">
          <MainChart ticker={selected} live={selected ? prices[selected] : undefined} />
          <div className="grid min-h-0 grid-cols-2 gap-2">
            <Treemap positions={portfolio.positions} onSelect={setSelected} />
            <PnLChart snapshots={snapshots} />
          </div>
          <PositionsTable positions={portfolio.positions} prices={prices} onSelect={setSelected} />
          <TradeBar initialTicker={selected} onTrade={doTrade} />
        </div>

        {/* Columna derecha: chat IA */}
        <div className="hidden min-h-0 lg:block">
          <ChatPanel onActions={afterChat} />
        </div>
      </main>
    </div>
  );
}
