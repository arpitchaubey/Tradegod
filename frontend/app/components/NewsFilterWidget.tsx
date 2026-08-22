"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Newspaper, AlertTriangle, CheckCircle, Calendar, Clock } from "lucide-react";

function formatEventDate(isoStr: string) {
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true
    });
  } catch {
    return isoStr;
  }
}

function formatCountdown(isoStr: string) {
  try {
    const d = new Date(isoStr).getTime();
    const now = new Date().getTime();
    const diffMs = d - now;
    if (diffMs <= 0) return "RELEASED";
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      return `in ${days}d ${hours % 24}h`;
    }
    if (hours > 0) return `in ${hours}h ${mins}m`;
    return `in ${mins}m`;
  } catch {
    return "";
  }
}

export default function NewsFilterWidget() {
  const [newsData, setNewsData] = useState<any>(null);

  const fetchNews = () => {
    safeFetch(`${API_BASE}/api/execution/news`)
      .then((res) => res.json())
      .then((data) => setNewsData(data))
      .catch((err) => console.warn("News API offline:", err));
  };

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!newsData) return null;

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs font-sans space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <h4 className="text-xs font-extrabold text-slate-900 flex items-center gap-1.5">
          <Newspaper className="w-4 h-4 text-blue-600" />
          <span>Economic Calendar & News Releases</span>
        </h4>
        <span
          className={`text-[10px] px-2.5 py-0.5 rounded-full font-extrabold border flex items-center gap-1 ${
            newsData.is_blackout_active
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : "bg-emerald-50 text-emerald-700 border-emerald-200"
          }`}
        >
          {newsData.is_blackout_active ? (
            <>
              <AlertTriangle className="w-3 h-3 text-amber-600" />
              <span>HIGH VOLATILITY BLACKOUT</span>
            </>
          ) : (
            <>
              <CheckCircle className="w-3 h-3 text-emerald-600" />
              <span>NORMAL MARKET WINDOW</span>
            </>
          )}
        </span>
      </div>

      <div className="space-y-2">
        {newsData.events?.slice(0, 3).map((ev: any) => {
          const countdown = formatCountdown(ev.time);
          const dateFormatted = formatEventDate(ev.time);

          return (
            <div
              key={ev.id}
              className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs space-y-1.5 hover:border-slate-300 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-extrabold text-slate-800">{ev.title}</span>
                  <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono font-bold">
                    {ev.currency}
                  </span>
                </div>
                <span className="text-[10px] bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded font-extrabold uppercase">
                  {ev.impact} IMPACT
                </span>
              </div>

              {/* Release Date & Live Countdown */}
              <div className="flex items-center justify-between text-[11px] text-slate-600 pt-0.5">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5 text-blue-500" />
                  <span className="font-medium text-slate-700">{dateFormatted}</span>
                </div>

                <div className="flex items-center space-x-1 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-md text-blue-700 font-bold">
                  <Clock className="w-3 h-3 text-blue-600 animate-pulse" />
                  <span>{countdown}</span>
                </div>
              </div>

              {/* Forecast & Previous Metrics */}
              {(ev.forecast || ev.previous) && (
                <div className="flex items-center gap-3 text-[10px] text-slate-500 border-t border-slate-100 pt-1.5">
                  {ev.forecast && (
                    <span>
                      Forecast: <strong className="text-slate-700 font-bold">{ev.forecast}</strong>
                    </span>
                  )}
                  {ev.previous && (
                    <span>
                      Previous: <strong className="text-slate-700 font-bold">{ev.previous}</strong>
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
