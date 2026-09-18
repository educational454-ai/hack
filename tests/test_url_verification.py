import unittest
from core.url_pipeline import detect_input_mode, rank_page_passages_for_question, extract_key_claims_from_text
from core.url_fetcher import WebpageFetchResult
from core.schemas import AssessmentVerdict, ClaimType, AnalysisResult


class TestURLVerificationPipeline(unittest.TestCase):
    """Unit test suite for Task 13 URL & URL+Question verification features."""

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
