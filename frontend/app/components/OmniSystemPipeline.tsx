"use client";

import React, { useEffect, useState } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import {
  Database,
  Sliders,
  Bot,
  Send,
  Sparkles,
  ArrowDown,
  ArrowUp,
  ArrowRight,
  RefreshCw,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  ShieldCheck,
  TrendingUp,
  Zap
} from "lucide-react";

interface PipelineStatus {
  status: string;
  bot_active: boolean;
  scan_count: number;
  alerts_sent_count: number;
  last_scan_time: string | null;
  scan_interval_seconds: number;
  nodes: {
    data: {
      provider: string;
      status: string;
      feed: string;
    };
    settings: {
      execution_mode: string;
      min_confidence_score: number;
      max_risk_percent: number;
      default_lot_size: number;
    };
    bot: {
      state: string;
      total_scans: number;
      total_alerts: number;
    };
    omni_engine: {
      status: string;
      multi_timeframe: string;
      last_projection?: any;
    };
    telegram: {
      configured: boolean;
      notify_on_signal: boolean;
      notify_on_close: boolean;
    };
  };
}

export default function OmniSystemPipeline() {
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [toggling, setToggling] = useState<boolean>(false);

  const fetchPipeline = () => {
    safeFetch(`${API_BASE}/api/bot/pipeline-status`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status) setPipeline(data);
      })
      .catch((err) => console.warn("Pipeline status error:", err));
  };

  useEffect(() => {
    fetchPipeline();
    const interval = setInterval(fetchPipeline, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleBot = async () => {
    setToggling(true);
    try {
      await safeFetch(`${API_BASE}/api/bot/toggle`, { method: "POST" });
      fetchPipeline();
    } catch (e) {
      console.error("Toggle error:", e);
    } finally {
      setToggling(false);
    }
  };

  const isRunning = pipeline?.bot_active ?? true;

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs font-sans space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs">
            <Zap className="w-4 h-4 text-amber-300" />
          </div>
          <div>
            <h3 className="font-extrabold text-slate-900 text-sm">System Flow Architecture</h3>
            <p className="text-[11px] text-slate-500 font-medium">
              Real-Time End-to-End Orchestrator: Data ➔ Bot ➔ Omni AI ➔ Telegram
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700">
            <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
            <span>Cycle #{pipeline?.scan_count || 0}</span>
          </span>

          <button
            onClick={handleToggleBot}
            disabled={toggling}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-bold text-xs shadow-xs transition ${
              isRunning
                ? "bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
          >
            {isRunning ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-amber-800" />
                <span>Pause Auto-Scan</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Start Auto-Scan</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Visual Node Diagram (Direct match of user's handwritten diagram) */}
      <div className="bg-slate-50/80 rounded-2xl p-5 border border-slate-200/80">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          
          {/* Top-Left: TELEGRAM BOX */}
          <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-sky-50 text-sky-600 border border-sky-100">
                  <Send className="w-4 h-4" />
                </div>
                <h4 className="font-bold text-xs text-slate-900">TELEGRAM</h4>
              </div>
              <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-md ${
                pipeline?.nodes?.telegram?.configured
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : "bg-slate-100 text-slate-600"
              }`}>
                {pipeline?.nodes?.telegram?.configured ? "CONNECTED" : "STANDBY"}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-tight">
              Instant rich alert broadcast for entries, TP/SL hits, and trade exits.
            </p>
            <div className="text-[10px] font-bold text-slate-600 flex items-center justify-between pt-1 border-t border-slate-100">
              <span>Alerts Sent:</span>
              <span className="text-blue-600 font-extrabold">{pipeline?.alerts_sent_count || 0}</span>
            </div>
          </div>

          {/* Empty Center-Top Spacer */}
          <div className="hidden md:flex flex-col items-center justify-center">
            <span className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider">
              Real-Time Pipeline
            </span>
          </div>

          {/* Top-Right: DATA BOX */}
          <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
                  <Database className="w-4 h-4" />
                </div>
                <h4 className="font-bold text-xs text-slate-900">DATA (MARKET)</h4>
              </div>
              <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                LIVE SPOT
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-tight">
              High-frequency spot candles (PAXG Spot Gold, FX & Crypto feeds).
            </p>
            <div className="text-[10px] font-bold text-slate-600 flex items-center justify-between pt-1 border-t border-slate-100">
              <span>Provider:</span>
              <span className="text-emerald-700 uppercase font-extrabold">
                {pipeline?.nodes?.data?.provider || "Spot Provider"}
              </span>
            </div>
          </div>
        </div>

        {/* Center Row: SETTING PREFERENCE -> BOT (Center Hub) */}
        <div className="my-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          {/* Left: SETTING PREFERENCE BOX */}
          <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600 border border-amber-100">
                  <Sliders className="w-4 h-4" />
                </div>
                <h4 className="font-bold text-xs text-slate-900">SETTING PREFERENCE</h4>
              </div>
              <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200">
                ACTIVE
              </span>
            </div>
            <div className="text-[11px] text-slate-600 space-y-0.5">
              <div className="flex justify-between">
                <span>Mode:</span>
                <strong className="text-slate-900">{pipeline?.nodes?.settings?.execution_mode || "PAPER_TRADING"}</strong>
              </div>
              <div className="flex justify-between">
                <span>Min Confidence:</span>
                <strong className="text-blue-600">{pipeline?.nodes?.settings?.min_confidence_score || 75}%</strong>
              </div>
              <div className="flex justify-between">
                <span>Risk Limit:</span>
                <strong className="text-slate-900">{pipeline?.nodes?.settings?.max_risk_percent || 2.0}%</strong>
              </div>
            </div>
          </div>

          {/* Center: BOT (ORCHESTRATOR HUB) */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-md space-y-3 md:col-span-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-white/15 text-white backdrop-blur-xs">
                  <Bot className="w-5 h-5 text-amber-300" />
                </div>
                <div>
                  <h4 className="font-black text-sm tracking-wide">BOT (CENTRAL ORCHESTRATOR)</h4>
                  <p className="text-[11px] text-blue-100">
                    Routes live data, applies risk rules, triggers AI vision & executes orders
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-black px-3 py-1 rounded-xl bg-white text-blue-700 shadow-2xs uppercase">
                {pipeline?.nodes?.bot?.state || "AUTO-SCANNING"}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/20 text-center">
              <div className="bg-white/10 p-2 rounded-xl">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">Scans Run</span>
                <span className="text-sm font-black">{pipeline?.scan_count || 0}</span>
              </div>
              <div className="bg-white/10 p-2 rounded-xl">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">Scan Frequency</span>
                <span className="text-sm font-black">Every 15s</span>
              </div>
              <div className="bg-white/10 p-2 rounded-xl">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">Risk Engine</span>
                <span className="text-sm font-black">Strict 1:2.5+</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row: OMNI AI ENGINE */}
        <div className="p-4 rounded-xl bg-white border border-indigo-200/90 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
                <Sparkles className="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <h4 className="font-extrabold text-xs text-slate-900">OMNI AI ENGINE</h4>
                <p className="text-[11px] text-slate-500">
                  FVG / iFVG • Session Sweeps • C2C Momentum • CHoCH Risk • Self-Learning Matrix
                </p>
              </div>
            </div>
            <span className="text-[10px] font-extrabold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
              RESULT SYNCED
            </span>
          </div>

          <div className="bg-indigo-50/50 p-2.5 rounded-xl border border-indigo-100/80 flex flex-wrap items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
              <span className="font-bold text-indigo-950">Multi-Timeframe Matrix:</span>
              <span className="text-slate-600 font-semibold">1H (Trend) + 15M (Setup) + 5M (Entry)</span>
            </div>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-md">
              Bayesian Feedback Self-Learning: ONLINE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
