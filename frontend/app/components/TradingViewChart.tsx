"use client";

import React, { useEffect, useRef, useState, memo } from "react";
import { ExternalLink, Maximize2, Minimize2, Sparkles, ChevronDown } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

export interface SymbolSpec {
  symbol: string;
  display_name: string;
  category: string;
}

interface TradingViewChartProps {
  candles?: any[];
  symbol: string;
  symbols?: SymbolSpec[];
  timeframe?: string;
  onSelectSymbol?: (symbol: string) => void;
  onSelectTimeframe?: (tf: string) => void;
  signalPriceLines?: {
    entry?: number;
    stopLoss?: number;
    takeProfit1?: number;
    takeProfit2?: number;
  };
}

export function getTradingViewSymbol(symbol: string): string {
  const clean = (symbol || "XAU/USD").toUpperCase().trim();
  const map: { [key: string]: string } = {
    "XAU/USD": "OANDA:XAUUSD", "XAUUSD": "OANDA:XAUUSD", "GOLD": "OANDA:XAUUSD",
    "XAG/USD": "OANDA:XAGUSD", "XAGUSD": "OANDA:XAGUSD",
    "EUR/USD": "FX:EURUSD",   "EURUSD": "FX:EURUSD",
    "GBP/USD": "FX:GBPUSD",   "GBPUSD": "FX:GBPUSD",
    "USD/JPY": "FX:USDJPY",   "USDJPY": "FX:USDJPY",
    "BTC/USD": "BITSTAMP:BTCUSD", "BTCUSD": "BITSTAMP:BTCUSD",
    "ETH/USD": "BITSTAMP:ETHUSD", "ETHUSD": "BITSTAMP:ETHUSD",
    "US30": "CAPITALCOM:US30", "DJI": "CAPITALCOM:US30"
  };
  if (map[clean]) return map[clean];
  return `OANDA:${clean.replace("/", "")}`;
}

export function getTradingViewInterval(timeframe: string): string {
  const map: { [key: string]: string } = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "4h": "240", "1d": "D", "1w": "W"
  };
  return map[(timeframe || "5m").toLowerCase().trim()] || "5";
}

const TradingViewEmbed = memo(function TradingViewEmbed({
  tvSymbol, tvInterval, height = "600px", isDark
}: { tvSymbol: string; tvInterval: string; height?: string; isDark: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.innerHTML = "";

    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    widgetDiv.style.height = height;
    widgetDiv.style.minHeight = height;
    widgetDiv.style.width = "100%";
    el.appendChild(widgetDiv);

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: tvInterval,
      timezone: "Etc/UTC",
      theme: isDark ? "dark" : "light",
      style: "1",
      locale: "en",
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      hide_volume: false,
      support_host: "https://www.tradingview.com",
      backgroundColor: isDark ? "#111113" : "#ffffff",
      gridColor: isDark ? "rgba(39,39,42,0.6)" : "rgba(228,229,233,0.6)"
    });

    el.appendChild(script);
    return () => { if (el) el.innerHTML = ""; };
  }, [tvSymbol, tvInterval, isDark, height]);

  return (
    <div
      ref={containerRef}
      className="tradingview-widget-container w-full"
      style={{ height: height, minHeight: height }}
    />
  );
});

const TradingViewChart = memo(function TradingViewChart({
  symbol, symbols, timeframe = "5m", onSelectSymbol
}: TradingViewChartProps) {
  const { isDark } = useTheme();
  const [isFullscreen, setIsFullscreen] = useState(false);

  const tvSymbol = getTradingViewSymbol(symbol);
  const tvInterval = getTradingViewInterval(timeframe);
  const externalTvUrl = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tvSymbol)}&interval=${tvInterval}`;
  const chartHeight = isFullscreen ? "calc(100vh - 80px)" : "600px";

  return (
    <div
      className="card overflow-hidden flex flex-col"
      style={isFullscreen ? {
        position: "fixed", inset: "12px", zIndex: 50,
        background: "var(--bg-elevated)"
      } : {}}
    >
      {/* Toolbar */}
      <div
        className="flex items-center justify-between px-4 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        {/* Symbol selector */}
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "var(--accent)" }}
          >
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="relative">
            <select
              value={symbol}
              onChange={(e) => onSelectSymbol?.(e.target.value)}
              className="appearance-none rounded-lg pr-7 pl-3 py-1.5 text-sm font-bold cursor-pointer border outline-none transition"
              style={{
                background: "var(--bg-subtle)",
                borderColor: "var(--border)",
                color: "var(--text)"
              }}
            >
              {symbols && symbols.length > 0
                ? symbols.map((s) => (
                  <option key={s.symbol} value={s.symbol}>
                    {s.symbol} — {s.display_name}
                  </option>
                ))
                : <option value={symbol}>{symbol}</option>
              }
            </select>
            <ChevronDown className="w-3.5 h-3.5 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: "var(--text-faint)" }} />
          </div>

          <span className="badge badge-blue hidden sm:inline-flex">
            {(symbols?.find(s => s.symbol === symbol)?.category) || "metals"}
          </span>

          <span className="hidden sm:flex items-center gap-1.5 text-xs font-semibold" style={{ color: "var(--green)" }}>
            <span className="live-dot" />
            Engine Synced
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="btn btn-ghost px-2 py-1.5"
            style={{ fontSize: "12px" }}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <a
            href={externalTvUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-ghost px-3 py-1.5 gap-1.5"
            style={{ fontSize: "12px" }}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>TradingView</span>
          </a>
        </div>
      </div>

      {/* Chart canvas - fixed pixel height guaranteed */}
      <div
        className="w-full overflow-hidden"
        style={{ height: chartHeight, minHeight: chartHeight }}
      >
        <TradingViewEmbed
          key={`${tvSymbol}_${tvInterval}_${isDark}_${isFullscreen}`}
          tvSymbol={tvSymbol}
          tvInterval={tvInterval}
          height={chartHeight}
          isDark={isDark}
        />
      </div>
    </div>
  );
});

export default TradingViewChart;
