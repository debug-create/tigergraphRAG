const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
export const isApiDisabled = process.env.NEXT_PUBLIC_API_URL === undefined || process.env.NEXT_PUBLIC_API_URL === "";

export interface PipelineResult {
  pipeline: string;
  answer: string;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  latency_seconds: number;
  cost_usd: number;
  llm_judge: string;
}

export interface QueryResponse {
  question: string;
  pipeline1: PipelineResult;
  pipeline2: PipelineResult;
  pipeline3: PipelineResult;
  token_reduction_pct: number;
}

export interface BenchmarkSummary {
  token_reduction_pct: number;
  pipeline1: { avg_tokens: number; pass_rate: number };
  pipeline2: { avg_tokens: number; pass_rate: number };
  pipeline3: { avg_tokens: number; pass_rate: number };
}

export async function runQuery(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getBenchmarkResults() {
  const res = await fetch(`${API_BASE}/benchmark/results`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getPresetQuestions() {
  const res = await fetch(`${API_BASE}/questions/presets`);
  if (!res.ok) return [];
  return res.json();
}

export async function loadPipelines() {
  const res = await fetch(`${API_BASE}/pipelines/load`, { method: "POST" });
  return res.json();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
