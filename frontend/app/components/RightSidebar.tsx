"use client";

import React, { useState } from "react";
import {
  Phone,
  Video,
  MoreVertical,
  Send,
  Paperclip,
  Zap,
  Bot
} from "lucide-react";
import { API_BASE, safeFetch } from "../utils/api";

export default function RightSidebar() {
  const [inputMsg, setInputMsg] = useState("");
  const [messages, setMessages] = useState<
    { sender: "user" | "bot"; text: string; time: string }[]
  >([
    {
      sender: "bot",
      text: "Hi Margaret! I'm watching XAU/USD live on 5M timeframe. Ask for live signal analysis anytime.",
      time: "10:15 AM"
    }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;

    const userText = inputMsg.trim();
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    setMessages((prev) => [...prev, { sender: "user", text: userText, time: timeStr }]);
    setInputMsg("");
    setLoading(true);

    try {
      const res = await safeFetch(`${API_BASE}/api/signals/generate?symbol=XAU%2FUSD`, {
        method: "POST"
      });
      const data = await res.json();
      const replyText = data
        ? `⚡ Signal Analysis: ${data.direction.toUpperCase()} setup on ${data.symbol}. Entry: $${data.entry_price}, SL: $${data.stop_loss}, TP2: $${data.take_profit_2}. Score: ${data.confidence_score}%`
        : "⚪ Analysis complete: No valid setup at this time.";

      setMessages((prev) => [...prev, { sender: "bot", text: replyText, time: timeStr }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Unable to communicate with trading engine backend.", time: timeStr }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="w-80 bg-white border-l border-slate-200/80 p-6 flex flex-col justify-between shrink-0 h-screen sticky top-0 font-sans">
      <div className="space-y-6">
        {/* Profile / Bot Card */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-5 text-center space-y-3">
          <div className="relative w-16 h-16 mx-auto">
            <div className="w-16 h-16 rounded-full bg-blue-600 p-0.5 shadow-sm flex items-center justify-center text-white text-xl">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <span className="absolute bottom-0 right-0 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white" />
          </div>

          <div>
            <h3 className="font-extrabold text-slate-900 text-sm">
              Tradegod Bot
            </h3>
            <span className="text-xs text-slate-400 font-medium">@tradegod_bot</span>
          </div>

          <div className="flex items-center justify-center space-x-2.5 pt-1">
            <button className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-blue-600 transition shadow-xs">
              <Phone className="w-3.5 h-3.5" />
            </button>
            <button className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-blue-600 transition shadow-xs">
              <Video className="w-3.5 h-3.5" />
            </button>
            <button className="p-2 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-blue-600 transition shadow-xs">
              <MoreVertical className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Activity & Chat Stream Header */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Live Activity & Bot Chat
            </h4>
            <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-bold">
              ONLINE
            </span>
          </div>

          {/* Messages Stream */}
          <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col space-y-1 ${
                  m.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div className="flex items-center space-x-1.5 text-[10px] text-slate-400">
                  <span className="font-bold">{m.sender === "user" ? "Margaret" : "Tradegod AI"}</span>
                  <span>•</span>
                  <span>{m.time}</span>
                </div>
                <div
                  className={`p-3 rounded-xl text-xs leading-relaxed max-w-[92%] ${
                    m.sender === "user"
                      ? "bg-blue-600 text-white font-bold rounded-tr-none shadow-xs"
                      : "bg-slate-100 text-slate-800 border border-slate-200/80 rounded-tl-none font-medium"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center space-x-2 text-xs text-blue-600 font-bold animate-pulse">
                <Zap className="w-3.5 h-3.5" />
                <span>Engine analyzing XAU/USD...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="pt-3 border-t border-slate-100">
        <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl p-1 focus-within:border-blue-600 focus-within:bg-white transition">
          <input
            type="text"
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            placeholder="Write a message..."
            className="w-full bg-transparent px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none font-medium"
          />
          <div className="flex items-center space-x-1 pr-1">
            <button
              type="button"
              className="p-1 text-slate-400 hover:text-slate-600 transition"
            >
              <Paperclip className="w-3.5 h-3.5" />
            </button>
            <button
              type="submit"
              disabled={loading || !inputMsg.trim()}
              className="p-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition font-bold"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </form>
    </aside>
  );
}
