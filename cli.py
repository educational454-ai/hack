"""Command-line interface for the Evidence-First Misinformation Analyzer."""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.config import config
from core.pipeline import analyze_claim
from core.schemas import AnalysisResult, AssessmentVerdict

def print_result_terminal(res: AnalysisResult):
    """Prints a beautiful formatted card for the analysis result."""
    border = "=" * 70
    sub_border = "-" * 70

    print(f"\n{border}")
    print(f"               AI EVIDENCE-FIRST MISINFORMATION ANALYZER")
    print(f"{border}")
    print(f" CLAIM:          \"{res.claim}\"")
    print(f" CLASSIFICATION: {res.claim_type.value.upper()}")
    print(f" ASSESSMENT:     {res.verdict_symbol} {res.verdict_title.upper()}")
    print(f" CONFIDENCE:     {int(res.confidence_score * 100)}%")
    if res.latency_seconds:
        print(f" PROCESSING TIME:{res.latency_seconds}s")
    print(sub_border)

    print("\n[EXPLANATION]")
    print(f"{res.explanation}\n")

    if res.supporting_evidence:
        print(sub_border)
        print("🟢 SUPPORTING EVIDENCE:")
        for idx, ev in enumerate(res.supporting_evidence, 1):
            print(f"  [{idx}] Source: {ev.domain} ({ev.source_tier.value.upper()}) | Relevance: {ev.similarity_score}")
            print(f"      Quote: \"{ev.passage[:220]}...\"")
            if ev.stance_explanation:
                print(f"      Reason: {ev.stance_explanation}")
            print()

    if res.contradicting_evidence:
        print(sub_border)
        print("🔴 CONTRADICTING EVIDENCE:")
        for idx, ev in enumerate(res.contradicting_evidence, 1):
            print(f"  [{idx}] Source: {ev.domain} ({ev.source_tier.value.upper()}) | Relevance: {ev.similarity_score}")
            print(f"      Quote: \"{ev.passage[:220]}...\"")
            if ev.stance_explanation:
                print(f"      Reason: {ev.stance_explanation}")
            print()

    if res.evidence_limitations:
        print(sub_border)
        print("⚠️ EVIDENCE LIMITATIONS:")
        for lim in res.evidence_limitations:
            print(f"  • {lim}")

    if res.all_sources:
        print(sub_border)
        print("🌐 AUTHORITATIVE SOURCES CONSULTED:")
        for idx, src in enumerate(res.all_sources[:6], 1):
            print(f"  {idx}. [{src.tier.value.upper()}] {src.domain} - {src.title[:60]}")
            print(f"     URL: {src.url}")

    print(f"\n{border}\n")


def main():
    if not config.has_hf_token:
        print("Note: HF_TOKEN is not configured in .env. Running in offline/heuristic verification mode.")
        print("Tip: Add HF_TOKEN=your_token in .env to use serverless Hugging Face LLM & BGE-M3 models.\n")

    if len(sys.argv) > 1:
        claim = " ".join(sys.argv[1:])
    else:
        print("Enter a claim to analyze (or type 'exit' to quit):")
        try:
            claim = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return

    if not claim or claim.lower() == "exit":
        return

    print(f"\nAnalyzing: \"{claim}\" ... please wait ...")
    result = analyze_claim(claim)
    print_result_terminal(result)


if __name__ == "__main__":
    main()
