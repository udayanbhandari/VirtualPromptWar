import React from "react";
import type { RiskLevel } from "../types";

interface RiskBadgeProps {
  level: RiskLevel;
  className?: string;
}

const RISK_CONFIG: Record<
  RiskLevel,
  { label: string; bg: string; text: string; border: string; dot: string }
> = {
  low: {
    label: "Low Risk",
    bg: "bg-[#10241b]",
    text: "text-[#86efac]",
    border: "border-[#1b4332]",
    dot: "bg-[#4ade80]",
  },
  medium: {
    label: "Medium Risk",
    bg: "bg-[#291b10]",
    text: "text-[#fde047]",
    border: "border-[#4a2e15]",
    dot: "bg-[#eab308]",
  },
  high: {
    label: "High Risk",
    bg: "bg-[#2d1417]",
    text: "text-[#fca5a5]",
    border: "border-[#542027]",
    dot: "bg-[#f87171]",
  },
  critical: {
    label: "Critical Risk",
    bg: "bg-[#331116]",
    text: "text-[#fda4af]",
    border: "border-[#5c1d24]",
    dot: "bg-[#fb7185]",
  },
};

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, className = "" }) => {
  const config = RISK_CONFIG[level] || RISK_CONFIG.low;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-medium tracking-wide uppercase border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
};
