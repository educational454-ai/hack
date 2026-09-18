"""Claim parsing, classification, and query formulation module."""

import re
from typing import List, Tuple
from .schemas import ClaimType, ParsedClaim

# Evaluative / Subjective markers
SUBJECTIVE_PATTERNS = [
    r"\b(best|worst|greatest|terrible|awesome|horrible|amazing|ugly|beautiful|finest|masterpiece|trash|overrated|underrated|goat)\b",
    r"\b(protagonist|antagonist|hero|villain|savior|evil|saint)\b",
    r"\b(better than|worse than|superior to|inferior to)\b",
    r"\b(should|ought to|deserves to|has the right to)\b",
    r"\b(in my opinion|i think|i believe|i feel|personally)\b",
    r"\b(favorite|unjust|immoral|moral|righteous)\b",
    r"^\s*(is|are|was|were|do|does)\s+.*\b(the\s+)?(best|worst|greatest|finest|most\s+\w+)\b",
    r"\b(the\s+)?(best|worst|greatest|finest)\s+\w+\s+(ever|of all time|in history)\b",
]

# Medical factual keywords
MEDICAL_PATTERNS = [
    r"\b(cure|cures|curing|cured)\b",
    r"\b(vaccine|vaccines|vaccination)\b",
    r"\b(cancer|tumor|chemotherapy)\b",
    r"\b(medicine|drug|pharmaceutical|antibiotic)\b",
    r"\b(treatment|prevent disease|infection|virus|covid|pathogen)\b",
]

# Factual markers: dates, numbers, policies, institutions, bans, announcements
FACTUAL_PATTERNS = [
    r"\b(banned|launched|announced|declared|passed|approved|signed|released)\b",
    r"\b(gdp|inflation|rate|budget|growth|billion|million|trillion|percent|%)\b",
    r"\b(20\d\d|19\d\d)\b", # years like 2024, 2025
    r"\b(law|act|bill|regulation|scheme|policy|court|supreme court)\b",
    r"\b(minister|president|government|rbi|isro|nasa|un|who)\b",
]


def classify_claim_heuristics(text: str) -> Tuple[ClaimType, str, List[str]]:
    """Classifies a claim using linguistic pattern analysis.
    
    Returns:
        (ClaimType, explanation, perspectives_if_subjective)
    """
    clean_text = text.strip()
    lower_text = clean_text.lower()

    # Check for medical claims first
    for pat in MEDICAL_PATTERNS:
        if re.search(pat, lower_text):
            return (
                ClaimType.MEDICAL_FACTUAL,
                "The statement makes an empirical claim regarding health, medicine, or disease treatment that requires scientific and clinical evidence.",
                [],
            )

    # Check for subjective/opinion markers
    matched_subjective = []
    for pat in SUBJECTIVE_PATTERNS:
        m = re.search(pat, lower_text)
        if m:
            matched_subjective.append(m.group(0))

    if matched_subjective:
        # Generate perspective explanation
        cleaned_markers = ", ".join(dict.fromkeys(matched_subjective[:3]))
        perspectives = [
            f"The statement employs subjective or interpretive framing ('{cleaned_markers}').",
            "This expresses a qualitative characterization, value judgment, or narrative trope rather than an objectively verifiable empirical fact.",
            "Different observers and analysts hold contrasting viewpoints based on their values, political stances, or interpretive frameworks.",
        ]
        return (
            ClaimType.SUBJECTIVE_OPINION,
            "The statement is subjective, interpretive, or an expression of opinion. It cannot be categorized with a binary TRUE/FALSE label.",
            perspectives,
        )

    # Check for factual indicators
    for pat in FACTUAL_PATTERNS:
        if re.search(pat, lower_text):
            return (
                ClaimType.FACTUAL,
                "The statement asserts verifiable actions, quantitative metrics, or policy decisions that can be corroborated against documentation.",
                [],
            )

    # Default fallback: Treat as factual claim to test against evidence
    return (
        ClaimType.FACTUAL,
        "The statement presents an empirical proposition that can be evaluated against available public evidence.",
        [],
    )


def generate_search_queries(claim: str) -> List[str]:
    """Generates targeted search queries for candidate evidence retrieval."""
    clean = re.sub(r'["\']', '', claim).strip()
    queries = [clean]

    # Add targeted verification query
    queries.append(f"{clean} official announcement fact check")

    # Add specific news / source query
    words = clean.split()
    if len(words) > 3:
        core_query = " ".join(words[:6])
        queries.append(f"{core_query} news report")

    return list(dict.fromkeys(queries))[:3]


def parse_claim(text: str) -> ParsedClaim:
    """Entrypoint to parse and classify a user input claim."""
    claim_type, explanation, perspectives = classify_claim_heuristics(text)
    is_verifiable = claim_type != ClaimType.SUBJECTIVE_OPINION

    queries = generate_search_queries(text) if is_verifiable else []

    return ParsedClaim(
        original_text=text.strip(),
        claim_type=claim_type,
        type_explanation=explanation,
        is_verifiable=is_verifiable,
        perspectives=perspectives if not is_verifiable else None,
        extracted_queries=queries,
    )
