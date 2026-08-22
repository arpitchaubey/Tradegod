"use client";

import React, { useState } from "react";
import { X, Lock, Mail, User, ShieldCheck, ArrowRight, Zap, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { API_BASE, safeFetch } from "../utils/api";

export default function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, authModalMode, login, isAuthenticated } = useAuth();
  
  const [mode, setMode] = useState<"login" | "signup">(authModalMode || "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Sync mode if changed from props
  React.useEffect(() => {
    setMode(authModalMode);
    setErrorMsg("");
  }, [authModalMode, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setLoading(true);

    const endpoint = mode === "login" ? `${API_BASE}/api/auth/login` : `${API_BASE}/api/auth/register`;
    const payload = mode === "login" ? { email, password } : { email, password, full_name: fullName };

    try {
      const res = await safeFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed");
      }

      login(data);
      // Reset form
      setEmail("");
      setPassword("");
      setFullName("");
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in duration-200">
        
        {/* Header Branding */}
        <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6 text-white relative">
          {isAuthenticated && (
            <button
              onClick={closeAuthModal}
              className="absolute top-4 right-4 p-2 text-white/80 hover:text-white rounded-full hover:bg-white/10 transition"
            >
              <X className="w-5 h-5" />
            </button>
          )}
          
          <div className="flex items-center space-x-3 mb-3">
            <img
              src="/tradegod-logo.png"
              alt="TRADE GOD Logo"
              className="w-10 h-10 rounded-full border border-amber-400/40 object-cover shadow-md bg-slate-950"
            />
            <div>
              <span className="font-black text-lg tracking-tight block text-white">TRADE GOD</span>
              <span className="text-[10px] text-amber-200 uppercase font-bold tracking-widest block -mt-1">Quantitative Insights</span>
            </div>
          </div>

          <h2 className="text-xl font-bold">
            {mode === "login" ? "Welcome Back Trader" : "Create Trader Account"}
          </h2>
          <p className="text-xs text-blue-100 mt-1">
            {mode === "login" 
              ? "Access your live AI strategy signal engine & active risk dashboard."
              : "Start automated gold strategy monitoring with smart execution limits."}
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-slate-100 bg-slate-50/50 p-1.5 gap-1">
          <button
            type="button"
            onClick={() => { setMode("login"); setErrorMsg(""); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl transition ${
              mode === "login"
                ? "bg-white text-blue-600 shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => { setMode("signup"); setErrorMsg(""); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl transition ${
              mode === "signup"
                ? "bg-white text-blue-600 shadow-xs"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 text-xs rounded-xl flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{errorMsg}</span>
            </div>
          )}

          {mode === "signup" && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 block">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Arpit Sharma"
                  className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-hidden transition"
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 block">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="trader@tradegod.ai"
                className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-hidden transition"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 block">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-hidden transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-md transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <>
                <span>{mode === "login" ? "Log In to Engine" : "Create Account"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <p className="text-[11px] text-center text-slate-500 pt-2">
            By continuing, you agree to TradeGod's Terms of Service and Risk Disclaimer.
          </p>
        </form>

      </div>
    </div>
  );
}
