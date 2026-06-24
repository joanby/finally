"use client";

import { useState } from "react";
import type { PriceMap } from "@/lib/usePriceStream";
import { PriceFlash } from "./PriceFlash";
import { Sparkline } from "./Sparkline";
import { fmtNum, fmtPct } from "@/lib/format";

interface Props {
  tickers: string[];
  prices: PriceMap;
  selected: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

export function Watchlist({ tickers, prices, selected, onSelect, onAdd, onRemove }: Props) {
  const [draft, setDraft] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = draft.trim().toUpperCase();
    if (t) onAdd(t);
    setDraft("");
  };

  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>Watchlist</span>
        <form onSubmit={submit} className="flex items-center gap-1">
          <input
            aria-label="Add ticker"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="ADD"
            maxLength={6}
            className="w-16 rounded border border-border bg-panel-2 px-1.5 py-0.5 font-mono text-[11px] uppercase text-[#e6e6f0] outline-none focus:border-primary"
          />
        </form>
      </div>

      <div className="scroll-y min-h-0 flex-1">
        <table className="w-full border-collapse text-sm">
          <tbody>
            {tickers.map((t) => {
              const p = prices[t];
              const pct =
                p && p.prev_price ? ((p.price - p.prev_price) / p.prev_price) * 100 : 0;
              const isSel = t === selected;
              const color = p?.direction === "down" ? "#ea3943" : "#16c784";
              return (
                <tr
                  key={t}
                  onClick={() => onSelect(t)}
                  className={`group cursor-pointer border-b border-border/60 ${
                    isSel ? "bg-primary/10" : "hover:bg-white/[0.03]"
                  }`}
                >
                  <td className="py-1.5 pl-3 pr-2">
                    <span
                      className={`font-mono text-[13px] font-semibold ${
                        isSel ? "text-primary" : "text-[#e6e6f0]"
                      }`}
                    >
                      {t}
                    </span>
                  </td>
                  <td className="px-1 py-1.5">
                    <Sparkline data={p?.spark ?? []} color={color} />
                  </td>
                  <td className="px-2 py-1.5 text-right font-mono text-[13px]">
                    <PriceFlash
                      value={p?.price ?? null}
                      direction={p?.direction ?? "flat"}
                      seq={p?.seq ?? 0}
                      format={(n) => fmtNum(n)}
                    />
                  </td>
                  <td
                    className={`tnum px-2 py-1.5 text-right font-mono text-[12px] ${
                      pct < 0 ? "text-down" : "text-up"
                    }`}
                  >
                    {p ? fmtPct(pct) : "—"}
                  </td>
                  <td className="pr-2 text-right">
                    <button
                      aria-label={`Remove ${t}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(t);
                      }}
                      className="px-1 text-muted opacity-0 transition group-hover:opacity-100 hover:text-down"
                    >
                      ×
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {tickers.length === 0 && (
          <p className="p-4 text-center text-xs text-muted">
            Watchlist is empty. Add a ticker to start streaming.
          </p>
        )}
      </div>
    </section>
  );
}
