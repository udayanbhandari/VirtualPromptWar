/**
 * Typed API client for ClauseWise backend.
 *
 * All fetch wrappers live here. Each function is typed with the
 * shared request/response interfaces. Includes automatic retry
 * with exponential backoff and request timeouts.
 */

import type {
  IngestResponse,
  ClausesResponse,
  CompareRequest,
  CompareResponse,
  AskRequest,
  AskResponse,
  NextStepsRequest,
  NextStepsResponse,
  RiskLevel,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

// ── Retry & Timeout Configuration ──────────────────────────────────

const DEFAULT_TIMEOUT_MS = 30_000;
const EXTRACTION_TIMEOUT_MS = 60_000;
const MAX_RETRIES = 2;
const RETRY_BACKOFF_MS = 1000;

// ── Helpers ────────────────────────────────────────────────────────

class ApiError extends Error {
  status: number;
  body: string;
  isRetryable: boolean;

  constructor(status: number, body: string) {
    const userMessage = ApiError.toUserMessage(status, body);
    super(userMessage);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.isRetryable = status >= 500 || status === 429;
  }

  static toUserMessage(status: number, body: string): string {
    // Try to extract FastAPI detail message
    try {
      const parsed = JSON.parse(body);
      if (parsed.detail) return parsed.detail;
    } catch {
      // not JSON
    }

    if (status === 413) return "File is too large. Maximum size is 25MB.";
    if (status === 422) return body || "The uploaded document could not be processed.";
    if (status === 429) return "Too many requests. Please wait a moment and try again.";
    if (status >= 500) return "Server error. Please try again in a moment.";
    return `Request failed (${status}): ${body}`;
  }
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Request timed out. The server may be processing a large document — please try again."
      );
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

async function fetchJSON<T>(
  url: string,
  init?: RequestInit,
  options?: { timeoutMs?: number; maxRetries?: number }
): Promise<T> {
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const maxRetries = options?.maxRetries ?? MAX_RETRIES;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetchWithTimeout(url, init ?? {}, timeoutMs);
      if (!res.ok) {
        const body = await res.text();
        const apiErr = new ApiError(res.status, body);
        // Don't retry client errors (4xx) except 429
        if (!apiErr.isRetryable) throw apiErr;
        lastError = apiErr;
      } else {
        return (await res.json()) as T;
      }
    } catch (err) {
      if (err instanceof ApiError && !err.isRetryable) throw err;
      lastError = err instanceof Error ? err : new Error(String(err));
    }

    // Exponential backoff before retry
    if (attempt < maxRetries) {
      await new Promise((r) =>
        setTimeout(r, RETRY_BACKOFF_MS * Math.pow(2, attempt))
      );
    }
  }

  throw lastError ?? new Error("Request failed after retries");
}

// ── Ingest ──────────────────────────────────────────────────────────

export async function ingestDocument(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  return fetchJSON<IngestResponse>(
    `${API_BASE}/ingest/`,
    { method: "POST", body: form },
    { timeoutMs: EXTRACTION_TIMEOUT_MS }
  );
}

// ── Clauses ─────────────────────────────────────────────────────────

/**
 * Trigger structured clause extraction via Gemini (POST /clauses/{docId})
 */
export async function extractClauses(docId: string): Promise<ClausesResponse> {
  return fetchJSON<ClausesResponse>(
    `${API_BASE}/clauses/${docId}`,
    { method: "POST" },
    { timeoutMs: EXTRACTION_TIMEOUT_MS }
  );
}

/**
 * Fetch extracted clauses for a document (GET /clauses/{docId})
 */
export async function getClauses(
  docId: string,
  filters?: { category?: string; riskLevel?: RiskLevel }
): Promise<ClausesResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.set("category", filters.category);
  if (filters?.riskLevel) params.set("riskLevel", filters.riskLevel);
  const qs = params.toString();
  return fetchJSON<ClausesResponse>(
    `${API_BASE}/clauses/${docId}${qs ? `?${qs}` : ""}`
  );
}

// ── Compare ─────────────────────────────────────────────────────────

export async function compareDocuments(
  body: CompareRequest
): Promise<CompareResponse> {
  return fetchJSON<CompareResponse>(
    `${API_BASE}/compare/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    { timeoutMs: EXTRACTION_TIMEOUT_MS }
  );
}

// ── Ask ─────────────────────────────────────────────────────────────

export async function askQuestion(body: AskRequest): Promise<AskResponse> {
  return fetchJSON<AskResponse>(`${API_BASE}/ask/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ── Next Steps ─────────────────────────────────────────────────────

export async function getNextSteps(
  body: NextStepsRequest
): Promise<NextStepsResponse> {
  return fetchJSON<NextStepsResponse>(
    `${API_BASE}/nextsteps/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    { timeoutMs: EXTRACTION_TIMEOUT_MS }
  );
}
