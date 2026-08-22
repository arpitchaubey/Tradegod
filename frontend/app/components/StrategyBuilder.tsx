"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Brain, Zap, CheckCircle2, AlertTriangle, Terminal, Bookmark, Save, FolderHeart, Check, RefreshCw } from "lucide-react";

interface StrategyBuilderProps {
  onStrategySaved?: () => void;
}

const PRESET_STRATEGIES = [
  {
    name: "5M Gold EMA Breakout",
    text: "Analyze XAU/USD on 5-minute chart. Buy when price breaks resistance, 20 EMA is above 50 EMA, RSI is above 55, and candle closes above resistance. Use 1:2 risk/reward ratio."
  },
  {
    name: "1M Quick Scalper Momentum",
    text: "Scalp XAU/USD on 1-minute chart. Sell when price breaks 5M support, 20 EMA is below 50 EMA, RSI is below 45. Use tight 1:1.5 risk/reward ratio."
  },
  {
    name: "15M Trend Follower",
    text: "Trade XAU/USD on 15-minute chart. Buy when 1H trend is bullish, 20 EMA crosses above 50 EMA, and RSI > 50. Use 1:2.5 risk/reward ratio."
  }
];

export default function StrategyBuilder({ onStrategySaved }: StrategyBuilderProps) {
  const [prompt, setPrompt] = useState(PRESET_STRATEGIES[0].text);
  const [strategyName, setStrategyName] = useState("5M Gold EMA Breakout");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [parsedStrategy, setParsedStrategy] = useState<any>(null);
  const [savedStrategies, setSavedStrategies] = useState<any[]>([]);

  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const fetchCurrentStrategy = async () => {
    try {
      const res = await safeFetch(`${API_BASE}/api/strategy/current`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.name) {
          setParsedStrategy(data);
          if (data.name) setStrategyName(data.name);
          if (data.raw_prompt) setPrompt(data.raw_prompt);
        }
      }
    } catch (err) {
      console.warn("Could not fetch current strategy:", err);
    }
  };

  const fetchSavedStrategies = async () => {
    try {
      const res = await safeFetch(`${API_BASE}/api/strategy/list`);
      if (res.ok) {
        const data = await res.json();
        if (data.strategies) {
          setSavedStrategies(data.strategies);
        }
      }
    } catch (err) {
      console.warn("Could not list saved strategies:", err);
    }
  };

  useEffect(() => {
    fetchCurrentStrategy();
    fetchSavedStrategies();
  }, []);

  const handleParseStrategy = async (overridePrompt?: string, customName?: string) => {
    const textToParse = overridePrompt || prompt;
    const nameToUse = customName || strategyName;
    setLoading(true);
    setSuccessMsg("");
    setErrorMsg("");
    try {
      const res = await safeFetch(`${API_BASE}/api/strategy/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToParse, name: nameToUse })
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setParsedStrategy(data);
      setSuccessMsg("Strategy parsed & activated in trading engine!");
      fetchSavedStrategies();
      if (onStrategySaved) onStrategySaved();
    } catch (err: any) {
      console.error("Strategy parse error:", err);
      setErrorMsg("Unable to reach trading engine. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveStrategy = async () => {
    if (!strategyName.trim()) {
      setErrorMsg("Please enter a name for your strategy.");
      return;
    }
    setSaving(true);
    setSuccessMsg("");
    setErrorMsg("");
    try {
      const res = await safeFetch(`${API_BASE}/api/strategy/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: strategyName,
          prompt: prompt,
          strategy: parsedStrategy
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      if (data.strategy) {
        setParsedStrategy(data.strategy);
      }
      setSuccessMsg(`Strategy "${strategyName}" saved and activated successfully!`);
      fetchSavedStrategies();
      if (onStrategySaved) onStrategySaved();
    } catch (err: any) {
      console.error("Save strategy error:", err);
      setErrorMsg("Failed to save strategy.");
    } finally {
      setSaving(false);
    }
  };

  const handleActivateSavedStrategy = async (name: str) => {
    setLoading(true);
    setSuccessMsg("");
    setErrorMsg("");
    try {
      const res = await safeFetch(`${API_BASE}/api/strategy/activate/${encodeURIComponent(name)}`, {
        method: "POST"
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      if (data.strategy) {
        setParsedStrategy(data.strategy);
        setStrategyName(data.strategy.name || name);
        if (data.strategy.raw_prompt) setPrompt(data.strategy.raw_prompt);
      }
      setSuccessMsg(`Activated strategy "${name}"!`);
      fetchSavedStrategies();
      if (onStrategySaved) onStrategySaved();
    } catch (err: any) {
      console.error("Activate strategy error:", err);
      setErrorMsg(`Failed to activate strategy "${name}".`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs font-sans space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3.5 gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-blue-600 text-white font-bold shadow-xs">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <span>AI Strategy Builder & Rule Parser</span>
              </h3>
              <p className="text-xs text-slate-400 font-normal mt-0.5">
                Build, parse, and save custom trading strategies. Active strategies persist across sessions and page reloads.
              </p>
            </div>
          </div>

          <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1 rounded-full font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            STRATEGY PERSISTENCE ACTIVE
          </span>
        </div>

        {/* Preset Strategy Buttons */}
        <div className="space-y-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Quick Preset Strategy Templates:
          </span>
          <div className="flex flex-wrap gap-2">
            {PRESET_STRATEGIES.map((preset, i) => (
              <button
                key={i}
                onClick={() => {
                  setPrompt(preset.text);
                  setStrategyName(preset.name);
                  handleParseStrategy(preset.text, preset.name);
                }}
                className="px-3 py-1.5 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 text-slate-700 border border-slate-200 hover:border-blue-200 rounded-xl text-xs font-medium transition flex items-center gap-1.5"
              >
                <Bookmark className="w-3.5 h-3.5 text-blue-600" />
                <span>{preset.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Strategy Name & Input Prompt */}
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 block">
              Strategy Name:
            </label>
            <input
              type="text"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
              className="w-full max-w-md bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 font-semibold focus:outline-none focus:border-blue-600 focus:bg-white transition"
              placeholder="e.g. My Gold 5M Scalper"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-blue-600" />
              <span>Strategy Rules Description (Plain English):</span>
            </label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition font-mono leading-relaxed"
              placeholder="e.g. Buy XAU/USD on 5M when 20 EMA > 50 EMA and RSI > 55 with 1:2 Risk/Reward..."
            />
          </div>
        </div>

        {/* Parse & Save Actions */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => handleParseStrategy()}
              disabled={loading || !prompt.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition shadow-xs flex items-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Zap className="w-4 h-4 fill-white" />
                  <span>Parse & Activate Strategy</span>
                </>
              )}
            </button>

            <button
              onClick={handleSaveStrategy}
              disabled={saving || !strategyName.trim()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition shadow-xs flex items-center gap-2"
            >
              {saving ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Strategy to Library</span>
                </>
              )}
            </button>
          </div>

          {successMsg && (
            <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          )}

          {errorMsg && (
            <div className="flex items-center gap-1.5 text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Active Rules Breakdown */}
        {parsedStrategy && (
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between text-xs text-slate-700 border-b border-slate-200 pb-2.5 gap-2">
              <span>Strategy: <strong className="text-blue-600 font-bold">{parsedStrategy.name}</strong></span>
              <span>Target Symbol: <strong className="text-slate-900 font-bold">{parsedStrategy.symbol}</strong></span>
              <span>Risk/Reward: <strong className="text-emerald-600 font-bold">1:{parsedStrategy.risk_reward_ratio}</strong></span>
            </div>

            <div className="space-y-2">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Parsed Deterministic Rule Specifications:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {parsedStrategy.rules?.map((rule: any, idx: number) => (
                  <div
                    key={idx}
                    className="bg-white border border-slate-200 rounded-lg p-2.5 text-xs flex items-center justify-between gap-2 shadow-xs"
                  >
                    <span className="text-slate-800 font-medium">{rule.description}</span>
                    <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono border border-blue-200 font-bold">
                      {rule.condition_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Saved Custom Strategy Library */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs font-sans space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <FolderHeart className="w-5 h-5 text-blue-600" />
          <h4 className="text-sm font-bold text-slate-900">Saved Strategy Library</h4>
        </div>

        {savedStrategies.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No saved strategies found in library. Parse and click "Save Strategy to Library" above to store your custom rules.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {savedStrategies.map((item: any) => {
              const isActive = parsedStrategy?.name === item.name || item.is_active;
              return (
                <div
                  key={item.id}
                  className={`border rounded-xl p-4 flex flex-col justify-between space-y-3 transition ${
                    isActive ? "bg-emerald-50/40 border-emerald-300 shadow-xs" : "bg-slate-50 border-slate-200 hover:border-blue-200"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <h5 className="text-xs font-bold text-slate-900 truncate">{item.name}</h5>
                      {isActive && (
                        <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-md font-bold flex items-center gap-1">
                          <Check className="w-3 h-3 text-emerald-600" />
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 font-mono">
                      {item.raw_prompt || item.description || "Custom trading rules"}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] text-slate-400">
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    {!isActive && (
                      <button
                        onClick={() => handleActivateSavedStrategy(item.name)}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold transition flex items-center gap-1 text-[11px]"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Activate</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
