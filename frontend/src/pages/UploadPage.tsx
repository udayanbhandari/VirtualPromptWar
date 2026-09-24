import { useState, useCallback } from "react";
import type { Clause, IngestResponse } from "../types";
import { ingestDocument, extractClauses } from "../api";
import { ClauseCard } from "../components/ClauseCard";
import { AskPanel } from "../components/AskPanel";

const SAMPLE_CONTRACTS = [
  { name: "rental_agreement.pdf", title: "Residential Lease Agreement", note: "Includes lease break fee vs strict forfeiture conflict" },
  { name: "freelance_contract_v1_favorable.pdf", title: "Freelance Consulting (Standard / Favorable)", note: "Net 15 days, liability cap, bilateral notice" },
  { name: "freelance_contract_v2_worse.pdf", title: "Freelance Consulting (Restrictive)", note: "Net 60, uncapped liability, 24-mo non-compete" },
  { name: "freelance_nda.pdf", title: "Mutual Non-Disclosure Agreement", note: "2-year confidentiality vs perpetual survival conflict" },
];

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");
  const [ingestData, setIngestData] = useState<IngestResponse | null>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [error, setError] = useState<string | null>(null);

  const processFile = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setIngestData(null);
    setClauses([]);
    setProcessing(true);
    setProgressMsg("Analyzing document...");

    try {
      const res = await ingestDocument(selectedFile);
      setIngestData(res);

      setProgressMsg("Extracting and evaluating clauses...");
      const clausesRes = await extractClauses(res.docId);
      setClauses(clausesRes.clauses);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setProcessing(false);
      setProgressMsg("");
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) processFile(droppedFile);
    },
    [processFile]
  );

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) processFile(selected);
  };

  const handleSampleSelect = async (fileName: string) => {
    const sampleTextMap: Record<string, string> = {
      "rental_agreement.pdf":
        "RESIDENTIAL LEASE AGREEMENT\nLandlord: Oakridge Properties LLC\nTenant: Jane Doe\n\n1. RENT: $2,400 per month due on 1st.\n4.1. Tenant may terminate prior to expiration upon 30 days written notice.\n7.1. Tenant indemnifies Landlord against all claims, even if Landlord is negligent.\n9.1. Neither party may terminate prior to 12 months for any reason; early vacancy accelerates all remaining rent.",
      "freelance_contract_v1_favorable.pdf":
        "FREELANCE CONSULTING AGREEMENT (STANDARD / FAVORABLE)\n1. Client shall pay Contractor within Net 15 days of invoice submission.\n2. IP transfers upon complete receipt of full payment.\n3. Either party may terminate with 30 days prior written notice.\n4. Contractor liability strictly capped at total fees paid.\n5. Contractor retains unrestricted freedom to work with competitors.\n6. Binding arbitration in Bengaluru under Indian Arbitration Act.",
      "freelance_contract_v2_worse.pdf":
        "FREELANCE CONSULTING AGREEMENT (RESTRICTIVE / ADVERSE)\n1. Client shall pay Contractor within Net 60 days with zero interest and unilateral withholding.\n2. All IP vests in Client immediately upon creation.\n3. Client may terminate immediately at any time without notice or pay for in-progress work.\n4. Contractor liability is completely uncapped with strict indemnity.\n5. 24-month worldwide non-compete prohibiting tech consulting.\n6. Mandatory binding arbitration in London under English law.",
      "freelance_nda.pdf":
        "MUTUAL NON-DISCLOSURE AGREEMENT\n3.1. Confidentiality obligations expire exactly two (2) years after disclosure.\n5.1. Contractor indemnifies Company regardless of fault or negligence.\n6.1. Recipient confidentiality obligations for Proprietary Information survive in perpetuity.",
    };

    const text = sampleTextMap[fileName] || "CONTRACT DOCUMENT";
    const dummyBlob = new Blob([text], { type: "application/pdf" });
    const dummyFile = new File([dummyBlob], fileName, { type: "application/pdf" });
    await processFile(dummyFile);
  };

  const handleScrollToClause = (targetClauseId: string) => {
    const element = document.getElementById(targetClauseId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      element.classList.add("ring-2", "ring-amber-500");
      setTimeout(() => {
        element.classList.remove("ring-2", "ring-amber-500");
      }, 2000);
    }
  };

  const highRiskCount = clauses.filter((c) => c.riskLevel === "high" || c.riskLevel === "critical").length;
  const mediumRiskCount = clauses.filter((c) => c.riskLevel === "medium").length;
  const conflictCount = clauses.filter((c) => c.conflictsWith && c.conflictsWith.length > 0).length;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="border-b border-[#1b2640] pb-6">
        <h1 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight text-white mb-2">
          Contract Ingestion & Analysis
        </h1>
        <p className="text-slate-300 text-sm leading-relaxed max-w-2xl">
          Upload PDF or image contracts for multimodal clause extraction, statute-grounded risk scoring, and docked interactive legal Q&A.
        </p>
      </div>

      {/* Upload & Drop Zone */}
      {!ingestData && (
        <div className="space-y-6">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`border border-dashed rounded-lg p-10 text-center transition-colors ${
              dragging
                ? "border-amber-500/80 bg-[#121c33]"
                : "border-[#223150] bg-[#0c1324] hover:border-[#354870]"
            }`}
          >
            <div className="max-w-md mx-auto space-y-3">
              <div className="text-2xl text-slate-400">📄</div>
              <div>
                <p className="text-base font-semibold text-slate-100">
                  {file ? file.name : "Drag and drop your contract here"}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  PDF, PNG, JPG, or WEBP. Direct multimodal understanding without third-party OCR.
                </p>
              </div>

              <div className="pt-2">
                <input
                  type="file"
                  id="contract-upload"
                  accept=".pdf,.png,.jpg,.jpeg,.webp"
                  onChange={onFileInputChange}
                  className="hidden"
                />
                <label
                  htmlFor="contract-upload"
                  className="inline-block px-5 py-2 bg-[#1b2640] hover:bg-[#253556] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#2d3e64] transition-colors"
                >
                  Select File from Computer
                </label>
              </div>
            </div>
          </div>

          {processing && (
            <div className="p-4 bg-[#0d1424] border border-[#233150] rounded-lg flex items-center justify-between text-xs text-slate-300">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="font-medium text-slate-200">{progressMsg}</span>
              </div>
              <span className="font-mono text-slate-500">Multimodal Gemini Flash</span>
            </div>
          )}

          <div className="p-5 bg-[#0a101f] border border-[#1b2640] rounded-lg space-y-3">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Or test with pre-configured legal fixtures:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SAMPLE_CONTRACTS.map((sample) => (
                <button
                  key={sample.name}
                  type="button"
                  onClick={() => handleSampleSelect(sample.name)}
                  disabled={processing}
                  className="text-left p-3 rounded bg-[#0e1628] hover:bg-[#141f38] border border-[#1e2a44] transition-colors cursor-pointer disabled:opacity-50"
                >
                  <div className="text-xs font-semibold text-slate-200">{sample.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{sample.note}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-[#2c1417] border border-[#521f26] rounded-lg text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[#fca5a5]">
            <span className="text-base">⚠</span>
            <span>{error}</span>
          </div>
          <div className="flex items-center gap-2 self-end sm:self-auto">
            {file && (
              <button
                type="button"
                onClick={() => processFile(file)}
                disabled={processing}
                className="px-3 py-1 bg-[#441a20] hover:bg-[#57222a] border border-[#6b2632] text-white text-[11px] font-semibold rounded cursor-pointer transition-colors"
              >
                Retry Analysis
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                setError(null);
                setIngestData(null);
                setClauses([]);
                setFile(null);
              }}
              className="px-2.5 py-1 text-slate-400 hover:text-slate-200 text-[11px] cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Screen 2: Clause Dashboard Docked with Ask Panel */}
      {ingestData && (
        <div className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <span className="text-xs text-slate-400 font-mono">
              Document ID: <strong className="text-slate-200">{ingestData.docId}</strong>
            </span>
            <button
              type="button"
              onClick={() => {
                setIngestData(null);
                setClauses([]);
                setFile(null);
              }}
              className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
            >
              ← Upload another document
            </button>
          </div>

          {/* Document Summary Header */}
          <div className="p-6 bg-[#0c1424] border border-[#1c2944] rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-[#18233a] pb-3">
              <h2 className="font-display text-xl font-semibold text-white tracking-tight">
                {ingestData.fileName.replace(".pdf", "").replace(/_/g, " ").toUpperCase()}
              </h2>
              <span className="text-xs font-mono text-slate-400 bg-[#141c30] px-2.5 py-1 rounded border border-[#202c48]">
                {clauses.length} Clauses Extracted
              </span>
            </div>

            <div className="font-editorial text-sm sm:text-base text-slate-200 leading-relaxed pt-1">
              {highRiskCount > 0 ? (
                <span>
                  This agreement establishes enforceable operational commitments but contains{" "}
                  <strong className="text-[#fca5a5] font-semibold">{highRiskCount} elevated risk provision(s)</strong> that shift disproportionate financial or legal burden onto you. Key areas warranting negotiation include uncapped liabilities, strict forfeiture mechanisms, or restrictive non-compete covenants. We recommend reviewing the flagged sections below and discussing recommended modifications with legal counsel prior to execution.
                </span>
              ) : (
                <span>
                  This agreement reflects balanced standard contractual terms with transparent payment schedules and mutual termination provisions. No critical statutory violations or unconscionable indemnification clauses were detected. The agreement provides a dependable commercial baseline for both parties.
                </span>
              )}
            </div>

            <div className="pt-3 border-t border-[#18233a] flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span>
                Critical / High Risks: <strong className="text-[#fca5a5] font-mono">{highRiskCount}</strong>
              </span>
              <span>•</span>
              <span>
                Medium Risks: <strong className="text-[#fde047] font-mono">{mediumRiskCount}</strong>
              </span>
              <span>•</span>
              <span>
                Contradictions Detected: <strong className="text-rose-400 font-mono">{conflictCount}</strong>
              </span>
            </div>
          </div>

          {/* Docked Layout: Clause Dashboard (Left) + Ask Panel (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Clause Feed (7 cols on lg) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400 border-b border-[#1b2640] pb-2">
                <span className="font-semibold uppercase tracking-wider text-slate-300">
                  Extracted Contract Clauses ({clauses.length})
                </span>
                <span>Click to view verbatim text</span>
              </div>

              <div className="space-y-3">
                {clauses.map((clause) => (
                  <ClauseCard
                    key={clause.id}
                    clause={clause}
                    onJumpToClause={handleScrollToClause}
                  />
                ))}
              </div>
            </div>

            {/* Docked Ask Panel (5 cols on lg) */}
            <div className="lg:col-span-5 sticky top-20">
              <AskPanel
                docId={ingestData.docId}
                clauses={clauses}
                onScrollToClause={handleScrollToClause}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
