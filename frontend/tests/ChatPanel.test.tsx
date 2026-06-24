import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPanel } from "@/components/ChatPanel";

beforeEach(() => {
  vi.restoreAllMocks();
});

function mockFetch(body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: async () => body,
  } as Response);
}

describe("ChatPanel", () => {
  it("renders the assistant greeting", () => {
    render(<ChatPanel onActions={() => {}} />);
    expect(screen.getByText(/FinAlly, your AI trading copilot/i)).toBeInTheDocument();
  });

  it("sends a message and renders the response with action receipts", async () => {
    const onActions = vi.fn();
    vi.stubGlobal(
      "fetch",
      mockFetch({
        message: "Bought 5 AAPL for you.",
        actions: { trades: [{ ticker: "AAPL", side: "buy", quantity: 5 }], watchlist_changes: [], errors: [] },
      })
    );

    render(<ChatPanel onActions={onActions} />);
    await userEvent.type(screen.getByLabelText("Message FinAlly"), "buy 5 AAPL");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(screen.getByText("Bought 5 AAPL for you.")).toBeInTheDocument());
    expect(screen.getByText("BUY 5 AAPL")).toBeInTheDocument();
    expect(onActions).toHaveBeenCalled();
  });

  it("shows the user message immediately (optimistic)", async () => {
    let resolve!: (v: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>((r) => (resolve = r)))
    );
    render(<ChatPanel onActions={() => {}} />);
    await userEvent.type(screen.getByLabelText("Message FinAlly"), "hello");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(screen.getByText("hello")).toBeInTheDocument();
    // resolve to avoid dangling promise warnings
    resolve({ ok: true, json: async () => ({ message: "hi", actions: { trades: [], watchlist_changes: [], errors: [] } }) } as Response);
  });
});
