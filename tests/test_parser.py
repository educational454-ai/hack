"""Unit tests for claim parser and classifier."""

import unittest
from core.claim_parser import parse_claim
from core.schemas import ClaimType


class TestClaimParser(unittest.TestCase):

    def test_factual_claim(self):
        parsed = parse_claim("India banned UPI in 2025")
        self.assertEqual(parsed.claim_type, ClaimType.FACTUAL)
        self.assertTrue(parsed.is_verifiable)
        self.assertTrue(len(parsed.extracted_queries) > 0)

    def test_subjective_claim_protagonist(self):
        parsed = parse_claim("Modi is a protagonist.")
        self.assertEqual(parsed.claim_type, ClaimType.SUBJECTIVE_OPINION)
        self.assertFalse(parsed.is_verifiable)
        self.assertIsNotNone(parsed.perspectives)
        self.assertTrue(len(parsed.perspectives) >= 2)

    def test_subjective_claim_best_government(self):
        parsed = parse_claim("This is the best government in history.")
        self.assertEqual(parsed.claim_type, ClaimType.SUBJECTIVE_OPINION)
        self.assertFalse(parsed.is_verifiable)

    def test_medical_claim(self):
        parsed = parse_claim("This herbal medicine cures cancer without chemotherapy.")
        self.assertEqual(parsed.claim_type, ClaimType.MEDICAL_FACTUAL)
        self.assertTrue(parsed.is_verifiable)

    def test_economic_factual_claim(self):
        parsed = parse_claim("India's GDP grew by 8.2 percent in 2024.")
        self.assertEqual(parsed.claim_type, ClaimType.FACTUAL)
        self.assertTrue(parsed.is_verifiable)


    def test_subjective_claim_neutral_explanation(self):
        parsed = parse_claim("Mumbai is the best city in India.")
        self.assertEqual(parsed.claim_type, ClaimType.SUBJECTIVE_OPINION)
        self.assertFalse(parsed.is_verifiable)
        explanation = " ".join(parsed.perspectives or [])
        self.assertNotIn("political", explanation.lower())
        self.assertIn("qualitative", explanation.lower())


if __name__ == "__main__":
    unittest.main()
