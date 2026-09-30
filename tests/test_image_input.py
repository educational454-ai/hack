"""Unit tests for Multimodal Image Input & Verification Pipeline."""

import base64
import io
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

from core.image_ocr import (
    preprocess_image_for_ocr,
    clean_extracted_ocr_text,
    extract_text_from_image_bytes,
)
from core.image_pipeline import analyze_image, generate_thumbnail_data_url
from core.schemas import AnalysisResult, AssessmentVerdict, ClaimType
from core.url_pipeline import detect_input_mode
from fastapi.testclient import TestClient
from api.main import app


class TestImageInputPipeline(unittest.TestCase):
    """Test suite for image OCR, image pipeline, and API endpoints."""

    def setUp(self):
        # Create a small valid test image in memory
        img = Image.new("RGB", (200, 100), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.sample_png_bytes = buf.getvalue()

    def test_preprocess_image_scales_small_images(self):
        small_img = Image.new("RGBA", (150, 80), color=(255, 0, 0, 255))
        processed = preprocess_image_for_ocr(small_img)
        self.assertEqual(processed.mode, "RGB")
        self.assertGreaterEqual(processed.size[0], 600)
        self.assertGreaterEqual(processed.size[1], 300)

    def test_clean_extracted_ocr_text_filters_noise(self):
        raw = "12:45 PM\n98%\nLTE\nIndia banned UPI in 2025\n-----\n"
        cleaned = clean_extracted_ocr_text(raw)
        self.assertEqual(cleaned, "India banned UPI in 2025")

    def test_extract_text_empty_and_invalid(self):
        text, err = extract_text_from_image_bytes(b"")
        self.assertEqual(text, "")
        self.assertIn("Empty image", err)

        text2, err2 = extract_text_from_image_bytes(b"not-an-image")
        self.assertEqual(text2, "")
        self.assertIn("Invalid image format", err2)

    def test_generate_thumbnail_data_url(self):
        data_url = generate_thumbnail_data_url(self.sample_png_bytes)
        self.assertIsNotNone(data_url)
        self.assertTrue(data_url.startswith("data:image/jpeg;base64,"))

    def test_analyze_image_no_text_no_question_returns_insufficient_evidence(self):
        with patch("core.image_pipeline.extract_text_from_image_bytes", return_value=("", "No readable text")):
            res = analyze_image(self.sample_png_bytes, filename="blank.png")
            self.assertEqual(res.mode, "image")
            self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
            self.assertIn("No legible text", res.explanation)
            self.assertIsNotNone(res.image_preview)

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_analyze_image_with_extracted_text(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("India banned UPI in 2025", None)
        mock_single.return_value = AnalysisResult(
            claim="India banned UPI in 2025",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.CONTRADICTED,
            verdict_symbol="🔴",
            verdict_title="CONTRADICTED",
            confidence_score=0.9,
            explanation="No, India did not ban UPI in 2025.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
            latency_seconds=1.2,
            targeted_answer="No, India did not ban UPI in 2025.",
        )

        res = analyze_image(self.sample_png_bytes, filename="upi.png", user_question="Is this true?")
        self.assertEqual(res.mode, "image")
        self.assertEqual(res.verdict, AssessmentVerdict.CONTRADICTED)
        self.assertEqual(res.extracted_image_text, "India banned UPI in 2025")
        self.assertEqual(res.user_question, "Is this true?")
        self.assertEqual(res.targeted_answer, "No, India did not ban UPI in 2025.")
        self.assertTrue(res.image_preview.startswith("data:image/jpeg;base64,"))

    def test_detect_input_mode_image_url(self):
        mode, url, extra = detect_input_mode("https://example.com/assets/screenshot.png Did this happen?")
        self.assertEqual(mode, "image_url")
        self.assertEqual(url, "https://example.com/assets/screenshot.png")
        self.assertEqual(extra, "Did this happen?")

        mode2, url2, extra2 = detect_input_mode("https://example.com/image.jpg")
        self.assertEqual(mode2, "image_url")
        self.assertEqual(url2, "https://example.com/image.jpg")
        self.assertIsNone(extra2)

    @patch("api.main.analyze_image")
    def test_api_analyze_image_endpoint(self, mock_analyze_image):
        mock_analyze_image.return_value = AnalysisResult(
            claim="Extracted claim text",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.SUPPORTED,
            verdict_symbol="🟢",
            verdict_title="SUPPORTED",
            confidence_score=0.85,
            explanation="Evidence supports the image claim.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
            latency_seconds=0.5,
            mode="image",
            targeted_answer="Yes, the claim is supported.",
        )

        client = TestClient(app)
        resp = client.post(
            "/api/analyze-image",
            files={"file": ("test.png", self.sample_png_bytes, "image/png")},
            data={"question": "Is this verified?"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["mode"], "image")
        self.assertEqual(data["verdict"], "supported")

    @patch("api.main.analyze_image")
    def test_api_analyze_base64_payload(self, mock_analyze_image):
        mock_analyze_image.return_value = AnalysisResult(
            claim="Extracted base64 claim",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.CONTRADICTED,
            verdict_symbol="🔴",
            verdict_title="CONTRADICTED",
            confidence_score=0.88,
            explanation="Evidence contradicts the image claim.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
            latency_seconds=0.5,
            mode="image",
            targeted_answer="No, this is false.",
        )

        client = TestClient(app)
        b64_str = base64.b64encode(self.sample_png_bytes).decode("utf-8")
        resp = client.post(
            "/api/analyze",
            json={
                "image_base64": f"data:image/png;base64,{b64_str}",
                "image_filename": "uploaded.png",
                "question": "Is this real?"
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["mode"], "image")
        self.assertEqual(data["verdict"], "contradicted")


if __name__ == "__main__":
    unittest.main()
