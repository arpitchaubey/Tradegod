import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  subsets: ["latin"],
  variable: "--font-poppins"
});

export const metadata: Metadata = {
  title: "Tradegod AI - Signal & Execution Engine",
  description: "Live XAU/USD trading bot, natural language AI strategy parser, and alert system.",
};

import { AuthProvider } from "./context/AuthContext";
import AuthModal from "./components/AuthModal";
import ProfileModal from "./components/ProfileModal";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${poppins.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <AuthProvider>
          {children}
          <AuthModal />
          <ProfileModal />
        </AuthProvider>
      </body>
    </html>
  );
}
