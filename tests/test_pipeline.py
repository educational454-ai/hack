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


from unittest.mock import patch


class TestTask81SyntheticEvidenceRemoval(unittest.TestCase):
    """Task 8.1 regression tests ensuring no synthetic evidence enters the pipeline."""

    @patch("core.pipeline.retrieve_search_candidates", return_value=[])
    def test_empty_failed_search_produces_no_synthetic_evidence(self, mock_retriever):
        """Verifies that failed/empty search returns [] and does not fabricate EvidenceItems."""
        from core.pipeline import analyze_claim
        from core.schemas import AssessmentVerdict
        result = analyze_claim("Unindexed claim for synthetic test")
        self.assertEqual(result.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(result.supporting_evidence), 0)
        self.assertEqual(len(result.contradicting_evidence), 0)
        self.assertEqual(len(result.all_sources), 0)

    def test_retriever_returns_empty_on_search_exception(self):
        """Verifies that retrieve_search_candidates returns [] when search client fails."""
        from core.retriever import retrieve_search_candidates
        try:
            import ddgs
            with patch("ddgs.DDGS", side_effect=Exception("Search failed")):
                candidates = retrieve_search_candidates(["unindexed query text"])
                self.assertEqual(candidates, [])
        except ImportError:
            try:
                # pyrefly: ignore [missing-import]
                import duckduckgo_search
                with patch("duckduckgo_search.DDGS", side_effect=Exception("Search failed")):
                    candidates = retrieve_search_candidates(["unindexed query text"])
                    self.assertEqual(candidates, [])
            except ImportError:
                candidates = retrieve_search_candidates(["unindexed query text"])
                self.assertEqual(candidates, [])

    def test_existing_retrieval_behavior_with_real_candidates(self):
        """Verifies that retrieval behavior is unchanged when real candidates exist."""
        from core.retriever import retrieve_search_candidates
        mock_results = [
            {
                "href": "https://real-source.org/article",
                "title": "Real Source Title",
                "body": "Real article text snippet describing factual event.",
            }
        ]
        try:
            import ddgs
            with patch("ddgs.DDGS") as mock_ddgs_cls:
                mock_inst = mock_ddgs_cls.return_value
                mock_inst.text.return_value = mock_results
                candidates = retrieve_search_candidates(["real query"])
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["url"], "https://real-source.org/article")
        except ImportError:
            try:
                # pyrefly: ignore [missing-import]
                import duckduckgo_search
                with patch("duckduckgo_search.DDGS") as mock_ddgs_cls:
                    mock_inst = mock_ddgs_cls.return_value
                    mock_inst.text.return_value = mock_results
                    candidates = retrieve_search_candidates(["real query"])
                    self.assertEqual(len(candidates), 1)
                    self.assertEqual(candidates[0]["url"], "https://real-source.org/article")
            except ImportError:
                pass

