"use client";

import React from "react";
import { Activity, Database, Layers, Clock, ChevronDown, Sparkles } from "lucide-react";

interface ActiveChartInfo {
  symbol: string;
  display_name: string;
  category: string;
  provider: string;
  timeframes: { [key: string]: string };
  last_price: number;
  bid_price: number;
  ask_price: number;
  spread: number;
  candle_count: number;
  last_updated: string;
  status: string;
  data_quality: string;
}

interface SymbolSpec {
  symbol: string;
  display_name: string;
  category: string;
}

interface ChartHeaderProps {
  chartInfo: ActiveChartInfo | null;
  symbols: SymbolSpec[];
  selectedSymbol: string;
  selectedTimeframe: string;
  onSelectSymbol: (symbol: string) => void;
  onSelectTimeframe: (tf: string) => void;
  onRefresh: () => void;
}

export default function ChartHeader({
  chartInfo,
  symbols,
  selectedSymbol,
  selectedTimeframe,
  onSelectSymbol,
  onSelectTimeframe
}: ChartHeaderProps) {
  const currentSymbolObj = symbols.find((s) => s.symbol === selectedSymbol) || {
    symbol: "XAU/USD",
    display_name: "Gold Spot / US Dollar",
    category: "metals"
  };

  return (
    <header className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-xs font-sans">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Symbol Selector */}
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-blue-600 rounded-xl shadow-xs text-white font-black">
            <Sparkles className="w-4 h-4" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <div className="relative inline-block">
                <select
                  value={selectedSymbol}
                  onChange={(e) => onSelectSymbol(e.target.value)}
                  className="appearance-none bg-slate-50 hover:bg-slate-100 text-slate-900 font-extrabold text-base rounded-xl px-3 py-1.5 pr-8 border border-slate-200 focus:outline-none focus:border-blue-600 cursor-pointer shadow-xs"
                >
                  {symbols.length > 0 ? (
                    symbols.map((s) => (
                      <option key={s.symbol} value={s.symbol}>
                        {s.symbol} — {s.display_name}
                      </option>
                    ))
                  ) : (
                    <option value="XAU/USD">XAU/USD — Gold Spot / US Dollar</option>
                  )}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-3 pointer-events-none" />
              </div>

              <span className="text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full font-bold bg-blue-50 text-blue-700 border border-blue-200">
                {currentSymbolObj.category}
              </span>
            </div>

            <p className="text-xs text-slate-400 font-medium mt-0.5">
              {chartInfo?.display_name || currentSymbolObj.display_name}
            </p>
          </div>
        </div>

        {/* Live Metadata Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-semibold">
          {/* Data Source */}
          <div className="flex items-center space-x-1.5 bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-200 text-blue-700">
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-blue-500">Source:</span>
            <span className="font-extrabold uppercase">
              REAL LIVE ({chartInfo?.provider || "YFINANCE"})
            </span>
          </div>

          {/* Sync Time */}
          <div className="flex items-center space-x-1 text-slate-400 text-xs">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Sync: {chartInfo?.last_updated ? new Date(chartInfo.last_updated).toLocaleTimeString() : "Live"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
