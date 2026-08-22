"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Sliders, CheckCircle2, Shield, Layers, DollarSign, Activity } from "lucide-react";

interface BotControlSettings {
  bot_active: boolean;
  default_lot_size: number;
  max_positions: number;
  max_risk_percent: number;
  execution_mode: string;
  min_confidence_score: number;
  min_risk_reward_ratio: number;
  include_ai_explanation: boolean;
}

export default function BotControlPanel() {
  const [settings, setSettings] = useState<BotControlSettings>({
    bot_active: true,
    default_lot_size: 0.10,
    max_positions: 3,
    max_risk_percent: 2.0,
    execution_mode: "PAPER_TRADING",
    min_confidence_score: 75,
    min_risk_reward_ratio: 1.5,
    include_ai_explanation: true
  });

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const fetchSettings = () => {
    safeFetch(`${API_BASE}/api/bot/settings`)
      .then((res) => res.json())
      .then((data) => {
        if (data.settings) {
          setSettings((prev) => ({
            ...prev,
            ...data.settings,
            default_lot_size: data.settings.default_lot_size ?? 0.10,
            max_positions: data.settings.max_positions ?? 3,
            max_risk_percent: data.settings.max_risk_percent ?? 2.0,
            execution_mode: data.settings.execution_mode ?? "PAPER_TRADING",
            min_confidence_score: data.settings.min_confidence_score ?? 75,
            min_risk_reward_ratio: data.settings.min_risk_reward_ratio ?? 1.5
          }));
        }
      })
      .catch((err) => console.warn("Bot Settings API offline:", err));
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveSettings = async () => {
    setSaving(true);
    setSuccessMsg("");
    try {
      const res = await safeFetch(`${API_BASE}/api/bot/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      if (data.status === "success") {
        setSuccessMsg("Bot analysis & execution parameters saved successfully!");
      }
    } catch (err) {
      console.error("Save Bot Control settings error:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs font-sans space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3.5 gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-600 text-white font-bold shadow-xs">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <span>Bot Analysis & Risk Management Control Panel</span>
            </h3>
            <p className="text-xs text-slate-400 font-normal mt-0.5">
              Control bot execution parameters, lot sizes, risk limits, confidence thresholds, and broker connectors.
            </p>
          </div>
        </div>

        <span className="text-xs px-3 py-1 rounded-full font-medium border bg-blue-50 text-blue-700 border-blue-200 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          EXECUTION MODE: {settings.execution_mode}
        </span>
      </div>

      {/* Grid: Lot Size & Risk Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lot Size & Execution Mode Box */}
        <div className="space-y-4 bg-slate-50 border border-slate-200/80 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-4 h-4 text-blue-600" />
            <span>Position Size & Execution Connector</span>
          </h4>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Default Position Size (Lots):
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10.0"
                value={settings.default_lot_size}
                onChange={(e) => setSettings({ ...settings, default_lot_size: parseFloat(e.target.value) || 0.01 })}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 font-extrabold font-mono focus:outline-none focus:border-blue-600 shadow-xs"
              />
              <span className="text-[10px] text-slate-400 block mt-1">Standard XAU/USD lot size per trade signal (0.10 lots = 10 oz).</span>
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Broker Execution Adapter:
              </label>
              <select
                value={settings.execution_mode}
                onChange={(e) => setSettings({ ...settings, execution_mode: e.target.value })}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 font-bold focus:outline-none focus:border-blue-600 shadow-xs cursor-pointer"
              >
                <option value="PAPER_TRADING">Paper Trading Simulator (Simulated $10,000 Equity)</option>
                <option value="OANDA_LIVE">OANDA v20 REST API (Live Broker)</option>
                <option value="META_TRADER_5">MetaTrader 5 Bridge Connector</option>
              </select>
            </div>
          </div>
        </div>

        {/* Risk Management Limits Box */}
        <div className="space-y-4 bg-slate-50 border border-slate-200/80 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-blue-600" />
            <span>Capital Protection & Position Limits</span>
          </h4>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Max Concurrent Open Positions:
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={settings.max_positions}
                onChange={(e) => setSettings({ ...settings, max_positions: parseInt(e.target.value) || 1 })}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 font-extrabold font-mono focus:outline-none focus:border-blue-600 shadow-xs"
              />
              <span className="text-[10px] text-slate-400 block mt-1">Maximum allowed active trades open simultaneously.</span>
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Max Account Risk Per Trade (% Equity):
              </label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="10.0"
                value={settings.max_risk_percent}
                onChange={(e) => setSettings({ ...settings, max_risk_percent: parseFloat(e.target.value) || 1.0 })}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 font-extrabold font-mono focus:outline-none focus:border-blue-600 shadow-xs"
              />
              <span className="text-[10px] text-slate-400 block mt-1">Cap maximum equity loss per trade setup.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Filter Thresholds */}
      <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
        <h4 className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-blue-600" />
          <span>AI Technical Analysis & Signal Evaluation Thresholds</span>
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
            <div className="flex justify-between text-xs">
              <span className="text-slate-600 font-semibold">Min Confidence Score:</span>
              <span className="font-bold text-blue-600">{settings.min_confidence_score}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={settings.min_confidence_score}
              onChange={(e) => setSettings({ ...settings, min_confidence_score: Number(e.target.value) })}
              className="w-full accent-blue-600 cursor-pointer"
            />
            <span className="text-[10px] text-slate-400 block font-normal">Reject setups below confidence score.</span>
          </div>

          <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
            <label className="text-xs text-slate-600 font-semibold block">
              Min Risk/Reward Ratio:
            </label>
            <select
              value={String(Number(settings.min_risk_reward_ratio || 1.5).toFixed(1))}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setSettings((prev) => ({ ...prev, min_risk_reward_ratio: val }));
              }}
              className="w-full bg-slate-50 text-slate-900 border border-slate-200 rounded-lg p-2 text-xs font-semibold focus:outline-none focus:border-blue-600 cursor-pointer"
            >
              <option value="1.0">1 : 1.0 Minimum</option>
              <option value="1.5">1 : 1.5 Minimum (Recommended)</option>
              <option value="2.0">1 : 2.0 Minimum</option>
              <option value="2.5">1 : 2.5 Minimum</option>
              <option value="3.0">1 : 3.0 Minimum</option>
            </select>
            <span className="text-[10px] text-slate-400 block font-normal">Filter setups below R:R ratio.</span>
          </div>

          <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200 flex flex-col justify-between">
            <label className="text-xs text-slate-600 font-semibold block">
              AI Rule Explanation:
            </label>
            <button
              type="button"
              onClick={() => setSettings({ ...settings, include_ai_explanation: !settings.include_ai_explanation })}
              className={`w-full py-1.5 px-2.5 text-xs font-semibold rounded-lg border transition ${
                settings.include_ai_explanation
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-slate-50 text-slate-500 border-slate-200"
              }`}
            >
              {settings.include_ai_explanation ? "✓ Full AI Explanation" : "Short Summary Only"}
            </button>
            <span className="text-[10px] text-slate-400 block font-normal">Generate institutional breakdown.</span>
          </div>
        </div>
      </div>

      {/* Save Action */}
      <div className="flex items-center justify-between pt-1">
        <button
          onClick={handleSaveSettings}
          disabled={saving}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition shadow-xs flex items-center gap-2"
        >
          {saving ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>Save Bot Analysis & Risk Parameters</span>
            </>
          )}
        </button>

        {successMsg && (
          <span className="text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
            {successMsg}
          </span>
        )}
      </div>
    </div>
  );
}
