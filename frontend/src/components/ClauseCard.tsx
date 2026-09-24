import React, { useState } from "react";
import type { Clause } from "../types";
import { RiskBadge } from "./RiskBadge";

interface ClauseCardProps {
  clause: Clause;
  onJumpToClause?: (clauseId: string) => void;
}

export const ClauseCard: React.FC<ClauseCardProps> = ({ clause, onJumpToClause }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      id={clause.id}
      className={`border rounded-lg transition-colors duration-150 ${
        clause.riskLevel === "high" || clause.riskLevel === "critical"
          ? "border-[#3d1e24] bg-[#0d1424]"
          : clause.riskLevel === "medium"
          ? "border-[#382b1d] bg-[#0d1424]"
          : "border-[#1e2a42] bg-[#0d1424]"
      }`}
    >
      {/* Clause Item Header / Summary Row */}
      <div className="p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-xs text-slate-400 bg-[#162035] border border-[#233150] px-2 py-0.5 rounded">
              {clause.id}
            </span>
            <span className="text-xs font-semibold text-slate-300 tracking-wider uppercase">
              {clause.category.replace("_", " ")}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <RiskBadge level={clause.riskLevel} />
          </div>
        </div>

        {/* Plain Language Interpretation (Primary read) */}
        <div className="text-slate-100 text-sm sm:text-base leading-relaxed mb-3">
          {clause.plainLanguage || clause.text}
        </div>

        {/* Risk Reason Context (if Medium or High) */}
        {clause.riskReason && (
          <div className="mb-3 text-xs leading-relaxed text-slate-300 bg-[#131b2e] border-l-2 border-amber-500/70 py-1.5 px-3 rounded-r">
            <span className="text-amber-300 font-semibold">Risk factor: </span>
            {clause.riskReason}
          </div>
        )}

        {/* Intra-document Conflict Inline Flag */}
        {clause.conflictsWith && clause.conflictsWith.length > 0 && (
          <div className="mb-3 p-2.5 bg-[#261518] border border-[#4d1f27] rounded text-xs text-[#fca5a5] flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-sm">⚠</span>
              <span>
                <strong>Conflicting Provision:</strong> Contradicts{" "}
                {clause.conflictsWith.join(", ")}
              </span>
            </div>
            {onJumpToClause && (
              <button
                type="button"
                onClick={() => onJumpToClause(clause.conflictsWith[0])}
                className="text-[11px] underline font-medium hover:text-white cursor-pointer"
              >
                Jump to {clause.conflictsWith[0]} →
              </button>
            )}
          </div>
        )}

        {/* Expand / Collapse Original Verbatim Wording */}
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 cursor-pointer font-medium pt-1"
        >
          <span>{expanded ? "▾ Hide original legal text" : "▸ View verbatim contract text"}</span>
        </button>
      </div>

      {/* Expandable Original Verbatim Text Drawer */}
      {expanded && (
        <div className="border-t border-[#1a253c] bg-[#090f1d] p-4 sm:p-5 rounded-b-lg">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Original Contract Clause (Verbatim)
          </div>
          <div className="font-editorial text-sm sm:text-[15px] text-slate-200 leading-relaxed italic bg-[#0b1222] p-4 rounded border border-[#1b2640]">
            "{clause.text}"
          </div>
        </div>
      )}
    </div>
  );
};
