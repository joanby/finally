"use client";

import type { ConnectionStatus } from "@/lib/types";
import { fmtUsd, fmtSignedUsd, pnlClass } from "@/lib/format";

const STATUS: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: "#16c784", label: "LIVE" },
  reconnecting: { color: "#ecad0a", label: "RECONNECTING" },
  disconnected: { color: "#ea3943", label: "OFFLINE" },
};

interface Props {
  totalValue: number;
  cash: number;
  pnl: number;
  status: ConnectionStatus;
}

export function Header({ totalValue, cash, pnl, status }: Props) {
  const s = STATUS[status];
  return (
    <header className="flex items-center justify-between border-b border-border bg-panel-2 px-4 py-2.5">
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-lg font-semibold tracking-tight text-accent">
          Fin<span className="text-primary">Ally</span>
        </span>
        <span className="hidden text-[11px] uppercase tracking-[0.2em] text-muted sm:inline">
          AI Trading Workstation
        </span>
      </div>

      <div className="flex items-center gap-6">
        <Metric label="Cash" value={fmtUsd(cash)} />
        <Metric label="Unrealized P&L" value={fmtSignedUsd(pnl)} valueClass={pnlClass(pnl)} />
        <Metric label="Portfolio" value={fmtUsd(totalValue)} valueClass="text-accent" big />

        <div className="flex items-center gap-2" title={s.label} aria-live="polite">
          <span
            className="h-2.5 w-2.5 rounded-full animate-pulse-dot"
            style={{ backgroundColor: s.color }}
          />
          <span
            className="text-[10px] font-medium uppercase tracking-[0.15em]"
            style={{ color: s.color }}
          >
            {s.label}
          </span>
        </div>
      </div>
    </header>
  );
}

function Metric({
  label,
  value,
  valueClass = "text-[#e6e6f0]",
  big = false,
}: {
  label: string;
  value: string;
  valueClass?: string;
  big?: boolean;
}) {
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className={`tnum font-mono ${big ? "text-base" : "text-sm"} font-semibold ${valueClass}`}>
        {value}
      </div>
    </div>
  );
}
