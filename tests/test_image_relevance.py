import unittest
from core.ranker import score_image_relevance, rank_and_filter_images
from core.schemas import RelevantImage


class TestImageRelevanceFilter(unittest.TestCase):
    """Unit tests for generic semantic image relevance filtering."""

    def test_generic_unrelated_image_rejected(self):
        """Test that generic tourist photos for a country claim are rejected."""
        claim = "India banned UPI in 2025"
        img_dict = {
            "title": "India Gate tourist photograph",
            "source_url": "https://www.pexels.com/photo/brown-concrete-india-gate-789750/",
        }

        score = score_image_relevance(claim, img_dict)
        self.assertLess(score, 0.45, f"Unrelated tourist image should be rejected but got score {score}")

    def test_generic_country_wikipedia_rejected(self):
        """Test that generic Wikipedia country page images are rejected for specific claim."""
        claim = "India banned UPI in 2025"
        img_dict = {
            "title": "India - Wikipedia",
            "source_url": "https://et.wikipedia.org/wiki/India",
        }

        score = score_image_relevance(claim, img_dict)
        self.assertLess(score, 0.45, f"Generic Wikipedia country image should be rejected but got score {score}")

    def test_relevant_article_image_accepted(self):
        """Test that a topic-specific article image is accepted."""
        claim = "India banned UPI in 2025"
        img_dict = {
            "title": "Fact Check: Did Govt Ban UPI Payments in 2025?",
            "source_url": "https://factcheck.org/2025/01/upi-payment-rules/",
        }

        score = score_image_relevance(claim, img_dict)
        self.assertGreaterEqual(score, 0.45, f"Relevant article image should be accepted but got score {score}")

    def test_missing_metadata_honest_handling(self):
        """Test missing title and source_url remain None and don't fabricate data."""
        claim = "India banned UPI in 2025"
        raw_candidates = [
            {
                "title": None,
                "image_url": "https://cdn.example.com/pic1.jpg",
                "thumbnail_url": None,
                "source_url": None,
            }
        ]

        filtered = rank_and_filter_images(claim, raw_candidates, top_k=2, min_threshold=0.45)
        self.assertEqual(len(filtered), 0, "Image without textual metadata cannot establish relevance and must be excluded.")

    def test_source_url_integrity(self):
        """Test image_url is never used as fallback for source_url."""
        claim = "Chandrayaan-3 landed on the Moon in 2023"
        raw_candidates = [
            {
                "title": "ISRO Chandrayaan-3 successful Moon landing 2023",
                "image_url": "https://images.example.com/chandrayaan3.jpg",
                "thumbnail_url": "https://images.example.com/thumb.jpg",
                "source_url": "https://news.example.com/space/chandrayaan3-moon-landing-2023",
            }
        ]

        filtered = rank_and_filter_images(claim, raw_candidates, top_k=2, min_threshold=0.45)
        self.assertEqual(len(filtered), 1)
        img = filtered[0]
        self.assertNotEqual(img.image_url, img.source_url, "image_url must not be used as source_url fallback.")
        self.assertEqual(img.source_url, "https://news.example.com/space/chandrayaan3-moon-landing-2023")

    def test_zero_relevant_images_returns_empty(self):
        """Test rank_and_filter_images returns [] if all candidates fail threshold."""
        claim = "India banned UPI in 2025"
        raw_candidates = [
            {"title": "India Gate photograph", "image_url": "https://cdn.example.com/img1.jpg", "source_url": "https://pexels.com/india-gate"},
            {"title": "India - Wikipedia", "image_url": "https://cdn.example.com/img2.jpg", "source_url": "https://wikipedia.org/wiki/India"},
        ]

        filtered = rank_and_filter_images(claim, raw_candidates, top_k=2, min_threshold=0.45)
        self.assertEqual(filtered, [], "When zero candidates satisfy threshold, [] must be returned.")

    def test_claim_independence(self):
        """Test filtering works generically across completely different claims without hardcoded rules."""
        claim1 = "Earth takes approximately 365 days to orbit the Sun"
        bad_img = {"title": "Solar System Overview PPT", "image_url": "https://cdn.example.com/ppt.jpg", "source_url": "https://slideshare.net/ppt"}
        good_img = {"title": "Why Does Earth Orbit The Sun In 365 Days?", "image_url": "https://cdn.example.com/earth.jpg", "source_url": "https://science.com/earth-orbit-365-days"}

        res = rank_and_filter_images(claim1, [bad_img, good_img], top_k=2, min_threshold=0.45)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_url, "https://science.com/earth-orbit-365-days")


if __name__ == "__main__":
    unittest.main()
