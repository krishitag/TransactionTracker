// Typed client for the FastAPI backend. Shapes mirror backend/main.py and backend/ask.py.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type RiskLevel = "high" | "medium" | "low";

export type Stats = {
  total: number;
  high: number;
  medium: number;
  low: number;
  high_risk_amount: number;
  medium_risk_amount: number;
  low_risk_amount: number;
  total_amount: number;
  model_version: string;
};

export type Transaction = {
  id: number;
  trans_num: string;
  card_last4: string;
  merchant: string;
  category: string;
  category_name: string;
  amount: number;
  trans_time: string;
  is_fraud: boolean | null;
  risk_score: number;
  risk_level: RiskLevel;
  reasons: string[];
  features: Record<string, number | boolean>;
  model_version: string;
};

export type TransactionPage = {
  total: number;
  limit: number;
  offset: number;
  items: Transaction[];
};

export type Citation = { id: number; trans_num: string; summary: string };

export type AskResponse = {
  question: string;
  answer: string;
  citations: Citation[];
  removed_invalid_citations: number[];
  filters: { risk_level: RiskLevel | null; time_of_day: string | null; categories: string[] | null };
  filters_relaxed: boolean;
  examples_retrieved: number;
  model: string;
};

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch (e) {
    // Cancelled or timed out by us: let the caller decide what to say.
    if (e instanceof DOMException) throw e;
    throw new ApiError(
      `Can't reach the API at ${API_URL}. Start the backend (venv/bin/uvicorn main:app) and refresh this page.`,
    );
  }
  if (!res.ok) {
    // FastAPI puts the reason in "detail" (a string, or a list for validation errors).
    const body = await res.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`;
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const getStats = (signal?: AbortSignal) => request<Stats>("/stats", { signal });

export function getTransactions(
  { riskLevel, limit, offset }: { riskLevel: RiskLevel | null; limit: number; offset: number },
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (riskLevel) params.set("risk_level", riskLevel);
  return request<TransactionPage>(`/transactions?${params}`, { signal });
}

export const getTransaction = (id: number, signal?: AbortSignal) =>
  request<Transaction>(`/transactions/${id}`, { signal });

export const ask = (question: string, signal?: AbortSignal) =>
  request<AskResponse>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
