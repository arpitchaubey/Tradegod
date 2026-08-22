"use client";

import React, { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";
import { TrendingUp, Activity, DollarSign, Calendar } from "lucide-react";

const PERFORMANCE_DATA = [
  { time: "09:00", equity: 10000, pnl: 0, signals: 2 },
  { time: "10:00", equity: 10120, pnl: 120, signals: 4 },
  { time: "11:00", equity: 10090, pnl: 90, signals: 5 },
  { time: "12:00", equity: 10250, pnl: 250, signals: 8 },
  { time: "13:00", equity: 10380, pnl: 380, signals: 11 },
  { time: "14:00", equity: 10340, pnl: 340, signals: 12 },
  { time: "15:00", equity: 10520, pnl: 520, signals: 15 },
  { time: "16:00", equity: 10680, pnl: 680, signals: 18 }
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-lg font-sans text-xs space-y-1">
        <p className="font-extrabold text-slate-900 flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5 text-blue-600" />
          <span>{label} Session</span>
        </p>
        <div className="flex items-center justify-between gap-4 text-slate-600">
          <span>Account Equity:</span>
          <strong className="text-slate-900 font-mono">${data.equity.toLocaleString()}</strong>
        </div>
        <div className="flex items-center justify-between gap-4 text-slate-600">
          <span>Cumulative PnL:</span>
          <strong className={data.pnl >= 0 ? "text-emerald-600 font-mono" : "text-rose-600 font-mono"}>
            +${data.pnl}
          </strong>
        </div>
      </div>
    );
  }
  return null;
};

export default function PerformanceChart() {
  const [metric, setMetric] = useState<"EQUITY" | "PNL">("EQUITY");

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs font-sans space-y-4">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3.5 gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">
              Live Equity & Strategy Performance
            </h3>
            <p className="text-xs text-slate-400 font-medium">
              Real-time portfolio curve and cumulative profit tracking
            </p>
          </div>
        </div>

        <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-bold gap-1">
          <button
            onClick={() => setMetric("EQUITY")}
            className={`px-3 py-1 rounded-lg transition ${
              metric === "EQUITY"
                ? "bg-blue-600 text-white shadow-xs font-extrabold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Account Equity
          </button>
          <button
            onClick={() => setMetric("PNL")}
            className={`px-3 py-1 rounded-lg transition ${
              metric === "PNL"
                ? "bg-emerald-600 text-white shadow-xs font-extrabold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Cumulative PnL
          </button>
        </div>
      </div>

      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={PERFORMANCE_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey={metric === "EQUITY" ? "equity" : "pnl"}
              stroke={metric === "EQUITY" ? "#2563eb" : "#10b981"}
              strokeWidth={2.5}
              fillOpacity={1}
              fill={`url(#${metric === "EQUITY" ? "equityGrad" : "pnlGrad"})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
