/**
 * Shared TypeScript types for ClauseWise.
 *
 * These mirror the backend Pydantic schemas exactly.
 * All property names use camelCase to match the JSON API.
 */

// ── Core domain types ──────────────────────────────────────────────

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type ClauseCategory =
  | "payment"
  | "termination"
  | "liability"
  | "indemnity"
  | "auto_renewal"
  | "arbitration"
  | "confidentiality"
  | "other";

export interface Clause {
  id: string;
  text: string;
  category: ClauseCategory | string;
  plainLanguage: string;
  riskLevel: RiskLevel;
  riskReason: string;
  conflictsWith: string[];
}

export interface DocumentSummary {
  docId: string;
  fileName: string;
  plainSummary: string;
  clauses: Clause[];
}

// ── Ingest ──────────────────────────────────────────────────────────

export interface IngestResponse {
  docId: string;
  fileName: string;
  rawText: string;
  filePath?: string;
  mimeType?: string;
  document?: DocumentSummary;
}

// ── Clauses ─────────────────────────────────────────────────────────

export interface ClausesResponse {
  docId: string;
  clauses: Clause[];
}

// ── Compare (Phase 3 Structured Diff) ────────────────────────────────

export type FavorsParty = "docA" | "docB" | "neutral";

export interface ClauseDiffItem {
  topic: string;
  docA_text?: string | null;
  docB_text?: string | null;
  difference_summary: string;
  favors: FavorsParty;
  riskDelta: string;
  clauseA?: Clause | null;
  clauseB?: Clause | null;
  difference?: string | null;
}

export interface MissingClauseItem {
  clauseId?: string | null;
  presentIn: string;
  missingFrom: string;
  topic: string;
  text: string;
  impact: string;
}

export interface ComparisonResult {
  docIdA: string;
  docIdB: string;
  overallAssessment: string;
  overallFavors: FavorsParty;
  pairs: ClauseDiffItem[];
  missingClauses: MissingClauseItem[];
  results: ClauseDiffItem[];
}

export interface CompareRequest {
  docIdA: string;
  docIdB: string;
}

export interface CompareResponse {
  comparison: ComparisonResult;
  results: ClauseDiffItem[];
}

// ── Ask (RAG Q&A) ──────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AskRequest {
  docId: string;
  question: string;
  history?: ChatMessage[];
}

export interface AskResponse {
  answer: string;
  sourceClauseIds: string[];
  relevantStatutes?: string[];
}

// ── Next Steps ─────────────────────────────────────────────────────

export interface ClauseNextSteps {
  clauseId: string;
  category: string;
  riskLevel: RiskLevel;
  clauseText: string;
  plainLanguage: string;
  actionChecklist: string[];
  lawyerQuestions: string[];
}

export interface NextStep {
  title: string;
  description: string;
  priority: RiskLevel;
}

export interface NextStepsRequest {
  docId: string;
}

export interface NextStepsResponse {
  docId: string;
  documentBrief?: string[];
  flaggedClauses?: ClauseNextSteps[];
  steps: NextStep[];
}
