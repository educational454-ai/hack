"""Integration tests for FastAPI endpoints and end-to-end API contract preservation."""

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
from core.schemas import (
    AnalysisResult,
    AssessmentVerdict,
    ClaimType,
    EvidenceItem,
    EvidenceStance,
    SourceTier,
    SourceMetadata,
)


class TestFastAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("docs_url", res.json())

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("llm_model", data)

    def test_analyze_subjective_claim(self):
        res = self.client.post("/api/analyze", json={"claim": "Modi is a protagonist."})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "subjective_opinion")
        self.assertEqual(data["claim_type"], "subjective_opinion")
        self.assertIn("interpretive", data["explanation"].lower())

    def test_empty_claim_validation(self):
        res = self.client.post("/api/analyze", json={"claim": ""})
        self.assertEqual(res.status_code, 422)  # Unprocessable Entity from Pydantic min_length=3

    @patch("api.main.analyze_claim")
    def test_A_supported_result_survives_api_unchanged(self, mock_analyze):
        mock_analyze.return_value = AnalysisResult(
            claim="Country X banned service Y",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.SUPPORTED,
            verdict_symbol="🟢",
            verdict_title="Supported",
            confidence_score=0.88,
            explanation="The ban was verified through official trade gazettes.",
            supporting_evidence=[
                EvidenceItem(
                    id="ev_1",
                    url="https://gov.x/policy",
                    title="Official Regulation",
                    domain="gov.x",
                    source_tier=SourceTier.PRIMARY,
                    passage="Service Y is prohibited from operating in Country X.",
                    similarity_score=0.85,
                    stance=EvidenceStance.SUPPORTS,
                    stance_explanation="Direct confirmation of prohibition.",
                )
            ],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[
                SourceMetadata(
                    url="https://gov.x/policy",
                    domain="gov.x",
                    title="Official Regulation",
                    tier=SourceTier.PRIMARY,
                    tier_reason="Government domain",
                )
            ],
        )

        res = self.client.post("/api/analyze", json={"claim": "Country X banned service Y"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "supported")
        self.assertEqual(data["confidence_score"], 0.88)
        self.assertEqual(len(data["supporting_evidence"]), 1)
        self.assertEqual(data["supporting_evidence"][0]["url"], "https://gov.x/policy")
        self.assertEqual(data["supporting_evidence"][0]["source_tier"], "primary")

    @patch("api.main.analyze_claim")
    def test_B_contradicted_result_survives_api_unchanged(self, mock_analyze):
        mock_analyze.return_value = AnalysisResult(
            claim="Country X banned service Y",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.CONTRADICTED,
            verdict_symbol="🔴",
            verdict_title="Contradicted",
            confidence_score=0.92,
            explanation="Service Y continues to operate under active permits.",
            supporting_evidence=[],
            contradicting_evidence=[
                EvidenceItem(
                    id="ev_1",
                    url="https://gov.x/permits",
                    title="Active Permits Registry",
                    domain="gov.x",
                    source_tier=SourceTier.PRIMARY,
                    passage="Service Y maintains an active operating license.",
                    similarity_score=0.80,
                    stance=EvidenceStance.CONTRADICTS,
                    stance_explanation="Confirms legal operation.",
                )
            ],
            evidence_limitations=[],
            all_sources=[],
        )

        res = self.client.post("/api/analyze", json={"claim": "Country X banned service Y"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "contradicted")
        self.assertEqual(len(data["contradicting_evidence"]), 1)
        self.assertEqual(data["contradicting_evidence"][0]["id"], "ev_1")

    @patch("api.main.analyze_claim")
    def test_C_insufficient_evidence_survives_api_unchanged(self, mock_analyze):
        mock_analyze.return_value = AnalysisResult(
            claim="Random unverified claim 2026",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            verdict_symbol="🟡",
            verdict_title="Insufficient Evidence",
            confidence_score=0.70,
            explanation="No conclusive reporting disproves or corroborates this claim.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=["No primary source documentation found."],
            all_sources=[],
        )

        res = self.client.post("/api/analyze", json={"claim": "Random unverified claim 2026"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "insufficient_evidence")
        self.assertEqual(len(data["supporting_evidence"]), 0)
        self.assertEqual(len(data["contradicting_evidence"]), 0)

    @patch("api.main.analyze_claim")
    def test_D_conflicting_evidence_survives_api_unchanged(self, mock_analyze):
        mock_analyze.return_value = AnalysisResult(
            claim="Controversial policy event",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.CONFLICTING_EVIDENCE,
            verdict_symbol="🟠",
            verdict_title="Conflicting Evidence",
            confidence_score=0.75,
            explanation="Credible sources report directly contradictory statements.",
            supporting_evidence=[
                EvidenceItem(
                    id="ev_1",
                    url="https://news.org/supp",
                    title="News Article 1",
                    domain="news.org",
                    source_tier=SourceTier.SECONDARY,
                    passage="Passage supporting claim.",
                    similarity_score=0.70,
                    stance=EvidenceStance.SUPPORTS,
                )
            ],
            contradicting_evidence=[
                EvidenceItem(
                    id="ev_2",
                    url="https://official.gov/denial",
                    title="Official Denial",
                    domain="official.gov",
                    source_tier=SourceTier.PRIMARY,
                    passage="Passage refuting claim.",
                    similarity_score=0.75,
                    stance=EvidenceStance.CONTRADICTS,
                )
            ],
            evidence_limitations=[],
            all_sources=[],
        )

        res = self.client.post("/api/analyze", json={"claim": "Controversial policy event"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "conflicting_evidence")
        self.assertEqual(len(data["supporting_evidence"]), 1)
        self.assertEqual(len(data["contradicting_evidence"]), 1)

    @patch("api.main.analyze_claim")
    def test_J_unicode_multilingual_evidence_serialization(self, mock_analyze):
        mock_analyze.return_value = AnalysisResult(
            claim="भारत में डिजिटल लेनदेन 2025",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.SUPPORTED,
            verdict_symbol="🟢",
            verdict_title="Supported",
            confidence_score=0.90,
            explanation="भारतीय रिज़र्व बैंक के अनुसार 2025 में डिजिटल लेनदेन में वृद्धि हुई।",
            supporting_evidence=[
                EvidenceItem(
                    id="ev_hi_1",
                    url="https://rbi.org.in/hindi/report",
                    title="भारतीय रिज़र्व बैंक रिपोर्ट",
                    domain="rbi.org.in",
                    source_tier=SourceTier.PRIMARY,
                    passage="वर्ष 2025 के दौरान यूपीआई के माध्यम से कुल लेनदेन में 30% की वृद्धि दर्ज की गई।",
                    similarity_score=0.89,
                    stance=EvidenceStance.SUPPORTS,
                )
            ],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
        )

        res = self.client.post("/api/analyze", json={"claim": "भारत में डिजिटल लेनदेन 2025"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["claim"], "भारत में डिजिटल लेनदेन 2025")
        self.assertEqual(data["supporting_evidence"][0]["passage"], "वर्ष 2025 के दौरान यूपीआई के माध्यम से कुल लेनदेन में 30% की वृद्धि दर्ज की गई।")

    @patch("api.main.analyze_claim")
    def test_K_pipeline_error_handled_sanitized(self, mock_analyze):
        mock_analyze.side_effect = RuntimeError("Internal database or service connection timeout")
        res = self.client.post("/api/analyze", json={"claim": "Any valid test claim string"})
        self.assertEqual(res.status_code, 500)
        data = res.json()
        self.assertEqual(data["detail"], "An internal error occurred while processing the verification pipeline.")


if __name__ == "__main__":
    unittest.main()
