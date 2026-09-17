"""Integration tests for the end-to-end evidence-first pipeline."""

import unittest
from core.pipeline import analyze_claim
from core.schemas import AssessmentVerdict, ClaimType


class TestPipeline(unittest.TestCase):

    def test_subjective_claim_flow(self):
        result = analyze_claim("Modi is a protagonist.")
        self.assertEqual(result.claim_type, ClaimType.SUBJECTIVE_OPINION)
        self.assertEqual(result.verdict, AssessmentVerdict.SUBJECTIVE_OPINION)
        self.assertEqual(result.verdict_symbol, "🔵")
        self.assertIn("interpretive characterization", result.explanation)
        self.assertTrue(result.latency_seconds is not None and result.latency_seconds < 2.0)

    def test_factual_claim_structure(self):
        result = analyze_claim("India banned UPI in 2025")
        self.assertEqual(result.claim_type, ClaimType.FACTUAL)
        self.assertIn(result.verdict, [
            AssessmentVerdict.CONTRADICTED,
            AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            AssessmentVerdict.SUPPORTED,
        ])
        self.assertTrue(len(result.explanation) > 20)
        self.assertTrue(result.latency_seconds is not None)


if __name__ == "__main__":
    unittest.main()
