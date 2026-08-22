"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Brain, CheckCircle2, ShieldCheck, Bell, BellOff } from "lucide-react";

export default function ActiveStrategyCard() {
  const [strategy, setStrategy] = useState<any>(null);
  const [botSettings, setBotSettings] = useState<any>(null);

  const fetchCurrentStrategy = () => {
    safeFetch(`${API_BASE}/api/strategy/current`)
      .then((res) => res.json())
      .then((data) => setStrategy(data))
      .catch((err) => console.warn("Error loading strategy:", err));

    safeFetch(`${API_BASE}/api/bot/settings`)
      .then((res) => res.json())
      .then((data) => setBotSettings(data))
      .catch((err) => console.warn("Error loading bot settings:", err));
  };

  useEffect(() => {
    fetchCurrentStrategy();
    const interval = setInterval(fetchCurrentStrategy, 4000);
    return () => clearInterval(interval);
  }, []);

  const rules = strategy?.rules || [];
  const trendRule = rules.find((r: any) => r.timeframe === "trend") || rules[0];
  const momentumRule = rules.find((r: any) => r.left_operand === "rsi" || r.id.includes("rsi")) || rules[1] || rules[0];

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs font-sans space-y-3">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-2.5 gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-xl border border-blue-100">
            <Brain className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
              <span>Active Strategy Engine:</span>
              <span className="text-blue-600 font-extrabold">{strategy?.name || "Gold Multi-Timeframe Strategy"}</span>
            </h3>
            <span className="text-[10px] text-slate-400 font-medium">
              Symbol: <strong className="text-slate-700">{strategy?.symbol || "XAU/USD"}</strong> | Direction: <strong className="text-slate-700 uppercase">{strategy?.direction || "LONG"}</strong>
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            LIVE ENFORCING
          </span>

          <span
            className={`text-[10px] px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1 border ${
              botSettings?.notify_on_new_signal !== false
                ? "bg-blue-50 text-blue-700 border-blue-200"
                : "bg-slate-50 text-slate-500 border-slate-200"
            }`}
          >
            {botSettings?.notify_on_new_signal !== false ? (
              <>
                <Bell className="w-3 h-3 text-blue-600" />
                TELEGRAM BROADCAST ON
              </>
            ) : (
              <>
                <BellOff className="w-3 h-3 text-slate-400" />
                TELEGRAM PAUSED
              </>
            )}
          </span>
        </div>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold block">Trend Rule</span>
            <span className="font-bold text-slate-800 text-xs truncate max-w-[180px] block">
              {trendRule?.description || "20 EMA > 50 EMA (1H Trend)"}
            </span>
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold block">Momentum Filter</span>
            <span className="font-bold text-slate-800 text-xs truncate max-w-[180px] block">
              {momentumRule?.description || "RSI > 55 Threshold"}
            </span>
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5 flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold block">Risk Management</span>
            <span className="font-bold text-blue-600 text-xs">
              1 : {strategy?.risk_reward_ratio || 2.0} Target R:R Ratio
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
