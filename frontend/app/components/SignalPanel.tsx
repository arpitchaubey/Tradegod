"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import {
  Cpu,
  ShieldCheck,
  Zap,
  Sparkles,
  CheckCircle2,
  BarChart2,
  TrendingUp,
  TrendingDown,
  Target,
  ArrowRight,
  Clock,
  Compass
} from "lucide-react";

interface SignalPayload {
  alert_id: string;
  symbol: string;
  direction: string;
  entry_price: number;
  entry_market_price?: number;
  entry_limit_price?: number;
  entry_reachability_percent?: number;
  entry_reachability_state?: string;
  entry_distance_pips?: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3?: number;
  risk_reward_ratio: number;
  min_profit_pips?: number;
  expected_profit_pips?: number;
  expected_profit_usd?: number;
  position_size_lots: number;
  confidence_score: number;
  higher_tf_trend: string;
  confirmations: string[];
  ai_explanation?: string;
}

interface SignalPanelProps {
  signal: SignalPayload | null;
  selectedSymbol?: string;
  selectedTimeframe?: string;
  onGenerateSignal: () => void;
  loading: boolean;
}

export default function SignalPanel({
  signal: initialSignal,
  selectedSymbol = "XAU/USD",
  selectedTimeframe = "5m",
  onGenerateSignal,
  loading
}: SignalPanelProps) {
  const [signal, setSignal] = useState<SignalPayload | null>(initialSignal);
  const [activeEntryMode, setActiveEntryMode] = useState<"market" | "limit">("market");
  useEffect(() => setSignal(initialSignal), [initialSignal]);

  const isBuy = signal?.direction?.toUpperCase() === "BUY";
  const marketPrice = signal?.entry_market_price || signal?.entry_price || 0;
  const limitPrice = signal?.entry_limit_price || signal?.entry_price || 0;
  const chosenEntry = activeEntryMode === "market" ? marketPrice : limitPrice;
  const reachability = signal?.entry_reachability_percent ?? 95;

  return (
    <div className="card flex flex-col gap-0 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4" style={{ color: "var(--accent)" }} />
          <div>
            <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>Omni Signal Engine</p>
            <p className="text-[10px] font-medium uppercase tracking-wider mt-px" style={{ color: "var(--text-faint)" }}>
              {selectedSymbol} · {selectedTimeframe.toUpperCase()}
            </p>
          </div>
        </div>

        <button
          onClick={onGenerateSignal}
          disabled={loading}
          className="btn btn-primary"
          style={{ fontSize: "12px", padding: "6px 12px" }}
        >
          {loading ? (
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Zap className="w-3.5 h-3.5" />
              Scan Setup
            </>
          )}
        </button>
      </div>

      {/* Body */}
      {signal ? (
        <div className="flex flex-col gap-3 p-4">
          {/* Direction badge + confidence */}
          <div
            className="flex items-center justify-between rounded-xl p-3"
            style={{ background: "var(--bg-subtle)", border: "1px solid var(--border)" }}
          >
            <div className="flex items-center gap-2.5">
              <span
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wide"
                style={{
                  background: isBuy ? "var(--green-soft)" : "var(--red-soft)",
                  color: isBuy ? "var(--green)" : "var(--red)"
                }}
              >
                {isBuy ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                {signal.direction.toUpperCase()} Setup
              </span>
              <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Regime: <strong style={{ color: "var(--text)" }}>{signal.higher_tf_trend}</strong>
              </span>
            </div>
            <div className="text-right">
              <p className="text-[10px] uppercase font-semibold tracking-wider" style={{ color: "var(--text-faint)" }}>Win Prob</p>
              <p className="text-base font-bold font-mono" style={{ color: "var(--accent)" }}>
                {signal.confidence_score}<span className="text-xs">/100</span>
              </p>
            </div>
          </div>

          {/* Entry Execution Selector: Market vs Pullback */}
          <div
            className="p-2.5 rounded-xl border space-y-2"
            style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold uppercase tracking-wider text-[10px]" style={{ color: "var(--text-faint)" }}>
                Entry Strategy
              </span>
              <span className="badge badge-green font-bold text-[10px]">
                {reachability}% Feasibility
              </span>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => setActiveEntryMode("market")}
                className="px-2.5 py-1.5 rounded-lg text-xs font-bold flex flex-col text-left transition border cursor-pointer"
                style={{
                  background: activeEntryMode === "market" ? "var(--bg-elevated)" : "transparent",
                  borderColor: activeEntryMode === "market" ? "var(--accent)" : "transparent",
                  color: activeEntryMode === "market" ? "var(--accent)" : "var(--text-muted)"
                }}
              >
                <span className="text-[10px] uppercase">⚡ Market Order</span>
                <span className="font-mono text-sm font-black mt-0.5" style={{ color: "var(--text)" }}>
                  ${marketPrice.toFixed(2)}
                </span>
                <span className="text-[9px]" style={{ color: "var(--green)" }}>Instant Fill (0.0 pips)</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveEntryMode("limit")}
                className="px-2.5 py-1.5 rounded-lg text-xs font-bold flex flex-col text-left transition border cursor-pointer"
                style={{
                  background: activeEntryMode === "limit" ? "var(--bg-elevated)" : "transparent",
                  borderColor: activeEntryMode === "limit" ? "var(--accent)" : "transparent",
                  color: activeEntryMode === "limit" ? "var(--accent)" : "var(--text-muted)"
                }}
              >
                <span className="text-[10px] uppercase">🎯 Pullback Limit</span>
                <span className="font-mono text-sm font-black mt-0.5" style={{ color: "var(--text)" }}>
                  ${limitPrice.toFixed(2)}
                </span>
                <span className="text-[9px]" style={{ color: "var(--accent)" }}>
                  {signal.entry_distance_pips ? `${signal.entry_distance_pips} pips away` : "Discount Fill"}
                </span>
              </button>
            </div>
          </div>

          {/* Price levels grid */}
          <div className="grid grid-cols-2 gap-2">
            <PriceCell label="Chosen Entry" value={`$${chosenEntry.toFixed(2)}`} color="var(--accent)" />
            <PriceCell label="Stop Loss" value={`$${signal.stop_loss.toFixed(2)}`} color="var(--red)" />
            <PriceCell label="Take Profit 2" value={`$${signal.take_profit_2.toFixed(2)}`} color="var(--green)" />
            <PriceCell label="Risk : Reward" value={`1 : ${signal.risk_reward_ratio}`} color="var(--gold)" />
          </div>

          {/* Profit & Sizing Matrix */}
          <div
            className="flex items-center justify-between rounded-xl px-3 py-2.5 border"
            style={{ background: "rgba(37,99,235,0.06)", borderColor: "rgba(37,99,235,0.18)" }}
          >
            <div>
              <span className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: "var(--accent)" }}>
                <ShieldCheck className="w-3.5 h-3.5" />
                Target & Size
              </span>
              <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                Min Target: <strong style={{ color: "var(--text)" }}>{signal.min_profit_pips || 30} Pips</strong>
              </p>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold font-mono" style={{ color: "var(--text)" }}>
                {signal.position_size_lots} Lots
              </span>
              {signal.expected_profit_usd ? (
                <p className="text-[10px] font-mono font-bold" style={{ color: "var(--green)" }}>
                  Est +${signal.expected_profit_usd.toFixed(2)}
                </p>
              ) : null}
            </div>
          </div>

          {/* Execution Guidance */}
          <div
            className="rounded-xl p-3 text-xs leading-relaxed"
            style={{ background: "var(--bg-subtle)", border: "1px solid var(--border)", color: "var(--text-muted)" }}
          >
            {activeEntryMode === "market" ? (
              <p>
                ⚡ <strong>Instant Market Execution:</strong> Enter at current spot{" "}
                <strong style={{ color: "var(--accent)" }}>${marketPrice.toFixed(2)}</strong>. Guaranteed fill with SL at{" "}
                <strong style={{ color: "var(--red)" }}>${signal.stop_loss.toFixed(2)}</strong> and TP at{" "}
                <strong style={{ color: "var(--green)" }}>${signal.take_profit_2.toFixed(2)}</strong>.
              </p>
            ) : (
              <p>
                🎯 <strong>Sniper Pullback Execution:</strong> Set {signal.direction.toUpperCase()} Limit at{" "}
                <strong style={{ color: "var(--accent)" }}>${limitPrice.toFixed(2)}</strong> ({reachability}% historical fill rate).
              </p>
            )}
          </div>

          {/* Confirmations */}
          {signal.confirmations?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase font-bold tracking-wider mb-2" style={{ color: "var(--text-faint)" }}>
                Omni Confirmations
              </p>
              <div className="flex flex-col gap-1">
                {signal.confirmations.map((c, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-px" style={{ color: "var(--green)" }} />
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI narrative */}
          {signal.ai_explanation && (
            <div
              className="rounded-xl p-3 text-xs leading-relaxed"
              style={{
                background: "rgba(37,99,235,0.06)",
                border: "1px solid rgba(37,99,235,0.15)",
                color: "var(--text-muted)"
              }}
            >
              <strong className="flex items-center gap-1 mb-1.5 text-xs" style={{ color: "var(--accent)" }}>
                <Sparkles className="w-3.5 h-3.5" /> AI Summary
              </strong>
              {signal.ai_explanation}
            </div>
          )}
        </div>
      ) : (
        <div className="py-14 flex flex-col items-center gap-3 px-4">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center"
            style={{ background: "var(--bg-subtle)" }}
          >
            <BarChart2 className="w-6 h-6" style={{ color: "var(--text-faint)" }} />
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>Omni Engine Standing By</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-faint)" }}>
              Click <strong>Scan Setup</strong> to evaluate live market structure & reachability
            </p>
          </div>
        </div>
      )}

      {/* Footer */}
      <div
        className="flex items-center justify-between px-4 py-2 text-[10px] font-mono shrink-0"
        style={{ borderTop: "1px solid var(--border)", color: "var(--text-faint)" }}
      >
        <span>ALERT_ID</span>
        <code style={{ color: "var(--accent)" }}>{signal?.alert_id || "AWAITING_TRIGGER"}</code>
      </div>
    </div>
  );
}

function PriceCell({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div
      className="rounded-xl p-2.5"
      style={{ background: "var(--bg-subtle)", border: "1px solid var(--border)" }}
    >
      <p className="text-[10px] uppercase font-semibold tracking-wider mb-0.5" style={{ color: "var(--text-faint)" }}>
        {label}
      </p>
      <p className="text-sm font-bold font-mono" style={{ color }}>{value}</p>
    </div>
  );
}
