"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "./utils/api";
import Sidebar from "./components/Sidebar";
import StatCardsRow from "./components/StatCardsRow";
import ActiveStrategyCard from "./components/ActiveStrategyCard";
import ChartHeader from "./components/ChartHeader";
import TradingViewChart from "./components/TradingViewChart";
import SignalPanel from "./components/SignalPanel";
import BacktestPanel from "./components/BacktestPanel";
import StrategyBuilder from "./components/StrategyBuilder";
import BotControlPanel from "./components/BotControlPanel";
import TelegramAlertsPanel from "./components/TelegramAlertsPanel";
import SettingsPage from "./components/SettingsPage";
import PositionsTable from "./components/PositionsTable";
import NewsFilterWidget from "./components/NewsFilterWidget";
import { useAuth } from "./context/AuthContext";
import { Calendar, User as UserIcon } from "lucide-react";

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
  const [activeTab, setActiveTab] = useState<string>("dashboard");

  // Fetch supported symbols
  useEffect(() => {
    safeFetch(`${API_BASE}/api/market/symbols`)
      .then((res) => res.json())
      .then((data) => {
        if (data.symbols) setSymbols(data.symbols);
      })
      .catch((err) => console.log("API offline, fallback to defaults", err));
  }, []);

  // Fetch candles & chart info with live auto-refresh
  const loadMarketData = (sym: string, tf: string) => {
    safeFetch(`${API_BASE}/api/market/chart-info?symbol=${encodeURIComponent(sym)}`)
      .then((res) => res.json())
      .then((data) => setChartInfo(data))
      .catch((err) => console.warn("Chart info offline:", err));

    safeFetch(`${API_BASE}/api/market/candles?symbol=${encodeURIComponent(sym)}&timeframe=${encodeURIComponent(tf)}&limit=100&provider=yfinance`)
      .then((res) => res.json())
      .then((data) => {
        if (data.candles) setCandles(data.candles);
      })
      .catch((err) => console.warn("Candles API offline:", err));
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    loadMarketData(selectedSymbol, selectedTimeframe);
    const timer = setInterval(() => loadMarketData(selectedSymbol, selectedTimeframe), 5000);
    return () => clearInterval(timer);
  }, [selectedSymbol, selectedTimeframe, isAuthenticated]);

  // Handle Signal Generation
  const handleGenerateSignal = () => {
    setLoadingSignal(true);
    safeFetch(`${API_BASE}/api/signals/generate?symbol=${encodeURIComponent(selectedSymbol)}`, {
      method: "POST"
    })
      .then((res) => res.json())
      .then((data) => {
        setActiveSignal(data);
      })
      .catch((err) => {
        console.error("Signal API error:", err);
      })
      .finally(() => setLoadingSignal(false));
  };

  // Handle Backtest Execution
  const handleRunBacktest = () => {
    setLoadingBacktest(true);
    safeFetch(`${API_BASE}/api/backtest/run?symbol=${encodeURIComponent(selectedSymbol)}&limit=200`, {
      method: "POST"
    })
      .then((res) => res.json())
      .then((data) => {
        setBacktestReport(data);
      })
      .catch((err) => {
        console.error("Backtest API error:", err);
      })
      .finally(() => setLoadingBacktest(false));
  };

  if (!isAuthenticated) {
    return (
      <div className="h-screen bg-slate-950 text-white flex items-center justify-center p-6 font-sans relative overflow-hidden">
        <div className="max-w-md w-full text-center space-y-6 z-10">
          <img
            src="/tradegod-logo.png"
            alt="TRADE GOD Logo"
            className="w-24 h-24 mx-auto rounded-full border-4 border-amber-500/40 shadow-2xl bg-slate-900 object-cover"
          />
          <div className="space-y-1">
            <h1 className="text-3xl font-black tracking-tight text-white">TRADE GOD</h1>
            <p className="text-xs text-amber-400 font-bold uppercase tracking-widest">Quantitative Insights Engine</p>
          </div>
          <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-3xl space-y-4 shadow-2xl backdrop-blur-md">
            <p className="text-xs text-slate-300 leading-relaxed">
              Access to live AI signal engine, strategies, and execution monitoring requires an authenticated trader account.
            </p>
            <button
              onClick={() => openAuthModal("login")}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-black text-xs rounded-xl shadow-lg transition uppercase tracking-wider"
            >
              Log In / Create Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#f8fafc] text-slate-900 flex overflow-hidden font-sans">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* 2. Main Center Content Column */}
      <main className="flex-1 p-6 md:p-8 space-y-6 w-full overflow-y-auto">
        {/* Header Greeting Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <img
              src="/tradegod-logo.png"
              alt="TRADE GOD"
              className="w-12 h-12 rounded-full border-2 border-amber-500/30 object-cover shadow-md bg-slate-950"
            />
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-900 flex items-center gap-1.5">
                <span>TRADE GOD</span>
                <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-800 rounded-md uppercase tracking-wider">
                  Quantitative Insights
                </span>
              </h1>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                Live algorithmic signal analysis engine, multi-timeframe market structure, and risk protection.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {isAuthenticated && user ? (
              <button
                onClick={openProfileModal}
                className="flex items-center space-x-2 bg-white border border-slate-200/80 px-3 py-1.5 rounded-xl text-xs font-bold text-slate-700 shadow-xs hover:border-blue-300 transition"
              >
                <img
                  src={user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=2563eb&color=fff`}
                  alt={user.full_name}
                  className="w-5 h-5 rounded-lg object-cover"
                />
                <span>{user.full_name.split(" ")[0]}</span>
              </button>
            ) : (
              <button
                onClick={() => openAuthModal("login")}
                className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-xs transition"
              >
                Sign In
              </button>
            )}
            <div className="flex items-center space-x-2 bg-white border border-slate-200/80 px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-700 shadow-xs">
              <Calendar className="w-3.5 h-3.5 text-blue-600" />
              <span>{new Date().toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })}</span>
            </div>
          </div>
        </div>

        {/* Top 3 Stat Cards Row */}
        <StatCardsRow
          lastPrice={chartInfo?.last_price}
        />

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <ActiveStrategyCard />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <TradingViewChart
                  candles={candles}
                  symbol={selectedSymbol}
                  symbols={symbols}
                  timeframe={selectedTimeframe}
                  onSelectSymbol={(sym) => setSelectedSymbol(sym)}
                  onSelectTimeframe={(tf) => setSelectedTimeframe(tf)}
                  signalPriceLines={
                    activeSignal
                      ? {
                          entry: activeSignal.entry_price,
                          stopLoss: activeSignal.stop_loss,
                          takeProfit1: activeSignal.take_profit_1,
                          takeProfit2: activeSignal.take_profit_2
                        }
                      : undefined
                  }
                />

                <PositionsTable />

                <BacktestPanel
                  report={backtestReport}
                  onRunBacktest={handleRunBacktest}
                  loading={loadingBacktest}
                />
              </div>

              <div className="lg:col-span-1 space-y-6">
                <SignalPanel
                  signal={activeSignal}
                  onGenerateSignal={handleGenerateSignal}
                  loading={loadingSignal}
                />
                <NewsFilterWidget />
              </div>
            </div>
          </div>
        )}

        {/* Strategy Tab */}
        {activeTab === "strategy" && (
          <div className="space-y-6">
            <StrategyBuilder onStrategySaved={() => loadMarketData(selectedSymbol, selectedTimeframe)} />
          </div>
        )}

        {/* Bot Control Tab */}
        {activeTab === "bot" && (
          <div className="space-y-6">
            <BotControlPanel />
          </div>
        )}

        {/* Telegram Alerts Tab */}
        {activeTab === "telegram" && (
          <div className="space-y-6">
            <TelegramAlertsPanel />
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === "settings" && (
          <div className="space-y-6">
            <SettingsPage />
          </div>
        )}
      </main>
    </div>
  );
}
