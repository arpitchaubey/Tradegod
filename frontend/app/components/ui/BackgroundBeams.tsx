"use client";

import React from "react";

export const BackgroundBeams = () => {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* Top Ambient Glow Spotlights */}
      <div className="absolute -top-40 left-1/4 h-[500px] w-[500px] rounded-full bg-amber-500/10 blur-[120px] animate-pulse-glow" />
      <div className="absolute top-1/3 -right-20 h-[600px] w-[600px] rounded-full bg-blue-600/10 blur-[150px] animate-pulse-glow" />
      <div className="absolute -bottom-40 left-1/3 h-[500px] w-[500px] rounded-full bg-emerald-500/10 blur-[130px] animate-pulse-glow" />

      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40" />

      {/* Radial Gradient Mask */}
      <div className="absolute inset-0 bg-slate-950 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_80%)]" />
    </div>
  );
};
