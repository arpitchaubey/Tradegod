"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Newspaper, AlertTriangle, CheckCircle } from "lucide-react";

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
          <span>Economic Calendar Filter</span>
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

      <div className="space-y-1.5">
        {newsData.events?.slice(0, 2).map((ev: any) => (
          <div
            key={ev.id}
            className="bg-slate-50 border border-slate-200/80 rounded-xl p-2.5 text-xs flex items-center justify-between"
          >
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-slate-800">{ev.title}</span>
              <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono font-bold">
                {ev.currency}
              </span>
            </div>
            <span className="text-[10px] bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded font-extrabold uppercase">
              {ev.impact} IMPACT
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
