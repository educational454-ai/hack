import logging
import json
from core.pipeline import analyze_claim
from core.url_pipeline import detect_input_mode

logging.basicConfig(level=logging.INFO)

raw_input = "https://en.wikipedia.org/wiki/Zendaya\nIs Zendaya unmarried"

# 1, 2, 3: detect_input_mode output
mode, url, user_question = detect_input_mode(raw_input)
print("=== DIAGNOSTIC INSPECTION ===")
print("1. detect_input_mode() output:", mode)
print("2. extracted URL:", url)
print("3. extracted user_question:", user_question)

# Run pipeline
result = analyze_claim(raw_input)

print("\n4. relevant_page_context actually selected:")
if result.relevant_page_context:
    for i, p in enumerate(result.relevant_page_context, 1):
        print(f"   [{i}] {p[:150]}...")
else:
    print("   None selected / Empty")

print("\n5. exact proposition/claim passed to independent verification:")
print("  ", result.claim)

print("\n6. exact retrieval/search query used:")
# We can check from logs or parsed claim queries
from core.claim_parser import parse_claim
parsed_q = parse_claim(user_question)
print("  ", parsed_q.extracted_queries)

print("\n7. retrieved evidence URLs/domains:")
all_ev = result.supporting_evidence + result.contradicting_evidence
if all_ev:
    for e in all_ev:
        print(f"   - {e.domain} | {e.url} | Title: {e.title}")
else:
    print("   No evidence items returned")

print("\n8. whether the provided Wikipedia URL entered supporting_evidence or contradicting_evidence:")
wiki_in_supp = any("en.wikipedia.org" in e.domain or "en.wikipedia.org" in e.url for e in result.supporting_evidence)
wiki_in_cont = any("en.wikipedia.org" in e.domain or "en.wikipedia.org" in e.url for e in result.contradicting_evidence)
print(f"   In supporting_evidence: {wiki_in_supp}")
print(f"   In contradicting_evidence: {wiki_in_cont}")

print("\n9. final verifier input claim:")
print("  ", result.claim)

print("\n10. final verdict and confidence:")
print(f"    Verdict: {result.verdict_title} ({result.verdict})")
print(f"    Confidence: {result.confidence_score}")

print("\n11. why the result became Insufficient Evidence:")
print("    Explanation:", result.explanation)
print("    Limitations:", result.evidence_limitations)
