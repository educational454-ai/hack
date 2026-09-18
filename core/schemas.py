"""Pydantic data contracts for the Evidence-First Misinformation Analyzer."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    FACTUAL = "factual"
    MEDICAL_FACTUAL = "medical_factual"
    SUBJECTIVE_OPINION = "subjective_opinion"


class SourceTier(str, Enum):
    PRIMARY = "primary"              # Government, academic, legal, official bureaus
    SECONDARY = "secondary"          # Reputable journalism, news agencies, wire services
    LOW_CONFIDENCE = "low_confidence"# Blogs, social media, forums, unverified sites


class EvidenceStance(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"


class AssessmentVerdict(str, Enum):
    SUPPORTED = "supported"                     # 🟢 Strong reliable evidence supports the claim
    CONTRADICTED = "contradicted"               # 🔴 Reliable evidence conflicts with the claim
    INSUFFICIENT_EVIDENCE = "insufficient_evidence" # 🟡 Available evidence isn't enough
    CONFLICTING_EVIDENCE = "conflicting_evidence"   # 🟠 Credible sources disagree / mixed
    SUBJECTIVE_OPINION = "subjective_opinion"   # 🔵 Statement isn't objectively verifiable


class SourceMetadata(BaseModel):
    url: str
    domain: str
    title: Optional[str] = ""
    tier: SourceTier
    tier_reason: str


class EvidenceItem(BaseModel):
    id: str
    url: str
    title: str
    domain: str
    source_tier: SourceTier
    passage: str
    similarity_score: float = 0.0
    stance: Optional[EvidenceStance] = None
    stance_explanation: Optional[str] = None


class ParsedClaim(BaseModel):
    original_text: str
    claim_type: ClaimType
    type_explanation: str
    is_verifiable: bool
    perspectives: Optional[List[str]] = None
    extracted_queries: List[str] = Field(default_factory=list)


class RelevantImage(BaseModel):
    title: str
    image_url: str
    thumbnail_url: str
    source_url: str


class AnalysisResult(BaseModel):
    claim: str
    claim_type: ClaimType
    verdict: AssessmentVerdict
    verdict_symbol: str
    verdict_title: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list)
    evidence_limitations: List[str] = Field(default_factory=list)
    all_sources: List[SourceMetadata] = Field(default_factory=list)
    relevant_images: List[RelevantImage] = Field(default_factory=list)
    latency_seconds: Optional[float] = None
