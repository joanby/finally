import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Watchlist } from "@/components/Watchlist";
import type { PriceMap } from "@/lib/usePriceStream";

const prices: PriceMap = {
  AAPL: { price: 190.12, prev_price: 189.0, direction: "up", spark: [188, 189, 190.12], seq: 3 },
};

describe("Watchlist", () => {
  it("renders tickers and live price", () => {
    render(
      <Watchlist
        tickers={["AAPL", "MSFT"]}
        prices={prices}
        selected="AAPL"
        onSelect={() => {}}
        onAdd={() => {}}
        onRemove={() => {}}
      />
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("MSFT")).toBeInTheDocument();
    expect(screen.getByText("190.12")).toBeInTheDocument();
  });

  it("adds a ticker (uppercased) on submit", async () => {
    const onAdd = vi.fn();
    render(
      <Watchlist
        tickers={["AAPL"]}
        prices={prices}
        selected="AAPL"
        onSelect={() => {}}
        onAdd={onAdd}
        onRemove={() => {}}
      />
    );
    const input = screen.getByLabelText("Add ticker");
    await userEvent.type(input, "nvda{enter}");
    expect(onAdd).toHaveBeenCalledWith("NVDA");
  });

  it("removes a ticker via the × button", async () => {
    const onRemove = vi.fn();
    render(
      <Watchlist
        tickers={["AAPL"]}
        prices={prices}
        selected="AAPL"
        onSelect={() => {}}
        onAdd={() => {}}
        onRemove={onRemove}
      />
    );
    await userEvent.click(screen.getByLabelText("Remove AAPL"));
    expect(onRemove).toHaveBeenCalledWith("AAPL");
  });

  it("selects a ticker on row click", async () => {
    const onSelect = vi.fn();
    render(
      <Watchlist
        tickers={["AAPL", "MSFT"]}
        prices={prices}
        selected="AAPL"
        onSelect={onSelect}
        onAdd={() => {}}
        onRemove={() => {}}
      />
    );
    await userEvent.click(screen.getByText("MSFT"));
    expect(onSelect).toHaveBeenCalledWith("MSFT");
  });
});
