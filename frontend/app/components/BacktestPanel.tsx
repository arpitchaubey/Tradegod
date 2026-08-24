"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  TrendingUp,
  DollarSign,
  Percent,
  Award,
  AlertCircle,
  History,
  Trash2,
  ChevronRight,
  Sparkles,
  Calendar,
  Layers,
  RefreshCw
} from "lucide-react";
import { API_BASE, safeFetch } from "../utils/api";

interface SimulatedTrade {
  trade_id: number;
  direction: string;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  profit_loss: number;
  r_multiple: number;
  result: string;
}

interface BacktestReport {
  symbol: string;
  timeframe: string;
  total_candles: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_percent: number;
  profit_factor: number;
  net_profit: number;
  max_drawdown_percent: number;
  expectancy: number;
  trades: SimulatedTrade[];
}

interface BacktestHistoryItem {
  id: string;
  symbol: string;
  timeframe: string;
  candle_limit: number;
  created_at: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_percent: number;
  profit_factor: number;
  net_profit: number;
  max_drawdown_percent: number;
  expectancy: number;
  report: BacktestReport;
}

interface BacktestPanelProps {
  report: BacktestReport | null;
  onRunBacktest: () => void;
  loading: boolean;
}

export default function BacktestPanel({ report: initialReport, onRunBacktest, loading }: BacktestPanelProps) {
  const [activeTab, setActiveTab] = useState<"current" | "history">("current");
  const [activeReport, setActiveReport] = useState<BacktestReport | null>(initialReport);
  const [history, setHistory] = useState<BacktestHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (initialReport) {
      setActiveReport(initialReport);
      fetchHistory();
    }
  }, [initialReport]);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await safeFetch(`${API_BASE}/api/backtest/history`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setHistory(data);
      }
    } catch (e) {
      console.warn("Failed to fetch backtest history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDeleteHistory = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await safeFetch(`${API_BASE}/api/backtest/history/${id}`, { method: "DELETE" });
      setHistory(history.filter((h) => h.id !== id));
      if (activeReport && history.find((h) => h.id === id)?.report === activeReport) {
        setActiveReport(null);
      }
    } catch (e) {
      console.error("Failed to delete history item:", e);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm("Are you sure you want to clear all backtesting history?")) return;
    try {
      await safeFetch(`${API_BASE}/api/backtest/history`, { method: "DELETE" });
      setHistory([]);
    } catch (e) {
      console.error("Failed to clear history:", e);
    }
  };

  const report = activeReport;

  return (
    <div className="card p-5 lg:p-6 space-y-5">
      {/* Header */}
      <div
        className="flex flex-wrap items-center justify-between gap-4 pb-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center space-x-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center font-bold"
            style={{
              background: "linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)",
              color: "white"
            }}
          >
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm" style={{ color: "var(--text)" }}>
              Backtesting Simulation Lab
            </h3>
            <p className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
              Historical candle-by-candle simulation, equity curves & full performance logs.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Sub-tab switcher */}
          <div
            className="flex items-center p-1 rounded-xl border"
            style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
          >
            <button
              onClick={() => setActiveTab("current")}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer"
              style={{
                background: activeTab === "current" ? "var(--bg-elevated)" : "transparent",
                color: activeTab === "current" ? "var(--accent)" : "var(--text-muted)",
                border: activeTab === "current" ? "1px solid var(--border)" : "1px solid transparent"
              }}
            >
              Current Report
            </button>
            <button
              onClick={() => {
                setActiveTab("history");
                fetchHistory();
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
              style={{
                background: activeTab === "history" ? "var(--bg-elevated)" : "transparent",
                color: activeTab === "history" ? "var(--accent)" : "var(--text-muted)",
                border: activeTab === "history" ? "1px solid var(--border)" : "1px solid transparent"
              }}
            >
              <History className="w-3 h-3" />
              <span>History ({history.length})</span>
            </button>
          </div>

          <button
            onClick={onRunBacktest}
            disabled={loading}
            className="btn btn-primary text-xs font-bold px-4 py-2"
          >
            {loading ? (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run New Backtest</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Active Report View ─────────────────────────────── */}
      {activeTab === "current" && (
        <>
          {report ? (
            <div className="space-y-5">
              {/* Summary Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div
                  className="p-3.5 rounded-xl border space-y-1"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
                >
                  <span className="text-[10px] font-semibold uppercase flex items-center gap-1" style={{ color: "var(--text-faint)" }}>
                    <Percent className="w-3.5 h-3.5 text-emerald-500" /> Win Rate
                  </span>
                  <span className="text-xl font-bold font-mono block" style={{ color: "var(--green)" }}>
                    {report.win_rate_percent}%
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>
                    {report.winning_trades} Wins / {report.losing_trades} Losses
                  </span>
                </div>

                <div
                  className="p-3.5 rounded-xl border space-y-1"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
                >
                  <span className="text-[10px] font-semibold uppercase flex items-center gap-1" style={{ color: "var(--text-faint)" }}>
                    <TrendingUp className="w-3.5 h-3.5" style={{ color: "var(--accent)" }} /> Profit Factor
                  </span>
                  <span className="text-xl font-bold font-mono block" style={{ color: "var(--accent)" }}>
                    {report.profit_factor}x
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>
                    Expectancy: ${report.expectancy}
                  </span>
                </div>

                <div
                  className="p-3.5 rounded-xl border space-y-1"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
                >
                  <span className="text-[10px] font-semibold uppercase flex items-center gap-1" style={{ color: "var(--text-faint)" }}>
                    <DollarSign className="w-3.5 h-3.5 text-indigo-500" /> Net Return
                  </span>
                  <span
                    className="text-xl font-bold font-mono block"
                    style={{ color: report.net_profit >= 0 ? "var(--green)" : "var(--red)" }}
                  >
                    ${report.net_profit}
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>
                    {report.total_trades} total trades
                  </span>
                </div>

                <div
                  className="p-3.5 rounded-xl border space-y-1"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
                >
                  <span className="text-[10px] font-semibold uppercase flex items-center gap-1" style={{ color: "var(--text-faint)" }}>
                    <AlertCircle className="w-3.5 h-3.5" style={{ color: "var(--red)" }} /> Max Drawdown
                  </span>
                  <span className="text-xl font-bold font-mono block" style={{ color: "var(--red)" }}>
                    {report.max_drawdown_percent}%
                  </span>
                  <span className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>
                    Peak-to-trough
                  </span>
                </div>
              </div>

              {/* Trade History Table */}
              {report.trades && report.trades.length > 0 ? (
                <div
                  className="rounded-xl border overflow-hidden"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div className="p-3 border-b flex items-center justify-between" style={{ borderColor: "var(--border)", background: "var(--bg-subtle)" }}>
                    <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
                      Simulated Executions Log ({report.trades.length})
                    </h4>
                    <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                      {report.symbol} · {report.timeframe}
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="tbl w-full text-xs">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Direction</th>
                          <th>Entry Price</th>
                          <th>Exit Price</th>
                          <th>P&L ($)</th>
                          <th>R Multiple</th>
                          <th>Result</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.trades.map((t) => (
                          <tr key={t.trade_id}>
                            <td className="font-mono">{t.trade_id}</td>
                            <td>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  t.direction === "BUY" ? "badge-green" : "badge-red"
                                }`}
                              >
                                {t.direction}
                              </span>
                            </td>
                            <td className="font-mono">${t.entry_price.toFixed(2)}</td>
                            <td className="font-mono">${t.exit_price.toFixed(2)}</td>
                            <td
                              className="font-mono font-bold"
                              style={{ color: t.profit_loss >= 0 ? "var(--green)" : "var(--red)" }}
                            >
                              ${t.profit_loss.toFixed(2)}
                            </td>
                            <td className="font-mono">{t.r_multiple}R</td>
                            <td>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  t.result === "WIN"
                                    ? "badge-green"
                                    : t.result === "LOSS"
                                    ? "badge-red"
                                    : "badge-muted"
                                }`}
                              >
                                {t.result}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div
                  className="text-center py-10 rounded-xl border text-xs"
                  style={{ background: "var(--bg-subtle)", borderColor: "var(--border)", color: "var(--text-muted)" }}
                >
                  No trade setups triggered during this historical candle window.
                </div>
              )}
            </div>
          ) : (
            /* Empty State */
            <div
              className="text-center py-14 rounded-xl border space-y-3"
              style={{ background: "var(--bg-subtle)", borderColor: "var(--border)" }}
            >
              <Award className="w-8 h-8 mx-auto" style={{ color: "var(--text-faint)" }} />
              <h4 className="text-sm font-bold" style={{ color: "var(--text)" }}>
                No Active Backtest Simulation
              </h4>
              <p className="text-xs max-w-sm mx-auto" style={{ color: "var(--text-muted)" }}>
                Click <strong>"Run New Backtest"</strong> or choose a previous simulation from the <strong>History</strong> tab.
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Historical Backtest Log View ───────────────────── */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text)" }}>
              Saved Backtest Runs ({history.length})
            </h4>
            {history.length > 0 && (
              <button
                onClick={handleClearHistory}
                className="btn btn-ghost text-xs text-rose-500 hover:text-rose-600 gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
            )}
          </div>

          {loadingHistory ? (
            <div className="py-12 flex justify-center items-center">
              <RefreshCw className="w-5 h-5 animate-spin" style={{ color: "var(--accent)" }} />
            </div>
          ) : history.length > 0 ? (
            <div className="grid grid-cols-1 gap-3">
              {history.map((h) => (
                <div
                  key={h.id}
                  onClick={() => {
                    setActiveReport(h.report);
                    setActiveTab("current");
                  }}
                  className="p-4 rounded-xl border flex flex-wrap items-center justify-between gap-4 transition hover:border-blue-500/50 cursor-pointer"
                  style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
                >
                  <div className="flex items-center space-x-3.5">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs"
                      style={{
                        background: h.win_rate_percent >= 50 ? "var(--green-soft)" : "var(--red-soft)",
                        color: h.win_rate_percent >= 50 ? "var(--green)" : "var(--red)"
                      }}
                    >
                      {h.win_rate_percent}%
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs" style={{ color: "var(--text)" }}>
                          {h.symbol} · {h.timeframe.toUpperCase()}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: "var(--bg-subtle)", color: "var(--text-faint)" }}>
                          {h.candle_limit} candles
                        </span>
                      </div>
                      <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>
                        {new Date(h.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Quick stats */}
                  <div className="flex items-center gap-4 text-xs font-mono">
                    <div className="text-right">
                      <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Net Profit</span>
                      <strong style={{ color: h.net_profit >= 0 ? "var(--green)" : "var(--red)" }}>
                        ${h.net_profit}
                      </strong>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Profit Factor</span>
                      <strong style={{ color: "var(--accent)" }}>{h.profit_factor}x</strong>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] block font-sans" style={{ color: "var(--text-faint)" }}>Trades</span>
                      <strong style={{ color: "var(--text)" }}>{h.total_trades}</strong>
                    </div>

                    <button
                      onClick={(e) => handleDeleteHistory(h.id, e)}
                      className="p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-500 transition cursor-pointer"
                      title="Delete run"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div
              className="text-center py-12 rounded-xl border text-xs"
              style={{ background: "var(--bg-subtle)", borderColor: "var(--border)", color: "var(--text-muted)" }}
            >
              No backtests in history. Run a simulation to start tracking performance logs!
            </div>
          )}
        </div>
      )}
    </div>
  );
}
