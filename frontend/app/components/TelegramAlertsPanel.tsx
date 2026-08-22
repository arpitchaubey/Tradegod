"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Send, Bell, Key, CheckCircle2, OctagonAlert, Play, Square, ShieldAlert } from "lucide-react";

interface TelegramSettings {
  bot_active: boolean;
  telegram_bot_token: string;
  telegram_chat_id: string;
  notify_on_new_signal: boolean;
  notify_on_position_close: boolean;
  notify_on_news_blackout: boolean;
  notify_on_max_loss: boolean;
  min_confidence_score: number;
  min_risk_reward_ratio: number;
  include_ai_explanation: boolean;
}

export default function TelegramAlertsPanel() {
  const [settings, setSettings] = useState<TelegramSettings>({
    bot_active: true,
    telegram_bot_token: "8804382779:AAHISLzIbffQcJfRJG7oYaO_FtY6rtFVdZY",
    telegram_chat_id: "1432053067",
    notify_on_new_signal: true,
    notify_on_position_close: true,
    notify_on_news_blackout: true,
    notify_on_max_loss: true,
    min_confidence_score: 75,
    min_risk_reward_ratio: 1.5,
    include_ai_explanation: true
  });

  const [isConnected, setIsConnected] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);

  const fetchSettings = () => {
    safeFetch(`${API_BASE}/api/bot/settings`)
      .then((res) => res.json())
      .then((data) => {
        if (data.settings) {
          setSettings((prev) => ({
            ...prev,
            ...data.settings,
            telegram_bot_token: data.settings.telegram_bot_token ?? "",
            telegram_chat_id: data.settings.telegram_chat_id ?? ""
          }));
          setIsConnected(data.is_connected);
        }
      })
      .catch((err) => console.warn("Bot Settings API offline:", err));
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleToggleBot = async () => {
    setToggling(true);
    try {
      const res = await safeFetch(`${API_BASE}/api/bot/toggle`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        setSettings((prev) => ({ ...prev, bot_active: data.bot_active }));
      }
    } catch (err) {
      console.error("Toggle bot error:", err);
    } finally {
      setToggling(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setSuccessMsg("");
    setTestResult(null);
    try {
      const res = await safeFetch(`${API_BASE}/api/bot/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      if (data.status === "success") {
        setSuccessMsg("Telegram alert settings saved successfully!");
        setIsConnected(Boolean(settings.telegram_bot_token && settings.telegram_chat_id));
      }
    } catch (err) {
      console.error("Save Telegram settings error:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleSendTestAlert = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await safeFetch(`${API_BASE}/api/bot/test-alert`, { method: "POST" });
      const data = await res.json();
      setTestResult(data);
    } catch (err) {
      setTestResult({ status: "error", message: "Failed to communicate with bot backend." });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs font-sans space-y-6">
      {/* Emergency Stop / Start Banner */}
      <div className={`p-4 rounded-2xl border flex flex-wrap items-center justify-between gap-4 transition ${
        settings.bot_active
          ? "bg-slate-900 border-slate-800 text-white shadow-xs"
          : "bg-rose-50 border-rose-200 text-rose-950 shadow-xs"
      }`}>
        <div className="flex items-center space-x-3.5">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black ${
            settings.bot_active ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-600 text-white"
          }`}>
            <OctagonAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${settings.bot_active ? "bg-emerald-500 animate-pulse" : "bg-rose-600"}`} />
              <h3 className="text-sm font-extrabold tracking-tight">
                {settings.bot_active ? "BOT ENGINE RUNNING & BROADCASTING" : "BOT ENGINE STOPPED / PAUSED"}
              </h3>
            </div>
            <p className={`text-xs mt-0.5 font-medium ${settings.bot_active ? "text-slate-400" : "text-rose-700"}`}>
              {settings.bot_active
                ? "The AI signal engine is actively scanning live markets and sending alerts."
                : "All automated trading signals and Telegram alert broadcasts are currently HALTED."}
            </p>
          </div>
        </div>

        <button
          onClick={handleToggleBot}
          disabled={toggling}
          className={`px-5 py-2.5 rounded-xl font-bold text-xs transition shadow-md flex items-center gap-2 ${
            settings.bot_active
              ? "bg-rose-600 hover:bg-rose-700 text-white"
              : "bg-emerald-600 hover:bg-emerald-700 text-white"
          }`}
        >
          {toggling ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : settings.bot_active ? (
            <>
              <Square className="w-4 h-4 fill-white" />
              <span>STOP BOT IMMEDIATELY</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>START BOT ENGINE</span>
            </>
          )}
        </button>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3.5 gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-600 text-white font-bold shadow-xs">
            <Send className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <span>Telegram Alert Dispatch System</span>
            </h3>
            <p className="text-xs text-slate-400 font-normal mt-0.5">
              Manage bot credentials, notification triggers, and live alert delivery settings.
            </p>
          </div>
        </div>

        <span
          className={`text-xs px-3 py-1 rounded-full font-medium border flex items-center gap-1.5 ${
            isConnected
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-blue-50 text-blue-700 border-blue-200"
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-blue-600"}`} />
          {isConnected ? "TELEGRAM BOT CONNECTED" : "CREDENTIALS REQUIRED"}
        </span>
      </div>

      {/* Grid: Credentials & Triggers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Credentials & Test Box */}
        <div className="space-y-4 bg-slate-50 border border-slate-200/80 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-1.5">
            <Key className="w-4 h-4 text-blue-600" />
            <span>Telegram API Credentials</span>
          </h4>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Telegram Bot Token:
              </label>
              <input
                type="text"
                value={settings.telegram_bot_token}
                onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                placeholder="e.g. 8804382779:AAHISLzIbffQcJfRJG7oYaO_FtY6rtFVdZY"
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 font-mono shadow-xs"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-700 block mb-1">
                Telegram Chat ID:
              </label>
              <input
                type="text"
                value={settings.telegram_chat_id}
                onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                placeholder="e.g. 1432053067"
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 font-mono shadow-xs"
              />
            </div>
          </div>

          <div className="pt-1">
            <button
              onClick={handleSendTestAlert}
              disabled={testing}
              className="w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition shadow-xs flex items-center justify-center gap-2"
            >
              {testing ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Send className="w-3.5 h-3.5 text-white" />
                  <span>Send Live Test Alert to Telegram</span>
                </>
              )}
            </button>

            {testResult && (
              <div
                className={`mt-2 p-2.5 rounded-lg text-xs font-medium border ${
                  testResult.status === "sent" || testResult.status === "mock_sent"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-rose-50 text-rose-700 border-rose-200"
                }`}
              >
                {testResult.message}
              </div>
            )}
          </div>
        </div>

        {/* Triggers */}
        <div className="space-y-4 bg-slate-50 border border-slate-200/80 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center gap-1.5">
            <Bell className="w-4 h-4 text-blue-600" />
            <span>Automated Notification Triggers</span>
          </h4>

          <div className="space-y-2">
            {[
              {
                key: "notify_on_new_signal",
                label: "New Trade Signal Broadcasts",
                desc: "Send instant notifications when AI generates a valid setup"
              },
              {
                key: "notify_on_position_close",
                label: "Position Exits (TP1 / TP2 / Stop Loss)",
                desc: "Notify when price reaches target exit levels"
              },
              {
                key: "notify_on_news_blackout",
                label: "Economic News Blackout Warnings",
                desc: "Notify when CPI/FOMC high volatility window activates"
              },
              {
                key: "notify_on_max_loss",
                label: "Drawdown & Capital Protection Alerts",
                desc: "Alert when max daily loss limit threshold is reached"
              }
            ].map(({ key, label, desc }) => {
              const checked = (settings as any)[key];
              return (
                <label
                  key={key}
                  onClick={() => setSettings({ ...settings, [key]: !checked })}
                  className={`flex items-start justify-between p-2.5 rounded-xl border cursor-pointer transition ${
                    checked
                      ? "bg-white border-blue-600 text-slate-900 shadow-xs"
                      : "bg-slate-50 border-slate-200 text-slate-400 hover:border-slate-300"
                  }`}
                >
                  <div className="pr-3">
                    <span className="text-xs font-semibold block">{label}</span>
                    <span className="text-[10px] text-slate-500 font-normal block mt-0.5">{desc}</span>
                  </div>
                  <div className={`w-5 h-5 rounded flex items-center justify-center shrink-0 border ${checked ? "bg-blue-600 border-blue-600 text-white font-bold text-xs" : "border-slate-300 bg-white"}`}>
                    {checked && "✓"}
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      </div>

      {/* Save Action */}
      <div className="flex items-center justify-between pt-1">
        <button
          onClick={handleSaveSettings}
          disabled={saving}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs rounded-xl transition shadow-xs flex items-center gap-2"
        >
          {saving ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>Save Telegram Alert Credentials & Settings</span>
            </>
          )}
        </button>

        {successMsg && (
          <span className="text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
            {successMsg}
          </span>
        )}
      </div>
    </div>
  );
}
