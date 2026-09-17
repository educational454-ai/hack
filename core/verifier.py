"""Claim vs. Evidence verification module using Hugging Face LLMs."""

import json
import logging
import re
from typing import List, Dict, Any, Tuple
from .config import config
from .schemas import (
    AssessmentVerdict,
    EvidenceItem,
    EvidenceStance,
    ParsedClaim,
    ClaimType,
)

logger = logging.getLogger(__name__)

VERDICT_SYMBOLS = {
    AssessmentVerdict.SUPPORTED: ("🟢", "Supported"),
    AssessmentVerdict.CONTRADICTED: ("🔴", "Contradicted"),
    AssessmentVerdict.INSUFFICIENT_EVIDENCE: ("🟡", "Insufficient Evidence"),
    AssessmentVerdict.CONFLICTING_EVIDENCE: ("🟠", "Conflicting Evidence"),
    AssessmentVerdict.SUBJECTIVE_OPINION: ("🔵", "Subjective / Opinion"),
}

SYSTEM_PROMPT = """You are an rigorous evidence analysis system. Your purpose is to evaluate a specific claim against retrieved real-world evidence passages.

You must adhere strictly to these principles:
1. Grounding: Rely ONLY on the provided evidence. Do NOT extrapolate or assume information not present in the passages.
2. Source Hierarchy: Prioritize Primary sources (official government agencies, regulatory bodies, peer-reviewed science) over Secondary news, and treat Low-confidence sources skeptically.
3. Non-Binary Assessment: Never force a simplistic TRUE/FALSE label. Choose from:
   - "supported": Strong, reliable evidence corroborates the claim.
   - "contradicted": Reliable evidence directly disproves or conflicts with the claim.
   - "insufficient_evidence": The retrieved passages do not contain adequate empirical data to confirm or refute.
   - "conflicting_evidence": Credible sources directly contradict one another or evidence is mixed.
   - "subjective_opinion": The statement is a value judgment, opinion, or qualitative framing.
4. Terminological & Definitional Nuance:
   - Watch out for terms with dual meanings (e.g., in political science/international law a "state" means an independent, sovereign nation-state, whereas in everyday language a "state" means a subnational administrative unit/province like California, Texas, or Maharashtra).
   - If a claim is technically true in one legal/academic sense but contrary to everyday usage (e.g., "India is a country composed of states, but legally a sovereign state"), explicitly clarify this distinction in your explanation so the user understands the exact context.

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


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Safely extracts and parses JSON from LLM output."""
    # Try finding JSON within markdown code blocks or brackets
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(1)
    else:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1:
            raw_text = raw_text[start : end + 1]

    return json.loads(raw_text)


def analyze_with_huggingface(
    claim: str, evidence: List[EvidenceItem]
) -> Dict[str, Any]:
    """Runs the Hugging Face InferenceClient chat completion for evidence verification."""
    from huggingface_hub import InferenceClient

    client = InferenceClient(token=config.hf_token)
    user_prompt = format_evidence_prompt(claim, evidence)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat_completion(
        messages=messages,
        model=config.hf_llm_model,
        max_tokens=900,
        temperature=0.1,
    )

    content = response.choices[0].message.content
    return parse_llm_json(content)


def analyze_with_heuristics(
    parsed: ParsedClaim, evidence: List[EvidenceItem]
) -> Dict[str, Any]:
    """Deterministic evidence-grounded comparative analysis fallback."""
    if not evidence:
        return {
            "assessment": "insufficient_evidence",
            "confidence_score": 0.85,
            "explanation": "No relevant public documentation or verifiable reports were found to corroborate or refute this claim.",
            "evidence_evaluations": [],
            "evidence_limitations": ["Absence of indexed public statements or news reporting."],
        }

    claim_lower = parsed.original_text.lower()
    negation_words = {"ban", "banned", "shut down", "halted", "illegal", "prohibited", "fake", "cures"}
    contradiction_signals = {"denies", "clarified", "refutes", "hoax", "false", "no ban", "fake news", "fact check", "misleading", "continues normal", "operational", "reaffirms"}
    support_signals = {"confirmed", "officially launched", "enacted", "approved", "growth rate", "recorded"}

    evals = []
    support_count = 0
    contradict_count = 0

    for ev in evidence:
        passage_lower = ev.passage.lower()
        title_lower = ev.title.lower()
        combined = f"{title_lower} {passage_lower}"

        stance = EvidenceStance.NEUTRAL
        reason = "Passage mentions background context but does not explicitly confirm or refute."

        if any(w in combined for w in contradiction_signals):
            stance = EvidenceStance.CONTRADICTS
            reason = "Passage refutes, clarifies, or contradicts the asserted proposition."
            contradict_count += 1
        elif any(w in combined for w in support_signals):
            stance = EvidenceStance.SUPPORTS
            reason = "Passage provides positive corroboration of the asserted event or figure."
            support_count += 1

        evals.append({
            "id": ev.id,
            "stance": stance.value,
            "reasoning": reason,
        })

    if contradict_count > support_count:
        verdict = "contradicted"
        explanation = f"Available official records and reporting explicitly contradict or refute the claim. Multiple sources clarify that no such measure or event occurred."
        confidence = 0.90 if any(e.source_tier.value == "primary" for e in evidence) else 0.80
    elif support_count > contradict_count:
        verdict = "supported"
        explanation = f"Available documentation and verified reporting support the proposition with direct corroborating evidence."
        confidence = 0.88
    elif support_count > 0 and contradict_count > 0:
        verdict = "conflicting_evidence"
        explanation = "Retrieved sources present conflicting statements; authoritative consensus has not been established."
        confidence = 0.75
    else:
        verdict = "insufficient_evidence"
        explanation = "Retrieved records provide contextual background, but do not provide definitive proof to confirm or refute the specific claim."
        confidence = 0.70

    return {
        "assessment": verdict,
        "confidence_score": confidence,
        "explanation": explanation,
        "evidence_evaluations": evals,
        "evidence_limitations": [
            "Analysis relies on publicly indexed web pages and published releases.",
            "Real-time developing news may have delayed indexing."
        ],
    }


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

    # 3. Use Hugging Face Inference API if configured
    llm_result = None
    if config.has_hf_token:
        try:
            logger.info(f"Calling Hugging Face LLM model: {config.hf_llm_model}...")
            llm_result = analyze_with_huggingface(parsed.original_text, evidence)
        except Exception as e:
            logger.warning(f"Hugging Face Inference call failed: {e}. Falling back to heuristic analysis.")

    # 4. Fallback to heuristic verifier if LLM was unavailable
    if not llm_result:
        llm_result = analyze_with_heuristics(parsed, evidence)

    # Map LLM verdict to Enum
    raw_verdict = llm_result.get("assessment", "insufficient_evidence").lower()
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
    verdict = verdict_map.get(raw_verdict, AssessmentVerdict.INSUFFICIENT_EVIDENCE)

    confidence = float(llm_result.get("confidence_score", 0.8))
    explanation = llm_result.get("explanation", "Evidence comparison concluded.")
    limitations = llm_result.get("evidence_limitations", [])

    # Map stances back to evidence items
    eval_dict = {
        ev.get("id"): (ev.get("stance"), ev.get("reasoning"))
        for ev in llm_result.get("evidence_evaluations", [])
    }

    supporting: List[EvidenceItem] = []
    contradicting: List[EvidenceItem] = []

    for item in evidence:
        stance_str, reason_str = eval_dict.get(item.id, (None, None))
        if stance_str == "supports":
            item.stance = EvidenceStance.SUPPORTS
            item.stance_explanation = reason_str
            supporting.append(item)
        elif stance_str == "contradicts":
            item.stance = EvidenceStance.CONTRADICTS
            item.stance_explanation = reason_str
            contradicting.append(item)
        else:
            item.stance = EvidenceStance.NEUTRAL
            item.stance_explanation = reason_str

    return verdict, confidence, explanation, supporting, contradicting, limitations
