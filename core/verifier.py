"""Claim vs. Evidence verification module using Hugging Face LLMs."""

import json
import logging
import math
import re
from typing import List, Dict, Any, Tuple, Optional
from .config import config
from .schemas import (
    AssessmentVerdict,
    EvidenceItem,
    EvidenceStance,
    ParsedClaim,
    ClaimType,
    SourceTier,
)

logger = logging.getLogger(__name__)

VERDICT_SYMBOLS = {
    AssessmentVerdict.SUPPORTED: ("🟢", "Supported"),
    AssessmentVerdict.CONTRADICTED: ("🔴", "Contradicted"),
    AssessmentVerdict.INSUFFICIENT_EVIDENCE: ("🟡", "Insufficient Evidence"),
    AssessmentVerdict.CONFLICTING_EVIDENCE: ("🟠", "Conflicting Evidence"),
    AssessmentVerdict.SUBJECTIVE_OPINION: ("🔵", "Subjective / Opinion"),
}

SYSTEM_PROMPT = """You are a rigorous evidence analysis system. Your purpose is to evaluate a specific claim against retrieved real-world evidence passages.

You must adhere strictly to these principles:
1. Grounding & Strict Entailment:
   - Rely ONLY on facts explicitly stated in the provided evidence. Do NOT extrapolate, infer, or assume missing facts from general world knowledge, search result titles, URLs, or domain names.
   - Distinguish TOPIC OVERLAP from LOGICAL ENTAILMENT: A passage that mentions the same subject, entities, or time period as the claim does NOT automatically support or contradict the claim.
   - To mark an evidence item as "supports", the passage MUST explicitly establish or corroborate the claim's specific core factual proposition.
   - To mark an evidence item as "contradicts", the passage MUST explicitly refute, deny, or state facts directly incompatible with the claim's specific core factual proposition.
   - If evidence is topically related but non-probative (does not confirm or refute the specific claim assertion), mark its stance as "neutral".

2. Source Hierarchy & Adequacy:
   - Prioritize Primary sources (official government agencies, regulatory bodies, peer-reviewed science) over Secondary news.
   - Low-confidence sources (blogs, forums, unverified user content) cannot serve as the sole basis for strong factual conclusions ("supported" or "contradicted").
   - Multiple weak or topically overlapping sources saying similar things do NOT constitute proof of support or contradiction.

3. Non-Binary Assessment: Choose strictly from:
   - "supported": Direct, reliable evidence (from primary or secondary sources) explicitly corroborates the claim.
   - "contradicted": Direct, reliable evidence (from primary or secondary sources) explicitly refutes or disproves the claim.
   - "insufficient_evidence": The retrieved passages do not contain adequate empirical data or explicit facts to confirm or refute the claim (even if topically relevant).
   - "conflicting_evidence": Credible sources directly contradict one another or present conflicting empirical facts.
   - "subjective_opinion": The statement is a value judgment, opinion, or qualitative framing.

4. Terminological & Definitional Nuance:
   - Watch out for terms with dual meanings (e.g., in political science/international law a "state" means an independent, sovereign nation-state, whereas in everyday language a "state" means a subnational administrative unit/province).
   - If a claim is technically true in one legal/academic sense but contrary to everyday usage, explicitly clarify this distinction in your explanation.

5. Explanation Grounding:
   - Your explanation must cite facts exclusively present in the provided evidence items. Do NOT generate stronger claims or draw conclusions beyond what the cited passages establish.

6. Evidence Limitations & Caveats Guidance:
   - Formulate limitations strictly based on actual, observable gaps visible in the supplied evidence relative to the claim.
   - Do NOT demand or criticize evidence for lacking quantitative data, statistics, mathematical measurements, or formal lab experiments UNLESS the claim specifically requests numerical metrics or statistical proofs. Descriptive factual statements from primary or secondary sources are fully valid evidence.
   - Use generic, claim-appropriate reasoning patterns such as:
     * "The retrieved passages are indirect or contextual rather than explicitly asserting the core proposition."
     * "The evidence directly addresses the claim but does not establish specific underlying mechanisms or sub-details."
     * "Available sources differ in emphasis, scope, or regional coverage."
     * "The source passage discusses the broader topic but does not explicitly state the specific assertion."
   - Do NOT invent artificial limitations that contradict a well-supported or contradicted assessment.

You must respond with ONLY a valid JSON object conforming to this format:
{
  "assessment": "supported" | "contradicted" | "insufficient_evidence" | "conflicting_evidence" | "subjective_opinion",
  "confidence_score": 0.0 to 1.0,
  "explanation": "Clear, objective breakdown explaining why the evidence supports or contradicts the claim, citing specific sources.",
  "evidence_evaluations": [
    {
      "id": "ev_1",
      "stance": "supports" | "contradicts" | "neutral",
      "reasoning": "Brief justification"
    }
  ],
  "evidence_limitations": [
    "Key limitation or gap in the available evidence"
  ]
}
"""


def format_evidence_prompt(claim: str, evidence: List[EvidenceItem]) -> str:
    """Formats the claim and ranked evidence into an LLM prompt."""
    prompt_lines = [
        f"Claim to Analyze:\n\"{claim}\"\n",
        "Retrieved Evidence Passages (Ranked by Relevance & Authority):",
        "INSTRUCTION: Evaluate logical entailment (supports / contradicts / neutral) STRICTLY and EXCLUSIVELY against the text inside Passage: \"...\". Source titles and domain metadata are for provenance identification only and must NOT be treated as factual passage evidence.",
    ]

    for ev in evidence:
        prompt_lines.append(
            f"\n[ID: {ev.id}] (Source: {ev.domain} | Tier: {ev.source_tier.value.upper()} | Score: {ev.similarity_score})\n"
            f"Title: {ev.title}\n"
            f"Passage: \"{ev.passage}\""
        )

    prompt_lines.append(
        "\nProvide your evidence-grounded comparative analysis in the specified JSON structure."
    )
    return "\n".join(prompt_lines)


def parse_llm_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Safely extracts and parses JSON from LLM output.

    Returns:
        Optional[Dict[str, Any]]: Parsed JSON dictionary or None if unparseable/invalid.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None

    cleaned_text = raw_text.strip()

    # Try finding JSON within markdown code blocks (```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, re.DOTALL | re.IGNORECASE)
    if match:
        target = match.group(1).strip()
    else:
        start = cleaned_text.find("{")
        end = cleaned_text.rfind("}")
        if start != -1 and end != -1 and start < end:
            target = cleaned_text[start : end + 1].strip()
        else:
            return None

    try:
        data = json.loads(target)
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def _validate_and_sanitize_hf_output(llm_dict: Any) -> Optional[Dict[str, Any]]:
    """Strictly validates structured fields in untrusted HF model output.

    Returns sanitized output dict or None if structural validation fails completely.
    """
    if not isinstance(llm_dict, dict):
        return None

    # 1. Verdict validation
    raw_verdict = llm_dict.get("assessment")
    if not isinstance(raw_verdict, str):
        return None

    raw_verdict_clean = raw_verdict.strip().lower()
    verdict_map = {
        "supported": AssessmentVerdict.SUPPORTED,
        "contradicted": AssessmentVerdict.CONTRADICTED,
        "insufficient_evidence": AssessmentVerdict.INSUFFICIENT_EVIDENCE,
        "insufficient": AssessmentVerdict.INSUFFICIENT_EVIDENCE,
        "conflicting_evidence": AssessmentVerdict.CONFLICTING_EVIDENCE,
        "conflicting": AssessmentVerdict.CONFLICTING_EVIDENCE,
        "subjective_opinion": AssessmentVerdict.SUBJECTIVE_OPINION,
        "subjective": AssessmentVerdict.SUBJECTIVE_OPINION,
    }
    if raw_verdict_clean not in verdict_map:
        return None

    verdict_enum = verdict_map[raw_verdict_clean]

    # 2. Confidence validation
    raw_conf = llm_dict.get("confidence_score")
    conf_val: float = 0.0
    conf_valid = False
    if isinstance(raw_conf, (int, float)) and not isinstance(raw_conf, bool):
        val_float = float(raw_conf)
        if math.isfinite(val_float) and 0.0 <= val_float <= 1.0:
            conf_val = val_float
            conf_valid = True

    if not conf_valid:
        conf_val = 0.0

    # 3. Explanation validation
    raw_explanation = llm_dict.get("explanation")
    if isinstance(raw_explanation, str) and raw_explanation.strip():
        explanation = raw_explanation.strip()
    elif isinstance(raw_explanation, list):
        explanation = " ".join(str(x) for x in raw_explanation if str(x).strip()) or "Evidence comparison concluded."
    else:
        explanation = "Evidence comparison concluded."

    # 4. Evidence evaluations collection validation
    raw_evals = llm_dict.get("evidence_evaluations")
    evaluations_list: List[Dict[str, Any]] = []
    if isinstance(raw_evals, list):
        for item in raw_evals:
            if isinstance(item, dict):
                st = item.get("stance")
                if st is not None and str(st).lower() not in ("supports", "contradicts", "neutral"):
                    continue
                evaluations_list.append(item)

    # 5. Evidence limitations validation
    raw_limits = llm_dict.get("evidence_limitations")
    limitations_list: List[str] = []
    if isinstance(raw_limits, list):
        for limit_item in raw_limits:
            if isinstance(limit_item, str) and limit_item.strip():
                limitations_list.append(limit_item.strip())
            elif limit_item is not None:
                limitations_list.append(str(limit_item))

    return {
        "assessment_enum": verdict_enum,
        "confidence_score": conf_val,
        "explanation": explanation,
        "evidence_evaluations": evaluations_list,
        "evidence_limitations": limitations_list,
    }


def analyze_with_huggingface(
    claim: str, evidence: List[EvidenceItem]
) -> Optional[Dict[str, Any]]:
    """Runs the Hugging Face InferenceClient chat completion for evidence verification."""
    from huggingface_hub import InferenceClient

    token_len = len(config.hf_token or "")
    logger.info(f"[HF Audit] Initializing InferenceClient (token_len={token_len}, model={config.hf_llm_model})")
    client = InferenceClient(token=config.hf_token)
    user_prompt = format_evidence_prompt(claim, evidence)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    logger.info(f"[HF Audit] Sending chat completion request to model '{config.hf_llm_model}' (prompt_len={len(user_prompt)})...")
    try:
        response = client.chat_completion(
            messages=messages,
            model=config.hf_llm_model,
            max_tokens=900,
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        logger.info(f"[HF Audit] Received response from model '{config.hf_llm_model}' (response_len={len(content)})")
        parsed_json = parse_llm_json(content)
        if parsed_json is None:
            logger.warning(f"[HF Audit] Failed to parse JSON from HF output (prefix: '{content[:120]}...')")
        else:
            logger.info(f"[HF Audit] Successfully parsed JSON from HF output: assessment={parsed_json.get('assessment')}")
        return parsed_json
    except Exception as exc:
        logger.warning(f"[HF Audit] API request failed for model '{config.hf_llm_model}': {type(exc).__name__}: {exc}")
        raise


def analyze_with_heuristics(
    parsed: ParsedClaim, evidence: List[EvidenceItem]
) -> Dict[str, Any]:
    """Conservative fallback verifier when primary LLM inference is unavailable.

    Refrains from asserting binary SUPPORTED or CONTRADICTED verdicts based on rigid keyword rules or keyword matching.
    Conservatively defaults to INSUFFICIENT_EVIDENCE to prevent false claim assessments.
    """
    if not evidence:
        return {
            "assessment": "insufficient_evidence",
            "confidence_score": 0.85,
            "explanation": "No relevant public documentation or verifiable reports were found to corroborate or refute this claim.",
            "evidence_evaluations": [],
            "evidence_limitations": ["Absence of indexed public statements or news reporting."],
        }

    evals = [
        {
            "id": ev.id,
            "stance": "neutral",
            "reasoning": "Fallback mode: Logical entailment cannot be conclusively established without primary LLM inference.",
        }
        for ev in evidence
    ]

    return {
        "assessment": "insufficient_evidence",
        "confidence_score": 0.70,
        "explanation": "Retrieved sources provide related background context, but directional support or contradiction cannot be established without primary LLM inference.",
        "evidence_evaluations": evals,
        "evidence_limitations": [
            "Verification relies on LLM inference for natural language semantic entailment.",
            "Fallback mode conservatively refrains from asserting binary verdicts without LLM inference.",
        ],
    }


def _validate_llm_provenance(
    supplied_evidence: List[EvidenceItem],
    llm_evaluations: List[Dict[str, Any]]
) -> Tuple[Dict[str, Tuple[EvidenceStance, str]], List[str]]:
    """Validates LLM-supplied evidence evaluations against actual supplied EvidenceItem objects.

    Rules:
    1. Lookups can only match supplied EvidenceItem instances by exact ID, numeric index, or exact URL.
    2. Raw LLM JSON is NEVER used to instantiate new EvidenceItem objects.
    3. Original EvidenceItem metadata (url, domain, tier, passage, score) remains 100% authoritative and immutable.
    4. Unmappable or invented evidence references are rejected and recorded as limitations.

    Returns:
        (valid_stance_map, validation_limitations)
        where valid_stance_map maps item.id -> (EvidenceStance, reasoning_str)
    """
    if not supplied_evidence:
        return {}, []

    # Build authoritative lookup maps from supplied evidence
    id_map: Dict[str, EvidenceItem] = {}
    url_map: Dict[str, EvidenceItem] = {}
    index_map: Dict[int, EvidenceItem] = {}

    for idx, item in enumerate(supplied_evidence):
        id_map[item.id] = item
        id_map[item.id.lower()] = item
        # Map numeric index (1-based and 0-based)
        index_map[idx + 1] = item
        index_map[idx] = item
        # Map "ev_N" string to index N
        if item.id.lower().startswith("ev_"):
            try:
                n = int(item.id[3:])
                index_map[n] = item
            except ValueError:
                pass
        if item.url:
            url_map[item.url.strip().lower()] = item

    valid_stance_map: Dict[str, Tuple[EvidenceStance, str]] = {}
    limitations: List[str] = []

    if not isinstance(llm_evaluations, list):
        return {}, ["LLM evidence evaluations response was malformed."]

    for raw_eval in llm_evaluations:
        if not isinstance(raw_eval, dict):
            continue

        raw_id = str(raw_eval.get("id", "")).strip()
        raw_url = str(raw_eval.get("url", "")).strip().lower()
        stance_val = str(raw_eval.get("stance", "neutral")).lower()
        reasoning = str(raw_eval.get("reasoning", "")).strip()

        matched_item: Optional[EvidenceItem] = None
        clean_id = raw_id.lower().replace("[", "").replace("]", "").replace("id:", "").strip()

        # 1. Match by ID or clean_id
        if raw_id in id_map:
            matched_item = id_map[raw_id]
        elif clean_id in id_map:
            matched_item = id_map[clean_id]
        elif raw_id.lower() in id_map:
            matched_item = id_map[raw_id.lower()]
        # 2. Match by numeric index (e.g. "1" or 1 or "ev_1" or "ev1" or "passage 1")
        elif raw_id.isdigit() and int(raw_id) in index_map:
            matched_item = index_map[int(raw_id)]
        elif raw_id.lower().startswith("ev_") and raw_id[3:].isdigit() and int(raw_id[3:]) in index_map:
            matched_item = index_map[int(raw_id[3:])]
        else:
            digits = re.findall(r"\d+", raw_id)
            if digits and int(digits[0]) in index_map:
                matched_item = index_map[int(digits[0])]

        # 3. Match by exact URL
        if matched_item is None and raw_url and raw_url in url_map:
            matched_item = url_map[raw_url]

        if matched_item is not None:
            # Map raw stance string to EvidenceStance enum
            if stance_val == "supports":
                stance = EvidenceStance.SUPPORTS
            elif stance_val == "contradicts":
                stance = EvidenceStance.CONTRADICTS
            elif stance_val == "neutral":
                stance = EvidenceStance.NEUTRAL
            else:
                continue

            if matched_item.id in valid_stance_map:
                prev_stance, _ = valid_stance_map[matched_item.id]
                if prev_stance != stance and stance != EvidenceStance.NEUTRAL:
                    valid_stance_map[matched_item.id] = (EvidenceStance.NEUTRAL, "Conflicting stance evaluations in model response.")
                    limitations.append(f"Conflicting stance evaluations for evidence '{matched_item.id}' resolved to neutral.")
                    continue

            valid_stance_map[matched_item.id] = (stance, reasoning)
        else:
            ref_label = raw_id or raw_url or "unknown"
            limitations.append(f"Rejected unmappable LLM evidence reference: '{ref_label}' (not present in supplied retrieval evidence).")
            logger.warning(f"Provenance validation rejected unmappable LLM evidence reference: '{ref_label}'")

    return valid_stance_map, limitations


def verify_claim_evidence(
    parsed: ParsedClaim, evidence: List[EvidenceItem]
) -> Tuple[AssessmentVerdict, float, str, List[EvidenceItem], List[EvidenceItem], List[str]]:
    """Evaluates claim against evidence using Hugging Face LLM (or heuristic fallback)."""
    # 1. Subjective claim handling
    if parsed.claim_type == ClaimType.SUBJECTIVE_OPINION:
        explanation = (
            "The statement is subjective or an interpretive characterization. "
            "Because qualitative value judgments and narrative framing are not empirical facts, "
            "it cannot be assigned a binary true/false verdict.\n\n"
            "Key Perspectives & Context:\n" +
            "\n".join(f"• {p}" for p in (parsed.perspectives or []))
        )
        return (
            AssessmentVerdict.SUBJECTIVE_OPINION,
            1.0,
            explanation,
            [],
            [],
            ["Subjective claims are not empirically verifiable through factual evidence."],
        )

    # 2. Check if no evidence retrieved
    if not evidence:
        return (
            AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            0.85,
            "No verifiable evidence was found across authoritative primary or secondary sources.",
            [],
            [],
            ["No matching records found in search retrieval."],
        )

    # 3. Use Hugging Face Inference API
    llm_raw_result = None
    try:
        logger.info(f"Calling Hugging Face LLM model: {config.hf_llm_model}...")
        llm_raw_result = analyze_with_huggingface(parsed.original_text, evidence)
    except Exception as e:
        logger.warning(f"Hugging Face Inference call failed: {e}. Falling back to heuristic analysis.")

    # 4. Strict structured schema validation of HF response
    sanitized = _validate_and_sanitize_hf_output(llm_raw_result)

    if sanitized is None:
        logger.info("HF model response missing or failed structural schema validation. Falling back to conservative verifier.")
        fallback_dict = analyze_with_heuristics(parsed, evidence)
        sanitized = _validate_and_sanitize_hf_output(fallback_dict)

    assert sanitized is not None

    verdict: AssessmentVerdict = sanitized["assessment_enum"]
    confidence: float = sanitized["confidence_score"]
    explanation: str = sanitized["explanation"]
    limitations: List[str] = list(sanitized["evidence_limitations"])
    eval_list: List[Dict[str, Any]] = sanitized["evidence_evaluations"]

    # 5. Map stances back to evidence items with strict runtime provenance validation
    valid_stance_map, provenance_limitations = _validate_llm_provenance(evidence, eval_list)
    limitations.extend(provenance_limitations)

    supporting: List[EvidenceItem] = []
    contradicting: List[EvidenceItem] = []
    seen_supp_ids = set()
    seen_cont_ids = set()

    for item in evidence:
        stance_tuple = valid_stance_map.get(item.id)
        if stance_tuple:
            stance_val, reason_str = stance_tuple
            item.stance = stance_val
            item.stance_explanation = reason_str
            if stance_val == EvidenceStance.SUPPORTS:
                if item.id not in seen_supp_ids:
                    seen_supp_ids.add(item.id)
                    supporting.append(item)
            elif stance_val == EvidenceStance.CONTRADICTS:
                if item.id not in seen_cont_ids:
                    seen_cont_ids.add(item.id)
                    contradicting.append(item)
        else:
            item.stance = EvidenceStance.NEUTRAL
            item.stance_explanation = None

    # 6. Verdict consistency checks & source adequacy gating
    has_primary_or_secondary_supp = any(
        item.source_tier in (SourceTier.PRIMARY, SourceTier.SECONDARY) for item in supporting
    )
    has_primary_or_secondary_cont = any(
        item.source_tier in (SourceTier.PRIMARY, SourceTier.SECONDARY) for item in contradicting
    )

    if verdict == AssessmentVerdict.SUPPORTED:
        if not supporting or not has_primary_or_secondary_supp:
            verdict = AssessmentVerdict.INSUFFICIENT_EVIDENCE
            confidence = min(confidence, 0.70) if supporting else 0.0
            if not supporting:
                explanation += " (Note: All referenced supporting citations were unmappable to supplied sources.)"
            else:
                explanation = "Retrieved evidence is restricted to low-confidence or non-decisive sources and lacks authoritative primary or secondary corroboration for the claim."
                limitations.append("Supporting evidence is restricted to low-confidence sources; insufficient for a definitive supported verdict.")
            supporting = []
            contradicting = []

    elif verdict == AssessmentVerdict.CONTRADICTED:
        if not contradicting or not has_primary_or_secondary_cont:
            verdict = AssessmentVerdict.INSUFFICIENT_EVIDENCE
            confidence = min(confidence, 0.70) if contradicting else 0.0
            if not contradicting:
                explanation += " (Note: All referenced contradictory citations were unmappable to supplied sources.)"
            else:
                explanation = "Retrieved evidence is restricted to low-confidence or non-decisive sources and lacks authoritative primary or secondary refutation of the claim."
                limitations.append("Contradicting evidence is restricted to low-confidence sources; insufficient for a definitive contradicted verdict.")
            supporting = []
            contradicting = []

    elif verdict == AssessmentVerdict.CONFLICTING_EVIDENCE:
        if not supporting or not contradicting:
            verdict = AssessmentVerdict.INSUFFICIENT_EVIDENCE
            confidence = min(confidence, 0.70)
            supporting = []
            contradicting = []

    elif verdict in (AssessmentVerdict.INSUFFICIENT_EVIDENCE, AssessmentVerdict.SUBJECTIVE_OPINION):
        supporting = []
        contradicting = []

    return verdict, confidence, explanation, supporting, contradicting, limitations
