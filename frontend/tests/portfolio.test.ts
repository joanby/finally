import { describe, expect, it } from "vitest";
import { buildTreemap, pnlColor } from "@/lib/portfolio";
import type { Position } from "@/lib/types";

const pos = (ticker: string, quantity: number, current_price: number, pct_change = 0): Position => ({
  ticker,
  quantity,
  avg_cost: current_price,
  current_price,
  unrealized_pnl: 0,
  pct_change,
});

describe("buildTreemap", () => {
  it("computes weights summing to 1 and sorts by value desc", () => {
    const cells = buildTreemap([pos("A", 10, 100), pos("B", 10, 300)]);
    expect(cells[0].ticker).toBe("B");
    expect(cells.reduce((s, c) => s + c.weight, 0)).toBeCloseTo(1, 5);
    expect(cells[0].weight).toBeCloseTo(0.75, 5);
  });

  it("drops zero-value positions", () => {
    expect(buildTreemap([pos("A", 0, 100)])).toHaveLength(0);
  });
});

describe("pnlColor", () => {
  it("greens on profit, reds on loss", () => {
    expect(pnlColor(5)).toContain("22, 199, 132");
    expect(pnlColor(-5)).toContain("234, 57, 67");
  });
});
