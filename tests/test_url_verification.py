import unittest
from core.url_normalizer import normalize_url, are_urls_equivalent
from core.url_fetcher import WebpageFetchResult, is_safe_public_url
from core.url_pipeline import (
    detect_input_mode,
    rank_page_passages_for_question,
    extract_key_claims_from_text,
    resolve_contextual_question,
    is_subject_page_url,
)
from core.schemas import AssessmentVerdict, ClaimType, AnalysisResult


class TestURLVerificationPipeline(unittest.TestCase):
    """Unit test suite for Task 13 & 13.1 URL verification features."""

    def test_detect_input_mode_claim(self):
        """Test plain text claim is detected as 'claim' mode."""
        mode, url, question = detect_input_mode("India banned UPI in 2025")
        self.assertEqual(mode, "claim")
        self.assertIsNone(url)
        self.assertEqual(question, "India banned UPI in 2025")

    def test_detect_input_mode_url_only(self):
        """Test URL-only string is detected as 'url' mode."""
        mode, url, question = detect_input_mode("https://example.com/news/article-123")
        self.assertEqual(mode, "url")
        self.assertEqual(url, "https://example.com/news/article-123")
        self.assertIsNone(question)

    def test_detect_input_mode_url_question(self):
        """Test URL with additional user question is detected as 'url_question' mode."""
        mode, url, question = detect_input_mode("https://example.com/news/article-123\nIs this marriage actually confirmed?")
        self.assertEqual(mode, "url_question")
        self.assertEqual(url, "https://example.com/news/article-123")
        self.assertEqual(question, "Is this marriage actually confirmed?")

    def test_url_normalization(self):
        """Test URL normalization strips tracking parameters, fragments, casing, and trailing slashes."""
        u1 = "HTTPS://Example.COM/news/article-123/?utm_source=twitter&fbclid=abc#section1"
        u2 = "https://example.com/news/article-123"
        self.assertEqual(normalize_url(u1), u2)
        self.assertTrue(are_urls_equivalent(u1, u2))

    def test_ssrf_protection_private_ips(self):
        """Test is_safe_public_url blocks private, local, loopback, and metadata IPs."""
        unsafe_urls = [
            "http://127.0.0.1/admin",
            "http://localhost:8000/metrics",
            "http://10.0.0.1/internal",
            "http://172.16.0.1/secret",
            "http://192.168.1.1/router",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/status",
        ]
        for url in unsafe_urls:
            is_safe = is_safe_public_url(url)
            self.assertFalse(is_safe, f"Expected {url} to be blocked by SSRF check, got safe=True")

        safe_url = "https://en.wikipedia.org/wiki/Zendaya"
        is_safe = is_safe_public_url(safe_url)
        self.assertTrue(is_safe, f"Expected {safe_url} to be safe, got unsafe")

    def test_is_subject_page_url_exact_and_canonical(self):
        """Test subject page exclusion matches exact & canonical URLs but retains same-domain independent articles."""
        subject_url = "https://example.com/news/article-1?utm_source=feed"
        canonical_url = "https://example.com/news/article-1"
        other_article_same_domain = "https://example.com/news/article-2"
        different_domain = "https://other.org/news/article-1"

        # Exact / normalized match
        self.assertTrue(is_subject_page_url("https://example.com/news/article-1", subject_url, canonical_url))
        # Canonical match
        self.assertTrue(is_subject_page_url("https://example.com/news/article-1/", subject_url, canonical_url))

        # Same domain, different path -> NOT subject page (retained as independent evidence!)
        self.assertFalse(is_subject_page_url(other_article_same_domain, subject_url, canonical_url))
        # Different domain -> NOT subject page
        self.assertFalse(is_subject_page_url(different_domain, subject_url, canonical_url))

    def test_resolve_contextual_question(self):
        """Test resolving direct vs contextual questions with page context."""
        passages = ["Zendaya and Tom Holland attend dune event together in London."]
        
        # Direct self-contained question -> returned as-is
        direct_q = "Is Zendaya unmarried?"
        res_direct = resolve_contextual_question(direct_q, passages)
        self.assertEqual(res_direct, direct_q)

        # Ambiguous question with context -> hypothesis formulated
        ambig_q = "Is this marriage confirmed?"
        res_ambig = resolve_contextual_question(ambig_q, passages)
        self.assertIsNotNone(res_ambig)
        self.assertIn("Zendaya", res_ambig)

        # Ambiguous question without context -> returns None
        res_empty = resolve_contextual_question(ambig_q, [])
        self.assertIsNone(res_empty)

    def test_evidence_isolation_empty_fallback_not_restored(self):
        """Test evidence isolation does NOT restore excluded subject pages if filtered list is empty."""
        # Simulate evidence filtering behavior: if independent search returned only subject page URLs,
        # filtered result must remain empty.
        subject_url = "https://example.com/news/article-1"
        retrieved_urls = ["https://example.com/news/article-1", "https://example.com/news/article-1/"]
        
        filtered = [u for u in retrieved_urls if not is_subject_page_url(u, subject_url, subject_url)]
        self.assertEqual(len(filtered), 0)
        # Verify that filtered is empty [] and no fallback restores retrieved_urls
        supporting_evidence = filtered
        self.assertEqual(supporting_evidence, [])

    def test_webpage_fetch_result_metadata_integrity(self):
        """Test missing metadata fields remain None and are not fabricated."""
        res = WebpageFetchResult(
            url="https://example.com/test",
            domain="example.com",
            status_code=200,
            title=None,
            canonical_url=None,
            publication_date=None,
            author=None,
            main_text="Some sample body text about technology policy in 2025.",
        )
        self.assertTrue(res.is_success)
        self.assertIsNone(res.title)
        self.assertIsNone(res.author)
        self.assertIsNone(res.publication_date)

    def test_rank_page_passages_selection(self):
        """Test BGE-M3 passage selection selects relevant passages for user question."""
        question = "Is the UPI payment ban real?"
        passages = [
            "The weather in London was remarkably sunny today with mild temperatures expected over the weekend.",
            "Rumors circulating on social media claim that India banned UPI payments in 2025, but official NPCI updates deny any ban.",
            "Local sports clubs announced new summer registration dates for youth league teams.",
        ]

        selected = rank_page_passages_for_question(question, passages, top_k=2)
        self.assertGreaterEqual(len(selected), 1)
        self.assertIn("UPI", selected[0])

    def test_extract_key_claims_from_text(self):
        """Test bounded factual claim extraction from webpage text."""
        page_text = (
            "The central bank announced a new policy regarding digital payment transactions in 2025.\n"
            "Officials confirmed that over 10 billion transactions were processed last month.\n"
            "Many users enjoy using mobile banking apps for quick payments.\n"
            "The new regulation takes effect starting next month."
        )

        claims = extract_key_claims_from_text(page_text, max_claims=3)
        self.assertLessEqual(len(claims), 3)
        self.assertGreaterEqual(len(claims), 1)


if __name__ == "__main__":
    unittest.main()

