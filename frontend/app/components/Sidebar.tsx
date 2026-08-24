"use client";

import React from "react";
import * as Tooltip from "@radix-ui/react-tooltip";
import {
  LayoutDashboard,
  Brain,
  Send,
  Settings,
  Sliders,
  History,
  Sparkles,
  LogOut,
  LogIn,
  Sun,
  Moon,
  HelpCircle
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { cn } from "../lib/utils";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const navItems = [
  { id: "dashboard", label: "Dashboard",         icon: LayoutDashboard },
  { id: "omni",      label: "Omni AI Engine",    icon: Sparkles         },
  { id: "strategy",  label: "Strategy Builder",  icon: Brain            },
  { id: "backtest",  label: "Backtest Lab",       icon: History          },
  { id: "telegram",  label: "Telegram Alerts",   icon: Send             },
  { id: "settings",  label: "Settings",           icon: Settings         },
];


function NavBtn({
  id, label, icon: Icon, isActive, onClick
}: { id: string; label: string; icon: any; isActive: boolean; onClick: () => void }) {
  return (
    <Tooltip.Root delayDuration={150}>
      <Tooltip.Trigger asChild>
        <button
          onClick={(e) => {
            onClick();
            (e.currentTarget as HTMLElement).blur();
          }}
          aria-label={label}
          className={cn(
            "relative w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-150 group",
            isActive
              ? "bg-[var(--accent)] text-white shadow-sm"
              : "text-[var(--text-faint)] hover:text-[var(--text)] hover:bg-[var(--bg-subtle)]"
          )}
        >
          <Icon className="w-[18px] h-[18px]" strokeWidth={isActive ? 2.2 : 1.8} />
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[var(--accent)] rounded-r-full -ml-px" />
          )}
        </button>
      </Tooltip.Trigger>
      <Tooltip.Content
        side="right"
        sideOffset={12}
        className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg shadow-md"
        style={{
          background: "var(--bg-elevated)",
          color: "var(--text)",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow-md)"
        }}
      >
        {label}
        <Tooltip.Arrow style={{ fill: "var(--bg-elevated)" }} />
      </Tooltip.Content>
    </Tooltip.Root>
  );
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const { user, isAuthenticated, openAuthModal, openProfileModal, logout } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <Tooltip.Provider>
      <aside
        className="flex flex-col items-center justify-between w-[60px] shrink-0 h-full py-4 border-r"
        style={{
          background: "var(--bg-elevated)",
          borderColor: "var(--border)"
        }}
      >
        {/* TOP: Logo + Nav */}
        <div className="flex flex-col items-center gap-5">
          {/* Logo mark */}
          <button
            onClick={() => setActiveTab("dashboard")}
            className="w-9 h-9 flex items-center justify-center rounded-xl overflow-hidden border-2 shrink-0 transition hover:scale-105"
            style={{ borderColor: "var(--gold)" }}
            aria-label="TradeGod Dashboard"
          >
            <img
              src="/tradegod-logo.png"
              alt="TRADEGOD"
              className="w-full h-full object-cover"
              onError={(e) => {
                const t = e.target as HTMLImageElement;
                t.style.display = "none";
              }}
            />
            {/* Fallback if logo missing */}
            <span className="text-[var(--gold)] font-black text-xs hidden">TG</span>
          </button>

          {/* Divider */}
          <div className="w-6 h-px" style={{ background: "var(--border)" }} />

          {/* Nav links */}
          <nav className="flex flex-col items-center gap-1.5">
            {navItems.map(({ id, label, icon }) => (
              <NavBtn
                key={id}
                id={id}
                label={label}
                icon={icon}
                isActive={activeTab === id}
                onClick={() => setActiveTab(id)}
              />
            ))}
          </nav>
        </div>

        {/* BOTTOM: Theme toggle + User */}
        <div className="flex flex-col items-center gap-2">
          {/* Help */}
          <Tooltip.Root delayDuration={200}>
            <Tooltip.Trigger asChild>
              <button
                className="w-9 h-9 flex items-center justify-center rounded-xl transition hover:bg-[var(--bg-subtle)]"
                style={{ color: "var(--text-faint)" }}
                aria-label="Help"
              >
                <HelpCircle className="w-4 h-4" strokeWidth={1.8} />
              </button>
            </Tooltip.Trigger>
            <Tooltip.Content side="right" sideOffset={12}
              className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg"
              style={{ background: "var(--bg-elevated)", color: "var(--text)", border: "1px solid var(--border)" }}
            >
              Help & Docs
            </Tooltip.Content>
          </Tooltip.Root>

          {/* Theme Toggle */}
          <Tooltip.Root delayDuration={200}>
            <Tooltip.Trigger asChild>
              <button
                onClick={toggleTheme}
                className="w-9 h-9 flex items-center justify-center rounded-xl transition hover:bg-[var(--bg-subtle)]"
                style={{ color: "var(--text-muted)" }}
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              >
                {isDark ? (
                  <Sun className="w-4 h-4" strokeWidth={1.8} />
                ) : (
                  <Moon className="w-4 h-4" strokeWidth={1.8} />
                )}
              </button>
            </Tooltip.Trigger>
            <Tooltip.Content side="right" sideOffset={12}
              className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg"
              style={{ background: "var(--bg-elevated)", color: "var(--text)", border: "1px solid var(--border)" }}
            >
              {isDark ? "Light mode" : "Dark mode"}
            </Tooltip.Content>
          </Tooltip.Root>

          {/* User avatar / sign in */}
          {isAuthenticated && user ? (
            <Tooltip.Root delayDuration={200}>
              <Tooltip.Trigger asChild>
                <button
                  onClick={openProfileModal}
                  className="w-9 h-9 rounded-xl overflow-hidden border-2 transition hover:scale-105"
                  style={{ borderColor: "var(--accent)" }}
                  aria-label="Profile"
                >
                  <img
                    src={user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=2563eb&color=fff&size=64`}
                    alt={user.full_name}
                    className="w-full h-full object-cover"
                  />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Content side="right" sideOffset={12}
                className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg"
                style={{ background: "var(--bg-elevated)", color: "var(--text)", border: "1px solid var(--border)" }}
              >
                {user.full_name}
              </Tooltip.Content>
            </Tooltip.Root>
          ) : (
            <Tooltip.Root delayDuration={200}>
              <Tooltip.Trigger asChild>
                <button
                  onClick={() => openAuthModal("login")}
                  className="w-9 h-9 flex items-center justify-center rounded-xl transition"
                  style={{ background: "var(--accent)", color: "white" }}
                  aria-label="Sign in"
                >
                  <LogIn className="w-4 h-4" />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Content side="right" sideOffset={12}
                className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg"
                style={{ background: "var(--bg-elevated)", color: "var(--text)", border: "1px solid var(--border)" }}
              >
                Sign in
              </Tooltip.Content>
            </Tooltip.Root>
          )}

          {/* Logout (only when logged in) */}
          {isAuthenticated && (
            <Tooltip.Root delayDuration={200}>
              <Tooltip.Trigger asChild>
                <button
                  onClick={logout}
                  className="w-9 h-9 flex items-center justify-center rounded-xl transition hover:bg-[var(--red-soft)]"
                  style={{ color: "var(--text-faint)" }}
                  aria-label="Log out"
                >
                  <LogOut className="w-4 h-4" strokeWidth={1.8} />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Content side="right" sideOffset={12}
                className="z-50 px-2.5 py-1.5 text-xs font-medium rounded-lg"
                style={{ background: "var(--bg-elevated)", color: "var(--red)", border: "1px solid var(--border)" }}
              >
                Log out
              </Tooltip.Content>
            </Tooltip.Root>
          )}
        </div>
      </aside>
    </Tooltip.Provider>
  );
}
