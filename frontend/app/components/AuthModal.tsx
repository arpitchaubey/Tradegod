"use client";

import React, { useState } from "react";
import { 
  X, 
  Lock, 
  Mail, 
  User, 
  ShieldCheck, 
  ArrowRight, 
  KeyRound, 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  ArrowLeft, 
  Loader2, 
  Sparkles,
  RefreshCw
} from "lucide-react";
import { useAuth, AuthModalMode } from "../context/AuthContext";
import { API_BASE, safeFetch } from "../utils/api";

export default function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, authModalMode, login, isAuthenticated } = useAuth();
  
  const [mode, setMode] = useState<AuthModalMode>(authModalMode || "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [resetCode, setResetCode] = useState("");
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Sync mode if changed from context
  React.useEffect(() => {
    setMode(authModalMode);
    setErrorMsg("");
    setSuccessMsg("");
  }, [authModalMode, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  const handleLoginOrSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
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
        throw new Error(data.detail || (mode === "login" ? "Login failed" : "Registration failed"));
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

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    setLoading(true);

    try {
      const res = await safeFetch(`${API_BASE}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Unable to request password reset");
      }

      // Security: Reset code is delivered exclusively via email, never prefilled
      setResetCode("");
      setSuccessMsg(data.message || `Verification code sent to ${email}. Please check your email.`);
      setTimeout(() => {
        setMode("reset");
        setErrorMsg("");
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate reset code");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (password !== confirmPassword) {
      setErrorMsg("New passwords do not match");
      return;
    }

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      const res = await safeFetch(`${API_BASE}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          reset_code: resetCode,
          new_password: password
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Password reset failed");
      }

      setSuccessMsg("Password reset! Entering terminal...");
      setTimeout(() => {
        login(data);
        setPassword("");
        setConfirmPassword("");
        setResetCode("");
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reset password");
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setEmail("trader@tradegod.ai");
    setPassword("password123");
    setErrorMsg("");
    setSuccessMsg("");
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      {/* Ambient background glow */}
      <div className="absolute w-72 h-72 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -z-10" />

      {/* Main Glass Card */}
      <div className="bg-[#0b0e14]/95 text-zinc-100 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.8),0_0_0_1px_rgba(255,255,255,0.06)] max-w-[400px] w-full p-6 sm:p-7 relative border border-white/[0.08] animate-in fade-in zoom-in-95 duration-150">
        
        {/* Top bar: Brand + Close */}
        <div className="flex items-center justify-between pb-4">
          <div className="flex items-center gap-2.5">
            <img
              src="/tradegod-logo.png"
              alt="TradeGod"
              className="w-7 h-7 rounded-lg border border-amber-400/30 object-cover bg-black"
            />
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-xs tracking-wider text-white uppercase">TRADE GOD</span>
              <span className="text-[9px] font-semibold text-amber-300 bg-amber-400/10 border border-amber-400/20 px-1.5 py-0.2 rounded uppercase">
                QUANT
              </span>
            </div>
          </div>

          <button
            onClick={closeAuthModal}
            className="text-zinc-500 hover:text-zinc-200 p-1.5 rounded-lg hover:bg-white/5 transition"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Heading */}
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white tracking-tight">
            {mode === "login" && "Sign In"}
            {mode === "signup" && "Create Account"}
            {mode === "forgot" && "Reset Password"}
            {mode === "reset" && "Set New Password"}
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            {mode === "login" && "Access your live AI strategy signal engine"}
            {mode === "signup" && "Start automated gold strategy monitoring"}
            {mode === "forgot" && "Enter your email to receive a 6-digit reset code"}
            {mode === "reset" && "Enter your code and choose a new password"}
          </p>
        </div>

        {/* Segmented Mode Switcher */}
        {(mode === "login" || mode === "signup") ? (
          <div className="grid grid-cols-2 bg-zinc-900/80 p-1 rounded-xl border border-white/[0.05] mb-4 text-xs font-medium">
            <button
              type="button"
              onClick={() => { setMode("login"); setErrorMsg(""); setSuccessMsg(""); }}
              className={`py-1.5 rounded-lg transition text-center ${
                mode === "login"
                  ? "bg-zinc-800 text-white shadow-xs"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Log In
            </button>
            <button
              type="button"
              onClick={() => { setMode("signup"); setErrorMsg(""); setSuccessMsg(""); }}
              className={`py-1.5 rounded-lg transition text-center ${
                mode === "signup"
                  ? "bg-zinc-800 text-white shadow-xs"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Sign Up
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between pb-3 text-xs">
            <button
              type="button"
              onClick={() => { setMode("login"); setErrorMsg(""); setSuccessMsg(""); }}
              className="flex items-center gap-1 text-zinc-400 hover:text-blue-400 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to log in</span>
            </button>
            <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-mono">
              {mode === "forgot" ? "Step 1/2" : "Step 2/2"}
            </span>
          </div>
        )}

        {/* Alerts */}
        {errorMsg && (
          <div className="mb-3.5 p-2.5 bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-start gap-2">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-rose-400 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-3.5 p-2.5 bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs rounded-xl flex items-start gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-400 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* FORM CONTENT */}
        {(mode === "login" || mode === "signup") && (
          <form onSubmit={handleLoginOrSignup} className="space-y-3">
            {mode === "signup" && (
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-zinc-400">Full Name</label>
                <div className="relative">
                  <User className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Trader Name"
                    className="w-full pl-9 pr-3.5 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-[11px] font-medium text-zinc-400">Email Address</label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@tradegod.ai"
                  className="w-full pl-9 pr-3.5 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-medium text-zinc-400">Password</label>
                {mode === "login" && (
                  <button
                    type="button"
                    onClick={() => { setMode("forgot"); setErrorMsg(""); setSuccessMsg(""); }}
                    className="text-[11px] text-zinc-400 hover:text-blue-400 transition"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-9 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300 transition"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-2.5 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white font-medium text-xs rounded-xl shadow-[0_0_20px_rgba(37,99,235,0.25)] transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              ) : (
                <>
                  <span>{mode === "login" ? "Log In to Engine" : "Create Account"}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            {/* Subtle Demo Account Pill */}
            {mode === "login" && (
              <div className="pt-3 mt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-zinc-500">
                <span className="truncate">Demo: trader@tradegod.ai</span>
                <button
                  type="button"
                  onClick={fillDemoCredentials}
                  className="text-amber-400/90 hover:text-amber-300 hover:underline font-medium transition shrink-0 ml-2"
                >
                  Auto Fill
                </button>
              </div>
            )}
          </form>
        )}

        {/* FORGOT PASSWORD FORM */}
        {mode === "forgot" && (
          <form onSubmit={handleForgotPassword} className="space-y-3">
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-zinc-400">Account Email</label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@tradegod.ai"
                  className="w-full pl-9 pr-3.5 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white font-medium text-xs rounded-xl shadow-[0_0_20px_rgba(37,99,235,0.25)] transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              ) : (
                <>
                  <span>Send Reset Code</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>
        )}

        {/* RESET PASSWORD FORM */}
        {mode === "reset" && (
          <form onSubmit={handleResetPassword} className="space-y-3">
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-zinc-400">6-Digit Code</label>
              <div className="relative">
                <KeyRound className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value.trim())}
                  placeholder="123456"
                  className="w-full pl-9 pr-3.5 py-2 text-xs font-mono tracking-widest bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-medium text-zinc-400">New Password</label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="w-full pl-9 pr-9 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300 transition"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-medium text-zinc-400">Confirm New Password</label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 absolute left-3 top-3 text-zinc-500" />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="w-full pl-9 pr-9 py-2 text-xs bg-zinc-900/60 border border-zinc-800 rounded-xl text-zinc-100 placeholder-zinc-500 focus:outline-hidden focus:border-blue-500/80 focus:bg-zinc-900 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300 transition"
                >
                  {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 active:scale-[0.99] text-white font-medium text-xs rounded-xl shadow-[0_0_20px_rgba(37,99,235,0.25)] transition flex items-center justify-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              ) : (
                <>
                  <span>Save Password & Log In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={() => { setMode("forgot"); setErrorMsg(""); setSuccessMsg(""); }}
                className="text-[11px] text-zinc-500 hover:text-zinc-300 transition inline-flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Resend verification code</span>
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}
