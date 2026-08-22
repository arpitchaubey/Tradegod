"use client";

import React, { useState } from "react";
import { cn } from "../../utils/cn";

export const CardSpotlight = ({
  children,
  className,
  spotlightColor = "rgba(245, 158, 11, 0.15)"
}: {
  children: React.ReactNode;
  className?: string;
  spotlightColor?: string;
}) => {
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isFocused, setIsFocused] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsFocused(true)}
      onMouseLeave={() => setIsFocused(false)}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl transition duration-300 hover:border-amber-500/40 hover:shadow-2xl hover:shadow-amber-500/5",
        className
      )}
    >
      {/* Spotlight Glow Overlay */}
      <div
        className="pointer-events-none absolute -inset-px transition duration-300"
        style={{
          opacity: isFocused ? 1 : 0,
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 40%)`
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
};
