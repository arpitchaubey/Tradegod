"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Brain, CheckCircle2, ShieldCheck, Bell, BellOff } from "lucide-react";

export default function ActiveStrategyCard() {
  const [strategy, setStrategy] = useState<any>(null);
  const [botSettings, setBotSettings] = useState<any>(null);

  useEffect(() => {
    const fetch = () => {
      safeFetch(`${API_BASE}/api/strategy/current`)
        .then((r) => r.json()).then(setStrategy).catch(() => {});
      safeFetch(`${API_BASE}/api/bot/settings`)
        .then((r) => r.json()).then(setBotSettings).catch(() => {});
    };
    fetch();
    const t = setInterval(fetch, 5000);
    return () => clearInterval(t);
  }, []);

  const rules = strategy?.rules || [];
  const trendRule = rules.find((r: any) => r.timeframe === "trend") || rules[0];
  const momentumRule = rules.find((r: any) => r.left_operand === "rsi" || r.id?.includes?.("rsi")) || rules[1] || rules[0];
  const notifyOn = botSettings?.notify_on_new_signal !== false;

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="flex flex-wrap items-center justify-between gap-2 px-4 py-3"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "rgba(37,99,235,0.1)" }}
          >
            <Brain className="w-4 h-4" style={{ color: "var(--accent)" }} />
          </div>
          <div>
            <p className="text-xs font-semibold" style={{ color: "var(--text)" }}>
              {strategy?.name || "Gold Multi-TF Strategy"}
            </p>
            <p className="text-[10px] font-medium mt-px" style={{ color: "var(--text-faint)" }}>
              {strategy?.symbol || "XAU/USD"} · {(strategy?.direction || "LONG").toUpperCase()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="badge badge-green">
            <span className="live-dot" style={{ width: "5px", height: "5px" }} />
            Live
          </span>
          <span
            className="badge"
            style={{
              background: notifyOn ? "rgba(37,99,235,0.1)" : "var(--bg-subtle)",
              color: notifyOn ? "var(--accent)" : "var(--text-faint)",
              border: "1px solid var(--border)"
            }}
          >
            {notifyOn
              ? <><Bell className="w-3 h-3" /> Telegram On</>
              : <><BellOff className="w-3 h-3" /> Telegram Off</>
            }
          </span>
        </div>
      </div>

      {/* Rules */}
      <div className="grid grid-cols-3 divide-x" style={{ borderColor: "var(--border)" }}>
        <RuleCell
          icon={<CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: "var(--green)" }} />}
          label="Trend Filter"
          value={trendRule?.description || "20 EMA > 50 EMA (1H)"}
        />
        <RuleCell
          icon={<CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: "var(--green)" }} />}
          label="Momentum"
          value={momentumRule?.description || "RSI > 55 Threshold"}
        />
        <RuleCell
          icon={<ShieldCheck className="w-3.5 h-3.5 shrink-0" style={{ color: "var(--accent)" }} />}
          label="Risk Target"
          value={`1 : ${strategy?.risk_reward_ratio || 2.0} R:R`}
          valueColor="var(--accent)"
        />
      </div>
    </div>
  );
}

function RuleCell({
  icon, label, value, valueColor
}: { icon: React.ReactNode; label: string; value: string; valueColor?: string }) {
  return (
    <div className="px-3 py-2.5 flex items-start gap-2">
      {icon}
      <div className="min-w-0">
        <p className="text-[9px] uppercase font-bold tracking-wider mb-0.5" style={{ color: "var(--text-faint)" }}>
          {label}
        </p>
        <p className="text-xs font-semibold truncate" style={{ color: valueColor || "var(--text)" }}>
          {value}
        </p>
      </div>
    </div>
  );
}
