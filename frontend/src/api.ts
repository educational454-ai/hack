import { AnalysisResult, HealthStatus } from "./types";

const API_BASE = ""; // Vite proxy forwards /api to http://127.0.0.1:8000

export async function fetchHealth(): Promise<HealthStatus> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    return {
      status: "disconnected",
      hf_token_configured: false,
      llm_model: "Unavailable",
      embedding_model: "Unavailable",
    };
  }
}

export async function analyzeClaimAPI(claim: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ claim }),
  });

  if (!res.ok) {
    let errorDetail = "Verification analysis failed";
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // fallback to generic message
    }
    throw new Error(errorDetail);
  }

  return await res.json();
}
