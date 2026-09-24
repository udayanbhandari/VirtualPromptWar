import { useState } from "react";
import type { CompareResponse, ComparisonResult } from "../types";
import { compareDocuments } from "../api";

export default function ComparePage() {
  const [docIdA, setDocIdA] = useState("doc-001");
  const [docIdB, setDocIdB] = useState("doc-002");
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!docIdA.trim() || !docIdB.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareDocuments({ docIdA: docIdA.trim(), docIdB: docIdB.trim() });
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const comparison: ComparisonResult | undefined = data?.comparison;
  const pairs = comparison?.pairs || data?.results || [];
  const missingClauses = comparison?.missingClauses || [];

  const onlyInA = missingClauses.filter(
    (m) => m.presentIn.toLowerCase() === "doca" || m.missingFrom.toLowerCase() === "docb"
  );
  const onlyInB = missingClauses.filter(
    (m) => m.presentIn.toLowerCase() === "docb" || m.missingFrom.toLowerCase() === "doca"
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-[#1b2640] pb-5">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-white mb-1.5">
          Side-by-Side Contract Comparison
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-2xl">
          Pairwise clause alignment comparing baseline vs counterparty terms with subtle favor indicators and missing clause audits.
        </p>
      </div>

      {/* Input Controls */}
      <div className="p-5 bg-[#0c1324] border border-[#1e2a42] rounded-lg space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Document A ID (Baseline)
            </label>
            <input
              value={docIdA}
              onChange={(e) => setDocIdA(e.target.value)}
              placeholder="e.g. doc-001"
              className="w-full px-3.5 py-2 bg-[#080d1a] border border-[#1e2b44] rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#3b5282]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Document B ID (Counterparty / Amendment)
            </label>
            <input
              value={docIdB}
              onChange={(e) => setDocIdB(e.target.value)}
              placeholder="e.g. doc-002"
              className="w-full px-3.5 py-2 bg-[#080d1a] border border-[#1e2b44] rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#3b5282]"
            />
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading}
          className="w-full px-5 py-2.5 bg-[#17233c] hover:bg-[#203152] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#273859] transition-colors disabled:opacity-50"
        >
          {loading ? "Comparing Documents..." : "Run Clause Diff"}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-[#2c1417] border border-[#521f26] rounded text-[#fca5a5] text-xs">
          {error}
        </div>
      )}

      {comparison && (
        <div className="space-y-8">
          {/* Overall Favorability Assessment Banner */}
          <div className="p-5 bg-[#0c1424] border border-[#1e2a42] rounded-lg space-y-2">
            <div className="flex items-center justify-between border-b border-[#18233a] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
              <span>Overall Assessment</span>
              <span className="font-mono text-slate-400">
                {comparison.overallFavors === "docA"
                  ? "Benefits Document A (User)"
                  : comparison.overallFavors === "docB"
                  ? "Benefits Document B"
                  : "Neutral / Balanced Terms"}
              </span>
            </div>
            <p className="font-editorial text-sm sm:text-[15px] leading-relaxed text-slate-200 pt-1">
              {comparison.overallAssessment}
            </p>
          </div>

          {/* Paired Clauses Two-Column Layout */}
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-400 border-b border-[#1b2640] pb-2">
              <span className="font-semibold uppercase tracking-wider text-slate-300">
                Aligned Clause Pairs ({pairs.length})
              </span>
              <div className="flex items-center gap-4 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-1 rounded bg-[#34d399]" /> Favors Doc A
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-1 rounded bg-[#c084fc]" /> Favors Doc B
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-1 rounded bg-slate-600" /> Neutral
                </span>
              </div>
            </div>

            <div className="space-y-4">
              {pairs.map((item, idx) => {
                const textA = item.docA_text || item.clauseA?.text || "";
                const textB = item.docB_text || item.clauseB?.text || "";
                const diffSummary = item.difference_summary || item.difference || "";

                // Subtle colored indicator bar: Green for docA, purple for docB, subtle slate for neutral
                const indicatorBarClass =
                  item.favors === "docA"
                    ? "bg-[#10b981]"
                    : item.favors === "docB"
                    ? "bg-[#a855f7]"
                    : "bg-[#475569]";

                return (
                  <div
                    key={idx}
                    className="bg-[#0b1222] rounded-lg border border-[#1c2842] overflow-hidden"
                  >
                    {/* Top indicator bar for favored side */}
                    <div className="h-1 w-full bg-[#162138]">
                      <div
                        className={`h-full ${indicatorBarClass} ${
                          item.favors === "docA"
                            ? "w-1/2 ml-0"
                            : item.favors === "docB"
                            ? "w-1/2 ml-auto"
                            : "w-full"
                        }`}
                      />
                    </div>

                    <div className="p-4 sm:p-5 space-y-3">
                      <div className="flex items-center justify-between text-xs border-b border-[#162035] pb-2">
                        <span className="font-semibold text-slate-200 uppercase tracking-wide">
                          {item.topic}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {item.favors === "docA"
                            ? "Favors Doc A (Lower Risk)"
                            : item.favors === "docB"
                            ? "Favors Doc B"
                            : "Neutral"}
                        </span>
                      </div>

                      {/* Two Column Layout Side-by-Side */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Doc A Column */}
                        <div
                          className={`p-3.5 rounded border transition-colors ${
                            item.favors === "docA"
                              ? "bg-[#0e1828] border-[#1f385c]"
                              : "bg-[#090f1d] border-[#19243d]"
                          }`}
                        >
                          <div className="flex items-center justify-between text-[11px] text-slate-400 uppercase tracking-wider mb-1.5">
                            <span className="font-semibold">Doc A Baseline</span>
                            {item.favors === "docA" && (
                              <span className="text-[#6ee7b7] font-sans font-medium text-[10px]">
                                Protected
                              </span>
                            )}
                          </div>
                          <p className="font-editorial text-xs sm:text-[13px] text-slate-300 leading-relaxed italic">
                            "{textA}"
                          </p>
                        </div>

                        {/* Doc B Column */}
                        <div
                          className={`p-3.5 rounded border transition-colors ${
                            item.favors === "docB"
                              ? "bg-[#181226] border-[#3e2354]"
                              : "bg-[#090f1d] border-[#19243d]"
                          }`}
                        >
                          <div className="flex items-center justify-between text-[11px] text-slate-400 uppercase tracking-wider mb-1.5">
                            <span className="font-semibold">Doc B Counterparty</span>
                            {item.favors === "docB" && (
                              <span className="text-[#d8b4fe] font-sans font-medium text-[10px]">
                                Favored
                              </span>
                            )}
                          </div>
                          <p className="font-editorial text-xs sm:text-[13px] text-slate-300 leading-relaxed italic">
                            "{textB}"
                          </p>
                        </div>
                      </div>

                      {/* Plain Language Diff & Risk Delta Callout */}
                      <div className="pt-2 text-xs text-slate-300 space-y-1">
                        <div>
                          <strong className="text-slate-200">Difference: </strong>
                          <span>{diffSummary}</span>
                        </div>
                        {item.riskDelta && (
                          <div className="text-amber-300 pt-0.5">
                            <strong className="text-amber-200">Risk Assessment: </strong>
                            <span>{item.riskDelta}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Unmatched Clauses Section ("Only in Document A / Document B") */}
          {missingClauses.length > 0 && (
            <div className="space-y-4 pt-4 border-t border-[#1b2640]">
              <div>
                <h3 className="font-display text-xl font-semibold text-white mb-1">
                  Unmatched Clauses
                </h3>
                <p className="text-xs text-slate-400">
                  Provisions present in one agreement but omitted from the other.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Only in Document A */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 border-b border-[#1c2944] pb-1.5">
                    Only in Document A ({onlyInA.length})
                  </div>
                  {onlyInA.length > 0 ? (
                    onlyInA.map((item, i) => (
                      <div
                        key={i}
                        className="p-3.5 bg-[#0a1120] border border-[#1b2844] rounded text-xs space-y-1.5"
                      >
                        <div className="font-semibold text-slate-200 uppercase tracking-wide">
                          {item.topic}
                        </div>
                        <p className="font-editorial text-slate-300 italic">"{item.text}"</p>
                        <p className="text-slate-400 text-[11px]">
                          <strong>Significance: </strong>
                          {item.impact}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 text-xs text-slate-500 italic bg-[#0a101f] border border-[#172238] rounded">
                      No unique clauses exclusive to Document A.
                    </div>
                  )}
                </div>

                {/* Only in Document B */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-[#fca5a5] border-b border-[#3b1d24] pb-1.5">
                    Only in Document B ({onlyInB.length})
                  </div>
                  {onlyInB.length > 0 ? (
                    onlyInB.map((item, i) => (
                      <div
                        key={i}
                        className="p-3.5 bg-[#1d1217] border border-[#3e1f26] rounded text-xs space-y-1.5"
                      >
                        <div className="font-semibold text-[#fca5a5] uppercase tracking-wide">
                          {item.topic}
                        </div>
                        <p className="font-editorial text-slate-300 italic">"{item.text}"</p>
                        <p className="text-[#fca5a5]/80 text-[11px]">
                          <strong>Significance: </strong>
                          {item.impact}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 text-xs text-slate-500 italic bg-[#0a101f] border border-[#172238] rounded">
                      No unique clauses exclusive to Document B.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
