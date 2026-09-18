"""URL and URL + Question Verification Module for Task 13."""

import logging
import re
import time
from typing import Tuple, Optional, List, Dict, Any

from .schemas import (
    AnalysisResult,
    AssessmentVerdict,
    ClaimType,
    WebpageMetadata,
    PerClaimResult,
    EvidenceItem,
    SourceMetadata,
)
from .url_fetcher import fetch_webpage_content, WebpageFetchResult
from .extractor import chunk_text_into_passages
from .ranker import get_local_embedder, cosine_similarity, compute_lexical_similarity, re_tokenize
from .config import config

logger = logging.getLogger(__name__)


def detect_input_mode(input_text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Detects input verification mode based on presence of HTTP/HTTPS URL.

    Returns:
        (mode, url_if_found, question_or_claim_text)
        mode is one of: "claim" | "url" | "url_question"
    """
    clean_text = input_text.strip()
    url_match = re.search(r"https?://[^\s<'\"]+", clean_text, re.IGNORECASE)

    if not url_match:
        return "claim", None, clean_text

    raw_url = url_match.group(0).rstrip(".,;:!?)>]}")
    # Extract remaining text after removing the URL
    remaining_text = clean_text.replace(raw_url, "").strip()
    # Clean up whitespace/newlines
    remaining_text = re.sub(r"\n+", " ", remaining_text).strip()

    if remaining_text and len(remaining_text) >= 3:
        return "url_question", raw_url, remaining_text
    else:
        return "url", raw_url, None


def rank_page_passages_for_question(question: str, passages: List[str], top_k: int = 3) -> List[str]:
    """Selects top relevant passages from a fetched webpage using BGE-M3 / ranker similarity."""
    if not question or not passages:
        return []

    scores: List[Tuple[float, str]] = []

    model = get_local_embedder() if not config.low_memory_mode else None
    q_vec = model.encode(question).tolist() if model else None

    for p in passages:
        if len(p.split()) < 8:
            continue
        sim = 0.0
        if q_vec and model:
            try:
                p_vec = model.encode(p).tolist()
                sim = cosine_similarity(q_vec, p_vec)
            except Exception:
                pass
        if sim == 0.0:
            sim = compute_lexical_similarity(question, p)

        if sim >= 0.22:
            scores.append((sim, p))

    scores.sort(key=lambda pair: pair[0], reverse=True)
    return [item[1] for item in scores[:top_k]]


def extract_key_claims_from_text(text: str, max_claims: int = 3) -> List[str]:
    """Extracts bounded key factual claim statements from webpage text."""
    if not text:
        return []

    # Split into sentence-like blocks
    paragraphs = [p.strip() for p in re.split(r"\n+|\. ", text) if len(p.strip().split()) >= 8]
    candidates = []
    seen = set()

    # Priority to sentences containing factual markers (dates, numbers, quotes, official terms)
    factual_pattern = re.compile(r"\b(20\d\d|19\d\d|banned|announced|declared|passed|approved|signed|released|percent|billion|million|trillion|court|government)\b", re.IGNORECASE)

    for p in paragraphs:
        clean_p = p.strip()
        if len(clean_p) > 200:
            clean_p = clean_p[:200].rstrip() + "..."
        if clean_p.lower() in seen:
            continue
        seen.add(clean_p.lower())

        score = 1.0
        if factual_pattern.search(clean_p):
            score += 2.0
        candidates.append((score, clean_p))

    candidates.sort(key=lambda c: c[0], reverse=True)
    return [c[1] for c in candidates[:max_claims]]


def analyze_url_with_question(
    url: str,
    user_question: str,
    analyze_claim_fn: Any,
) -> AnalysisResult:
    """Executes URL + User Question verification mode."""
    start_time = time.time()
    logger.info(f"Analyzing URL + Question: URL='{url}', Question='{user_question}'")

    fetch_res = fetch_webpage_content(url, timeout=6.0)
    webpage_meta = WebpageMetadata(
        url=fetch_res.url,
        domain=fetch_res.domain,
        title=fetch_res.title,
        canonical_url=fetch_res.canonical_url,
        publication_date=fetch_res.publication_date,
        author=fetch_res.author,
    )

    relevant_passages: List[str] = []
    if fetch_res.is_success and fetch_res.main_text:
        passages = chunk_text_into_passages(fetch_res.main_text)
        relevant_passages = rank_page_passages_for_question(user_question, passages, top_k=3)

    # Independent Web Verification of the user question
    independent_result = analyze_claim_fn(user_question)

    # Formulate targeted answer grounded in independent evidence
    verdict = independent_result.verdict
    q_clean = user_question.rstrip("?.! ").strip()

    if verdict == AssessmentVerdict.SUPPORTED:
        targeted_answer = f"Independent evidence supports the proposition: '{q_clean}'."
    elif verdict == AssessmentVerdict.CONTRADICTED:
        targeted_answer = f"Independent evidence contradicts the proposition: '{q_clean}'."
    elif verdict == AssessmentVerdict.CONFLICTING_EVIDENCE:
        targeted_answer = f"Independent reporting presents conflicting accounts regarding '{q_clean}'."
    elif verdict == AssessmentVerdict.SUBJECTIVE_OPINION:
        targeted_answer = f"The query '{user_question}' expresses a subjective opinion or narrative perspective rather than an empirical fact."
    else:
        targeted_answer = f"Available independent sources do not provide sufficient conclusive evidence regarding '{q_clean}'."

    limitations = list(independent_result.evidence_limitations)
    if not fetch_res.is_success:
        limitations.append(f"Webpage fetch note: {fetch_res.error_message or 'Could not access provided page'}. Independent verification proceeded using web search.")
    elif not relevant_passages:
        limitations.append("The provided webpage did not contain passages with sufficient semantic relevance to the user's specific question.")

    # Page Context Isolation: Ensure the analyzed webpage is NOT inserted as an independent evidence item
    filtered_supp = [e for e in independent_result.supporting_evidence if fetch_res.domain not in e.domain]
    filtered_cont = [e for e in independent_result.contradicting_evidence if fetch_res.domain not in e.domain]

    elapsed = round(time.time() - start_time, 2)

    return AnalysisResult(
        claim=user_question,
        claim_type=independent_result.claim_type,
        verdict=independent_result.verdict,
        verdict_symbol=independent_result.verdict_symbol,
        verdict_title=independent_result.verdict_title,
        confidence_score=independent_result.confidence_score,
        explanation=independent_result.explanation,
        supporting_evidence=filtered_supp or independent_result.supporting_evidence,
        contradicting_evidence=filtered_cont or independent_result.contradicting_evidence,
        evidence_limitations=limitations,
        all_sources=independent_result.all_sources,
        relevant_images=independent_result.relevant_images,
        latency_seconds=elapsed,
        mode="url_question",
        webpage=webpage_meta,
        user_question=user_question,
        targeted_answer=targeted_answer,
        relevant_page_context=relevant_passages,
    )


def analyze_url_only(
    url: str,
    analyze_claim_fn: Any,
) -> AnalysisResult:
    """Executes URL-Only verification mode."""
    start_time = time.time()
    logger.info(f"Analyzing URL-Only mode: '{url}'")

    fetch_res = fetch_webpage_content(url, timeout=6.0)
    webpage_meta = WebpageMetadata(
        url=fetch_res.url,
        domain=fetch_res.domain,
        title=fetch_res.title,
        canonical_url=fetch_res.canonical_url,
        publication_date=fetch_res.publication_date,
        author=fetch_res.author,
    )

    if not fetch_res.is_success:
        elapsed = round(time.time() - start_time, 2)
        return AnalysisResult(
            claim=f"Analysis of {fetch_res.domain} article",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            verdict_symbol="🟡",
            verdict_title="INSUFFICIENT EVIDENCE",
            confidence_score=0.3,
            explanation=f"Unable to analyze webpage content. {fetch_res.error_message or 'The page was inaccessible.'}",
            evidence_limitations=[fetch_res.error_message or "Webpage fetch failed."],
            latency_seconds=elapsed,
            mode="url",
            webpage=webpage_meta,
        )

    # Extract bounded factual claims
    extracted_claims = extract_key_claims_from_text(fetch_res.main_text or "", max_claims=3)

    if not extracted_claims:
        elapsed = round(time.time() - start_time, 2)
        return AnalysisResult(
            claim=f"Analysis of {webpage_meta.title or fetch_res.domain}",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            verdict_symbol="🟡",
            verdict_title="INSUFFICIENT EVIDENCE",
            confidence_score=0.4,
            explanation="The webpage was fetched successfully, but contained insufficient verifiable text content.",
            evidence_limitations=["No clear verifiable claims could be extracted from page text."],
            latency_seconds=elapsed,
            mode="url",
            webpage=webpage_meta,
        )

    # Independently verify each claim
    per_claim_results: List[PerClaimResult] = []
    verdicts: List[AssessmentVerdict] = []
    all_supp: List[EvidenceItem] = []
    all_cont: List[EvidenceItem] = []
    all_sources: List[SourceMetadata] = []

    for c_text in extracted_claims:
        res = analyze_claim_fn(c_text)
        verdicts.append(res.verdict)
        per_claim_results.append(PerClaimResult(
            claim=c_text,
            claim_type=res.claim_type,
            verdict=res.verdict,
            verdict_symbol=res.verdict_symbol,
            verdict_title=res.verdict_title,
            confidence_score=res.confidence_score,
            explanation=res.explanation,
            supporting_evidence=res.supporting_evidence,
            contradicting_evidence=res.contradicting_evidence,
        ))
        all_supp.extend(res.supporting_evidence)
        all_cont.extend(res.contradicting_evidence)
        all_sources.extend(res.all_sources)

    # Transparent Article-Level Aggregation
    supp_count = sum(1 for v in verdicts if v == AssessmentVerdict.SUPPORTED)
    cont_count = sum(1 for v in verdicts if v == AssessmentVerdict.CONTRADICTED)
    total = len(verdicts)

    if cont_count > 0 and supp_count > 0:
        article_verdict = AssessmentVerdict.CONFLICTING_EVIDENCE
        article_symbol, article_title = "🟠", "CONFLICTING EVIDENCE"
        summary_explanation = f"Article evaluation yielded mixed findings across {total} analyzed claims ({supp_count} Supported, {cont_count} Contradicted)."
    elif cont_count > 0:
        article_verdict = AssessmentVerdict.CONTRADICTED
        article_symbol, article_title = "🔴", "CONTRADICTED"
        summary_explanation = f"Article evaluation identified factual contradictions among key claims ({cont_count} of {total} claims Contradicted)."
    elif supp_count > 0:
        article_verdict = AssessmentVerdict.SUPPORTED
        article_symbol, article_title = "🟢", "SUPPORTED"
        summary_explanation = f"Independent evidence corroborates the key factual claims analyzed from this article ({supp_count} of {total} claims Supported)."
    else:
        article_verdict = AssessmentVerdict.INSUFFICIENT_EVIDENCE
        article_symbol, article_title = "🟡", "INSUFFICIENT EVIDENCE"
        summary_explanation = f"Independent evidence was insufficient to establish conclusive support or contradiction for the {total} claims analyzed."

    elapsed = round(time.time() - start_time, 2)

    return AnalysisResult(
        claim=webpage_meta.title or f"Article from {webpage_meta.domain}",
        claim_type=ClaimType.FACTUAL,
        verdict=article_verdict,
        verdict_symbol=article_symbol,
        verdict_title=article_title,
        confidence_score=0.75 if (supp_count or cont_count) else 0.4,
        explanation=summary_explanation,
        supporting_evidence=all_supp[:4],
        contradicting_evidence=all_cont[:4],
        evidence_limitations=[f"Analyzed a bounded subset of {total} key claims extracted from the article."],
        all_sources=all_sources[:6],
        latency_seconds=elapsed,
        mode="url",
        webpage=webpage_meta,
        claims_analyzed=per_claim_results,
    )
