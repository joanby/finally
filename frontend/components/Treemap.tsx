"use client";

import type { Position } from "@/lib/types";
import { buildTreemap, pnlColor } from "@/lib/portfolio";
import { fmtPct } from "@/lib/format";

interface Props {
  positions: Position[];
  onSelect: (ticker: string) => void;
}

/**
 * Treemap de cartera por filas: cada celda dimensionada por peso (flex-grow) y
 * coloreada por P&L. Suficiente para densidad de terminal sin un layout de
 * squarified treemap completo.
 */
export function Treemap({ positions, onSelect }: Props) {
  const cells = buildTreemap(positions);
  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>Allocation</span>
      </div>
      <div className="min-h-0 flex-1 p-1.5">
        {cells.length === 0 ? (
          <div className="flex h-full items-center justify-center text-xs text-muted">
            No open positions.
          </div>
        ) : (
          <div className="flex h-full flex-wrap gap-1.5 content-stretch">
            {cells.map((c) => (
              <button
                key={c.ticker}
                onClick={() => onSelect(c.ticker)}
                title={`${c.ticker} · ${(c.weight * 100).toFixed(1)}% · ${fmtPct(c.pctChange)}`}
                className="flex min-w-[64px] flex-col justify-between rounded border border-border/50 p-2 text-left transition hover:border-primary"
                style={{ flexGrow: c.weight, flexBasis: 0, backgroundColor: pnlColor(c.pctChange) }}
              >
                <span className="font-mono text-[13px] font-semibold text-[#e6e6f0]">
                  {c.ticker}
                </span>
                <span className="tnum font-mono text-[11px] text-[#e6e6f0]/80">
                  {fmtPct(c.pctChange)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
