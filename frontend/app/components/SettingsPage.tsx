"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import {
  Settings,
  Key,
  Sliders,
  Bell,
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Database,
  Globe,
  Volume2,
  VolumeX,
  Moon,
  Sun,
  ShieldCheck
} from "lucide-react";

export default function SettingsPage() {
  const [settingsData, setSettingsData] = useState<any>({
    theme: "light",
    chart_default_timeframe: "5m",
    twelvedata_api_key: "",
    oanda_account_id: "",
    oanda_api_token: "",
    sound_alerts_enabled: true,
    browser_notifications: true,
    auto_refresh_rate_sec: 5
  });

  const [healthData, setHealthData] = useState<any>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchSettings = () => {
    safeFetch(`${API_BASE}/api/settings/`)
      .then((res) => res.json())
      .then((data) => {
        if (data.settings) {
          setSettingsData((prev: any) => ({
            ...prev,
            ...data.settings,
            twelvedata_api_key: data.settings.twelvedata_api_key ?? "",
            oanda_account_id: data.settings.oanda_account_id ?? "",
            oanda_api_token: data.settings.oanda_api_token ?? "",
            chart_default_timeframe: data.settings.chart_default_timeframe ?? "5m"
          }));
        }
      })
      .catch((err) => {
        console.warn("Settings API error:", err);
        showToast("error", "Failed to connect to backend settings store.");
      });
  };

  const fetchHealth = () => {
    setLoadingHealth(true);
    safeFetch(`${API_BASE}/api/settings/health`)
      .then((res) => res.json())
      .then((data) => setHealthData(data))
      .catch((err) => console.warn("Health check error:", err))
      .finally(() => setLoadingHealth(false));
  };

  useEffect(() => {
    fetchSettings();
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (type: "success" | "error", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await safeFetch(`${API_BASE}/api/settings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settingsData)
      });
      const data = await res.json();
      if (data.status === "success") {
        showToast("success", "Global settings & system configuration saved!");
      } else {
        showToast("error", "Failed to save settings.");
      }
    } catch (err) {
      showToast("error", "Error saving system settings to backend.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 font-sans animate-fade-in">
      {/* Top Banner Header */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-blue-600 text-white rounded-xl shadow-xs font-black">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <span>System & API Settings</span>
            </h2>
            <p className="text-xs text-slate-500 font-normal mt-0.5">
              Manage platform preferences, API keys, notification triggers, and live backend health diagnostics.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchHealth}
            disabled={loadingHealth}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? "animate-spin text-blue-600" : ""}`} />
            <span>Refresh Diagnostics</span>
          </button>

          <span className="text-xs px-3 py-1.5 rounded-xl font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            {healthData ? `BACKEND HEALTHY (${healthData.latency_ms}ms)` : "CONNECTING..."}
          </span>
        </div>
      </div>

      {/* Toast Notification Banner */}
      {toast && (
        <div
          className={`p-4 rounded-xl border text-xs font-semibold flex items-center justify-between transition-all duration-300 ${
            toast.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200 shadow-xs"
              : "bg-rose-50 text-rose-800 border-rose-200 shadow-xs"
          }`}
        >
          <div className="flex items-center space-x-2">
            {toast.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{toast.message}</span>
          </div>
          <button onClick={() => setToast(null)} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
      )}

      {/* 2-Column Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: API Integrations & Secret Keys */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Key className="w-4 h-4 text-blue-600" />
            <span>API Integrations & Connector Keys</span>
          </h3>

          <div className="space-y-3.5">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                TwelveData API Key (Live Candles):
              </label>
              <input
                type="text"
                value={settingsData.twelvedata_api_key}
                onChange={(e) => setSettingsData({ ...settingsData, twelvedata_api_key: e.target.value })}
                placeholder="Enter 32-character TwelveData key"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs font-mono text-slate-900 focus:outline-none focus:border-blue-600 transition"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                OANDA Live Account ID:
              </label>
              <input
                type="text"
                value={settingsData.oanda_account_id}
                onChange={(e) => setSettingsData({ ...settingsData, oanda_account_id: e.target.value })}
                placeholder="e.g. 001-001-1234567-001"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs font-mono text-slate-900 focus:outline-none focus:border-blue-600 transition"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                OANDA v20 Bearer API Token:
              </label>
              <input
                type="password"
                value={settingsData.oanda_api_token}
                onChange={(e) => setSettingsData({ ...settingsData, oanda_api_token: e.target.value })}
                placeholder="••••••••••••••••••••••••••••••••"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs font-mono text-slate-900 focus:outline-none focus:border-blue-600 transition"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Platform Preferences */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sliders className="w-4 h-4 text-blue-600" />
            <span>Platform UI & Sound Preferences</span>
          </h3>

          <div className="space-y-3.5">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Default Chart Timeframe:
              </label>
              <select
                value={settingsData.chart_default_timeframe}
                onChange={(e) => setSettingsData({ ...settingsData, chart_default_timeframe: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs font-semibold text-slate-900 focus:outline-none focus:border-blue-600 transition cursor-pointer"
              >
                <option value="1m">1 Minute (Scalping)</option>
                <option value="5m">5 Minutes (Default Setup)</option>
                <option value="15m">15 Minutes (Intraday)</option>
                <option value="1h">1 Hour (Trend Alignment)</option>
              </select>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-2.5">
                {settingsData.sound_alerts_enabled ? (
                  <Volume2 className="w-4 h-4 text-blue-600" />
                ) : (
                  <VolumeX className="w-4 h-4 text-slate-400" />
                )}
                <div>
                  <span className="text-xs font-semibold block text-slate-900">Audio Signal Alerts</span>
                  <span className="text-[10px] text-slate-500 font-normal">Play sound chime when new trade signal generates</span>
                </div>
              </div>
              <button
                onClick={() => setSettingsData({ ...settingsData, sound_alerts_enabled: !settingsData.sound_alerts_enabled })}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  settingsData.sound_alerts_enabled ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-600"
                }`}
              >
                {settingsData.sound_alerts_enabled ? "ON" : "OFF"}
              </button>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-2.5">
                <Bell className="w-4 h-4 text-blue-600" />
                <div>
                  <span className="text-xs font-semibold block text-slate-900">Browser Push Notifications</span>
                  <span className="text-[10px] text-slate-500 font-normal">Show popup toast on trade execution</span>
                </div>
              </div>
              <button
                onClick={() => setSettingsData({ ...settingsData, browser_notifications: !settingsData.browser_notifications })}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  settingsData.browser_notifications ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-600"
                }`}
              >
                {settingsData.browser_notifications ? "ON" : "OFF"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: Live System Health Diagnostics Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs space-y-4">
        <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
          <Activity className="w-4 h-4 text-blue-600" />
          <span>Real-time System Health & Service Diagnostics</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {healthData?.services ? (
            Object.entries(healthData.services).map(([serviceKey, serviceObj]: [string, any]) => (
              <div key={serviceKey} className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {serviceKey.replace("_", " ")}
                </span>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold text-slate-900 uppercase">
                    {serviceObj.status}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
                {serviceObj.ping && (
                  <span className="text-[10px] text-emerald-600 font-mono block">Latency: {serviceObj.ping}</span>
                )}
                {serviceObj.provider && (
                  <span className="text-[10px] text-slate-500 font-mono block">{serviceObj.provider}</span>
                )}
              </div>
            ))
          ) : (
            <div className="col-span-4 p-4 text-center text-xs text-slate-400">Loading system diagnostics...</div>
          )}
        </div>
      </div>

      {/* Save Action Footer */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl transition shadow-xs flex items-center gap-2"
        >
          {saving ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4" />
              <span>Save System Settings & Integrations</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
