"use client";

import { useEffect, useState } from "react";
import type { TradeSide } from "@/lib/types";

interface Props {
  initialTicker: string | null;
  onTrade: (ticker: string, quantity: number, side: TradeSide) => Promise<void>;
}

export function TradeBar({ initialTicker, onTrade }: Props) {
  const [ticker, setTicker] = useState("");
  const [qty, setQty] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialTicker) setTicker(initialTicker);
  }, [initialTicker]);

  const exec = async (side: TradeSide) => {
    const t = ticker.trim().toUpperCase();
    const q = Number(qty);
    if (!t || !(q > 0)) {
      setError("Enter a ticker and a positive quantity.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onTrade(t, q, side);
      setQty("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trade failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <div className="flex items-center gap-2 p-2.5">
        <input
          aria-label="Trade ticker"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="TICKER"
          maxLength={6}
          className="w-24 rounded border border-border bg-panel-2 px-2 py-1.5 font-mono text-sm uppercase outline-none focus:border-primary"
        />
        <input
          aria-label="Trade quantity"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          placeholder="QTY"
          inputMode="decimal"
          className="w-24 rounded border border-border bg-panel-2 px-2 py-1.5 font-mono text-sm outline-none focus:border-primary"
        />
        <button
          onClick={() => exec("buy")}
          disabled={busy}
          className="rounded bg-up/90 px-4 py-1.5 text-sm font-semibold text-bg transition hover:bg-up disabled:opacity-50"
        >
          Buy
        </button>
        <button
          onClick={() => exec("sell")}
          disabled={busy}
          className="rounded bg-down/90 px-4 py-1.5 text-sm font-semibold text-bg transition hover:bg-down disabled:opacity-50"
        >
          Sell
        </button>
        <span className="ml-1 text-[11px] uppercase tracking-wider text-muted">
          Market order · instant fill
        </span>
        {error && <span className="ml-auto text-xs text-down">{error}</span>}
      </div>
    </section>
  );
}
