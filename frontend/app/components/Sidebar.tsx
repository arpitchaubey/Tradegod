"use client";

import React from "react";
import {
  Home,
  Brain,
  Send,
  Settings,
  HelpCircle,
  LogOut,
  Zap,
  Sliders
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { User as UserIcon, LogIn, ChevronRight, Sparkles } from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const { user, isAuthenticated, openAuthModal, openProfileModal, logout } = useAuth();

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Home },
    { id: "strategy", label: "AI Strategy Builder", icon: Brain },
    { id: "bot", label: "Bot Control Panel", icon: Sliders },
    { id: "telegram", label: "Telegram Alerts", icon: Send },
    { id: "settings", label: "Settings", icon: Settings }
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 p-6 flex flex-col justify-between shrink-0 h-full font-sans">
      {/* Brand Logo */}
      <div className="space-y-8">
        <div className="flex items-center space-x-3">
          <img
            src="/tradegod-logo.png"
            alt="TRADE GOD Logo"
            className="w-10 h-10 rounded-full border border-amber-500/30 object-cover shadow-sm bg-slate-900"
          />
          <div>
            <h1 className="text-base font-black text-slate-900 tracking-tight flex items-center gap-1">
              <span>TRADE</span>
              <span className="text-amber-600">GOD</span>
            </h1>
            <span className="text-[9px] text-amber-700/80 font-bold uppercase tracking-wider block">
              Quantitative Insights
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="space-y-1">
          {navItems.map(({ id, label, icon: Icon }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs transition-all duration-150 ${
                  isActive
                    ? "bg-blue-600 text-white shadow-xs font-semibold"
                    : "text-slate-600 hover:text-blue-600 hover:bg-blue-50/60 font-medium"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                  <span>{label}</span>
                </div>
                {id === "strategy" && (
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Account Profile Footer */}
      <div className="space-y-3 pt-3 border-t border-slate-100">
        {isAuthenticated && user ? (
          <button
            onClick={openProfileModal}
            className="w-full p-2.5 bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 hover:border-blue-200 rounded-2xl transition flex items-center justify-between text-left group"
          >
            <div className="flex items-center space-x-3 min-w-0">
              <img
                src={user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=2563eb&color=fff`}
                alt={user.full_name}
                className="w-9 h-9 rounded-xl border border-blue-500/20 object-cover shrink-0"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <h4 className="text-xs font-bold text-slate-800 truncate group-hover:text-blue-600">{user.full_name}</h4>
                  <span className="px-1.5 py-0.2 bg-blue-100 text-blue-700 text-[9px] font-bold rounded-md">
                    {user.plan_tier || "PRO"}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 shrink-0" />
          </button>
        ) : (
          <button
            onClick={() => openAuthModal("login")}
            className="w-full p-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl shadow-md transition flex items-center justify-center space-x-2 text-xs font-semibold"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In / Create Account</span>
          </button>
        )}

        <div className="space-y-1 text-xs font-medium text-slate-500">
          <button className="w-full flex items-center space-x-3 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition text-[11px]">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>Help & documentation</span>
          </button>
          {isAuthenticated && (
            <button
              onClick={logout}
              className="w-full flex items-center space-x-3 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition text-rose-600 text-[11px]"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log out</span>
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
