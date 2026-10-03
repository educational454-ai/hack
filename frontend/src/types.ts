export type ClaimType = "factual" | "medical_factual" | "subjective_opinion";

export type SourceTier = "primary" | "secondary" | "low_confidence";

export type EvidenceStance = "supports" | "contradicts" | "neutral";

export type AssessmentVerdict =
  | "supported"
  | "contradicted"
  | "insufficient_evidence"
  | "conflicting_evidence"
  | "subjective_opinion";

export interface FactCheckReference {
  title: string;
  rating: string;
  fact_checker: string;
  review_date?: string | null;
  review_url: string;
}

export interface PublisherTransparencyRecord {
  domain: string;
  total_audited_claims: number;
  debunked_count: number;
  verified_count: number;
  recent_reviews: FactCheckReference[];
  credibility_modifier: number;
}

export interface SourceMetadata {
  url: string;
  domain: string;
  title: string;
  tier: SourceTier;
  tier_reason: string;
  publisher_record?: PublisherTransparencyRecord | null;
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

export interface WebpageMetadata {
  url: string;
  domain: string;
  title?: string | null;
  canonical_url?: string | null;
  publication_date?: string | null;
  author?: string | null;
}

export interface PerClaimResult {
  claim: string;
  claim_type: ClaimType;
  verdict: AssessmentVerdict;
  verdict_symbol: string;
  verdict_title: string;
  confidence_score: number;
  explanation: string;
  supporting_evidence: EvidenceItem[];
  contradicting_evidence: EvidenceItem[];
}

export interface FactCheckItem {
  claim_text: string;
  claimant?: string | null;
  claim_date?: string | null;
  rating: string;
  verdict_signal: string; // "contradicted" | "supported" | "conflicting" | "insufficient_evidence"
  publisher_name: string;
  publisher_site?: string | null;
  rating_url: string;
  title: string;
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
  fact_checks?: FactCheckItem[];
  mode?: "claim" | "url" | "url_question" | "image" | null;
  webpage?: WebpageMetadata | null;
  user_question?: string | null;
  targeted_answer?: string | null;
  relevant_page_context?: string[] | null;
  claims_analyzed?: PerClaimResult[] | null;
  extracted_image_text?: string | null;
  image_preview?: string | null;
  resolved_claim?: string | null;
  question_intent?: string | null;
  detected_language?: string | null;
  detected_language_name?: string | null;
  publisher_transparency?: PublisherTransparencyRecord[];
}

export interface HealthStatus {
  status: string;
  hf_token_configured: boolean;
  llm_model: string;
  embedding_model: string;
}

export interface HistoryItem {
  id: string;
  claim: string;
  timestamp: number;
  result: AnalysisResult;
}

