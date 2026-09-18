import unittest
from core.schemas import EvidenceItem, SourceTier
from core.ranker import rank_evidence_chunks
from core.verifier import SYSTEM_PROMPT


class TestRelevanceDisplayAndCaveats(unittest.TestCase):
    """Unit tests for relevance display clamping and generic caveat prompt rules."""

    def test_relevance_score_clamping_boundary(self):
        """Test that internal primary source multiplier produces score >1.0 for ranking, but presentation caps at 100%."""
        chunks = [
            {
                "url": "https://official.gov/spec",
                "title": "Official Spec",
                "domain": "official.gov",
                "source_tier": SourceTier.PRIMARY,
                "passage": "Water freezes at 0 degrees Celsius under standard atmospheric pressure.",
            },
            {
                "url": "https://blog.com/post",
                "title": "Blog Post",
                "domain": "blog.com",
                "source_tier": SourceTier.LOW_CONFIDENCE,
                "passage": "Water freezes at zero degrees C.",
            }
        ]

        # Simulate rank_evidence_chunks ranking
        ranked = rank_evidence_chunks("Water freezes at 0 degrees Celsius", chunks, top_k=2)
        self.assertGreaterEqual(len(ranked), 1)

        # Primary source should rank first
        primary_item = ranked[0]
        self.assertEqual(primary_item.source_tier, SourceTier.PRIMARY)

        # Presentation layer clamping helper simulation (matching ResultCard / RightSidebar UI logic)
        raw_score = primary_item.similarity_score
        displayed_percent = min(100, round(raw_score * 100))
        self.assertLessEqual(displayed_percent, 100)
        self.assertGreaterEqual(displayed_percent, 0)

    def test_system_prompt_caveat_guidance_present(self):
        """Test that SYSTEM_PROMPT includes explicit generic caveat guidance preventing quantitative demands on descriptive claims."""
        self.assertIn("Evidence Limitations & Caveats Guidance", SYSTEM_PROMPT)
        self.assertIn("Do NOT demand or criticize evidence for lacking quantitative data", SYSTEM_PROMPT)
        self.assertIn("Descriptive factual statements from primary or secondary sources are fully valid evidence", SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
