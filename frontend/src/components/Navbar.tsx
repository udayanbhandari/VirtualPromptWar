import React from "react";

export type NavPage = "upload" | "clauses" | "compare" | "ask" | "nextsteps";

interface NavbarProps {
  activePage: NavPage;
  onSelectPage: (page: NavPage) => void;
}

const NAV_ITEMS: { key: NavPage; label: string }[] = [
  { key: "upload", label: "Upload & Dashboard" },
  { key: "clauses", label: "Clause Explorer" },
  { key: "compare", label: "Compare Contracts" },
  { key: "ask", label: "Legal Q&A" },
  { key: "nextsteps", label: "Consultation Brief" },
];

export const Navbar: React.FC<NavbarProps> = ({ activePage, onSelectPage }) => {
  return (
    <header className="border-b border-[#1b2640] bg-[#090f1e] sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Brand */}
        <div
          className="flex items-center gap-3 cursor-pointer select-none"
          onClick={() => onSelectPage("upload")}
        >
          <div className="w-7 h-7 rounded bg-[#162137] border border-[#233252] flex items-center justify-center font-display font-bold text-amber-400 text-sm">
            §
          </div>
          <div>
            <div className="font-display text-lg font-semibold tracking-tight text-white leading-tight">
              ClauseWise
            </div>
            <div className="text-[10px] text-slate-400 tracking-wider uppercase font-medium">
              Contract Analysis & Grounding
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {NAV_ITEMS.map((item) => {
            const active = activePage === item.key;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onSelectPage(item.key)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer whitespace-nowrap ${
                  active
                    ? "bg-[#18233b] text-white border border-[#2b3c61]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#121b2f]"
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
