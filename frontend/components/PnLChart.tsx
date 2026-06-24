"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import type { Snapshot } from "@/lib/types";
import { fmtUsd } from "@/lib/format";

interface Props {
  snapshots: Snapshot[];
}

export function PnLChart({ snapshots }: Props) {
  const data = snapshots.map((s, i) => ({ i, value: s.total_value }));
  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>Portfolio Value</span>
      </div>
      <div className="min-h-0 flex-1 p-2">
        {data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 4 }}>
              <YAxis
                domain={["dataMin", "dataMax"]}
                width={56}
                tick={{ fill: "#8b8ba0", fontSize: 10, fontFamily: "monospace" }}
                tickFormatter={(v) => `$${Math.round(v).toLocaleString()}`}
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
                formatter={(v: number) => [fmtUsd(v), "value"]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#ecad0a"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted">
            Recording portfolio value…
          </div>
        )}
      </div>
    </section>
  );
}
