import React, { useState, useRef, useEffect } from "react";
import type { AskResponse, ChatMessage, Clause } from "../types";
import { askQuestion } from "../api";

interface AskPanelProps {
  docId: string;
  clauses?: Clause[];
  onScrollToClause?: (clauseId: string) => void;
  className?: string;
}

export const AskPanel: React.FC<AskPanelProps> = ({
  docId,
  clauses = [],
  onScrollToClause,
  className = "",
}) => {
  const [inputQuestion, setInputQuestion] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string; responseMeta?: AskResponse }>
  >([
    {
      role: "assistant",
      content:
        "Ask questions grounded strictly in this document's provisions and Indian law. Click any cited clause tag to highlight that section.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const q = inputQuestion.trim();
    if (!q || !docId.trim() || loading) return;

    const historyPayload: ChatMessage[] = messages
      .slice(-5)
      .map((m) => ({ role: m.role, content: m.content }));

    const userMessage = { role: "user" as const, content: q };
    setMessages((prev) => [...prev, userMessage]);
    setInputQuestion("");
    setLoading(true);
    setError(null);

    try {
      const res = await askQuestion({
        docId: docId.trim(),
        question: q,
        history: historyPayload,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant" as const,
          content: res.answer,
          responseMeta: res,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query document");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className={`flex flex-col bg-[#0a101f] border border-[#1b2640] rounded-lg overflow-hidden ${className}`}
    >
      {/* Panel Header */}
      <div className="p-3.5 border-b border-[#18233a] bg-[#0c1424] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-amber-400 font-bold text-xs">§</span>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Document Q&A
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-400 bg-[#141d33] px-2 py-0.5 rounded border border-[#1f2c4a]">
          {docId}
        </span>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 max-h-[500px] min-h-[300px]">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`p-3 rounded text-xs leading-relaxed max-w-[90%] border ${
                m.role === "user"
                  ? "bg-[#16233d] border-[#293d69] text-white"
                  : "bg-[#0d1424] border-[#1d2942] text-slate-200"
              }`}
            >
              <p className="whitespace-pre-line leading-relaxed">{m.content}</p>

              {/* Source Clause Reference Tags (Clickable to jump) */}
              {m.responseMeta && m.responseMeta.sourceClauseIds.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-[#18233a] flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className="text-slate-400 font-medium">Referenced:</span>
                  {m.responseMeta.sourceClauseIds.map((cid) => (
                    <button
                      key={cid}
                      type="button"
                      onClick={() => onScrollToClause && onScrollToClause(cid)}
                      className="font-mono bg-[#162138] hover:bg-[#203052] border border-[#2b3d63] text-amber-300 px-1.5 py-0.5 rounded cursor-pointer transition-colors"
                      title={`Scroll to ${cid}`}
                    >
                      {cid} ↗
                    </button>
                  ))}
                </div>
              )}

              {/* Statute Reference */}
              {m.responseMeta && m.responseMeta.relevantStatutes && m.responseMeta.relevantStatutes.length > 0 && (
                <div className="mt-1.5 flex flex-wrap items-center gap-1 text-[10px] text-slate-400">
                  <span className="text-amber-300 font-medium">Statute:</span>
                  <span>{m.responseMeta.relevantStatutes.join(", ")}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-[11px] text-slate-400 italic py-1">
            Analyzing document clauses & Indian statutes...
          </div>
        )}

        {error && (
          <div className="p-2.5 bg-[#2c1417] border border-[#521f26] rounded text-[#fca5a5] text-xs">
            {error}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Field */}
      <form onSubmit={handleSend} className="p-3 border-t border-[#18233a] bg-[#0c1424] flex gap-2">
        <input
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder="Ask a question about this contract..."
          disabled={loading}
          className="flex-1 px-3 py-1.5 bg-[#080d1a] border border-[#1e2a42] rounded text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#384e7a] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !inputQuestion.trim()}
          className="px-3 py-1.5 bg-[#1b2640] hover:bg-[#253556] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#2d3e64] transition-colors disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
};
