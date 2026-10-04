"""End-to-End Orchestration Pipeline for Evidence-First Misinformation Analysis."""

import logging
import time
from typing import List
from .config import config
from .schemas import (
    AnalysisResult,
    AssessmentVerdict,
    ClaimType,
    FactCheckItem,
    SourceMetadata,
    RelevantImage,
)
from .claim_parser import parse_claim
from .retriever import retrieve_search_candidates, retrieve_relevant_images
from .source_filter import build_source_metadata
from .extractor import extract_evidence_from_candidates
from .ranker import rank_evidence_chunks, rank_and_filter_images
from .evidence_gate import filter_evidence_for_verification
from .verifier import verify_claim_evidence, VERDICT_SYMBOLS, formulate_direct_statement
from .url_normalizer import normalize_url
from .fact_check_api import (
    search_fact_checks,
    fact_checks_to_evidence_items,
    aggregate_fact_check_verdict,
)
from .multilingual import detect_language, translate_to_english_for_verification
from .publisher_audit import audit_sources_batch

from .url_pipeline import detect_input_mode, analyze_url_with_question, analyze_url_only

logger = logging.getLogger(__name__)


def analyze_claim_single(claim_text: str) -> AnalysisResult:
    """Executes the full evidence-first verification pipeline for a single claim string.

    Pipeline steps:
      1. Claim parsing & classification
      2. Google Fact Check Tools API lookup (parallel, PRIMARY tier)
      3. DuckDuckGo web search retrieval
      4. Source metadata & tiering
      5. Full-page passage extraction
      6. BGE-M3 semantic similarity ranking
      7. Evidence quality gate
      8. HF LLM / heuristic verdict
      9. Relevant image retrieval
    """
    start_time = time.time()
    logger.info(f"Starting analysis for claim: '{claim_text}'")

    # Step 0: Multilingual Language Detection & Cross-Lingual Translation
    lang_code, lang_name = detect_language(claim_text)
    logger.info(f"[Multilingual] Detected language: {lang_name} ({lang_code})")
    
    # Generate English translation for universal search if non-English
    claim_en = translate_to_english_for_verification(claim_text, lang_code) if lang_code != "en" else claim_text

    # Step 1: Claim Parser
    parsed = parse_claim(claim_text, english_text=claim_en if claim_en != claim_text else None)
    logger.info(f"Claim classified as: {parsed.claim_type.value}")

    # Subjective early-return (no fact-check needed)
    if parsed.claim_type == ClaimType.SUBJECTIVE_OPINION:
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(parsed, [])
        sym, title = VERDICT_SYMBOLS[verdict]
        elapsed = round(time.time() - start_time, 2)
        direct_answer = formulate_direct_statement(parsed.original_text, verdict)
        return AnalysisResult(
            claim=parsed.original_text,
            claim_type=parsed.claim_type,
            verdict=verdict,
            verdict_symbol=sym,
            verdict_title=title,
            confidence_score=conf,
            explanation=expl,
            supporting_evidence=supp,
            contradicting_evidence=cont,
            evidence_limitations=limits,
            all_sources=[],
            latency_seconds=elapsed,
            mode="claim",
            targeted_answer=direct_answer,
            detected_language=lang_code,
            detected_language_name=lang_name,
        )

    # ── Step 2: Google Fact Check Tools API ────────────────────────────────────
    raw_fact_checks: list = []
    fact_check_items: List[FactCheckItem] = []
    fc_evidence_chunks: list = []

    gfc_key = config.google_fact_check_api_key
    if gfc_key:
        try:
            # Query Fact Check API in original text and translated text
            fc_lang = lang_code if lang_code in ("hi", "bn", "ta", "te", "mr", "gu") else "en"
            raw_fact_checks = search_fact_checks(
                claim_text, api_key=gfc_key, language_code=fc_lang, max_results=5
            )
            # If no results in regional script and translated text exists, check in English
            if not raw_fact_checks and claim_en != claim_text:
                raw_fact_checks = search_fact_checks(
                    claim_en, api_key=gfc_key, language_code="en", max_results=5
                )

            # Convert to FactCheckItem schema objects for the response
            fact_check_items = [
                FactCheckItem(
                    claim_text=fc["claim_text"],
                    claimant=fc.get("claimant"),
                    claim_date=fc.get("claim_date"),
                    rating=fc["rating"],
                    verdict_signal=fc["verdict_signal"],
                    publisher_name=fc["publisher_name"],
                    publisher_site=fc.get("publisher_site"),
                    rating_url=fc["rating_url"],
                    title=fc["title"],
                )
                for fc in raw_fact_checks
            ]
            # Convert to evidence dict format (PRIMARY tier) for the ranking step
            fc_evidence_chunks = fact_checks_to_evidence_items(raw_fact_checks)
            logger.info(
                f"Fact Check API: {len(fact_check_items)} result(s) found, "
                f"injecting as PRIMARY evidence."
            )
        except Exception as fc_exc:
            logger.warning(f"Fact Check API call failed: {fc_exc}")
    else:
        logger.debug("GOOGLE_FACT_CHECK_API_KEY not set — skipping Fact Check API step.")

    # ── Step 3: Web Search Retrieval (Bilingual Queries) ──────────────────────
    search_queries = list(parsed.extracted_queries)

    logger.info(f"Searching web using queries: {search_queries}")
    candidates = retrieve_search_candidates(
        search_queries, max_results=max(config.max_search_results, 10)
    )
    logger.info(f"Retrieved {len(candidates)} search candidates.")

    # ── Step 4: Source Metadata & Tiering ─────────────────────────────────────
    all_sources: List[SourceMetadata] = []
    seen_urls = set()
    candidate_domains: List[str] = []
    for item in candidates:
        u = item.get("url", "")
        if u:
            norm_u = normalize_url(u)
            if norm_u and norm_u not in seen_urls:
                seen_urls.add(norm_u)
                source_meta = build_source_metadata(u, item.get("title", ""))
                all_sources.append(source_meta)
                if source_meta.domain:
                    candidate_domains.append(source_meta.domain)

    # ── Step 4.5: Publisher Track-Record & Transparency Audit ─────────────────
    publisher_records = audit_sources_batch(
        candidate_domains, api_key=config.google_fact_check_api_key
    )
    for source in all_sources:
        if source.domain in publisher_records:
            source.publisher_record = publisher_records[source.domain]

    # ── Step 5: Passage Extraction & Boilerplate Cleaning ─────────────────────
    extracted_chunks = extract_evidence_from_candidates(
        candidates, timeout=config.http_timeout
    )
    logger.info(f"Extracted {len(extracted_chunks)} candidate passages.")

    # Prepend fact-check passages (they get highest priority in ranking)
    all_chunks = fc_evidence_chunks + extracted_chunks

    # ── Step 6: BGE-M3 Semantic Similarity Ranking with Publisher Modifiers ───
    ranking_query = parsed.english_text or parsed.original_text
    ranked_evidence = rank_evidence_chunks(
        ranking_query,
        all_chunks,
        top_k=config.top_k_evidence + len(fc_evidence_chunks),
        publisher_records=publisher_records,
    )
    logger.info(f"Selected top {len(ranked_evidence)} most relevant evidence chunks.")

    # ── Step 7: Evidence Quality Gate ─────────────────────────────────────────
    usable_evidence, rejected_evidence = filter_evidence_for_verification(ranked_evidence)
    logger.info(
        f"Evidence Quality Gate: retained {len(usable_evidence)} usable items, "
        f"filtered out {len(rejected_evidence)} items."
    )

    # ── Step 8: HF LLM / Heuristic Verdict ────────────────────────────────────
    verdict, conf, expl, supp, cont, limits = verify_claim_evidence(
        parsed, usable_evidence
    )
    sym, title = VERDICT_SYMBOLS[verdict]

    # ── Fact-Check Verdict Override ────────────────────────────────────────────
    # If the pipeline returned insufficient evidence but Fact Check publishers
    # have a clear consensus, trust the publishers.
    if (
        verdict == AssessmentVerdict.INSUFFICIENT_EVIDENCE
        and raw_fact_checks
    ):
        fc_signal = aggregate_fact_check_verdict(raw_fact_checks)
        if fc_signal:
            fc_verdict_str, fc_conf = fc_signal
            verdict_map = {
                "contradicted": AssessmentVerdict.CONTRADICTED,
                "supported": AssessmentVerdict.SUPPORTED,
                "conflicting": AssessmentVerdict.CONFLICTING_EVIDENCE,
            }
            if fc_verdict_str in verdict_map:
                verdict = verdict_map[fc_verdict_str]
                conf = fc_conf
                sym, title = VERDICT_SYMBOLS[verdict]
                publishers = list(
                    dict.fromkeys(fc["publisher_name"] for fc in raw_fact_checks)
                )[:3]
                pub_str = ", ".join(publishers)
                logger.info(
                    f"Fact-check override: verdict upgraded to {title} "
                    f"based on {pub_str}."
                )
                expl = (
                    f"Google Fact Check Tools found {len(raw_fact_checks)} "
                    f"published fact-check(s) from {pub_str} rating this claim "
                    f'as "{raw_fact_checks[0]["rating"]}". ' + expl
                )

    # ── Step 9: Relevant Image Retrieval ──────────────────────────────────────
    relevant_images: List[RelevantImage] = []
    try:
        raw_images = retrieve_relevant_images(parsed.original_text, max_images=8)
        relevant_images = rank_and_filter_images(
            claim=parsed.original_text,
            raw_images=raw_images,
            top_k=2,
            min_threshold=0.45,
        )
    except Exception as img_ex:
        logger.warning(f"Could not retrieve/rank images: {img_ex}")

    direct_answer = formulate_direct_statement(parsed.original_text, verdict)
    if not expl.startswith("No,") and not expl.startswith("Yes,") and not expl.startswith("The statement"):
        expl = f"{direct_answer} {expl}"

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Completed analysis in {elapsed}s with verdict: {title} ({sym})")

    # Free memory from intermediate chunks and DOM trees
    del extracted_chunks
    import gc
    gc.collect()

    return AnalysisResult(
        claim=parsed.original_text,
        claim_type=parsed.claim_type,
        verdict=verdict,
        verdict_symbol=sym,
        verdict_title=title,
        confidence_score=conf,
        explanation=expl,
        supporting_evidence=supp,
        contradicting_evidence=cont,
        evidence_limitations=limits,
        all_sources=all_sources,
        relevant_images=relevant_images,
        fact_checks=fact_check_items,
        latency_seconds=elapsed,
        mode="claim",
        targeted_answer=direct_answer,
        detected_language=lang_code,
        detected_language_name=lang_name,
        publisher_transparency=list(publisher_records.values()),
    )


def analyze_claim(claim_text: str) -> AnalysisResult:
    """Main verification entrypoint detecting input mode and dispatching accordingly."""
    mode, url, text_or_question = detect_input_mode(claim_text)

    if mode == "image_url" and url:
        try:
            import requests
            resp = requests.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                from .image_pipeline import analyze_image
                return analyze_image(
                    image_bytes=resp.content,
                    filename=url.split("/")[-1].split("?")[0],
                    user_question=text_or_question,
                )
        except Exception as exc:
            logger.warning(f"Failed to fetch image from URL '{url}': {exc}")

    if mode == "url_question" and url and text_or_question:
        return analyze_url_with_question(url, text_or_question, analyze_claim_single)
    elif mode == "url" and url:
        return analyze_url_only(url, analyze_claim_single)
    else:
        return analyze_claim_single(claim_text)

