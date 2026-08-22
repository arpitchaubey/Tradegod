"use client";

import React, { useState, useEffect } from "react";
import { safeFetch, API_BASE } from "../utils/api";
import { ShieldCheck, ShieldAlert, Cpu, Wallet, TrendingUp, Layers } from "lucide-react";

interface StatusResponse {
  mode: string;
  is_kill_switch_active: boolean;
  account: {
    balance?: number;
    equity?: number;
    unrealized_pnl?: number;
  };
  open_positions_count: number;
  news_filter: {
    active: boolean;
    blackout_active: boolean;
    impact_level: string;
    description: string;
  };
}

export default function ExecutionControlPanel() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = () => {
    safeFetch(`${API_BASE}/api/execution/status`)
      .then((res) => res.json())
      .then((data) => setStatus(data))
      .catch((err) => console.warn("Backend offline or starting up...", err));
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleModeChange = (newMode: string) => {
    setLoading(true);
    safeFetch(`${API_BASE}/api/execution/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode })
    })
      .then((res) => res.json())
      .then(() => {
        fetchStatus();
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const account: any = status?.account || {};

  return (
    <div className="relative z-10 rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-2xl transition duration-300 hover:border-amber-500/30 space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3.5">
        <h3 className="text-base font-extrabold text-slate-100 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-amber-400" />
          <span>Execution & Broker Control Panel</span>
        </h3>
        <span
          className={`text-xs px-3 py-1 rounded-full font-bold border shadow-sm flex items-center gap-1.5 ${
            status?.is_kill_switch_active
              ? "bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse"
              : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${status?.is_kill_switch_active ? "bg-rose-500 animate-ping" : "bg-emerald-400"}`} />
          {status?.is_kill_switch_active ? "KILL-SWITCH ACTIVE" : "SYSTEM NORMAL"}
        </span>
      </div>

      {/* Mode Switcher */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {[
          { key: "PAPER_TRADING", label: "Paper Trading", icon: Cpu },
          { key: "OANDA", label: "OANDA v20", icon: Wallet },
          { key: "MT5", label: "MetaTrader 5", icon: TrendingUp },
          { key: "DISABLED", label: "Disabled", icon: ShieldAlert }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => handleModeChange(key)}
            disabled={loading}
            className={`py-2.5 px-3 text-xs font-bold rounded-xl border transition-all duration-200 flex items-center justify-center gap-2 shadow-sm ${
              status?.mode === key
                ? "bg-gradient-to-r from-amber-500 to-yellow-500 text-slate-950 border-amber-400 shadow-amber-500/20 font-black scale-[1.02]"
                : "bg-slate-950/80 text-slate-400 border-slate-800/80 hover:border-slate-700 hover:text-white"
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Account Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 shadow-inner">
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Account Balance</span>
          <div className="text-base font-black text-slate-100 mt-0.5">
            ${account.balance?.toLocaleString() || "10,000.00"}
          </div>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Equity</span>
          <div className="text-base font-black text-slate-100 mt-0.5">
            ${account.equity?.toLocaleString() || "10,000.00"}
          </div>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Unrealized PnL</span>
          <div
            className={`text-base font-black mt-0.5 ${
              (account.unrealized_pnl || 0) >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            ${(account.unrealized_pnl || 0) >= 0 ? "+" : ""}
            {account.unrealized_pnl?.toFixed(2) || "0.00"}
          </div>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Open Positions</span>
          <div className="text-base font-black text-amber-400 mt-0.5 flex items-center gap-1">
            <Layers className="w-4 h-4 text-amber-400" />
            <span>{status?.open_positions_count || 0} / 3 Max</span>
          </div>
        </div>
      </div>
    </div>
  );
}
