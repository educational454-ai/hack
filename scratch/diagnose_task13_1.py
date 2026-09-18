from core.url_pipeline import analyze_url_with_question
from core.pipeline import analyze_claim

url = "https://en.wikipedia.org/wiki/Zendaya"
question = "Is Zendaya unmarried"

print(f"=== TASK 13.1 DIAGNOSTIC RUN ===")
print(f"URL: {url}")
print(f"Question: {question}\n")

res = analyze_url_with_question(url, question, analyze_claim)
print("=== RESULT SUMMARY ===")
print(f"Verdict: {res.verdict.value}")
print(f"Confidence: {res.confidence_score}")
print(f"User Question: {res.user_question}")
print(f"Claims Analyzed: {res.claims_analyzed}")
print(f"Supporting Evidence count: {len(res.supporting_evidence)}")
print(f"Contradicting Evidence count: {len(res.contradicting_evidence)}")
print(f"Webpage Metadata: {res.webpage}")
print(f"Context Quotes count: {len(res.relevant_page_context or [])}")
if res.relevant_page_context:
    for i, q in enumerate(res.relevant_page_context, 1):
        print(f"  Quote {i}: {q[:100]}...")

print("\nSupporting evidence sources:")
for e in res.supporting_evidence:
    print(f"  - {e.domain} | {e.source_url} | {e.text_snippet[:80]}...")

print("\nContradicting evidence sources:")
for e in res.contradicting_evidence:
    print(f"  - {e.domain} | {e.source_url} | {e.text_snippet[:80]}...")

print("\nExplanation:")
print(res.explanation)
