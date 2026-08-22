"use client";

import React from "react";
import { Play, TrendingUp, DollarSign, Percent, Award, AlertCircle } from "lucide-react";

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

interface BacktestPanelProps {
  report: BacktestReport | null;
  onRunBacktest: () => void;
  loading: boolean;
}

export default function BacktestPanel({ report, onRunBacktest, loading }: BacktestPanelProps) {
  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs font-sans space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Award className="w-4 h-4 text-blue-600" />
          <h3 className="font-semibold text-slate-900 text-sm">Backtesting Simulation Engine</h3>
        </div>
        <button
          onClick={onRunBacktest}
          disabled={loading}
          className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-xl transition shadow-xs disabled:opacity-50 flex items-center space-x-1.5 cursor-pointer"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{loading ? "Running Simulation..." : "Run Backtest"}</span>
        </button>
      </div>

      {report ? (
        <div className="space-y-4">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-slate-500 text-xs flex items-center gap-1 font-medium">
                <Percent className="w-3.5 h-3.5 text-emerald-600" /> Win Rate
              </span>
              <span className="text-lg font-bold text-emerald-600 mt-1 block">
                {report.win_rate_percent}%
              </span>
              <span className="text-[10px] text-slate-400 font-medium">
                {report.winning_trades} W / {report.losing_trades} L
              </span>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-slate-500 text-xs flex items-center gap-1 font-medium">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600" /> Profit Factor
              </span>
              <span className="text-lg font-bold text-blue-600 mt-1 block">
                {report.profit_factor}
              </span>
              <span className="text-[10px] text-slate-400 font-medium">Expectancy: ${report.expectancy}</span>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-slate-500 text-xs flex items-center gap-1 font-medium">
                <DollarSign className="w-3.5 h-3.5 text-indigo-600" /> Net Return
              </span>
              <span
                className={`text-lg font-bold mt-1 block ${
                  report.net_profit >= 0 ? "text-emerald-600" : "text-rose-600"
                }`}
              >
                ${report.net_profit}
              </span>
              <span className="text-[10px] text-slate-400 font-medium">{report.total_trades} trades</span>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-slate-500 text-xs flex items-center gap-1 font-medium">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" /> Max Drawdown
              </span>
              <span className="text-lg font-bold text-rose-600 mt-1 block">
                {report.max_drawdown_percent}%
              </span>
              <span className="text-[10px] text-slate-400 font-medium">Peak-to-trough</span>
            </div>
          </div>

          {/* Trade History Table */}
          {report.trades && report.trades.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-700">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] tracking-wider border-b border-slate-200 font-semibold">
                  <tr>
                    <th className="p-2.5">#</th>
                    <th className="p-2.5">Dir</th>
                    <th className="p-2.5">Entry</th>
                    <th className="p-2.5">Exit</th>
                    <th className="p-2.5">P&L ($)</th>
                    <th className="p-2.5">R Mult</th>
                    <th className="p-2.5">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {report.trades.slice(0, 5).map((t) => (
                    <tr key={t.trade_id} className="hover:bg-slate-50">
                      <td className="p-2.5 font-medium">{t.trade_id}</td>
                      <td className="p-2.5 font-bold text-blue-600">{t.direction}</td>
                      <td className="p-2.5 font-mono font-medium">${t.entry_price}</td>
                      <td className="p-2.5 font-mono font-medium">${t.exit_price}</td>
                      <td
                        className={`p-2.5 font-bold font-mono ${
                          t.profit_loss >= 0 ? "text-emerald-600" : "text-rose-600"
                        }`}
                      >
                        ${t.profit_loss}
                      </td>
                      <td className="p-2.5 font-mono text-slate-600">{t.r_multiple}R</td>
                      <td className="p-2.5">
                        <span
                          className={`px-2 py-0.5 rounded font-bold text-[10px] uppercase ${
                            t.result === "WIN"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-rose-50 text-rose-700 border border-rose-200"
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
          ) : (
            <p className="text-xs text-slate-400 italic text-center py-4 font-medium">
              Historical candles evaluated. No trades triggered for current rule strictness.
            </p>
          )}
        </div>
      ) : (
        <div className="py-6 text-center text-slate-400 text-xs font-medium">
          Click "Run Backtest" to execute historical candle simulation.
        </div>
      )}
    </div>
  );
}
