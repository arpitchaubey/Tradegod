"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Bell, CheckCircle2, TrendingUp } from "lucide-react";

interface StatCardsRowProps {
  lastPrice?: number;
}

export default function StatCardsRow({ lastPrice }: StatCardsRowProps) {
  const [stats, setStats] = useState<any>(null);

  const fetchStats = () => {
    safeFetch(`${API_BASE}/api/signals/stats`)
      .then((res) => res.json())
      .then((data) => {
        if (data) setStats(data);
      })
      .catch((err) => console.warn("Error fetching signal stats:", err));
  };

  useEffect(() => {
    fetchStats();
    const timer = setInterval(fetchStats, 1000);
    return () => clearInterval(timer);
  }, []);

  const totalAlerts = stats?.total_alerts ?? 0;
  const rightPredictions = stats?.right_predictions ?? 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-sans">
      {/* 1st Stat Card - Number of Alerts */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-medium border border-blue-100">
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[11px] text-slate-400 font-semibold block uppercase tracking-wider">
              Number of Alerts
            </span>
            <div className="mt-0.5">
              <span className="text-lg font-black text-slate-900 font-mono">
                {totalAlerts} Alerts
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2nd Stat Card - Right Predictions */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-medium border border-emerald-100">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[11px] text-slate-400 font-semibold block uppercase tracking-wider">
              Right Predictions
            </span>
            <div className="mt-0.5">
              <span className="text-lg font-black text-slate-900 font-mono">
                {rightPredictions} Win
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3rd Stat Card - Live Asset Price */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-medium border border-indigo-100">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[11px] text-slate-400 font-semibold block uppercase tracking-wider">
              Live Asset Price
            </span>
            <div className="mt-0.5">
              <span className="text-lg font-black text-slate-900 font-mono">
                {lastPrice ? `$${lastPrice.toFixed(2)}` : "Syncing..."}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
