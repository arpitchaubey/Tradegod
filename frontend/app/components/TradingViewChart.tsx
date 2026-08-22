"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, CandlestickSeries, LineSeries, CandlestickData, Time } from "lightweight-charts";
import { ExternalLink, BarChart2, Sparkles, ChevronDown } from "lucide-react";
import { API_BASE, safeFetch } from "../utils/api";

interface CandleItem {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface SymbolSpec {
  symbol: string;
  display_name: string;
  category: string;
}

interface TradingViewChartProps {
  candles: CandleItem[];
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

function calculateEMAData(candles: { time: Time; close: number }[], period: number) {
  if (candles.length < period) return [];
  const k = 2 / (period + 1);
  let ema = candles.slice(0, period).reduce((acc, val) => acc + val.close, 0) / period;
  const result = [{ time: candles[period - 1].time, value: roundTwo(ema) }];

  for (let i = period; i < candles.length; i++) {
    ema = candles[i].close * k + ema * (1 - k);
    result.push({ time: candles[i].time, value: roundTwo(ema) });
  }
  return result;
}

function roundTwo(num: number) {
  return Math.round(num * 100) / 100;
}

function getTradingViewSymbol(symbol: string): string {
  const map: { [key: string]: string } = {
    "XAU/USD": "OANDA:XAUUSD",
    "XAG/USD": "OANDA:XAGUSD",
    "EUR/USD": "FX:EURUSD",
    "GBP/USD": "FX:GBPUSD",
    "USD/JPY": "FX:USDJPY",
    "BTC/USD": "BITSTAMP:BTCUSD",
    "ETH/USD": "BITSTAMP:ETHUSD",
    "US30": "FOREXCOM:SPXUSD"
  };
  return map[symbol.toUpperCase()] || "OANDA:XAUUSD";
}

export default function TradingViewChart({
  candles,
  symbol,
  symbols,
  timeframe = "5m",
  onSelectSymbol,
  onSelectTimeframe,
  signalPriceLines
}: TradingViewChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [activeStrategyName, setActiveStrategyName] = useState<string>("Gold 5M Breakout Strategy");

  useEffect(() => {
    safeFetch(`${API_BASE}/api/strategy/current`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.name) setActiveStrategyName(data.name);
      })
      .catch((err) => console.warn("Error fetching current strategy:", err));
  }, []);

  const tvSymbol = getTradingViewSymbol(symbol);
  const externalTvUrl = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tvSymbol)}`;

  const currentSymbolObj = symbols?.find((s) => s.symbol === symbol) || {
    symbol,
    display_name: symbol === "XAU/USD" ? "Gold Spot / US Dollar" : symbol,
    category: "metals"
  };

  // Lightweight Chart setup
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 460,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#64748b"
      },
      grid: {
        vertLines: { color: "#f1f5f9" },
        horzLines: { color: "#f1f5f9" }
      },
      crosshair: {
        mode: 1
      },
      rightPriceScale: {
        borderColor: "#cbd5e1"
      },
      timeScale: {
        borderColor: "#cbd5e1",
        timeVisible: true,
        secondsVisible: false
      }
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444"
    });

    const ema20Series = chart.addSeries(LineSeries, {
      color: "#2563eb",
      lineWidth: 2,
      title: "EMA 20"
    });

    const ema50Series = chart.addSeries(LineSeries, {
      color: "#f59e0b",
      lineWidth: 2,
      title: "EMA 50"
    });

    if (candles && candles.length > 0) {
      const map = new Map<number, CandlestickData<Time>>();
      const closeValues: { time: Time; close: number }[] = [];

      candles.forEach((c) => {
        const timeSec = Math.floor(new Date(c.timestamp).getTime() / 1000);
        if (!isNaN(timeSec) && !map.has(timeSec)) {
          const item = {
            time: timeSec as Time,
            open: Number(c.open),
            high: Number(c.high),
            low: Number(c.low),
            close: Number(c.close)
          };
          map.set(timeSec, item);
        }
      });

      const sortedData = Array.from(map.values()).sort(
        (a, b) => (a.time as number) - (b.time as number)
      );

      if (sortedData.length > 0) {
        candlestickSeries.setData(sortedData);

        sortedData.forEach((d) => {
          closeValues.push({ time: d.time, close: d.close });
        });

        const ema20Data = calculateEMAData(closeValues, 20);
        const ema50Data = calculateEMAData(closeValues, 50);

        if (ema20Data.length > 0) ema20Series.setData(ema20Data);
        if (ema50Data.length > 0) ema50Series.setData(ema50Data);

        chart.timeScale().fitContent();
      }
    }

    if (signalPriceLines) {
      if (signalPriceLines.entry) {
        candlestickSeries.createPriceLine({
          price: signalPriceLines.entry,
          color: "#2563eb",
          lineWidth: 2,
          lineStyle: 0,
          title: "ENTRY"
        });
      }
      if (signalPriceLines.stopLoss) {
        candlestickSeries.createPriceLine({
          price: signalPriceLines.stopLoss,
          color: "#ef4444",
          lineWidth: 2,
          lineStyle: 2,
          title: "STOP LOSS"
        });
      }
      if (signalPriceLines.takeProfit1) {
        candlestickSeries.createPriceLine({
          price: signalPriceLines.takeProfit1,
          color: "#10b981",
          lineWidth: 2,
          lineStyle: 2,
          title: "TP1"
        });
      }
      if (signalPriceLines.takeProfit2) {
        candlestickSeries.createPriceLine({
          price: signalPriceLines.takeProfit2,
          color: "#059669",
          lineWidth: 2,
          lineStyle: 2,
          title: "TP2"
        });
      }
    }

    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
    }, [candles, signalPriceLines]);

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs font-sans space-y-3.5">
      {/* Tier 1: Main Control Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        {/* Left: Sparkles Icon + Symbol Selector Dropdown + Category Badge */}
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs">
            <Sparkles className="w-4 h-4" />
          </div>

          <div className="relative">
            <select
              value={symbol}
              onChange={(e) => onSelectSymbol && onSelectSymbol(e.target.value)}
              className="appearance-none bg-slate-50 hover:bg-slate-100 text-slate-900 font-extrabold text-sm rounded-xl px-3 py-1.5 pr-8 border border-slate-200/90 focus:outline-none focus:border-blue-600 cursor-pointer shadow-2xs transition"
            >
              {symbols && symbols.length > 0 ? (
                symbols.map((s) => (
                  <option key={s.symbol} value={s.symbol}>
                    {s.symbol} — {s.display_name}
                  </option>
                ))
              ) : (
                <option value={symbol}>{symbol} — Gold Spot / US Dollar</option>
              )}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>

          <span className="text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-lg font-bold bg-blue-50 text-blue-700 border border-blue-200/80">
            {currentSymbolObj.category}
          </span>
        </div>

        {/* Right: Timeframe Switcher + TradingView External Button */}
        <div className="flex items-center space-x-2.5">
          {/* Timeframe Switcher Pill */}
          {onSelectTimeframe && (
            <div className="flex items-center bg-slate-100/90 p-1 rounded-xl border border-slate-200/80 gap-0.5 shadow-2xs">
              <span className="text-[10px] text-slate-400 font-extrabold px-1.5 uppercase tracking-wide">TF</span>
              {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => onSelectTimeframe(tf)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold transition uppercase ${
                    timeframe.toLowerCase() === tf.toLowerCase()
                      ? "bg-blue-600 text-white shadow-xs"
                      : "text-slate-600 hover:bg-slate-200/70 hover:text-slate-900"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          )}

          {/* Open on TradingView Button */}
          <a
            href={externalTvUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-3 py-1.5 rounded-xl shadow-xs transition"
          >
            <span>TradingView</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-300" />
          </a>
        </div>
      </div>

      {/* Tier 2: Active Strategy, Indicators & Realtime Feed Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 text-xs font-semibold px-0.5">
        {/* Left Group: Active Strategy & Indicators */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Active Strategy Badge */}
          <span className="flex items-center gap-1.5 text-[11px] font-extrabold bg-blue-50/80 text-blue-900 border border-blue-200/70 px-2.5 py-1 rounded-lg shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-blue-500 font-medium">Active Strategy:</span>
            <span className="text-blue-950 font-bold">{activeStrategyName}</span>
          </span>

          {/* EMA Indicators */}
          <span className="flex items-center gap-1.5 text-blue-600 bg-slate-50 border border-slate-200/80 px-2 py-0.5 rounded-md text-[11px] font-bold">
            <span className="w-2 h-2 rounded-full bg-blue-600" /> EMA 20
          </span>
          <span className="flex items-center gap-1.5 text-amber-600 bg-slate-50 border border-slate-200/80 px-2 py-0.5 rounded-md text-[11px] font-bold">
            <span className="w-2 h-2 rounded-full bg-amber-500" /> EMA 50
          </span>
        </div>

        {/* Right Group: Realtime Data Feed */}
        <div className="flex items-center space-x-1.5 text-[11px] text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Realtime Feed:</span>
          <span className="text-slate-700 font-extrabold uppercase">Yahoo Finance / OANDA</span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div ref={chartContainerRef} className="w-full rounded-xl overflow-hidden border border-slate-100" />
    </div>
  );
}
