"""Unit tests for Multimodal Image Input & Verification Pipeline."""

import base64
import io
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image, ImageDraw

from core.image_ocr import (
    preprocess_image_for_ocr,
    clean_extracted_ocr_text,
    extract_text_from_image_bytes,
)
from core.image_pipeline import (
    analyze_image,
    generate_thumbnail_data_url,
    classify_question_intent,
    normalize_ocr_spacing_and_artifacts,
    extract_ocr_claim_proposition,
)
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

    def test_real_ocr_extraction_integration_on_pil_image(self):
        """Integration test using real OCR engine on a generated PIL image with clear text."""
        img = Image.new("RGB", (600, 200), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((30, 80), "The Earth orbits the Sun.", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        text, err = extract_text_from_image_bytes(buf.getvalue())
        self.assertIsNotNone(text)
        self.assertIn("Earth", text)

    def test_extract_ocr_claim_proposition_noisy_headline_and_artifacts(self):
        raw_ocr = "END OFAN ERA The Eiffel Tower isreportedlyset for demolition next year after lease expiry, due to rising complaints!C UPSCALERTS 347"
        prop = extract_ocr_claim_proposition(raw_ocr)
        self.assertIsNotNone(prop)
        self.assertIn("Eiffel Tower", prop)
        self.assertIn("is reportedly set for demolition", prop)
        self.assertNotIn("END OF AN ERA", prop)
        self.assertNotIn("UPSCALERTS", prop)

    def test_extract_ocr_claim_proposition_normal_factual_sentence(self):
        raw_ocr = "India banned UPI in 2025"
        prop = extract_ocr_claim_proposition(raw_ocr)
        self.assertEqual(prop, "India banned UPI in 2025")

    def test_extract_ocr_claim_proposition_spacing_artifacts(self):
        raw_ocr = "BREAKING NEWS Government announcednew EV subsidyfor all citizens"
        prop = extract_ocr_claim_proposition(raw_ocr)
        self.assertIsNotNone(prop)
        self.assertIn("Government announced new EV subsidy for all citizens", prop)
        self.assertNotIn("BREAKING NEWS", prop)

    def test_extract_ocr_claim_proposition_source_attribution_noise(self):
        raw_ocr = "NASA discovered liquid water on Mars surface @space_news_daily"
        prop = extract_ocr_claim_proposition(raw_ocr)
        self.assertEqual(prop, "NASA discovered liquid water on Mars surface")

    def test_extract_ocr_claim_proposition_unextractable(self):
        raw_ocr = "12345 67890 XYZ 999"
        prop = extract_ocr_claim_proposition(raw_ocr)
        self.assertIsNone(prop)

    def test_extract_ocr_claim_proposition_corrupted_word_order_rejected(self):
        self.assertIsNone(extract_ocr_claim_proposition("orbits The the"))
        self.assertIsNone(extract_ocr_claim_proposition("Earth Sun. orbits The the"))

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_analyze_image_unextractable_ocr_returns_insufficient_evidence(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("12345 67890 XYZ 999", None)
        res = analyze_image(self.sample_png_bytes, filename="garbage.png", user_question="verify")
        mock_single.assert_not_called()
        self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertIn("Could not extract a reliable", res.explanation)

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_analyze_image_corrupted_ocr_bypasses_retrieval(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Earth Sun. orbits The the", None)
        res = analyze_image(self.sample_png_bytes, filename="earth.png", user_question="verify")
        mock_single.assert_not_called()
        self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertIn("Could not extract a reliable", res.explanation)

    def test_generate_thumbnail_data_url(self):
        data_url = generate_thumbnail_data_url(self.sample_png_bytes)
        self.assertIsNotNone(data_url)
        self.assertTrue(data_url.startswith("data:image/jpeg;base64,"))

    def test_classify_question_intent_generic(self):
        # Verification intent
        self.assertEqual(classify_question_intent("verify"), "fact_check_verify")
        self.assertEqual(classify_question_intent("is this true?"), "fact_check_verify")
        self.assertEqual(classify_question_intent("fact check this"), "fact_check_verify")
        self.assertEqual(classify_question_intent("is this claim real?"), "fact_check_verify")
        self.assertEqual(classify_question_intent("Can you fact check this?"), "fact_check_verify")
        self.assertEqual(classify_question_intent(None), "fact_check_verify")

        # Visual question intent
        self.assertEqual(classify_question_intent("is it square?"), "visual_question")
        self.assertEqual(classify_question_intent("Is the object square?"), "visual_question")
        self.assertEqual(classify_question_intent("what object is shown?"), "visual_question")
        self.assertEqual(classify_question_intent("Describe the main object."), "visual_question")
        self.assertEqual(classify_question_intent("how many people are visible?"), "visual_question")
        self.assertEqual(classify_question_intent("what color is this?"), "visual_question")

        # Text extraction intent
        self.assertEqual(classify_question_intent("What text is visible in this image?"), "text_extraction")
        self.assertEqual(classify_question_intent("What does this image say?"), "text_extraction")
        self.assertEqual(classify_question_intent("Extract the text from this image."), "text_extraction")
        self.assertEqual(classify_question_intent("Read the text in this image."), "text_extraction")
        self.assertEqual(classify_question_intent("Can you transcribe this?"), "text_extraction")
        self.assertEqual(classify_question_intent("What words are written here?"), "text_extraction")
        self.assertEqual(classify_question_intent("Show me the text."), "text_extraction")
        self.assertEqual(classify_question_intent("OCR this image."), "text_extraction")
        self.assertEqual(classify_question_intent("Transcribe the writing."), "text_extraction")
        self.assertEqual(classify_question_intent("Read what is written in the image."), "text_extraction")
        self.assertEqual(classify_question_intent("Please tell me the writing shown in the picture."), "text_extraction")

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

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_observed_question_does_not_call_web_search(self, mock_ocr, mock_single):
        """Must NOT execute web search, analyze_claim_single, or HF verifier for 'What text is visible in this image?'."""
        mock_ocr.return_value = ("Emergency Notice: Road closed on October 5th.", None)

        res = analyze_image(self.sample_png_bytes, filename="notice.png", user_question="What text is visible in this image?")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.targeted_answer, "Emergency Notice: Road closed on October 5th.")
        self.assertEqual(res.resolved_claim, "Emergency Notice: Road closed on October 5th.")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_ocr_backend_unavailable_returns_truthful_limitation(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("", "Image text extraction is currently unavailable because no OCR backend is configured.")

        res = analyze_image(self.sample_png_bytes, filename="notice.png", user_question="What text is visible in this image?")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertIn("unavailable", res.explanation)
        self.assertIn("unavailable", res.evidence_limitations[0])

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_different_wording_1(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Sale 50% off all items", None)

        res = analyze_image(self.sample_png_bytes, filename="ad.png", user_question="What does this image say?")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.targeted_answer, "Sale 50% off all items")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_different_wording_2(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Meeting agenda at 10 AM", None)

        res = analyze_image(self.sample_png_bytes, filename="agenda.png", user_question="Can you transcribe this?")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.targeted_answer, "Meeting agenda at 10 AM")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_different_wording_3(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Caution: Wet floor", None)

        res = analyze_image(self.sample_png_bytes, filename="sign.png", user_question="Read the words written here.")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.targeted_answer, "Caution: Wet floor")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_unseen_wording(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Welcome to the Grand Hotel", None)

        res = analyze_image(self.sample_png_bytes, filename="hotel.png", user_question="Please tell me the writing shown in the picture.")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.targeted_answer, "Welcome to the Grand Hotel")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_text_extraction_empty_ocr_returns_limitation_no_web_search(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("", None)

        res = analyze_image(self.sample_png_bytes, filename="blank_photo.png", user_question="Read the text in this image.")
        mock_single.assert_not_called()
        self.assertEqual(res.question_intent, "text_extraction")
        self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertIn("No readable text", res.explanation)

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_visual_question_describe_main_object_no_web_search(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("", None)

        with patch("core.image_pipeline.analyze_with_multimodal_vision", return_value=None):
            res = analyze_image(self.sample_png_bytes, filename="photo.jpg", user_question="Describe the main object.")
            mock_single.assert_not_called()
            self.assertEqual(res.question_intent, "visual_question")
            self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_visual_question_is_object_square_no_web_search(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("", None)

        with patch("core.image_pipeline.analyze_with_multimodal_vision", return_value=None):
            res = analyze_image(self.sample_png_bytes, filename="shape.jpg", user_question="Is the object square?")
            mock_single.assert_not_called()
            self.assertEqual(res.question_intent, "visual_question")
            self.assertEqual(res.verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_image_factual_claim_question_verify_resolves_ocr_claim(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("The Eiffel Tower will be closed after midnight on December 31", None)
        mock_single.return_value = AnalysisResult(
            claim="The Eiffel Tower will be closed after midnight on December 31",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.CONTRADICTED,
            verdict_symbol="🔴",
            verdict_title="CONTRADICTED",
            confidence_score=0.9,
            explanation="Official statements confirm the tower remains open.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
            latency_seconds=0.8,
        )

        res = analyze_image(self.sample_png_bytes, filename="eiffel.png", user_question="verify")
        mock_single.assert_called_once_with("The Eiffel Tower will be closed after midnight on December 31")
        self.assertEqual(res.resolved_claim, "The Eiffel Tower will be closed after midnight on December 31")
        self.assertEqual(res.question_intent, "fact_check_verify")

    @patch("core.image_pipeline.analyze_claim_single")
    @patch("core.image_pipeline.extract_text_from_image_bytes")
    def test_verification_can_you_fact_check_this(self, mock_ocr, mock_single):
        mock_ocr.return_value = ("Government announced new EV subsidy", None)
        mock_single.return_value = AnalysisResult(
            claim="Government announced new EV subsidy",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.SUPPORTED,
            verdict_symbol="🟢",
            verdict_title="SUPPORTED",
            confidence_score=0.9,
            explanation="Official ministry release confirms the subsidy.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=[],
            all_sources=[],
        )

        res = analyze_image(self.sample_png_bytes, filename="ev.png", user_question="Can you fact check this?")
        mock_single.assert_called_once_with("Government announced new EV subsidy")
        self.assertEqual(res.question_intent, "fact_check_verify")

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
