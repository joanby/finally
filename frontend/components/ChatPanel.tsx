"use client";

import { useEffect, useRef, useState } from "react";
import { sendChat } from "@/lib/api";
import type { ChatActions } from "@/lib/types";

interface Msg {
  role: "user" | "assistant";
  content: string;
  actions?: ChatActions;
}

interface Props {
  onActions: () => void; // refrescar cartera/watchlist tras acciones del LLM
}

export function ChatPanel({ onActions }: Props) {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "I'm FinAlly, your AI trading copilot. Ask me to analyze your portfolio, or tell me to buy, sell, or watch a ticker.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", content: text }]);
    setDraft("");
    setLoading(true);
    try {
      const res = await sendChat(text);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.message, actions: res.actions },
      ]);
      const a = res.actions;
      if (a && (a.trades.length || a.watchlist_changes.length)) onActions();
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            err instanceof Error ? `Couldn't reach the assistant: ${err.message}` : "Request failed.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel flex min-h-0 flex-col">
      <div className="panel-head">
        <span>AI Copilot</span>
      </div>

      <div ref={scroller} className="scroll-y min-h-0 flex-1 space-y-3 p-3">
        {messages.map((m, i) => (
          <ChatBubble key={i} msg={m} />
        ))}
        {loading && (
          <div className="flex items-center gap-1 px-1 text-muted">
            <Dot delay="0ms" />
            <Dot delay="150ms" />
            <Dot delay="300ms" />
          </div>
        )}
      </div>

      <form onSubmit={submit} className="border-t border-border p-2.5">
        <div className="flex items-center gap-2">
          <input
            aria-label="Message FinAlly"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask FinAlly…"
            className="flex-1 rounded border border-border bg-panel-2 px-3 py-2 text-sm outline-none focus:border-primary"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-secondary px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}

function ChatBubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={isUser ? "text-right" : "text-left"}>
      <div
        className={`inline-block max-w-[90%] rounded-lg px-3 py-2 text-sm leading-snug ${
          isUser ? "bg-primary/15 text-[#e6e6f0]" : "bg-panel-2 text-[#d6d6e4]"
        }`}
      >
        {msg.content}
      </div>
      {msg.actions && <ActionReceipt actions={msg.actions} />}
    </div>
  );
}

function ActionReceipt({ actions }: { actions: ChatActions }) {
  const { trades, watchlist_changes, errors } = actions;
  if (!trades.length && !watchlist_changes.length && !errors.length) return null;
  return (
    <div className="mt-1.5 space-y-1 text-left">
      {trades.map((t, i) => (
        <Pill key={`t${i}`} color={t.side === "buy" ? "up" : "down"}>
          {t.side.toUpperCase()} {t.quantity} {t.ticker}
        </Pill>
      ))}
      {watchlist_changes.map((w, i) => (
        <Pill key={`w${i}`} color="primary">
          {w.action === "add" ? "+ WATCH" : "− UNWATCH"} {w.ticker}
        </Pill>
      ))}
      {errors.map((e, i) => (
        <Pill key={`e${i}`} color="down">
          {e}
        </Pill>
      ))}
    </div>
  );
}

function Pill({ children, color }: { children: React.ReactNode; color: "up" | "down" | "primary" }) {
  const cls = { up: "border-up text-up", down: "border-down text-down", primary: "border-primary text-primary" }[color];
  return (
    <span
      className={`mr-1 inline-block rounded border px-1.5 py-0.5 font-mono text-[11px] ${cls} bg-bg/40`}
    >
      {children}
    </span>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="h-1.5 w-1.5 rounded-full bg-muted animate-pulse-dot"
      style={{ animationDelay: delay }}
    />
  );
}
