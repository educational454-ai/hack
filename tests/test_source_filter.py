"""Unit tests for source filtering and tier classification."""

import unittest
from core.source_filter import classify_source, extract_domain
from core.schemas import SourceTier


class TestSourceFilter(unittest.TestCase):

    def test_extract_domain(self):
        self.assertEqual(extract_domain("https://www.reuters.com/article/123"), "reuters.com")
        self.assertEqual(extract_domain("http://pib.gov.in/press-release"), "pib.gov.in")

    def test_primary_source_classification(self):
        tier, _, weight = classify_source("https://pib.gov.in/release/12345")
        self.assertEqual(tier, SourceTier.PRIMARY)
        self.assertEqual(weight, 1.0)

        tier2, _, _ = classify_source("https://www.whitehouse.gov/briefing")
        self.assertEqual(tier2, SourceTier.PRIMARY)

        tier3, _, _ = classify_source("https://arxiv.org/abs/2301.00000")
        self.assertEqual(tier3, SourceTier.PRIMARY)

    def test_secondary_source_classification(self):
        tier, _, weight = classify_source("https://www.reuters.com/world/india/news")
        self.assertEqual(tier, SourceTier.SECONDARY)
        self.assertTrue(weight >= 0.8)

        tier2, _, _ = classify_source("https://thehindu.com/news/national")
        self.assertEqual(tier2, SourceTier.SECONDARY)

    def test_low_confidence_source_classification(self):
        tier, _, weight = classify_source("https://www.reddit.com/r/india/comments/xyz")
        self.assertEqual(tier, SourceTier.LOW_CONFIDENCE)
        self.assertTrue(weight <= 0.5)

        tier2, _, _ = classify_source("https://somemediablog.blogspot.com/post")
        self.assertEqual(tier2, SourceTier.LOW_CONFIDENCE)


if __name__ == "__main__":
    unittest.main()
