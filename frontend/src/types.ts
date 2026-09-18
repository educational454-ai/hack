export type ClaimType = "factual" | "medical_factual" | "subjective_opinion";

export type SourceTier = "primary" | "secondary" | "low_confidence";

export type EvidenceStance = "supports" | "contradicts" | "neutral";

export type AssessmentVerdict =
  | "supported"
  | "contradicted"
  | "insufficient_evidence"
  | "conflicting_evidence"
  | "subjective_opinion";

export interface SourceMetadata {
  url: string;
  domain: string;
  title: string;
  tier: SourceTier;
  tier_reason: string;
}

export interface EvidenceItem {
  id: string;
  url: string;
  title: string;
  domain: string;
  source_tier: SourceTier;
  passage: string;
  similarity_score: number;
  stance?: EvidenceStance | null;
  stance_explanation?: string | null;
}

export interface RelevantImage {
  title?: string | null;
  image_url: string;
  thumbnail_url?: string | null;
  source_url?: string | null;
  relevance_score?: number | null;
}

export interface AnalysisResult {
  claim: string;
  claim_type: ClaimType;
  verdict: AssessmentVerdict;
  verdict_symbol: string;
  verdict_title: string;
  confidence_score: number;
  explanation: string;
  supporting_evidence: EvidenceItem[];
  contradicting_evidence: EvidenceItem[];
  evidence_limitations: string[];
  all_sources: SourceMetadata[];
  relevant_images?: RelevantImage[];
  latency_seconds?: number | null;
}

export interface HealthStatus {
  status: string;
  hf_token_configured: boolean;
  llm_model: string;
  embedding_model: string;
}
