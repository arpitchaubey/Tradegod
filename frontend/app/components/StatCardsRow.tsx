"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { TrendingUp, Bell, CheckCircle2, Zap } from "lucide-react";

interface StatCardsRowProps {
  lastPrice?: number;
  symbol?: string;
}

export default function StatCardsRow({ lastPrice, symbol = "XAU/USD" }: StatCardsRowProps) {
  const [stats, setStats] = useState<any>(null);
  const [tick, setTick] = useState(false);

  useEffect(() => {
    const fetch = () =>
      safeFetch(`${API_BASE}/api/signals/stats`)
        .then((r) => r.json())
        .then((d) => { if (d) setStats(d); })
        .catch(() => {});
    fetch();
    const t = setInterval(fetch, 2500);
    return () => clearInterval(t);
  }, []);

  // Subtle tick animation on price change
  useEffect(() => {
    if (!lastPrice) return;
    setTick(true);
    const t = setTimeout(() => setTick(false), 500);
    return () => clearTimeout(t);
  }, [lastPrice]);

  const totalAlerts = stats?.total_alerts ?? 0;
  const wins = stats?.right_predictions ?? 0;
  const winRate = stats?.win_rate_percent ?? 0;

  return (
    <div
      className="flex items-center gap-px rounded-xl overflow-hidden border text-sm"
      style={{
        background: "var(--bg-elevated)",
        borderColor: "var(--border)",
        boxShadow: "var(--shadow-sm)"
      }}
    >
      {/* 1 — Spot price */}
      <StatCell
        icon={<TrendingUp className="w-3.5 h-3.5" style={{ color: "var(--accent)" }} strokeWidth={2} />}
        label={symbol}
        value={
          <span
            className="font-mono font-bold transition-all duration-200"
            style={{
              color: tick ? "var(--green)" : "var(--text)",
              fontSize: "15px"
            }}
          >
            {lastPrice ? `$${lastPrice.toLocaleString("en-US", { minimumFractionDigits: 2 })}` : "Live Feed"}
          </span>
        }
      />

      <Div />

      {/* 2 — Bot status */}
      <StatCell
        icon={<span className="live-dot" />}
        label="Omni Bot"
        value={
          <span className="font-semibold text-xs uppercase tracking-wide" style={{ color: "var(--green)" }}>
            Auto-Scan
          </span>
        }
      />

      <Div />

      {/* 3 — Alerts */}
      <StatCell
        icon={<Bell className="w-3.5 h-3.5" style={{ color: "var(--gold)" }} strokeWidth={2} />}
        label="Alerts Sent"
        value={
          <span className="font-mono font-bold" style={{ fontSize: "15px" }}>{totalAlerts}</span>
        }
      />

      <Div />

      {/* 4 — Accuracy */}
      <StatCell
        icon={<CheckCircle2 className="w-3.5 h-3.5" style={{ color: "var(--green)" }} strokeWidth={2} />}
        label="Accuracy"
        value={
          <span className="font-mono font-bold" style={{ fontSize: "15px", color: "var(--green)" }}>
            {winRate.toFixed(1)}%
            <span className="font-normal text-xs ml-1" style={{ color: "var(--text-muted)" }}>
              ({wins}W)
            </span>
          </span>
        }
      />
    </div>
  );
}

function Div() {
  return <div className="self-stretch w-px" style={{ background: "var(--border)" }} />;
}

function StatCell({
  icon, label, value
}: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-2.5 flex-1 min-w-0">
      <div className="shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-wider truncate" style={{ color: "var(--text-faint)" }}>
          {label}
        </p>
        <div className="mt-0.5">{value}</div>
      </div>
    </div>
  );
}
