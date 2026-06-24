"use client";

import type { Position } from "@/lib/types";
import type { PriceMap } from "@/lib/usePriceStream";
import { PriceFlash } from "./PriceFlash";
import { fmtNum, fmtSignedUsd, fmtPct, pnlClass } from "@/lib/format";

interface Props {
  positions: Position[];
  prices: PriceMap;
  onSelect: (ticker: string) => void;
}

/**
 * Tabla de posiciones. El precio actual y el P&L no realizado se recalculan en
 * vivo con el último precio del stream cuando está disponible, cayendo al valor
 * del backend si aún no hay tick.
 */
export function PositionsTable({ positions, prices, onSelect }: Props) {
  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>Positions</span>
        <span className="tnum">{positions.length}</span>
      </div>
      <div className="scroll-y min-h-0 flex-1">
        <table className="w-full border-collapse text-[12px]">
          <thead className="sticky top-0 bg-panel">
            <tr className="text-[10px] uppercase tracking-wider text-muted">
              <th className="py-1.5 pl-3 text-left font-medium">Ticker</th>
              <th className="px-2 text-right font-medium">Qty</th>
              <th className="px-2 text-right font-medium">Avg</th>
              <th className="px-2 text-right font-medium">Last</th>
              <th className="px-2 text-right font-medium">P&L</th>
              <th className="px-3 text-right font-medium">%</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => {
              const live = prices[p.ticker];
              const last = live?.price ?? p.current_price;
              const pnl = (last - p.avg_cost) * p.quantity;
              const pct = p.avg_cost ? ((last - p.avg_cost) / p.avg_cost) * 100 : 0;
              return (
                <tr
                  key={p.ticker}
                  onClick={() => onSelect(p.ticker)}
                  className="cursor-pointer border-b border-border/60 hover:bg-white/[0.03]"
                >
                  <td className="py-1.5 pl-3 font-mono font-semibold text-[#e6e6f0]">
                    {p.ticker}
                  </td>
                  <td className="tnum px-2 text-right font-mono">{fmtNum(p.quantity, 2)}</td>
                  <td className="tnum px-2 text-right font-mono text-muted">
                    {fmtNum(p.avg_cost)}
                  </td>
                  <td className="px-2 text-right font-mono">
                    <PriceFlash
                      value={last}
                      direction={live?.direction ?? "flat"}
                      seq={live?.seq ?? 0}
                      format={(n) => fmtNum(n)}
                    />
                  </td>
                  <td className={`tnum px-2 text-right font-mono ${pnlClass(pnl)}`}>
                    {fmtSignedUsd(pnl)}
                  </td>
                  <td className={`tnum px-3 text-right font-mono ${pnlClass(pct)}`}>
                    {fmtPct(pct)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {positions.length === 0 && (
          <p className="p-4 text-center text-xs text-muted">
            No positions yet. Place a trade below.
          </p>
        )}
      </div>
    </section>
  );
}
