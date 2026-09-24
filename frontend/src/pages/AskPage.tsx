import { useState, useRef, useEffect } from "react";
import type { AskResponse, ChatMessage } from "../types";
import { askQuestion } from "../api";

export default function AskPage() {
  const [docId, setDocId] = useState("doc-001");
  const [inputQuestion, setInputQuestion] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string; responseMeta?: AskResponse }>
  >([
    {
      role: "assistant",
      content:
        "ClauseWise Q&A is strictly scoped to answer questions grounded in your uploaded document's clauses and Indian statutory provisions. What would you like to clarify about this agreement?",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
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

      const assistantMessage = {
        role: "assistant" as const,
        content: res.answer,
        responseMeta: res,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to query document");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-9rem)] space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1b2640] pb-4">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-white mb-1">
            Grounded Document Q&A
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm">
            Chat bounded strictly to document clauses and Indian statutes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Doc ID:
          </label>
          <input
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="e.g. doc-001"
            className="w-32 sm:w-36 px-2.5 py-1 bg-[#0c1324] border border-[#233150] rounded text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#384e7a]"
          />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              m.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`max-w-2xl p-4 rounded text-sm leading-relaxed border ${
                m.role === "user"
                  ? "bg-[#16233d] border-[#293d69] text-white"
                  : "bg-[#0d1424] border-[#1d2942] text-slate-200"
              }`}
            >
              <div className="flex items-center justify-between gap-4 mb-2 border-b border-white/10 pb-1 text-[11px] font-semibold tracking-wider uppercase text-slate-400">
                <span>{m.role === "user" ? "Inquiry" : "Grounded Analysis"}</span>
              </div>

              <p className="whitespace-pre-line text-sm leading-relaxed">{m.content}</p>

              {/* Source Clause Badges */}
              {m.responseMeta && m.responseMeta.sourceClauseIds.length > 0 && (
                <div className="mt-3 pt-2 border-t border-[#1a253d] flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Cited Clauses:</span>
                  {m.responseMeta.sourceClauseIds.map((id) => (
                    <span
                      key={id}
                      className="font-mono bg-[#162138] border border-[#25365a] text-slate-300 px-2 py-0.5 rounded text-[11px]"
                    >
                      {id}
                    </span>
                  ))}
                </div>
              )}

              {/* Statutory Grounding */}
              {m.responseMeta && m.responseMeta.relevantStatutes && m.responseMeta.relevantStatutes.length > 0 && (
                <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                  <span className="font-semibold text-amber-300">Statutory Reference:</span>
                  {m.responseMeta.relevantStatutes.map((statute, i) => (
                    <span
                      key={i}
                      className="bg-[#291b10] border border-[#4a2e15] text-[#fde047] px-2 py-0.5 rounded text-[11px]"
                    >
                      {statute}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-slate-400 text-xs italic py-2 pl-2">
            Searching contract clauses and Indian statutes...
          </div>
        )}

        {error && (
          <div className="p-3 bg-[#2c1417] border border-[#521f26] rounded text-[#fca5a5] text-xs">
            {error}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex items-center gap-2 pt-2 border-t border-[#1b2640]">
        <input
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder="Ask a question about this contract..."
          disabled={loading}
          className="flex-1 px-4 py-2.5 bg-[#0c1324] border border-[#233150] rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#384e7a] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !inputQuestion.trim()}
          className="px-5 py-2.5 bg-[#1b2640] hover:bg-[#253556] text-slate-200 text-xs font-semibold rounded cursor-pointer border border-[#2d3e64] transition-colors disabled:opacity-50"
        >
          {loading ? "Searching..." : "Submit Question"}
        </button>
      </form>
    </div>
  );
}
