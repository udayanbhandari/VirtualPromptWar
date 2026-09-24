import { useState } from "react";
import type { NextStepsResponse } from "../types";
import { getNextSteps } from "../api";
import { RiskBadge } from "../components/RiskBadge";

export default function NextStepsPage() {
  const [docId, setDocId] = useState("doc-001");
  const [data, setData] = useState<NextStepsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!docId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getNextSteps({ docId: docId.trim() });
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load next steps");
    } finally {
      setLoading(false);
    }
  };

  const handleExportBrief = () => {
    if (!data) return;

    // Create a printable, standalone document window for export/download
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      window.print();
      return;
    }

    const briefBulletsHtml = (data.documentBrief || [])
      .map((b) => `<li style="margin-bottom: 8px; font-size: 13.5px; line-height: 1.5;">${b}</li>`)
      .join("");

    const flaggedClausesHtml = (data.flaggedClauses || [])
      .map(
        (fc) => `
        <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 14px; margin-bottom: 14px; page-break-inside: avoid;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12px; font-weight: 600; text-transform: uppercase;">
            <span>[${fc.clauseId}] ${fc.category.replace("_", " ")}</span>
            <span style="color: ${fc.riskLevel === "high" ? "#dc2626" : "#d97706"};">${fc.riskLevel.toUpperCase()} RISK</span>
          </div>
          <p style="font-style: italic; color: #4b5563; font-size: 12px; margin: 4px 0 8px 0;">"${fc.clauseText}"</p>
          <p style="font-size: 12.5px; margin-bottom: 8px;"><strong>Plain English:</strong> ${fc.plainLanguage}</p>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px;">
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px; border-radius: 4px;">
              <strong style="font-size: 11px; text-transform: uppercase; color: #166534;">Recommended User Actions:</strong>
              <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 12px;">
                ${fc.actionChecklist.map((a) => `<li>${a}</li>`).join("")}
              </ul>
            </div>
            <div style="background: #faf5ff; border: 1px solid #e9d5ff; padding: 10px; border-radius: 4px;">
              <strong style="font-size: 11px; text-transform: uppercase; color: #6b21a8;">Questions for Legal Counsel:</strong>
              <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 12px; font-style: italic;">
                ${fc.lawyerQuestions.map((q) => `<li>“${q}”</li>`).join("")}
              </ul>
            </div>
          </div>
        </div>
      `
      )
      .join("");

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>ClauseWise Legal Consultation Brief - ${data.docId}</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #111827; padding: 32px; max-width: 850px; margin: 0 auto; }
            h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
            .meta { font-size: 12px; color: #6b7280; margin-bottom: 24px; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; }
            .brief-box { background: #f9fafb; border: 1px solid #e5e7eb; padding: 16px; border-radius: 8px; margin-bottom: 24px; }
            @media print {
              body { padding: 0; }
              button { display: none; }
            }
          </style>
        </head>
        <body>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>ClauseWise Legal Consultation Brief</h1>
            <button onclick="window.print()" style="padding: 6px 14px; background: #1f2937; color: white; border: none; border-radius: 4px; cursor: pointer;">Print / Save as PDF</button>
          </div>
          <div class="meta">Document ID: <strong>${data.docId}</strong> | Prepared for attorney consultation</div>
          
          <div class="brief-box">
            <h2 style="font-size: 14px; text-transform: uppercase; margin-top: 0; color: #374151;">Executive Document Summary</h2>
            <ul style="margin: 0; padding-left: 18px;">
              ${briefBulletsHtml}
            </ul>
          </div>

          <h2 style="font-size: 16px; margin-bottom: 12px;">Flagged Clauses & Consultation Items</h2>
          ${flaggedClausesHtml}
        </body>
      </html>
    `);

    printWindow.document.close();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1b2640] pb-5">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-white mb-1.5">
            Consultation Brief & Next Steps
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm">
            Per-clause negotiation action checklists, questions for counsel, and a compiled exportable document brief.
          </p>
        </div>

        {data && (
          <button
            onClick={handleExportBrief}
            className="px-4 py-2 bg-[#1b2640] hover:bg-[#253556] text-amber-300 text-xs font-semibold rounded border border-[#3b4e76] transition-colors cursor-pointer self-start sm:self-auto flex items-center gap-2"
          >
            <span>📄</span> Export Brief
          </button>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={docId}
          onChange={(e) => setDocId(e.target.value)}
          placeholder="Document ID (e.g. doc-001)"
          className="flex-1 px-4 py-2 bg-[#0c1324] border border-[#233150] rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#384e7a]"
        />
        <button
          onClick={handleFetch}
          disabled={loading}
          className="px-5 py-2 bg-[#1b2640] hover:bg-[#253556] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#2d3e64] transition-colors disabled:opacity-50"
        >
          {loading ? "Generating Brief..." : "Generate Brief"}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-[#2c1417] border border-[#521f26] rounded text-[#fca5a5] text-xs">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-8">
          {/* Executive Document Brief */}
          {data.documentBrief && data.documentBrief.length > 0 && (
            <div className="p-6 bg-[#0c1424] border border-[#233150] rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-[#18233a] pb-3">
                <h2 className="font-display text-lg font-semibold text-white tracking-wide">
                  Executive Brief for Legal Consultation
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400 bg-[#141c30] px-2 py-0.5 rounded border border-[#202c48]">
                    Doc: {data.docId}
                  </span>
                  <button
                    onClick={handleExportBrief}
                    className="text-xs text-amber-400 hover:text-amber-300 underline cursor-pointer ml-1"
                  >
                    Export Brief →
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-400">
                Key contractual exposure areas to discuss with attorney prior to contract execution:
              </p>

              <ul className="space-y-2">
                {data.documentBrief.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-200">
                    <span className="text-amber-400 font-bold leading-none mt-1">—</span>
                    <span className="leading-relaxed">{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Grouped Flagged Clauses: Checklist + Lawyer Questions */}
          {data.flaggedClauses && data.flaggedClauses.length > 0 && (
            <div className="space-y-4">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 border-b border-[#1b2640] pb-2">
                Flagged Clause Action Items & Lawyer Queries ({data.flaggedClauses.length})
              </div>

              {data.flaggedClauses.map((fc, idx) => (
                <div
                  key={idx}
                  className="p-5 bg-[#0d1424] rounded-lg border border-[#1e2a42] space-y-4"
                >
                  <div className="flex items-center justify-between border-b border-[#182236] pb-2">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs text-slate-400 bg-[#162035] border border-[#233150] px-2 py-0.5 rounded font-semibold">
                        {fc.clauseId}
                      </span>
                      <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                        {fc.category.replace("_", " ")}
                      </span>
                    </div>
                    <RiskBadge level={fc.riskLevel} />
                  </div>

                  <div className="p-3 bg-[#090f1d] border border-[#1b2640] rounded space-y-1">
                    <p className="font-editorial text-xs text-slate-400 italic">
                      "{fc.clauseText}"
                    </p>
                    <p className="text-xs text-slate-300 pt-1">
                      <strong>Plain meaning:</strong> {fc.plainLanguage}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Actions */}
                    <div className="p-3.5 bg-[#10211a] border border-[#1b3d2f] rounded space-y-2">
                      <div className="text-xs font-semibold text-[#86efac] uppercase tracking-wider">
                        Practical Actions to Take
                      </div>
                      <ul className="space-y-1.5">
                        {fc.actionChecklist.map((act, aIdx) => (
                          <li key={aIdx} className="text-xs text-slate-200 flex items-start gap-1.5">
                            <span className="text-[#86efac]">•</span>
                            <span>{act}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Lawyer Questions */}
                    <div className="p-3.5 bg-[#201828] border border-[#39244a] rounded space-y-2">
                      <div className="text-xs font-semibold text-[#d8b4fe] uppercase tracking-wider">
                        Read Aloud to Your Lawyer
                      </div>
                      <ul className="space-y-1.5">
                        {fc.lawyerQuestions.map((q, qIdx) => (
                          <li key={qIdx} className="text-xs text-slate-200 font-editorial italic flex items-start gap-1.5">
                            <span className="text-[#d8b4fe]">“</span>
                            <span>{q}”</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
