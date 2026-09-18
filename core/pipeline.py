"""End-to-End Orchestration Pipeline for Evidence-First Misinformation Analysis."""

import logging
import time
from typing import List
from .config import config
from .schemas import (
    AnalysisResult,
    AssessmentVerdict,
    ClaimType,
    SourceMetadata,
    RelevantImage,
)
from .claim_parser import parse_claim
from .retriever import retrieve_search_candidates, retrieve_relevant_images
from .source_filter import build_source_metadata
from .extractor import extract_evidence_from_candidates
from .ranker import rank_evidence_chunks
from .evidence_gate import filter_evidence_for_verification
from .verifier import verify_claim_evidence, VERDICT_SYMBOLS

logger = logging.getLogger(__name__)


def analyze_claim(claim_text: str) -> AnalysisResult:
    """Executes the full 8-step evidence-first verification pipeline.

    Workflow:
    1. Parse Claim & determine claim type (Factual vs Subjective).
    2. If Subjective: bypass false fact-check, provide perspectives & context.
    3. If Factual:
       - Multi-query search candidate retrieval.
       - Source tiering (Primary, Secondary, Low-confidence).
       - Passage extraction & HTML cleaning.
       - BGE-M3 semantic similarity ranking.
       - Claim <-> Evidence comparative analysis (via Hugging Face LLM).
       - Non-binary transparent result compilation.
    """
    start_time = time.time()
    logger.info(f"Starting analysis for claim: '{claim_text}'")

    # Step 1: Claim Parser
    parsed = parse_claim(claim_text)
    logger.info(f"Claim classified as: {parsed.claim_type.value}")

    # Subjective early-return
    if parsed.claim_type == ClaimType.SUBJECTIVE_OPINION:
        verdict, conf, expl, supp, cont, limits = verify_claim_evidence(parsed, [])
        sym, title = VERDICT_SYMBOLS[verdict]
        elapsed = round(time.time() - start_time, 2)
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
        )

    # Step 2: Web Search Retrieval
    logger.info(f"Searching web using queries: {parsed.extracted_queries}")
    candidates = retrieve_search_candidates(
        parsed.extracted_queries, max_results=config.max_search_results
    )
    logger.info(f"Retrieved {len(candidates)} search candidates.")

    # Step 3: Source Metadata & Tiering
    all_sources: List[SourceMetadata] = []
    seen_urls = set()
    for item in candidates:
        u = item.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            all_sources.append(build_source_metadata(u, item.get("title", "")))

    # Step 4: Passage Extraction & Boilerplate Cleaning
    extracted_chunks = extract_evidence_from_candidates(
        candidates, timeout=config.http_timeout
    )
    logger.info(f"Extracted {len(extracted_chunks)} candidate passages.")

    # Step 5: BGE-M3 Semantic Similarity Ranking
    ranked_evidence = rank_evidence_chunks(
        parsed.original_text, extracted_chunks, top_k=config.top_k_evidence
    )
    logger.info(f"Selected top {len(ranked_evidence)} most relevant evidence chunks.")

    # Step 5.5: Evidence Quality Gate
    usable_evidence, rejected_evidence = filter_evidence_for_verification(ranked_evidence)
    logger.info(
        f"Evidence Quality Gate: retained {len(usable_evidence)} usable evidence items, "
        f"filtered out {len(rejected_evidence)} items."
    )

    # Step 6 & 7: Claim <-> Evidence Comparative Verification (HF LLM)
    verdict, conf, expl, supp, cont, limits = verify_claim_evidence(
        parsed, usable_evidence
    )
    sym, title = VERDICT_SYMBOLS[verdict]

    # Retrieve relevant images for the claim
    relevant_images = []
    try:
        raw_images = retrieve_relevant_images(
            parsed.extracted_queries[0] if parsed.extracted_queries else parsed.original_text,
            max_images=4,
        )
        for img in raw_images:
            if isinstance(img, dict) and img.get("image_url"):
                relevant_images.append(RelevantImage(
                    title=str(img.get("title") or "Related Image"),
                    image_url=str(img.get("image_url")),
                    thumbnail_url=str(img.get("thumbnail_url") or img.get("image_url")),
                    source_url=str(img.get("source_url") or img.get("image_url")),
                ))
    except Exception as img_ex:
        logger.warning(f"Could not retrieve/instantiate images: {img_ex}")

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
        latency_seconds=elapsed,
    )
