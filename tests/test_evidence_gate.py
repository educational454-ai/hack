"""Unit tests for Evidence Quality Gate module."""

import unittest
from core.evidence_gate import filter_evidence_for_verification, is_valid_url
from core.schemas import EvidenceItem, SourceTier, AssessmentVerdict, ParsedClaim, ClaimType
from core.verifier import verify_claim_evidence


class TestEvidenceQualityGate(unittest.TestCase):

    def test_url_validation(self):
        self.assertTrue(is_valid_url("https://pib.gov.in/release/123"))
        self.assertTrue(is_valid_url("http://reuters.com/article"))
        self.assertFalse(is_valid_url(""))
        self.assertFalse(is_valid_url(None))
        self.assertFalse(is_valid_url("javascript:void(0)"))
        self.assertFalse(is_valid_url("not_a_valid_url"))

    def test_clearly_relevant_good_source_accepted(self):
        item = EvidenceItem(
            id="ev_1",
            url="https://pib.gov.in/press-release/100",
            title="Official Press Release on UPI",
            domain="pib.gov.in",
            source_tier=SourceTier.PRIMARY,
            passage="The Government of India clarified today that NPCI UPI services remain fully operational with zero disruption.",
            similarity_score=0.75,
        )
        usable, rejected = filter_evidence_for_verification([item])
        self.assertEqual(len(usable), 1)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(usable[0].id, "ev_1")

    def test_clearly_irrelevant_high_quality_source_rejected(self):
        item = EvidenceItem(
            id="ev_2",
            url="https://who.int/about/headquarters",
            title="WHO Office Locations",
            domain="who.int",
            source_tier=SourceTier.PRIMARY,
            passage="The World Health Organization is headquartered in Geneva Switzerland with regional offices worldwide.",
            similarity_score=0.08,  # Below PRIMARY threshold of 0.15
        )
        usable, rejected = filter_evidence_for_verification([item])
        self.assertEqual(len(usable), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reason"], "insufficient_relevance")

    def test_relevant_weak_low_quality_source_handled_conservatively(self):
        # Low confidence source with score 0.35 (below 0.45 low_conf threshold)
        weak_item = EvidenceItem(
            id="ev_weak",
            url="https://someunvettedblog.com/post/123",
            title="Personal Finance Blog",
            domain="someunvettedblog.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="A blogger thinks UPI might face new regulations in coming years due to transaction growth.",
            similarity_score=0.35,
        )
        usable, rejected = filter_evidence_for_verification([weak_item])
        self.assertEqual(len(usable), 0)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reason"], "low_confidence_quality_bar")

        # Low confidence source with high score (>= 0.45) passes the gate
        strong_low_conf = EvidenceItem(
            id="ev_strong_low",
            url="https://medium.com/@author/fintech-analysis",
            title="Fintech Deep Dive",
            domain="medium.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="Comprehensive industry breakdown analyzing digital payments architecture and regulatory compliance in India.",
            similarity_score=0.60,
        )
        usable2, rejected2 = filter_evidence_for_verification([strong_low_conf])
        self.assertEqual(len(usable2), 1)
        self.assertEqual(len(rejected2), 0)

    def test_invalid_empty_evidence_rejected(self):
        # Invalid URL
        bad_url_item = EvidenceItem(
            id="ev_bad_url",
            url="not_a_valid_url",
            title="Invalid Link",
            domain="invalid",
            source_tier=SourceTier.SECONDARY,
            passage="This is a passage with enough words to pass text count checks but invalid URL.",
            similarity_score=0.80,
        )
        # Empty text passage
        empty_passage_item = EvidenceItem(
            id="ev_empty",
            url="https://reuters.com/news",
            title="Headline only",
            domain="reuters.com",
            source_tier=SourceTier.SECONDARY,
            passage="Too short",  # < 10 words
            similarity_score=0.80,
        )
        usable, rejected = filter_evidence_for_verification([bad_url_item, empty_passage_item])
        self.assertEqual(len(usable), 0)
        self.assertEqual(len(rejected), 2)
        reasons = [r["reason"] for r in rejected]
        self.assertIn("invalid_url", reasons)
        self.assertIn("empty_content", reasons)

    def test_same_url_identical_passage_retains_one(self):
        item1 = EvidenceItem(
            id="ev_1",
            url="https://reuters.com/article/1",
            title="RBI Statement",
            domain="reuters.com",
            source_tier=SourceTier.SECONDARY,
            passage="Reserve Bank of India clarified that digital payment services continue without restriction.",
            similarity_score=0.80,
        )
        item2 = EvidenceItem(
            id="ev_2",
            url="https://reuters.com/article/1",
            title="RBI Statement Copy",
            domain="reuters.com",
            source_tier=SourceTier.SECONDARY,
            passage="Reserve Bank of India clarified that digital payment services continue without restriction.",
            similarity_score=0.75,
        )
        usable, rejected = filter_evidence_for_verification([item1, item2])
        self.assertEqual(len(usable), 1)
        self.assertEqual(usable[0].id, "ev_1")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reason"], "duplicate_content")

    def test_same_url_different_passage_retains_both(self):
        item1 = EvidenceItem(
            id="ev_chunk_1",
            url="https://aljazeera.com/features/upi-report",
            title="UPI Deep Dive Article",
            domain="aljazeera.com",
            source_tier=SourceTier.SECONDARY,
            passage="Prime Minister Narendra Modi government is poised to levy new charges for using the country popular payment network.",
            similarity_score=0.60,
        )
        item2 = EvidenceItem(
            id="ev_chunk_2",
            url="https://aljazeera.com/features/upi-report",
            title="UPI Deep Dive Article",
            domain="aljazeera.com",
            source_tier=SourceTier.SECONDARY,
            passage="NPCI officials clarified that merchant transaction guidelines remain separate from personal peer to peer transfers.",
            similarity_score=0.55,
        )
        usable, rejected = filter_evidence_for_verification([item1, item2])
        self.assertEqual(len(usable), 2)
        self.assertEqual(len(rejected), 0)
        self.assertEqual([item.id for item in usable], ["ev_chunk_1", "ev_chunk_2"])

    def test_different_urls_identical_passage_retains_higher_ranked(self):
        item1 = EvidenceItem(
            id="ev_orig",
            url="https://reuters.com/article/original",
            title="Wire Report",
            domain="reuters.com",
            source_tier=SourceTier.SECONDARY,
            passage="Government bars fees on UPI payments up to Rupees 2000 for merchant transactions.",
            similarity_score=0.70,
        )
        item2 = EvidenceItem(
            id="ev_syndicated",
            url="https://syndicatednews.net/article/copy",
            title="Syndicated Copy",
            domain="syndicatednews.net",
            source_tier=SourceTier.SECONDARY,
            passage="Government bars fees on UPI payments up to Rupees 2000 for merchant transactions.",
            similarity_score=0.65,
        )
        usable, rejected = filter_evidence_for_verification([item1, item2])
        self.assertEqual(len(usable), 1)
        self.assertEqual(usable[0].id, "ev_orig")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reason"], "duplicate_content")

    def test_mixed_evidence_set(self):
        good = EvidenceItem(
            id="ev_good",
            url="https://thehindu.com/news/national/upi-status",
            title="UPI Services Operational",
            domain="thehindu.com",
            source_tier=SourceTier.SECONDARY,
            passage="NPCI and major banking partners confirmed all UPI systems are operating smoothly.",
            similarity_score=0.65,
        )
        irrelevant = EvidenceItem(
            id="ev_irrelevant",
            url="https://bbc.com/sport/cricket",
            title="Cricket Highlights",
            domain="bbc.com",
            source_tier=SourceTier.SECONDARY,
            passage="The national cricket team secured a dramatic victory in the final over of the match.",
            similarity_score=0.10,
        )
        weak = EvidenceItem(
            id="ev_weak",
            url="https://randomforum.com/t/upi",
            title="Forum Speculation",
            domain="randomforum.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="User post discussing rumors seen on social media platforms about app updates.",
            similarity_score=0.25,
        )
        usable, rejected = filter_evidence_for_verification([good, irrelevant, weak])
        self.assertEqual(len(usable), 1)
        self.assertEqual(usable[0].id, "ev_good")
        self.assertEqual(len(rejected), 2)

    def test_all_evidence_rejected_leads_to_insufficient_evidence(self):
        irrelevant_item = EvidenceItem(
            id="ev_irr",
            url="https://example.com/page",
            title="Unrelated Page",
            domain="example.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="Unrelated general information about software engineering best practices.",
            similarity_score=0.12,
        )
        usable, rejected = filter_evidence_for_verification([irrelevant_item])
        self.assertEqual(len(usable), 0)

        # Pass empty usable evidence list to verifier
        parsed = ParsedClaim(
            original_text="India banned UPI payments in 2025",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Empirical claim",
            is_verifiable=True,
            extracted_queries=["India UPI ban 2025"],
        )
        verdict, confidence, explanation, supp, cont, limits = verify_claim_evidence(parsed, usable)
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertTrue(len(explanation) > 10)


if __name__ == "__main__":
    unittest.main()
