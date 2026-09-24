import { useState } from "react";
import type { ClausesResponse } from "../types";
import { getClauses } from "../api";
import { ClauseCard } from "../components/ClauseCard";

export default function ClausesPage() {
  const [docId, setDocId] = useState("doc-001");
  const [data, setData] = useState<ClausesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!docId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getClauses(docId);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load clauses");
    } finally {
      setLoading(false);
    }
  };

  const handleJumpToClause = (targetClauseId: string) => {
    const element = document.getElementById(targetClauseId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      element.classList.add("ring-2", "ring-amber-500");
      setTimeout(() => {
        element.classList.remove("ring-2", "ring-amber-500");
      }, 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border-b border-[#1b2640] pb-4">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-white mb-1">
          Clause Explorer
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm">
          Examine extracted contractual clauses, grounded risk ratings, and intra-document conflicts.
        </p>
      </div>

      <div className="flex gap-2">
        <input
          value={docId}
          onChange={(e) => setDocId(e.target.value)}
          placeholder="Document ID (e.g. doc-001)"
          className="flex-1 px-4 py-2 bg-[#0c1324] border border-[#233150] rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#384e7a]"
        />
        <button
          type="button"
          onClick={handleFetch}
          disabled={loading}
          className="px-5 py-2 bg-[#1b2640] hover:bg-[#253556] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#2d3e64] transition-colors disabled:opacity-50"
        >
          {loading ? "Loading..." : "Load Clauses"}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-[#2c1417] border border-[#521f26] rounded text-[#fca5a5] text-xs">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-[#1b2640] pb-2">
            <span>
              Document Record: <strong className="text-slate-200 font-mono">{data.docId}</strong>
            </span>
            <span>{data.clauses.length} clause(s) found</span>
          </div>

          <div className="space-y-3">
            {data.clauses.map((clause) => (
              <ClauseCard
                key={clause.id}
                clause={clause}
                onJumpToClause={handleJumpToClause}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
