"use client";

import React, { useState, useEffect, useCallback } from "react";
import { API_BASE, safeFetch } from "./utils/api";
import Sidebar from "./components/Sidebar";
import StatCardsRow from "./components/StatCardsRow";
import ActiveStrategyCard from "./components/ActiveStrategyCard";
import TradingViewChart from "./components/TradingViewChart";
import SignalPanel from "./components/SignalPanel";
import BacktestPanel from "./components/BacktestPanel";
import StrategyBuilder from "./components/StrategyBuilder";
import TelegramAlertsPanel from "./components/TelegramAlertsPanel";
import SettingsPage from "./components/SettingsPage";
import OmniEnginePanel from "./components/OmniEnginePanel";
import DashboardBottomWorkspace from "./components/DashboardBottomWorkspace";
import { useAuth } from "./context/AuthContext";
import { Calendar } from "lucide-react";

export default function DashboardPage() {
  const { user, isAuthenticated, openAuthModal, openProfileModal } = useAuth();
  const [selectedSymbol, setSelectedSymbol] = useState("XAU/USD");
  const [selectedTimeframe, setSelectedTimeframe] = useState("5m");
  const [symbols, setSymbols] = useState<any[]>([]);
  const [chartInfo, setChartInfo] = useState<any>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const [activeSignal, setActiveSignal] = useState<any>(null);
  const [backtestReport, setBacktestReport] = useState<any>(null);
  const [loadingSignal, setLoadingSignal] = useState(false);
  const [loadingBacktest, setLoadingBacktest] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  // Fetch supported symbols once on mount
  useEffect(() => {
    safeFetch(`${API_BASE}/api/market/symbols`)
      .then((r) => r.json())
      .then((d) => { if (d.symbols) setSymbols(d.symbols); })
      .catch(() => {});
  }, []);

  // Fetch chart info and candles stably
  const loadMarketData = useCallback((sym: string, tf: string) => {
    safeFetch(`${API_BASE}/api/market/chart-info?symbol=${encodeURIComponent(sym)}`)
      .then((r) => r.json()).then(setChartInfo).catch(() => {});
    safeFetch(`${API_BASE}/api/market/candles?symbol=${encodeURIComponent(sym)}&timeframe=${tf}&limit=100`)
      .then((r) => r.json())
      .then((d) => { if (d.candles) setCandles(d.candles); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadMarketData(selectedSymbol, selectedTimeframe);
    const t = setInterval(() => {
      loadMarketData(selectedSymbol, selectedTimeframe);
    }, 4000);
    return () => clearInterval(t);
  }, [selectedSymbol, selectedTimeframe, loadMarketData]);

  const handleGenerateSignal = useCallback(() => {
    setLoadingSignal(true);
    safeFetch(`${API_BASE}/api/signals/generate?symbol=${encodeURIComponent(selectedSymbol)}`, { method: "POST" })
      .then((r) => r.json()).then(setActiveSignal).catch(() => {})
      .finally(() => setLoadingSignal(false));
  }, [selectedSymbol]);

  const handleRunBacktest = useCallback(() => {
    setLoadingBacktest(true);
    safeFetch(`${API_BASE}/api/backtest/run?symbol=${encodeURIComponent(selectedSymbol)}&timeframe=${selectedTimeframe}&limit=300`, { method: "POST" })
      .then((r) => r.json()).then(setBacktestReport).catch(() => {})
      .finally(() => setLoadingBacktest(false));
  }, [selectedSymbol, selectedTimeframe]);


  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ background: "var(--bg)" }}
    >
      {/* Icon rail sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main scroll area */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        {/* Top header */}
        <header
          className="flex items-center justify-between px-5 py-3 shrink-0 sticky top-0 z-20"
          style={{
            background: "var(--bg-elevated)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          {/* Left: breadcrumb / page name */}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-faint)" }}>TradeGod</span>
              <span style={{ color: "var(--border)" }}>/</span>
              <span className="text-xs font-semibold capitalize" style={{ color: "var(--text)" }}>
                {activeTab === "dashboard" ? "Terminal" : activeTab}
              </span>
            </div>
            {activeTab === "dashboard" && (
              <p className="text-[11px] mt-0.5" style={{ color: "var(--text-faint)" }}>
                {selectedSymbol} · Live quantitative signal engine
              </p>
            )}
          </div>

          {/* Right: date + user */}
          <div className="flex items-center gap-2.5">
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{
                background: "var(--bg-subtle)",
                border: "1px solid var(--border)",
                color: "var(--text-muted)"
              }}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>{new Date().toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })}</span>
            </div>

            {isAuthenticated && user ? (
              <button
                onClick={openProfileModal}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition"
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border)",
                  color: "var(--text)"
                }}
              >
                <img
                  src={user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=2563eb&color=fff&size=32`}
                  alt={user.full_name}
                  className="w-5 h-5 rounded-md object-cover"
                />
                <span className="text-xs font-semibold hidden sm:block">{user.full_name}</span>
              </button>
            ) : (
              <button
                onClick={() => openAuthModal("login")}
                className="btn btn-primary"
                style={{ fontSize: "12px", padding: "5px 14px" }}
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Content area */}
        <div className="flex-1 p-4 lg:p-5 space-y-4">

          {/* ── DASHBOARD ──────────────────────────────────── */}
          {activeTab === "dashboard" && (
            <div className="space-y-4">
              {/* KPI strip */}
              <StatCardsRow lastPrice={chartInfo?.last_price} symbol={selectedSymbol} />

              {/* Main 2-column grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
                {/* Left: Chart + tabbed workspace */}
                <div className="lg:col-span-2 flex flex-col gap-4">
                  <TradingViewChart
                    candles={candles}
                    symbol={selectedSymbol}
                    symbols={symbols}
                    timeframe={selectedTimeframe}
                    onSelectSymbol={setSelectedSymbol}
                    onSelectTimeframe={setSelectedTimeframe}
                    signalPriceLines={
                      activeSignal ? {
                        entry: activeSignal.entry_price,
                        stopLoss: activeSignal.stop_loss,
                        takeProfit1: activeSignal.take_profit_1,
                        takeProfit2: activeSignal.take_profit_2
                      } : undefined
                    }
                  />
                  <DashboardBottomWorkspace
                    backtestReport={backtestReport}
                    onRunBacktest={handleRunBacktest}
                    loadingBacktest={loadingBacktest}
                  />
                </div>

                {/* Right: Signal + Strategy */}
                <div className="lg:col-span-1 flex flex-col gap-4">
                  <SignalPanel
                    signal={activeSignal}
                    selectedSymbol={selectedSymbol}
                    selectedTimeframe={selectedTimeframe}
                    onGenerateSignal={handleGenerateSignal}
                    loading={loadingSignal}
                  />
                  <ActiveStrategyCard />
                </div>
              </div>
            </div>
          )}

          {/* ── OMNI AI ENGINE ─────────────────────────────── */}
          {activeTab === "omni" && (
            <div className="space-y-4">
              <OmniEnginePanel
                selectedSymbol={selectedSymbol}
                selectedTimeframe={selectedTimeframe}
              />
            </div>
          )}

          {/* ── STRATEGY BUILDER ───────────────────────────── */}
          {activeTab === "strategy" && (
            <div className="space-y-4">
              <StrategyBuilder onStrategySaved={() => loadMarketData(selectedSymbol, selectedTimeframe)} />
            </div>
          )}

          {/* ── BACKTEST LAB ───────────────────────────────── */}
          {activeTab === "backtest" && (
            <div className="space-y-4">
              <BacktestPanel
                report={backtestReport}
                onRunBacktest={handleRunBacktest}
                loading={loadingBacktest}
              />
            </div>
          )}

          {/* ── TELEGRAM ───────────────────────────────────── */}
          {activeTab === "telegram" && (
            <div className="space-y-4">
              <TelegramAlertsPanel />
            </div>
          )}

          {/* ── SETTINGS ───────────────────────────────────── */}
          {activeTab === "settings" && (
            <div className="space-y-4">
              <SettingsPage />
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
