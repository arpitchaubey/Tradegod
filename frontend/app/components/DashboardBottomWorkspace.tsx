"use client";

import React, { useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import PositionsTable from "./PositionsTable";
import OmniSystemPipeline from "./OmniSystemPipeline";
import NewsFilterWidget from "./NewsFilterWidget";
import BacktestPanel from "./BacktestPanel";
import { Briefcase, Zap, Globe, History } from "lucide-react";

interface DashboardBottomWorkspaceProps {
  backtestReport?: any;
  onRunBacktest?: () => void;
  loadingBacktest?: boolean;
}

const tabs = [
  { id: "positions", label: "Positions",  icon: Briefcase },
  { id: "pipeline",  label: "System Flow", icon: Zap       },
  { id: "news",      label: "News Impact", icon: Globe      },
  { id: "backtest",  label: "Backtest",    icon: History    },
];

export default function DashboardBottomWorkspace({
  backtestReport, onRunBacktest, loadingBacktest = false
}: DashboardBottomWorkspaceProps) {
  return (
    <Tabs.Root defaultValue="positions" className="card overflow-hidden">
      {/* Tab list */}
      <Tabs.List
        className="flex items-center"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        {tabs.map(({ id, label, icon: Icon }) => (
          <Tabs.Trigger
            key={id}
            value={id}
            className="flex items-center gap-2 px-4 py-3 text-xs font-semibold transition-all outline-none border-b-2 -mb-px cursor-pointer"
            style={
              {
                "--active-color": "var(--accent)",
                "--active-bg": "transparent",
                color: "var(--text-muted)",
                borderBottomColor: "transparent",
              } as any
            }
            data-state-active-color="var(--accent)"
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </Tabs.Trigger>
        ))}
      </Tabs.List>

      {/* Tab panels */}
      <Tabs.Content value="positions" className="animate-fade-up">
        <PositionsTable />
      </Tabs.Content>
      <Tabs.Content value="pipeline" className="animate-fade-up">
        <OmniSystemPipeline />
      </Tabs.Content>
      <Tabs.Content value="news" className="animate-fade-up">
        <NewsFilterWidget />
      </Tabs.Content>
      <Tabs.Content value="backtest" className="animate-fade-up">
        <BacktestPanel
          report={backtestReport}
          onRunBacktest={onRunBacktest || (() => {})}
          loading={loadingBacktest}
        />
      </Tabs.Content>
    </Tabs.Root>
  );
}
