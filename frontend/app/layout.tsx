import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import AuthModal from "./components/AuthModal";
import ProfileModal from "./components/ProfileModal";

const inter = Inter({
  weight: ["300", "400", "500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

export const metadata: Metadata = {
  title: "TradeGod AI — Quantitative Signal & Execution Terminal",
  description: "Live XAU/USD AI trading bot, multi-timeframe strategy engine, and institutional-grade alert system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} h-full`} suppressHydrationWarning>
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <AuthProvider>
            {children}
            <AuthModal />
            <ProfileModal />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
