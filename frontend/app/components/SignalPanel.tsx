"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { ShieldCheck, Cpu, CheckCircle2, Zap, Sparkles, RefreshCw, BarChart2 } from "lucide-react";

interface SignalPayload {
  alert_id: string;
  symbol: string;
  direction: string;
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_reward_ratio: number;
  position_size_lots: number;
  confidence_score: number;
  higher_tf_trend: string;
  confirmations: string[];
  ai_explanation?: string;
}

interface SignalPanelProps {
  signal: SignalPayload | null;
  onGenerateSignal: () => void;
  loading: boolean;
}

export default function SignalPanel({ signal: initialSignal, onGenerateSignal, loading }: SignalPanelProps) {
  const [signal, setSignal] = useState<SignalPayload | null>(initialSignal);

  useEffect(() => {
    setSignal(initialSignal);
  }, [initialSignal]);

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs font-sans space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-blue-600" />
          <h3 className="font-semibold text-slate-900 text-sm">Analyze & Signal Engine</h3>
        </div>

        <button
          onClick={onGenerateSignal}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-xl transition shadow-xs disabled:opacity-50 flex items-center gap-1.5"
        >
          {loading ? (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 fill-white" />
              <span>Run Analysis</span>
            </>
          )}
        </button>
      </div>

      {signal ? (
        <div className="space-y-3.5">
          {/* Setup Badge & Score */}
          <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200/80">
            <div className="flex items-center space-x-2.5">
              <span
                className={`text-[11px] font-bold px-2.5 py-0.5 rounded uppercase tracking-wider ${
                  signal.direction.toUpperCase() === "BUY"
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-rose-50 text-rose-700 border border-rose-200"
                }`}
              >
                {signal.direction.toUpperCase()} SETUP
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Trend: <strong className="text-slate-900 uppercase font-semibold">{signal.higher_tf_trend}</strong>
              </span>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider block">Score</span>
              <span className="text-sm font-bold text-blue-600">
                {signal.confidence_score}/100
              </span>
            </div>
          </div>

          {/* Target Price Levels Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 block mb-0.5 text-[10px] uppercase font-semibold">Entry Price</span>
              <span className="text-sm font-bold text-blue-600">${signal.entry_price}</span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 block mb-0.5 text-[10px] uppercase font-semibold">Stop Loss</span>
              <span className="text-sm font-bold text-rose-600">${signal.stop_loss}</span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 block mb-0.5 text-[10px] uppercase font-semibold">Take Profit 2</span>
              <span className="text-sm font-bold text-emerald-600">${signal.take_profit_2}</span>
            </div>
            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
              <span className="text-slate-400 block mb-0.5 text-[10px] uppercase font-semibold">Risk / Reward</span>
              <span className="text-sm font-bold text-indigo-600">1:{signal.risk_reward_ratio}</span>
            </div>
          </div>

          {/* Sizing & Capital Protection */}
          <div className="flex items-center justify-between text-xs bg-blue-50/60 p-2.5 rounded-xl border border-blue-100">
            <span className="text-blue-700 font-semibold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" /> Sizing:
            </span>
            <span className="font-bold text-blue-900">{signal.position_size_lots} Lots</span>
          </div>

          {/* Rule Confirmations */}
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
              Evaluated Rule Confirmations:
            </span>
            <div className="space-y-1">
              {signal.confirmations && signal.confirmations.length > 0 ? (
                signal.confirmations.map((c, i) => (
                  <div key={i} className="flex items-center space-x-2 text-xs text-slate-700 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>{c}</span>
                  </div>
                ))
              ) : (
                <div className="flex items-center space-x-2 text-xs text-slate-700 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>✓ Multi-timeframe trend & EMA breakout aligned</span>
                </div>
              )}
            </div>
          </div>

          {/* AI Summary Narrative */}
          {signal.ai_explanation && (
            <div className="bg-blue-50/80 border border-blue-200 p-3 rounded-xl text-xs text-blue-950 leading-relaxed">
              <strong className="text-blue-700 font-semibold flex items-center gap-1 mb-1">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" /> AI Market Summary:
              </strong>
              {signal.ai_explanation}
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-slate-400 text-xs">
          <BarChart2 className="w-7 h-7 mx-auto mb-2 text-slate-300" />
          <p className="font-semibold text-slate-700">Market Analysis Standing By</p>
          <p className="mt-1 font-medium text-slate-400">
            Click "Run Analysis" or enable Live Scan to evaluate 5M price action.
          </p>
        </div>
      )}

      <div className="text-[10px] text-slate-400 border-t border-slate-100 pt-2.5 mt-2 flex items-center justify-between font-mono">
        <span>ALERT ID:</span>
        <code className="text-blue-600 font-medium">{signal?.alert_id || "WAITING_TRIGGER"}</code>
      </div>
    </div>
  );
}
