"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from "recharts";
import type { LivePrice } from "@/lib/usePriceStream";
import { PriceFlash } from "./PriceFlash";
import { fmtNum, fmtPct } from "@/lib/format";

interface Props {
  ticker: string | null;
  live: LivePrice | undefined;
}

export function MainChart({ ticker, live }: Props) {
  const data = (live?.spark ?? []).map((price, i) => ({ i, price }));
  const pct = live && live.prev_price ? ((live.price - live.prev_price) / live.prev_price) * 100 : 0;
  const stroke = live?.direction === "down" ? "#ea3943" : "#16c784";

  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>Chart {ticker && <span className="text-primary">· {ticker}</span>}</span>
        {live && (
          <span className="flex items-center gap-3 font-mono text-[12px]">
            <PriceFlash
              value={live.price}
              direction={live.direction}
              seq={live.seq}
              format={(n) => `$${fmtNum(n)}`}
              className="text-[#e6e6f0]"
            />
            <span className={pct < 0 ? "text-down" : "text-up"}>{fmtPct(pct)}</span>
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 p-2">
        {data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 4 }}>
              <defs>
                <linearGradient id="mainFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={stroke} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={stroke} stopOpacity={0} />
                </linearGradient>
              </defs>
              <YAxis
                domain={["dataMin", "dataMax"]}
                width={48}
                tick={{ fill: "#8b8ba0", fontSize: 10, fontFamily: "monospace" }}
                tickFormatter={(v) => fmtNum(v)}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: "#161625",
                  border: "1px solid #272735",
                  borderRadius: 6,
                  fontFamily: "monospace",
                  fontSize: 12,
                }}
                labelFormatter={() => ""}
                formatter={(v: number) => [fmtNum(v), "price"]}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={stroke}
                strokeWidth={1.5}
                fill="url(#mainFill)"
                isAnimationActive={false}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted">
            {ticker ? "Accumulating live prices…" : "Select a ticker from the watchlist."}
          </div>
        )}
      </div>
    </section>
  );
}
