"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import {
  Brain,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Activity,
  Layers,
  Zap,
  Target,
  ShieldAlert,
  BarChart3,
  RefreshCw,
  Cpu,
  ArrowRight,
  Flame,
  CheckCircle2,
  AlertTriangle,
  Compass,
  Clock,
  Crosshair,
  ShieldCheck,
  Sliders,
  Bell,
  Save,
  Check,
  History,
  Trash2,
  DollarSign
} from "lucide-react";

interface OmniEnginePanelProps {
  selectedSymbol?: string;
  selectedTimeframe?: string;
}

export default function OmniEnginePanel({
  selectedSymbol = "XAU/USD",
  selectedTimeframe = "5m"
}: OmniEnginePanelProps) {
  const [matrix, setMatrix] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [forecastHistory, setForecastHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [learningStats, setLearningStats] = useState<any>(null);
  const [loadingMatrix, setLoadingMatrix] = useState(false);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [tuning, setTuning] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<"forecast" | "forecastHistory" | "preferences" | "sweeps" | "choch" | "matrix" | "learning">("forecast");
  const [tuningMsg, setTuningMsg] = useState("");

  // User Preferences State
  const [prefs, setPrefs] = useState({
    preferred_lot_size: 0.10,
    min_profit_pips: 30.0,
    max_risk_percent: 2.0,
    min_confidence_score: 75,
    min_risk_reward_ratio: 1.5,
    entry_preference: "AI_ADAPTIVE",
    bot_active: true,
    telegram_notifications: true,
    notify_on_news_blackout: true,
    max_positions: 3,
    scan_interval_seconds: 15
  });
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSavedMsg, setPrefsSavedMsg] = useState("");

  const fetchPreferences = () => {
    safeFetch(`${API_BASE}/api/omni/preferences`)
      .then((r) => r.json())
      .then((d) => { if (d && d.preferred_lot_size !== undefined) setPrefs(d); })
      .catch(() => {});
  };

  const handleSavePreferences = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSavingPrefs(true);
    setPrefsSavedMsg("");
    try {
      const res = await safeFetch(`${API_BASE}/api/omni/preferences`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs)
      });
      if (res.ok) {
        setPrefsSavedMsg("Preferences saved & synchronized with Omni Engine!");
        setTimeout(() => setPrefsSavedMsg(""), 4000);
      }
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setSavingPrefs(false);
    }
  };

  const fetchMatrix = () => {
    setLoadingMatrix(true);
    safeFetch(`${API_BASE}/api/omni/market-matrix?symbol=${encodeURIComponent(selectedSymbol)}&timeframe=${encodeURIComponent(selectedTimeframe)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data && !data.detail) setMatrix(data);
      })
      .catch((err) => console.warn("Error fetching Omni matrix:", err))
      .finally(() => setLoadingMatrix(false));
  };

  const fetchForecastHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await safeFetch(`${API_BASE}/api/omni/forecasts/history`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setForecastHistory(data);
      }
    } catch (err) {
      console.warn("Error fetching forecast history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteForecast = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await safeFetch(`${API_BASE}/api/omni/forecasts/history/${id}`, { method: "DELETE" });
      setForecastHistory(forecastHistory.filter((f) => f.id !== id));
    } catch (err) {
      console.error("Failed to delete forecast:", err);
    }
  };

  const handleClearForecastHistory = async () => {
    if (!confirm("Are you sure you want to clear all AI forecast projection history?")) return;
    try {
      await safeFetch(`${API_BASE}/api/omni/forecasts/history`, { method: "DELETE" });
      setForecastHistory([]);
    } catch (err) {
      console.error("Failed to clear forecast history:", err);
    }
  };

  const fetchLearningStats = () => {
    safeFetch(`${API_BASE}/api/omni/learning-stats`)
      .then((res) => res.json())
      .then((data) => {
        if (data) setLearningStats(data);
      })
      .catch((err) => console.warn("Error fetching learning stats:", err));
  };

  const handlePredictFutureTrade = () => {
    setLoadingForecast(true);
    safeFetch(`${API_BASE}/api/omni/predict?symbol=${encodeURIComponent(selectedSymbol)}&timeframe=${encodeURIComponent(selectedTimeframe)}`, {
      method: "POST"
    })
      .then((res) => res.json())
      .then((data) => {
        if (data && !data.detail) {
          setForecast(data);
          setActiveSubTab("forecast");
          fetchForecastHistory();
        }
      })
      .catch((err) => console.error("Error predicting future trade:", err))
      .finally(() => setLoadingForecast(false));
  };

  const handleSelfUpdateTuning = () => {
    setTuning(true);
    setTuningMsg("");
    safeFetch(`${API_BASE}/api/omni/self-update`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => {
        setTuningMsg(data.message || "Autonomous parameter self-tuning completed!");
        fetchLearningStats();
      })
      .catch((err) => console.error("Error self-tuning:", err))
      .finally(() => setTuning(false));
  };

  useEffect(() => {
    fetchMatrix();
    fetchLearningStats();
    fetchPreferences();
    fetchForecastHistory();
  }, [selectedSymbol, selectedTimeframe]);

  const radar = matrix?.matrix_radar || { trend: 85, volume: 80, momentum: 75, structure: 88, volatility: 65 };

  // Calculated preview of expected return based on lot size and min pips
  const estimatedMinReturnUSD = (prefs.min_profit_pips * 0.1 * prefs.preferred_lot_size * 100.0).toFixed(2);

  return (
    <div className="card p-5 lg:p-6 space-y-6">
      {/* Header Bar */}
      <div
        className="flex flex-wrap items-center justify-between gap-4 pb-5"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center space-x-3.5">
          <div
            className="w-11 h-11 rounded-2xl flex items-center justify-center shadow-sm shrink-0"
            style={{
              background: "linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #06b6d4 100%)",
              color: "white"
            }}
          >
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold tracking-tight" style={{ color: "var(--text)" }}>
                Omni AI Unified Engine
              </h2>
              <span className="badge badge-blue text-[10px]">
                <span className="live-dot" style={{ width: "5px", height: "5px" }} />
                {prefs.bot_active ? "AUTO-SCANNING ACTIVE" : "BOT PAUSED"}
              </span>
            </div>
            <p className="text-xs font-medium mt-0.5" style={{ color: "var(--text-muted)" }}>
              Vision, Reachability Analysis, Custom Profit Targets, Forecast History & Bayesian Learning.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={fetchMatrix}
            disabled={loadingMatrix}
            className="btn btn-ghost text-xs px-3 py-2"
            title="Refresh Live Market Matrix"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingMatrix ? "animate-spin text-blue-500" : ""}`} />
            <span>Sync Matrix</span>
          </button>

          <button
            onClick={handlePredictFutureTrade}
            disabled={loadingForecast}
            className="btn btn-primary text-xs font-bold px-4 py-2 shadow-xs"
          >
            {loadingForecast ? (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Forecast Future Trade</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Modern Sub-Navigation Tabs */}
      <div
        className="flex flex-wrap items-center gap-1.5 p-1.5 rounded-xl border"
        style={{
          background: "var(--bg-subtle)",
          borderColor: "var(--border)"
        }}
      >
        {[
          { id: "forecast",        label: "AI Trade Forecast",                icon: Target },
          { id: "forecastHistory", label: `Forecast History (${forecastHistory.length})`, icon: History },
          { id: "preferences",     label: "Preferences & Targets",           icon: Sliders },
          { id: "sweeps",          label: "Session Sweeps & S/R",            icon: Crosshair },
          { id: "choch",           label: "CHoCH Transitions",               icon: Activity },
          { id: "matrix",          label: "C2C & Inversion FVGs",            icon: Layers },
          { id: "learning",        label: "Self-Learning Hub",               icon: Cpu }
        ].map(({ id, label, icon: Icon }) => {
          const isActive = activeSubTab === id;
          return (
            <button
              key={id}
              onClick={() => {
                setActiveSubTab(id as any);
                if (id === "forecastHistory") fetchForecastHistory();
              }}
              className="flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer"
              style={{
                background: isActive ? "var(--bg-elevated)" : "transparent",
                color: isActive ? "var(--accent)" : "var(--text-muted)",
                border: isActive ? "1px solid var(--border)" : "1px solid transparent",
                boxShadow: isActive ? "var(--shadow-sm)" : "none"
              }}
            >
              <Icon className="w-3.5 h-3.5" style={{ color: isActive ? "var(--accent)" : "var(--text-faint)" }} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      {/* ── 1. AI Future Trade Forecast View ──────────────── */}
      {activeSubTab === "forecast" && (
        <div className="space-y-6">
          {forecast ? (
            <div
              className="rounded-2xl p-6 border space-y-5 shadow-xs"
              style={{
                background: "var(--bg-elevated)",
                borderColor: "var(--border)"
              }}
            >
              {/* Forecast Header */}
              <div
                className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b"
                style={{ borderColor: "var(--border)" }}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center font-bold"
                    style={{
                      background:
                        forecast.primary_direction === "BUY"
                          ? "var(--green-soft)"
                          : forecast.primary_direction === "SELL"
                          ? "var(--red-soft)"
                          : "var(--gold-soft)",
                      color:
                        forecast.primary_direction === "BUY"
                          ? "var(--green)"
                          : forecast.primary_direction === "SELL"
                          ? "var(--red)"
                          : "var(--gold)"
                    }}
                  >
                    {forecast.primary_direction === "BUY" ? (
                      <TrendingUp className="w-5 h-5" />
                    ) : forecast.primary_direction === "SELL" ? (
                      <TrendingDown className="w-5 h-5" />
                    ) : (
                      <Activity className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider block" style={{ color: "var(--text-faint)" }}>
                      AI Projected Trade
                    </span>
                    <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: "var(--text)" }}>
                      <span>{forecast.symbol} {forecast.primary_direction}</span>
                      <span className="badge badge-blue">
                        {forecast.timeframe.toUpperCase()} Timeframe
                      </span>
                    </h3>
                  </div>
                </div>

                {/* Win Probability & Reachability */}
                <div className="text-right flex items-center gap-4">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider block" style={{ color: "var(--text-faint)" }}>
                      Entry Reachability
                    </span>
                    <span className="badge badge-green mt-1 text-xs font-bold">
                      ⚡ {forecast.entry_reachability_percent || 96}% Feasibility
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider block" style={{ color: "var(--text-faint)" }}>
                      Win Probability
                    </span>
                    <div className="flex items-center justify-end gap-2 mt-0.5">
                      <span className="text-2xl font-bold font-mono" style={{ color: "var(--accent)" }}>
                        {forecast.win_probability_percent}%
                      </span>
                      <span className="badge badge-green">
                        1:{forecast.risk_reward_ratio} R:R
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Price Targets Grid with User Preferences */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div
                  className="rounded-xl p-3.5 border"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
                >
                  <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                    Target Entry
                  </span>
                  <span className="text-sm font-bold font-mono block mt-1" style={{ color: "var(--text)" }}>
                    ${forecast.entry_zone.ideal}
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--green)" }}>
                    {forecast.entry_reachability_state === "INSTANT_MARKET_FILL" ? "⚡ Live Spot Fill" : `🎯 Pullback (${forecast.entry_distance_pips} pips)`}
                  </span>
                </div>

                <div
                  className="rounded-xl p-3.5 border"
                  style={{
                    background: "var(--red-soft)",
                    borderColor: "color-mix(in srgb, var(--red) 25%, transparent)"
                  }}
                >
                  <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--red)" }}>
                    Stop Loss (SL)
                  </span>
                  <span className="text-sm font-bold font-mono block mt-1" style={{ color: "var(--red)" }}>
                    ${forecast.stop_loss}
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--red)" }}>
                    Structure + ATR Buffer
                  </span>
                </div>

                <div
                  className="rounded-xl p-3.5 border"
                  style={{
                    background: "var(--green-soft)",
                    borderColor: "color-mix(in srgb, var(--green) 25%, transparent)"
                  }}
                >
                  <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--green)" }}>
                    Take Profit 1
                  </span>
                  <span className="text-sm font-bold font-mono block mt-1" style={{ color: "var(--green)" }}>
                    ${forecast.take_profit_1}
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--green)" }}>
                    Scale-out 50%
                  </span>
                </div>

                <div
                  className="rounded-xl p-3.5 border"
                  style={{
                    background: "var(--green-soft)",
                    borderColor: "color-mix(in srgb, var(--green) 35%, transparent)"
                  }}
                >
                  <span className="text-[10px] font-bold block uppercase" style={{ color: "var(--green)" }}>
                    Take Profit 2 ({forecast.expected_profit_pips} Pips)
                  </span>
                  <span className="text-sm font-bold font-mono block mt-1" style={{ color: "var(--green)" }}>
                    ${forecast.take_profit_2}
                  </span>
                  <span className="text-[10px] font-bold" style={{ color: "var(--green)" }}>
                    Est +${forecast.expected_profit_usd} ({forecast.position_size_lots} Lots)
                  </span>
                </div>
              </div>

              {/* Institutional Key Drivers */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" style={{ color: "var(--text)" }}>
                  <Sparkles className="w-3.5 h-3.5" style={{ color: "var(--gold)" }} />
                  <span>Market Confluence & Drivers</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {forecast.institutional_drivers.map((d: string, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center space-x-2 text-xs p-2.5 rounded-lg border"
                      style={{
                        background: "var(--bg-subtle)",
                        borderColor: "var(--border)",
                        color: "var(--text)"
                      }}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: "var(--green)" }} />
                      <span className="font-medium">{d}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Invalidation Alert */}
              <div
                className="p-3 rounded-xl text-xs flex items-start space-x-2.5 border"
                style={{
                  background: "var(--gold-soft)",
                  borderColor: "color-mix(in srgb, var(--gold) 30%, transparent)",
                  color: "var(--gold)"
                }}
              >
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" style={{ color: "var(--gold)" }} />
                <div>
                  <span className="font-bold">Trade Invalidation Criteria: </span>
                  <span style={{ color: "var(--text)" }}>{forecast.invalidation_criteria}</span>
                </div>
              </div>
            </div>
          ) : (
            /* Empty State */
            <div
              className="text-center py-16 px-6 rounded-2xl border space-y-4"
              style={{
                background: "var(--bg-elevated)",
                borderColor: "var(--border)"
              }}
            >
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto border shadow-xs"
                style={{
                  background: "var(--bg-subtle)",
                  borderColor: "var(--border)"
                }}
              >
                <Sparkles className="w-7 h-7" style={{ color: "var(--accent)" }} />
              </div>
              <div>
                <h4 className="text-base font-bold" style={{ color: "var(--text)" }}>
                  No Active Forecast Generated
                </h4>
                <p className="text-xs max-w-md mx-auto mt-1 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  Click <strong>"Forecast Future Trade"</strong> or browse past predictions in the <strong>Forecast History</strong> tab.
                </p>
              </div>
              <button
                onClick={handlePredictFutureTrade}
                disabled={loadingForecast}
                className="btn btn-primary text-xs font-bold px-6 py-2.5 shadow-xs"
              >
                {loadingForecast ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Run Predictive Trade Synthesis</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── 2. AI Trade Forecast History Sub-Tab ──────────── */}
      {activeSubTab === "forecastHistory" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
              Saved AI Projections Log ({forecastHistory.length})
            </h4>
            {forecastHistory.length > 0 && (
              <button
                onClick={handleClearForecastHistory}
                className="btn btn-ghost text-xs text-rose-500 hover:text-rose-600 gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear History</span>
              </button>
            )}
          </div>

          {loadingHistory ? (
            <div className="py-12 flex justify-center items-center">
              <RefreshCw className="w-5 h-5 animate-spin" style={{ color: "var(--accent)" }} />
            </div>
          ) : forecastHistory.length > 0 ? (
            <div className="grid grid-cols-1 gap-3">
              {forecastHistory.map((fh) => {
                const isBuy = fh.primary_direction === "BUY";
                return (
                  <div
                    key={fh.id}
                    onClick={() => {
                      setForecast({
                        ...fh,
                        entry_zone: { ideal: fh.entry_market_price, min: fh.entry_market_price, max: fh.entry_market_price }
                      });
                      setActiveSubTab("forecast");
                    }}
                    className="p-4 rounded-xl border flex flex-wrap items-center justify-between gap-4 transition hover:border-blue-500/50 cursor-pointer"
                    style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
                  >
                    <div className="flex items-center space-x-3.5">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs"
                        style={{
                          background: isBuy ? "var(--green-soft)" : "var(--red-soft)",
                          color: isBuy ? "var(--green)" : "var(--red)"
                        }}
                      >
                        {isBuy ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs" style={{ color: "var(--text)" }}>
                            {fh.symbol} · {fh.primary_direction}
                          </span>
                          <span className="badge badge-blue text-[10px]">
                            {fh.timeframe.toUpperCase()}
                          </span>
                          <span className="badge badge-green text-[10px]">
                            {fh.entry_reachability_percent || 95}% Reachable
                          </span>
                        </div>
                        <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                          {new Date(fh.created_at).toLocaleString()} • {fh.market_regime}
                        </span>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-4 text-xs font-mono">
                      <div className="text-right">
                        <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Entry</span>
                        <strong style={{ color: "var(--accent)" }}>${fh.entry_market_price}</strong>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>TP2 / Pips</span>
                        <strong style={{ color: "var(--green)" }}>${fh.take_profit_2} ({fh.expected_profit_pips}p)</strong>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Win Prob</span>
                        <strong style={{ color: "var(--accent)" }}>{fh.win_probability_percent}%</strong>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Est USD</span>
                        <strong style={{ color: "var(--green)" }}>+${fh.expected_profit_usd}</strong>
                      </div>

                      <button
                        onClick={(e) => handleDeleteForecast(fh.id, e)}
                        className="p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-500 transition cursor-pointer"
                        title="Delete forecast"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div
              className="text-center py-12 rounded-xl border text-xs"
              style={{ background: "var(--bg-subtle)", borderColor: "var(--border)", color: "var(--text-muted)" }}
            >
              No AI trade projections saved yet. Click <strong>"Forecast Future Trade"</strong> to generate one.
            </div>
          )}
        </div>
      )}

      {/* ── 3. User Preferences & Bot Controls Sub-Tab ─────── */}
      {activeSubTab === "preferences" && (
        <form onSubmit={handleSavePreferences} className="space-y-6">
          <div
            className="rounded-2xl p-5 border space-y-5"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: "var(--border)" }}>
              <div>
                <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: "var(--text)" }}>
                  <Sliders className="w-4 h-4" style={{ color: "var(--accent)" }} />
                  Omni User Trading Preferences & Auto-Scan Config
                </h3>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                  Customize minimum profit pips, preferred lot sizes, risk controls, and automated Telegram broadcasting.
                </p>
              </div>
              <button
                type="submit"
                disabled={savingPrefs}
                className="btn btn-primary text-xs font-bold px-4 py-2 flex items-center gap-2"
              >
                {savingPrefs ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Preferences</span>
                  </>
                )}
              </button>
            </div>

            {prefsSavedMsg && (
              <div
                className="p-3 rounded-xl text-xs font-semibold flex items-center gap-2 border"
                style={{
                  background: "var(--green-soft)",
                  borderColor: "color-mix(in srgb, var(--green) 30%, transparent)",
                  color: "var(--green)"
                }}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{prefsSavedMsg}</span>
              </div>
            )}

            {/* Live Calculation Preview Banner */}
            <div
              className="p-4 rounded-xl border flex flex-wrap items-center justify-between gap-3"
              style={{ background: "rgba(37,99,235,0.06)", borderColor: "rgba(37,99,235,0.18)" }}
            >
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5" style={{ color: "var(--accent)" }} />
                <div>
                  <span className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                    Target Return Calculation Preview
                  </span>
                  <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                    At <strong>{prefs.preferred_lot_size} Lots</strong> and min <strong>{prefs.min_profit_pips} Pips</strong> profit:
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-base font-bold font-mono" style={{ color: "var(--green)" }}>
                  Est. +${estimatedMinReturnUSD} USD / trade
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* 1. Preferred Lot Size */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  📦 Preferred Lot Size
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="50.0"
                  value={prefs.preferred_lot_size}
                  onChange={(e) => setPrefs({ ...prefs, preferred_lot_size: parseFloat(e.target.value) || 0.01 })}
                  className="input w-full font-mono font-bold text-sm"
                />
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Position size applied to future signals & bot executions.
                </p>
              </div>

              {/* 2. Min Profit in Pips */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  🎯 Minimum Target Profit (Pips)
                </label>
                <input
                  type="number"
                  step="1"
                  min="5"
                  max="1000"
                  value={prefs.min_profit_pips}
                  onChange={(e) => setPrefs({ ...prefs, min_profit_pips: parseFloat(e.target.value) || 10 })}
                  className="input w-full font-mono font-bold text-sm"
                />
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Guarantees Take Profit targets yield at least this distance in pips.
                </p>
              </div>

              {/* 3. Max Risk % per Trade */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  🛡️ Max Risk per Trade (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10.0"
                  value={prefs.max_risk_percent}
                  onChange={(e) => setPrefs({ ...prefs, max_risk_percent: parseFloat(e.target.value) || 1.0 })}
                  className="input w-full font-mono font-bold text-sm"
                />
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Stop loss risk cap calculated against total portfolio equity.
                </p>
              </div>

              {/* 4. Min Confidence Threshold */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  🧠 Min AI Confidence Rating (%)
                </label>
                <input
                  type="number"
                  step="1"
                  min="50"
                  max="99"
                  value={prefs.min_confidence_score}
                  onChange={(e) => setPrefs({ ...prefs, min_confidence_score: parseInt(e.target.value) || 75 })}
                  className="input w-full font-mono font-bold text-sm"
                />
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Signals below this score are suppressed as near-misses.
                </p>
              </div>

              {/* 5. Entry Execution Preference */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  ⚡ Entry Execution Style
                </label>
                <select
                  value={prefs.entry_preference}
                  onChange={(e) => setPrefs({ ...prefs, entry_preference: e.target.value })}
                  className="input w-full text-xs font-bold cursor-pointer"
                >
                  <option value="INSTANT_MARKET">⚡ Instant Market Fill (Guaranteed Fill)</option>
                  <option value="SNIPER_PULLBACK">🎯 Sniper Pullback Limit (Discount)</option>
                  <option value="AI_ADAPTIVE">🤖 AI Adaptive (Dynamic Momentum)</option>
                </select>
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Determines whether signals default to immediate spot or limit pullback.
                </p>
              </div>

              {/* 6. Auto-Scan Bot Loop Toggle */}
              <div className="p-4 rounded-xl border space-y-2" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <label className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                  🔄 Autonomous Background Scanning
                </label>
                <button
                  type="button"
                  onClick={() => setPrefs({ ...prefs, bot_active: !prefs.bot_active })}
                  className="btn w-full py-2 text-xs font-bold justify-center"
                  style={{
                    background: prefs.bot_active ? "var(--green-soft)" : "var(--bg-elevated)",
                    color: prefs.bot_active ? "var(--green)" : "var(--text-muted)",
                    border: "1px solid var(--border)"
                  }}
                >
                  <span className="live-dot" style={{ background: prefs.bot_active ? "var(--green)" : "var(--text-faint)" }} />
                  <span>{prefs.bot_active ? "Autonomous Scanning Active" : "Scanning Paused"}</span>
                </button>
                <p className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                  Continuously scans market matrix every 15s in the background.
                </p>
              </div>
            </div>

            {/* Telegram & News Blackout Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t" style={{ borderColor: "var(--border)" }}>
              <label className="flex items-center gap-3 p-3 rounded-xl border cursor-pointer" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <input
                  type="checkbox"
                  checked={prefs.telegram_notifications}
                  onChange={(e) => setPrefs({ ...prefs, telegram_notifications: e.target.checked })}
                  className="w-4 h-4 rounded text-blue-600 cursor-pointer"
                />
                <div>
                  <span className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                    Broadcast Signals to Telegram
                  </span>
                  <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                    Instantly push verified trade setups to your connected Telegram channel.
                  </span>
                </div>
              </label>

              <label className="flex items-center gap-3 p-3 rounded-xl border cursor-pointer" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <input
                  type="checkbox"
                  checked={prefs.notify_on_news_blackout}
                  onChange={(e) => setPrefs({ ...prefs, notify_on_news_blackout: e.target.checked })}
                  className="w-4 h-4 rounded text-blue-600 cursor-pointer"
                />
                <div>
                  <span className="text-xs font-bold block" style={{ color: "var(--text)" }}>
                    High-Impact News Blackout Shield
                  </span>
                  <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                    Automatically suppress new trades ±15 mins around CPI, NFP & FOMC.
                  </span>
                </div>
              </label>
            </div>
          </div>
        </form>
      )}

      {/* ── 4. Session Sweeps & S/R View ───────────────────── */}
      {activeSubTab === "sweeps" && matrix && (
        <div className="space-y-6">
          <div
            className="rounded-2xl p-5 border space-y-4"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <div
              className="flex items-center justify-between pb-3 border-b"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-center space-x-2.5">
                <Clock className="w-4 h-4" style={{ color: "var(--accent)" }} />
                <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
                  Session Liquidity Levels & Sweeps (Judas Swings)
                </h4>
              </div>
              <span className={`badge ${
                matrix.session_sweeps.liquidity_bias === "bullish_reversal_sweep"
                  ? "badge-green"
                  : matrix.session_sweeps.liquidity_bias === "bearish_reversal_sweep"
                  ? "badge-red"
                  : "badge-muted"
              }`}>
                {matrix.session_sweeps.liquidity_bias.replace("_", " ").toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                  Asian Session (00-08 UTC)
                </span>
                <span className="font-mono font-bold mt-1 block" style={{ color: "var(--text)" }}>
                  High: ${matrix.session_sweeps.asian_high} | Low: ${matrix.session_sweeps.asian_low}
                </span>
              </div>

              <div className="p-3 rounded-xl border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                  London Session (08-13 UTC)
                </span>
                <span className="font-mono font-bold mt-1 block" style={{ color: "var(--text)" }}>
                  High: ${matrix.session_sweeps.london_high} | Low: ${matrix.session_sweeps.london_low}
                </span>
              </div>

              <div className="p-3 rounded-xl border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                  Previous Day (PDH / PDL)
                </span>
                <span className="font-mono font-bold mt-1 block" style={{ color: "var(--text)" }}>
                  PDH: ${matrix.session_sweeps.prev_day_high} | PDL: ${matrix.session_sweeps.prev_day_low}
                </span>
              </div>
            </div>

            <div
              className="p-3 rounded-xl text-xs flex items-start space-x-2 border"
              style={{
                background: "rgba(37,99,235,0.08)",
                borderColor: "rgba(37,99,235,0.2)",
                color: "var(--text)"
              }}
            >
              <Compass className="w-4 h-4 shrink-0 mt-0.5" style={{ color: "var(--accent)" }} />
              <span><strong>Sweep Analysis:</strong> {matrix.session_sweeps.sweep_summary}</span>
            </div>
          </div>

          {/* S/R Price Action & Behavior */}
          <div
            className="rounded-2xl p-5 border space-y-4"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <div
              className="flex items-center justify-between pb-3 border-b"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-center space-x-2.5">
                <Crosshair className="w-4 h-4" style={{ color: "var(--accent)" }} />
                <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
                  Support & Resistance Price Behavior Analysis
                </h4>
              </div>
              <span className="text-xs font-bold" style={{ color: "var(--text-muted)" }}>
                {matrix.sr_price_behavior.active_levels_count} Key Levels Active
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {matrix.sr_price_behavior.nearest_resistance ? (
                <div
                  className="p-3.5 rounded-xl border space-y-2"
                  style={{
                    background: "var(--red-soft)",
                    borderColor: "color-mix(in srgb, var(--red) 25%, transparent)"
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase" style={{ color: "var(--red)" }}>
                      Overhead Resistance (${matrix.sr_price_behavior.nearest_resistance.level_price})
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold" style={{ background: "var(--red-soft)", color: "var(--red)" }}>
                      {matrix.sr_price_behavior.nearest_resistance.behavior}
                    </span>
                  </div>
                  <p className="text-xs font-medium" style={{ color: "var(--text)" }}>
                    {matrix.sr_price_behavior.nearest_resistance.description}
                  </p>
                  <span className="text-[10px] block" style={{ color: "var(--text-faint)" }}>
                    {matrix.sr_price_behavior.nearest_resistance.touches_history} historical touches • {matrix.sr_price_behavior.nearest_resistance.distance_pips} pips away
                  </span>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl border text-xs" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)", color: "var(--text-faint)" }}>
                  No immediate overhead resistance within range.
                </div>
              )}

              {matrix.sr_price_behavior.nearest_support ? (
                <div
                  className="p-3.5 rounded-xl border space-y-2"
                  style={{
                    background: "var(--green-soft)",
                    borderColor: "color-mix(in srgb, var(--green) 25%, transparent)"
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase" style={{ color: "var(--green)" }}>
                      Base Support (${matrix.sr_price_behavior.nearest_support.level_price})
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold" style={{ background: "var(--green-soft)", color: "var(--green)" }}>
                      {matrix.sr_price_behavior.nearest_support.behavior}
                    </span>
                  </div>
                  <p className="text-xs font-medium" style={{ color: "var(--text)" }}>
                    {matrix.sr_price_behavior.nearest_support.description}
                  </p>
                  <span className="text-[10px] block" style={{ color: "var(--text-faint)" }}>
                    {matrix.sr_price_behavior.nearest_support.touches_history} historical touches • {matrix.sr_price_behavior.nearest_support.distance_pips} pips away
                  </span>
                </div>
              ) : (
                <div className="p-3.5 rounded-xl border text-xs" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)", color: "var(--text-faint)" }}>
                  No immediate base support within range.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── 5. CHoCH Trend Transition View ─────────────────── */}
      {activeSubTab === "choch" && matrix?.choch_report && (
        <div className="space-y-5">
          <div
            className="p-4 rounded-xl border flex items-center justify-between"
            style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center space-x-3">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold ${
                matrix.choch_report.choch_risk_level === "LOW"
                  ? "badge-green"
                  : matrix.choch_report.choch_risk_level === "ELEVATED"
                  ? "badge-gold"
                  : "badge-red"
              }`}>
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                  Market Structure Regime
                </span>
                <h4 className="text-xs font-bold uppercase" style={{ color: "var(--text)" }}>
                  {matrix.choch_report.current_regime.replace("_", " ")} — CHoCH Risk: {matrix.choch_report.choch_risk_level}
                </h4>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                Key Reversal Trigger
              </span>
              <span className="text-xs font-bold font-mono" style={{ color: "var(--red)" }}>
                ${matrix.choch_report.key_reversal_trigger}
              </span>
            </div>
          </div>

          {/* Scenario Transition Probability Cards */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
              Market Transition Scenarios & Probability Distribution
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {matrix.choch_report.scenarios.map((sc: any, idx: number) => (
                <div
                  key={idx}
                  className="rounded-xl p-4 border space-y-2.5 flex flex-col justify-between"
                  style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
                >
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b" style={{ borderColor: "var(--border)" }}>
                      <h5 className="text-xs font-bold" style={{ color: "var(--text)" }}>{sc.name}</h5>
                      <span className="badge badge-blue font-mono font-bold">
                        {sc.probability_percent}%
                      </span>
                    </div>
                    <p className="text-[11px] font-medium mt-2 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                      {sc.description}
                    </p>
                  </div>

                  <div
                    className="pt-2 border-t text-[10px] flex items-center justify-between font-mono"
                    style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
                  >
                    <span>Trigger: <strong style={{ color: "var(--text)" }}>${sc.trigger_level}</strong></span>
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      sc.action_bias === "BUY" ? "badge-green" : sc.action_bias === "SELL" ? "badge-red" : "badge-muted"
                    }`}>
                      {sc.action_bias}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── 6. C2C & Inversion FVGs View ───────────────────── */}
      {activeSubTab === "matrix" && matrix && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: "Trend Confluence", val: radar.trend, color: "var(--accent)" },
              { label: "Volume Flow", val: radar.volume, color: "#818cf8" },
              { label: "C2C Momentum", val: radar.momentum, color: "var(--green)" },
              { label: "Structure & iFVGs", val: radar.structure, color: "var(--gold)" },
              { label: "Volatility Rank", val: radar.volatility, color: "var(--red)" }
            ].map(({ label, val, color }) => (
              <div
                key={label}
                className="rounded-xl p-3 border space-y-2"
                style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
              >
                <span className="text-[10px] font-semibold block uppercase truncate" style={{ color: "var(--text-faint)" }}>
                  {label}
                </span>
                <span className="text-lg font-bold font-mono block" style={{ color }}>
                  {val}/100
                </span>
                <div
                  className="w-full h-1.5 rounded-full overflow-hidden"
                  style={{ background: "var(--border)" }}
                >
                  <div className="h-full rounded-full transition-all" style={{ width: `${val}%`, background: color }} />
                </div>
              </div>
            ))}
          </div>

          <div
            className="rounded-xl p-4 border space-y-3"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" style={{ color: "var(--text)" }}>
              <Layers className="w-3.5 h-3.5" style={{ color: "var(--accent)" }} />
              <span>Inversion Fair Value Gaps (iFVG) & Standard FVGs</span>
            </h4>
            {matrix.inversion_fvgs && matrix.inversion_fvgs.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {matrix.inversion_fvgs.map((ifvg: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border"
                    style={{
                      background: "rgba(37,99,235,0.08)",
                      borderColor: "rgba(37,99,235,0.2)"
                    }}
                  >
                    <div className="flex items-center justify-between font-bold" style={{ color: "var(--text)" }}>
                      <span className="capitalize">{ifvg.fvg_type.replace("_", " ")}</span>
                      <span className="font-mono" style={{ color: "var(--accent)" }}>${ifvg.bottom_price} - ${ifvg.top_price}</span>
                    </div>
                    <p className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>{ifvg.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs" style={{ color: "var(--text-faint)" }}>
                No inverted FVGs active in immediate price neighborhood.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── 7. Self-Learning & Adaptive Hub View ────────────── */}
      {activeSubTab === "learning" && learningStats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="rounded-xl p-3.5 border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
              <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                Trades Evaluated
              </span>
              <span className="text-lg font-bold font-mono mt-1 block" style={{ color: "var(--text)" }}>
                {learningStats.total_trades_analyzed} Trades
              </span>
            </div>

            <div className="rounded-xl p-3.5 border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
              <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                Empirical Win Rate
              </span>
              <span className="text-lg font-bold font-mono mt-1 block" style={{ color: "var(--green)" }}>
                {learningStats.overall_win_rate}%
              </span>
            </div>

            <div className="rounded-xl p-3.5 border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
              <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                Tuning Generation
              </span>
              <span className="text-lg font-bold font-mono mt-1 block" style={{ color: "var(--accent)" }}>
                Gen {learningStats.active_adaptive_weights.tuning_generation}
              </span>
            </div>

            <div className="rounded-xl p-3.5 border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
              <span className="text-[10px] font-semibold block uppercase" style={{ color: "var(--text-faint)" }}>
                Adaptive ADX Gate
              </span>
              <span className="text-lg font-bold font-mono mt-1 block" style={{ color: "var(--gold)" }}>
                {learningStats.active_adaptive_weights.adx_gate_threshold.toFixed(1)}
              </span>
            </div>
          </div>

          {/* Active Adaptive Weights Display */}
          <div
            className="rounded-xl p-4 border space-y-3"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" style={{ color: "var(--text)" }}>
                <Cpu className="w-3.5 h-3.5" style={{ color: "var(--accent)" }} />
                <span>Active Strategy Auto-Tuned Weights</span>
              </h4>
              <button
                onClick={handleSelfUpdateTuning}
                disabled={tuning}
                className="btn btn-ghost text-xs px-3 py-1.5 gap-1.5"
              >
                <RefreshCw className={`w-3 h-3 ${tuning ? "animate-spin" : ""}`} />
                <span>Recalibrate Weights</span>
              </button>
            </div>

            {tuningMsg && (
              <div
                className="p-2.5 rounded-lg text-xs font-medium border"
                style={{
                  background: "var(--green-soft)",
                  borderColor: "color-mix(in srgb, var(--green) 25%, transparent)",
                  color: "var(--green)"
                }}
              >
                {tuningMsg}
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="block" style={{ color: "var(--text-faint)" }}>Rule Compliance:</span>
                <strong className="font-mono font-bold" style={{ color: "var(--text)" }}>{learningStats.active_adaptive_weights.rule_compliance_weight}%</strong>
              </div>
              <div className="p-3 rounded-lg border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="block" style={{ color: "var(--text-faint)" }}>Trend Alignment:</span>
                <strong className="font-mono font-bold" style={{ color: "var(--text)" }}>{learningStats.active_adaptive_weights.trend_alignment_weight}%</strong>
              </div>
              <div className="p-3 rounded-lg border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="block" style={{ color: "var(--text-faint)" }}>Structure Breakout:</span>
                <strong className="font-mono font-bold" style={{ color: "var(--text)" }}>{learningStats.active_adaptive_weights.structure_breakout_weight}%</strong>
              </div>
              <div className="p-3 rounded-lg border" style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}>
                <span className="block" style={{ color: "var(--text-faint)" }}>Volume Flow:</span>
                <strong className="font-mono font-bold" style={{ color: "var(--text)" }}>{learningStats.active_adaptive_weights.volume_flow_weight}%</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
