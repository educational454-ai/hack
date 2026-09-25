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
        self.assertEqual(weight, 0.85)

        tier2, _, _ = classify_source("https://thehindu.com/news/national")
        self.assertEqual(tier2, SourceTier.SECONDARY)

    def test_low_confidence_source_classification(self):
        tier, _, weight = classify_source("https://www.reddit.com/r/india/comments/xyz")
        self.assertEqual(tier, SourceTier.LOW_CONFIDENCE)
        self.assertEqual(weight, 0.4)

        tier2, _, _ = classify_source("https://somemediablog.blogspot.com/post")
        self.assertEqual(tier2, SourceTier.LOW_CONFIDENCE)

    def test_unknown_unclassified_domain_becomes_low_confidence(self):
        tier, _, weight = classify_source("https://unknown-commercial-blog.com/post")
        self.assertEqual(tier, SourceTier.LOW_CONFIDENCE)
        self.assertEqual(weight, 0.4)

        tier2, _, _ = classify_source("https://random-store.net")
        self.assertEqual(tier2, SourceTier.LOW_CONFIDENCE)

        tier3, _, _ = classify_source("https://some-unlisted-site.org")
        self.assertEqual(tier3, SourceTier.LOW_CONFIDENCE)

    def test_legitimate_subdomain_classification(self):
        tier, _, _ = classify_source("https://world.reuters.com/article/123")
        self.assertEqual(tier, SourceTier.SECONDARY)

        tier2, _, _ = classify_source("https://press.pib.gov.in/page")
        self.assertEqual(tier2, SourceTier.PRIMARY)

        tier3, _, _ = classify_source("https://sub.arxiv.org/abs/2301.00000")
        self.assertEqual(tier3, SourceTier.PRIMARY)

    def test_substring_domain_not_misclassified(self):
        tier, _, _ = classify_source("https://notreuters.com/article/123")
        self.assertEqual(tier, SourceTier.LOW_CONFIDENCE)

        tier2, _, _ = classify_source("https://reuters.com.attacker.com/article/123")
        self.assertEqual(tier2, SourceTier.LOW_CONFIDENCE)

        tier3, _, _ = classify_source("https://notreddit.com/post")
        self.assertEqual(tier3, SourceTier.LOW_CONFIDENCE)

        tier4, _, _ = classify_source("https://fake-arxiv.org/paper")
        self.assertEqual(tier4, SourceTier.LOW_CONFIDENCE)

    def test_malformed_and_invalid_hostname_handling(self):
        tier1, _, _ = classify_source("")
        self.assertEqual(tier1, SourceTier.LOW_CONFIDENCE)

        tier2, _, _ = classify_source("not_a_valid_url")
        self.assertEqual(tier2, SourceTier.LOW_CONFIDENCE)

        tier3, _, _ = classify_source(None)
        self.assertEqual(tier3, SourceTier.LOW_CONFIDENCE)

    def test_canonical_url_normalization_deduplication(self):
        from core.url_normalizer import normalize_url
        from core.source_filter import build_source_metadata

        raw_urls = [
            "https://en.wikipedia.org/wiki/India",
            "https://en.wikipedia.org/wiki/India#Geography",
            "http://en.wikipedia.org/wiki/India/",
            "https://en.wikipedia.org/wiki/India?utm_source=test",
        ]

        seen_urls = set()
        deduped = []
        for u in raw_urls:
            norm_u = normalize_url(u)
            if norm_u not in seen_urls:
                seen_urls.add(norm_u)
                deduped.append(build_source_metadata(u, "India - Wikipedia"))

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].domain, "en.wikipedia.org")

    def test_same_domain_distinct_pages_preserved(self):
        from core.url_normalizer import normalize_url
        from core.source_filter import build_source_metadata

        distinct_urls = [
            "https://en.wikipedia.org/wiki/India",
            "https://en.wikipedia.org/wiki/States_and_union_territories_of_India",
        ]

        seen_urls = set()
        deduped = []
        for u in distinct_urls:
            norm_u = normalize_url(u)
            if norm_u not in seen_urls:
                seen_urls.add(norm_u)
                deduped.append(build_source_metadata(u, "Wikipedia Page"))

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].domain, "en.wikipedia.org")
        self.assertEqual(deduped[1].domain, "en.wikipedia.org")


if __name__ == "__main__":
    unittest.main()
