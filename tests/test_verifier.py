"""Unit tests for Verifier module, entailment logic, and provenance validation."""

import unittest
from unittest.mock import patch
from core.schemas import EvidenceItem, SourceTier, AssessmentVerdict, ParsedClaim, ClaimType, EvidenceStance
from core.verifier import verify_claim_evidence, analyze_with_heuristics, format_evidence_prompt


class TestVerifierPrimaryLLMPath(unittest.TestCase):
    """Tests the primary Hugging Face LLM verification path."""

    def setUp(self):
        self.claim = ParsedClaim(
            original_text="Country X banned service Y",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim",
            is_verifiable=True,
            extracted_queries=["Country X banned service Y"],
        )
        self.evidence_item = EvidenceItem(
            id="ev_1",
            url="https://news.org/article",
            title="Policy Update",
            domain="news.org",
            source_tier=SourceTier.SECONDARY,
            passage="Country X prohibited service Y under new digital trade regulations.",
            similarity_score=0.70,
        )

    def test_prompt_formatting_preserves_evidence_context(self):
        prompt = format_evidence_prompt(self.claim.original_text, [self.evidence_item])
        self.assertIn("Country X banned service Y", prompt)
        self.assertIn("news.org", prompt)
        self.assertIn("prohibited service Y", prompt)

    @patch("core.verifier.analyze_with_huggingface")
    def test_llm_paraphrased_support_verdict(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.88,
            "explanation": "The passage states Country X prohibited service Y, which directly corroborates the ban.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Prohibited is synonymous with banned."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(len(supp), 1)
        self.assertEqual(supp[0].id, "ev_1")

    @patch("core.verifier.analyze_with_huggingface")
    def test_llm_paraphrased_contradiction_verdict(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "contradicted",
            "confidence_score": 0.90,
            "explanation": "The passage confirms service Y continues to operate legally, refuting the claim.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "contradicts", "reasoning": "Operating legally disproves a ban."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.CONTRADICTED)
        self.assertEqual(len(cont), 1)

    @patch("core.verifier.analyze_with_huggingface")
    def test_llm_conflicting_evidence_verdict(self, mock_hf):
        ev2 = EvidenceItem(
            id="ev_2",
            url="https://official.gov/statement",
            title="Official Statement",
            domain="official.gov",
            source_tier=SourceTier.PRIMARY,
            passage="Service Y operates legally under federal permits.",
            similarity_score=0.65,
        )
        mock_hf.return_value = {
            "assessment": "conflicting_evidence",
            "confidence_score": 0.75,
            "explanation": "Sources conflict on whether service Y is prohibited or operational.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "supports", "reasoning": "Mentions prohibition."},
                {"id": "ev_2", "stance": "contradicts", "reasoning": "States service operates legally."},
            ],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item, ev2])
        self.assertEqual(verdict, AssessmentVerdict.CONFLICTING_EVIDENCE)
        self.assertEqual(len(supp), 1)
        self.assertEqual(len(cont), 1)

    def test_subjective_claim_bypasses_evidence_check(self):
        subj_claim = ParsedClaim(
            original_text="This is the best government policy in history",
            claim_type=ClaimType.SUBJECTIVE_OPINION,
            type_explanation="Value judgment",
            is_verifiable=False,
            perspectives=["Interpretive framing"],
        )
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(subj_claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.SUBJECTIVE_OPINION)

    def test_empty_evidence_yields_insufficient_evidence(self):
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)


class TestVerifierConservativeFallback(unittest.TestCase):
    """Tests that deterministic fallback does NOT trigger false support/contradiction from keywords alone."""

    def setUp(self):
        self.claim = ParsedClaim(
            original_text="Country X banned service Y in 2025",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim",
            is_verifiable=True,
            extracted_queries=["Country X banned service Y"],
        )

    def test_fallback_with_support_keywords_does_not_falsely_return_supported(self):
        ev = EvidenceItem(
            id="ev_supp_kw",
            url="https://example.com/article",
            title="Keyword Heavy Article",
            domain="example.com",
            source_tier=SourceTier.SECONDARY,
            passage="Officials confirmed that regulations were officially enacted regarding transaction fees.",
            similarity_score=0.75,
        )
        result = analyze_with_heuristics(self.claim, [ev])
        self.assertEqual(result["assessment"], "insufficient_evidence")

    def test_fallback_with_contradiction_keywords_does_not_falsely_return_contradicted(self):
        ev = EvidenceItem(
            id="ev_cont_kw",
            url="https://example.com/article",
            title="Refutation Keyword Article",
            domain="example.com",
            source_tier=SourceTier.SECONDARY,
            passage="Reports regarding fake news and denied allegations were clarified in the daily press briefing.",
            similarity_score=0.70,
        )
        result = analyze_with_heuristics(self.claim, [ev])
        self.assertEqual(result["assessment"], "insufficient_evidence")

    def test_fallback_topically_related_evidence_returns_insufficient_evidence(self):
        ev = EvidenceItem(
            id="ev_topic",
            url="https://news.org/topic",
            title="Topic Related News",
            domain="news.org",
            source_tier=SourceTier.SECONDARY,
            passage="Country X and service Y were discussed in parliament during the 2025 session.",
            similarity_score=0.60,
        )
        result = analyze_with_heuristics(self.claim, [ev])
        self.assertEqual(result["assessment"], "insufficient_evidence")
        self.assertEqual(result["confidence_score"], 0.70)


class TestVerifierProvenanceValidation(unittest.TestCase):
    """Tests runtime provenance validation to prevent LLM evidence hallucination or metadata tampering."""

    def setUp(self):
        self.claim = ParsedClaim(
            original_text="Country X banned service Y",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim",
            is_verifiable=True,
            extracted_queries=["Country X banned service Y"],
        )
        self.supplied_item = EvidenceItem(
            id="ev_1",
            url="https://authentic-source.org/article",
            title="Real Article Title",
            domain="authentic-source.org",
            source_tier=SourceTier.PRIMARY,
            passage="Original authentic passage text from retrieval pipeline.",
            similarity_score=0.85,
        )

    @patch("core.verifier.analyze_with_huggingface")
    def test_valid_evidence_reference_preserves_metadata(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.90,
            "explanation": "Supported by primary source.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Direct confirmation."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(len(supp), 1)
        self.assertEqual(supp[0].id, "ev_1")
        self.assertEqual(supp[0].url, "https://authentic-source.org/article")
        self.assertEqual(supp[0].passage, "Original authentic passage text from retrieval pipeline.")

    @patch("core.verifier.analyze_with_huggingface")
    def test_unknown_evidence_id_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.90,
            "explanation": "LLM references non-existent ID.",
            "evidence_evaluations": [{"id": "ev_999", "stance": "supports", "reasoning": "Invented ID."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(len(supp), 0)
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertTrue(any("unmappable" in l.lower() for l in limits))

    @patch("core.verifier.analyze_with_huggingface")
    def test_invented_url_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.90,
            "explanation": "LLM invents fake URL.",
            "evidence_evaluations": [{"id": "ev_fake", "url": "https://invented-site.com/fake", "stance": "supports", "reasoning": "Fake URL."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(len(supp), 0)
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_metadata_tampering_ignored_original_retained(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.90,
            "explanation": "LLM tries overwriting metadata.",
            "evidence_evaluations": [{
                "id": "ev_1",
                "url": "https://tampered-site.com/fake",
                "passage": "Tampered passage text!",
                "stance": "supports",
                "reasoning": "Tampering attempt."
            }],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(len(supp), 1)
        self.assertEqual(supp[0].url, "https://authentic-source.org/article")
        self.assertEqual(supp[0].passage, "Original authentic passage text from retrieval pipeline.")

    @patch("core.verifier.analyze_with_huggingface")
    def test_out_of_range_evidence_index_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.90,
            "explanation": "Out of range index.",
            "evidence_evaluations": [{"id": "99", "stance": "supports", "reasoning": "Index out of range."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(len(supp), 0)
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_mixed_valid_and_invalid_references(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.88,
            "explanation": "Mixed references.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "supports", "reasoning": "Valid item."},
                {"id": "ev_bogus", "stance": "supports", "reasoning": "Bogus item."},
            ],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.supplied_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(len(supp), 1)
        self.assertEqual(supp[0].id, "ev_1")
        self.assertTrue(any("unmappable" in l.lower() for l in limits))


class TestHFResponseBoundaryHardening(unittest.TestCase):
    """Tests schema boundary validation and error hardening for untrusted HF model output."""

    def setUp(self):
        self.claim = ParsedClaim(
            original_text="Country X banned service Y",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim",
            is_verifiable=True,
            extracted_queries=["Country X banned service Y"],
        )
        self.evidence_item = EvidenceItem(
            id="ev_1",
            url="https://news.org/article",
            title="Policy Update",
            domain="news.org",
            source_tier=SourceTier.SECONDARY,
            passage="Country X prohibited service Y under new digital trade regulations.",
            similarity_score=0.70,
        )

    @patch("core.verifier.analyze_with_huggingface")
    def test_A_valid_structured_hf_response(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "explanation": "Valid structural analysis.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
            "evidence_limitations": ["Minor limitation."],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(conf, 0.85)

    @patch("core.verifier.analyze_with_huggingface")
    def test_B_invalid_verdict_string_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "invalid_verdict_string",
            "confidence_score": 0.99,
            "explanation": "Unrecognized verdict.",
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_C_missing_verdict_handled(self, mock_hf):
        mock_hf.return_value = {
            "confidence_score": 0.90,
            "explanation": "Missing assessment key.",
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_D_missing_explanation_handled(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertTrue(isinstance(expl, str))
        self.assertTrue(len(expl) > 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_E_missing_evidence_evaluations_handled(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "explanation": "No evaluations key.",
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_F_evidence_evaluations_wrong_type_handled(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "explanation": "Wrong evaluations type.",
            "evidence_evaluations": "invalid_string_type",
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_G_confidence_as_string_reset_to_zero(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": "high",
            "explanation": "Confidence string test.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_H_confidence_nan_reset_to_zero(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": float("nan"),
            "explanation": "Confidence NaN test.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_I_confidence_infinity_reset_to_zero(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": float("inf"),
            "explanation": "Confidence Inf test.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_J_confidence_below_range_reset_to_zero(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": -0.5,
            "explanation": "Confidence below range.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_K_confidence_above_range_reset_to_zero(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 1.5,
            "explanation": "Confidence above range.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Valid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_L_malformed_json_conservative_fallback(self, mock_hf):
        mock_hf.return_value = None
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_M_empty_hf_response_handled(self, mock_hf):
        mock_hf.return_value = {}
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    def test_N_markdown_fenced_json_parser(self):
        from core.verifier import parse_llm_json
        raw = "```json\n{\"assessment\": \"supported\", \"confidence_score\": 0.9, \"explanation\": \"Fenced json.\"}\n```"
        parsed = parse_llm_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["assessment"], "supported")

    @patch("core.verifier.analyze_with_huggingface")
    def test_O_unknown_evidence_references_provenance_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.9,
            "explanation": "Unknown ref.",
            "evidence_evaluations": [{"id": "ev_unknown", "stance": "supports", "reasoning": "Fake."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(supp), 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_P_supported_with_zero_supporting_evidence_downgraded(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.9,
            "explanation": "Supported with zero mapped evidence.",
            "evidence_evaluations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_Q_contradicted_with_zero_contradicting_evidence_downgraded(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "contradicted",
            "confidence_score": 0.9,
            "explanation": "Contradicted with zero mapped evidence.",
            "evidence_evaluations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(conf, 0.0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_R_invalid_evidence_stance_rejected(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.9,
            "explanation": "Invalid stance string.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "super_supported", "reasoning": "Invalid."}],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(supp), 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_S_duplicate_evidence_references_deduplicated(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "explanation": "Duplicate refs.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "supports", "reasoning": "First."},
                {"id": "ev_1", "stance": "supports", "reasoning": "Duplicate."},
            ],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(len(supp), 1)

    @patch("core.verifier.analyze_with_huggingface")
    def test_T_supporting_contradicting_overlap_resolved(self, mock_hf):
        mock_hf.return_value = {
            "assessment": "conflicting_evidence",
            "confidence_score": 0.75,
            "explanation": "Conflicting stances for same item.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "supports", "reasoning": "Claims support."},
                {"id": "ev_1", "stance": "contradicts", "reasoning": "Claims contradiction."},
            ],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim, [self.evidence_item])
        self.assertEqual(len(supp), 0)
        self.assertEqual(len(cont), 0)
        self.assertEqual(self.evidence_item.stance, EvidenceStance.NEUTRAL)


class TestTask8StanceGroundingAndSourceAdequacy(unittest.TestCase):
    """Task 8 regression tests for stance grounding, topic overlap, source adequacy, and provenance."""

    def setUp(self):
        self.claim_ram_6g = ParsedClaim(
            original_text="A phone with 6 GB RAM supports India's 6G mobile network.",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim regarding phone specs and 6G compatibility",
            is_verifiable=True,
            extracted_queries=["phone 6GB RAM 6G network India"],
        )
        self.claim_upi_ban = ParsedClaim(
            original_text="2025 mein India ne UPI ko ban kar diya tha",
            claim_type=ClaimType.FACTUAL,
            type_explanation="Factual claim regarding UPI ban in India in 2025",
            is_verifiable=True,
            extracted_queries=["India UPI ban 2025"],
        )

    @patch("core.verifier.analyze_with_huggingface")
    def test_A_topical_overlap_results_in_neutral_and_insufficient(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://tech-news.org/article",
            title="India 6G Research Update",
            domain="tech-news.org",
            source_tier=SourceTier.SECONDARY,
            passage="India is advancing 6G mobile technology research with target deployment planned for 2030.",
            similarity_score=0.75,
        )
        mock_hf.return_value = {
            "assessment": "insufficient_evidence",
            "confidence_score": 0.80,
            "explanation": "The passage discusses 6G research in India but does not state RAM requirements for network compatibility.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "neutral", "reasoning": "Topical overlap regarding 6G in India, but non-decisive for 6GB RAM compatibility."}],
            "evidence_limitations": ["Passage lacks specs on 6GB RAM requirements."],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_ram_6g, [ev])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(supp), 0)
        self.assertEqual(len(cont), 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_B_evidence_missing_decisive_relationship(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://finance-news.org/upi-2025",
            title="Digital Payments Report 2025",
            domain="finance-news.org",
            source_tier=SourceTier.SECONDARY,
            passage="In 2025, digital payment volume via UPI in India achieved record transaction milestones.",
            similarity_score=0.78,
        )
        mock_hf.return_value = {
            "assessment": "insufficient_evidence",
            "confidence_score": 0.82,
            "explanation": "The passage notes UPI transaction growth in 2025 but does not confirm or refute a ban.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "neutral", "reasoning": "Missing decisive relationship regarding a ban."}],
            "evidence_limitations": ["Passage does not explicitly address regulatory bans."],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_upi_ban, [ev])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(supp), 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_C_genuine_paraphrased_support(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://pib.gov.in/release/ram-6g",
            title="Official Telecom Specs",
            domain="pib.gov.in",
            source_tier=SourceTier.PRIMARY,
            passage="Official specs confirm smartphone devices equipped with 6 gigabytes of RAM fully support India 6G testbeds.",
            similarity_score=0.88,
        )
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.92,
            "explanation": "Primary official release confirms 6GB RAM smartphones support India 6G testbed networks.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "supports", "reasoning": "Paraphrased direct confirmation."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_ram_6g, [ev])
        self.assertEqual(verdict, AssessmentVerdict.SUPPORTED)
        self.assertEqual(len(supp), 1)

    @patch("core.verifier.analyze_with_huggingface")
    def test_D_genuine_paraphrased_contradiction(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://npci.org.in/press/upi-2025-status",
            title="NPCI Press Release",
            domain="npci.org.in",
            source_tier=SourceTier.PRIMARY,
            passage="NPCI clarifies that UPI operations remained fully functional throughout 2025 with zero bans or prohibitions.",
            similarity_score=0.91,
        )
        mock_hf.return_value = {
            "assessment": "contradicted",
            "confidence_score": 0.95,
            "explanation": "NPCI official statement confirms UPI was never banned in 2025.",
            "evidence_evaluations": [{"id": "ev_1", "stance": "contradicts", "reasoning": "Direct official refutation of ban."}],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_upi_ban, [ev])
        self.assertEqual(verdict, AssessmentVerdict.CONTRADICTED)
        self.assertEqual(len(cont), 1)

    @patch("core.verifier.analyze_with_huggingface")
    def test_E_multiple_weak_related_passages_yielding_insufficient(self, mock_hf):
        ev1 = EvidenceItem(
            id="ev_1",
            url="https://unverified-blog.com/post1",
            title="Tech Forum Post",
            domain="unverified-blog.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="Blog user claims 6GB RAM phones work on 6G networks in India.",
            similarity_score=0.60,
        )
        ev2 = EvidenceItem(
            id="ev_2",
            url="https://unverified-forum.com/post2",
            title="Discussion Thread",
            domain="unverified-forum.com",
            source_tier=SourceTier.LOW_CONFIDENCE,
            passage="Another user states 6GB RAM is sufficient for 6G band compatibility.",
            similarity_score=0.55,
        )
        mock_hf.return_value = {
            "assessment": "supported",
            "confidence_score": 0.85,
            "explanation": "Forum blogs claim 6GB RAM supports 6G.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "supports", "reasoning": "Blog claim."},
                {"id": "ev_2", "stance": "supports", "reasoning": "Forum claim."},
            ],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_ram_6g, [ev1, ev2])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)
        self.assertEqual(len(supp), 0)

    @patch("core.verifier.analyze_with_huggingface")
    def test_F_evidence_from_different_domains_relevant_but_non_decisive(self, mock_hf):
        ev1 = EvidenceItem(
            id="ev_1",
            url="https://reuters.com/tech/6g-overview",
            title="Reuters Tech",
            domain="reuters.com",
            source_tier=SourceTier.SECONDARY,
            passage="Telecom operators are testing 6G network prototypes worldwide.",
            similarity_score=0.72,
        )
        ev2 = EvidenceItem(
            id="ev_2",
            url="https://bbc.com/news/india-tech",
            title="BBC News",
            domain="bbc.com",
            source_tier=SourceTier.SECONDARY,
            passage="India announces trial spectrum allocation for next-generation mobile standards.",
            similarity_score=0.70,
        )
        mock_hf.return_value = {
            "assessment": "insufficient_evidence",
            "confidence_score": 0.75,
            "explanation": "Articles provide background on 6G testing but do not detail RAM specifications.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "neutral", "reasoning": "Topical 6G background."},
                {"id": "ev_2", "stance": "neutral", "reasoning": "Topical spectrum trial info."},
            ],
            "evidence_limitations": ["Lacks hardware RAM compatibility facts."],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_ram_6g, [ev1, ev2])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    @patch("core.verifier.analyze_with_huggingface")
    def test_G_provenance_validation_remains_valid(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://pib.gov.in/fact-check",
            title="PIB Fact Check",
            domain="pib.gov.in",
            source_tier=SourceTier.PRIMARY,
            passage="Official advisory confirms UPI is active and fully operational.",
            similarity_score=0.85,
        )
        mock_hf.return_value = {
            "assessment": "contradicted",
            "confidence_score": 0.90,
            "explanation": "Official statement refutes ban.",
            "evidence_evaluations": [
                {"id": "ev_1", "stance": "contradicts", "reasoning": "Valid refutation."},
                {"id": "ev_invented", "stance": "contradicts", "reasoning": "Fake reference."},
            ],
            "evidence_limitations": [],
        }
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_upi_ban, [ev])
        self.assertEqual(verdict, AssessmentVerdict.CONTRADICTED)
        self.assertEqual(len(cont), 1)
        self.assertEqual(cont[0].id, "ev_1")
        self.assertTrue(any("ev_invented" in limit for limit in limits))

    @patch("core.verifier.analyze_with_huggingface")
    def test_H_malformed_hf_output_safely_handled(self, mock_hf):
        ev = EvidenceItem(
            id="ev_1",
            url="https://news.org/item",
            title="News",
            domain="news.org",
            source_tier=SourceTier.SECONDARY,
            passage="Some article content about digital payments.",
            similarity_score=0.60,
        )
        mock_hf.return_value = {"random_key": "malformed_output"}
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(self.claim_upi_ban, [ev])
        self.assertEqual(verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)


if __name__ == "__main__":
    unittest.main()

