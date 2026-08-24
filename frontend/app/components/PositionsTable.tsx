"use client";

import React, { useState, useEffect } from "react";
import { API_BASE, safeFetch } from "../utils/api";
import { Briefcase, XCircle, TrendingUp, TrendingDown } from "lucide-react";

export default function PositionsTable() {
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchPositions = () => {
    safeFetch(`${API_BASE}/api/execution/positions`)
      .then((r) => r.json())
      .then((d) => { if (d.positions) setPositions(d.positions); })
      .catch(() => {});
  };

  useEffect(() => {
    fetchPositions();
    const t = setInterval(fetchPositions, 3000);
    return () => clearInterval(t);
  }, []);

  const handleClosePosition = (id: string, price: number) => {
    setLoading(true);
    safeFetch(`${API_BASE}/api/execution/positions/${encodeURIComponent(id)}/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exit_price: price })
    }).then(() => fetchPositions()).catch(() => {}).finally(() => setLoading(false));
  };

  const handleCloseAll = () => {
    setLoading(true);
    safeFetch(`${API_BASE}/api/execution/close-all`, { method: "POST" })
      .then(() => fetchPositions()).catch(() => {}).finally(() => setLoading(false));
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2.5">
          <Briefcase className="w-4 h-4" style={{ color: "var(--accent)" }} />
          <span className="text-sm font-semibold" style={{ color: "var(--text)" }}>
            Active Positions
          </span>
          <span
            className="badge"
            style={{
              background: positions.length > 0 ? "rgba(37,99,235,0.1)" : "var(--bg-subtle)",
              color: positions.length > 0 ? "var(--accent)" : "var(--text-faint)",
              border: "1px solid var(--border)"
            }}
          >
            {positions.length} Open
          </span>
        </div>

        {positions.length > 0 && (
          <button
            onClick={handleCloseAll}
            disabled={loading}
            className="btn btn-danger"
            style={{ fontSize: "11px", padding: "4px 10px" }}
          >
            <XCircle className="w-3.5 h-3.5" />
            Close All
          </button>
        )}
      </div>

      {/* Table or empty */}
      {positions.length === 0 ? (
        <div
          className="py-10 text-center text-xs"
          style={{ color: "var(--text-faint)" }}
        >
          No open positions — active trades appear here automatically.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="tbl">
            <thead>
              <tr>
                {["Symbol", "Direction", "Lots", "Entry", "SL", "TP2", "PnL", ""].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => {
                const isBuy = pos.direction === "BUY" || pos.direction === "long";
                const pnl = pos.unrealized_pnl || 0;
                return (
                  <tr key={pos.position_id}>
                    <td>
                      <span className="font-bold font-mono" style={{ color: "var(--accent)" }}>
                        {pos.symbol}
                      </span>
                    </td>
                    <td>
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold uppercase"
                        style={{
                          background: isBuy ? "var(--green-soft)" : "var(--red-soft)",
                          color: isBuy ? "var(--green)" : "var(--red)"
                        }}
                      >
                        {isBuy ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {pos.direction}
                      </span>
                    </td>
                    <td className="font-mono font-medium" style={{ color: "var(--text-muted)" }}>{pos.size_lots}</td>
                    <td className="font-mono font-semibold">${pos.entry_price?.toFixed(2)}</td>
                    <td className="font-mono" style={{ color: "var(--red)" }}>${pos.stop_loss?.toFixed(2)}</td>
                    <td className="font-mono" style={{ color: "var(--green)" }}>${pos.take_profit_2?.toFixed(2)}</td>
                    <td
                      className="font-mono font-bold"
                      style={{ color: pnl >= 0 ? "var(--green)" : "var(--red)" }}
                    >
                      {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)}
                    </td>
                    <td>
                      <button
                        onClick={() => handleClosePosition(pos.position_id, pos.current_price || pos.entry_price)}
                        disabled={loading}
                        className="btn btn-ghost"
                        style={{ fontSize: "11px", padding: "3px 10px" }}
                      >
                        Close
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
