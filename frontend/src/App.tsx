import { useState } from "react";
import { Navbar, type NavPage } from "./components/Navbar";
import UploadPage from "./pages/UploadPage";
import ClausesPage from "./pages/ClausesPage";
import ComparePage from "./pages/ComparePage";
import AskPage from "./pages/AskPage";
import NextStepsPage from "./pages/NextStepsPage";

export default function App() {
  const [activePage, setActivePage] = useState<NavPage>("upload");

  return (
    <div className="min-h-screen bg-[#080d1a] text-slate-200 flex flex-col font-sans">
      <Navbar activePage={activePage} onSelectPage={setActivePage} />

      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-8">
        {activePage === "upload" && <UploadPage />}
        {activePage === "clauses" && <ClausesPage />}
        {activePage === "compare" && <ComparePage />}
        {activePage === "ask" && <AskPage />}
        {activePage === "nextsteps" && <NextStepsPage />}
      </main>

      <footer className="border-t border-[#1b2640] py-6 text-xs text-slate-500 bg-[#070b16]">
        <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-display font-semibold text-slate-400">ClauseWise</span>
            <span>·</span>
            <span>AI for Legal Assistance & Access</span>
          </div>
          <span className="text-slate-500">
            Multimodal Gemini · Indian Statutes RAG · Flat Editorial Design
          </span>
        </div>
      </footer>
    </div>
  );
}
