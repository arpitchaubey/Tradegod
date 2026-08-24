"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "dark",
  toggleTheme: () => {},
  isDark: true
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");

  // Run ONCE on mount — read persisted preference
  useEffect(() => {
    const stored = (localStorage.getItem("tradegod-theme") as Theme) || "dark";
    // Only call setTheme if it actually differs from default to avoid extra render
    if (stored !== "dark") {
      setTheme(stored);
    }
    // Always sync the <html> class (covers the default "dark" case too)
    document.documentElement.classList.toggle("dark", stored === "dark");
  }, []);

  // Sync <html> class whenever theme changes (after toggle)
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  // Stable callback — won't change between renders
  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      localStorage.setItem("tradegod-theme", next);
      return next;
    });
  }, []);

  // Memoized value object — only changes when theme changes, not on every render
  const value = useMemo<ThemeContextValue>(
    () => ({ theme, toggleTheme, isDark: theme === "dark" }),
    [theme, toggleTheme]
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
