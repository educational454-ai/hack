import logging
from core.pipeline import analyze_claim

logging.basicConfig(level=logging.INFO)

test_cases = [
    {
        "name": "1. URL + Question (Relevant Page Content)",
        "input": "https://en.wikipedia.org/wiki/Chandrayaan-3\nDid Chandrayaan-3 land near the Moon's south pole?",
    },
    {
        "name": "2. URL + Question (Page Context Does NOT Establish Fact)",
        "input": "https://en.wikipedia.org/wiki/India\nDid India ban UPI payments in 2025?",
    },
    {
        "name": "3. URL-Only Factual Article",
        "input": "https://en.wikipedia.org/wiki/Unified_Payments_Interface",
    },
    {
        "name": "4. Inaccessible / Invalid URL",
        "input": "https://invalid-nonexistent-domain-12345.com/page",
    },
]

for tc in test_cases:
    print("\n=======================================================")
    print("SMOKE TEST:", tc["name"])
    print("INPUT:", repr(tc["input"]))
    print("=======================================================")

    res = analyze_claim(tc["input"])

    print("Detected Mode:", res.mode)
    print("Webpage Domain:", res.webpage.domain if res.webpage else None)
    print("Webpage Title:", res.webpage.title if res.webpage else None)
    print("User Question:", res.user_question)
    print("Final Assessment:", res.verdict_title)
    print("Targeted Answer:", res.targeted_answer)
    print("Relevant Page Passages:", len(res.relevant_page_context) if res.relevant_page_context else 0)
    print("Claims Analyzed Count:", len(res.claims_analyzed) if res.claims_analyzed else 0)
    print("Independent Sources Count:", len(res.all_sources))
    print("Limitations:", res.evidence_limitations)

    # Verification of Subject Isolation:
    if res.webpage:
        subject_in_evidence = any(res.webpage.domain in ev.domain for ev in res.supporting_evidence + res.contradicting_evidence)
        print("Webpage Excluded From Verification Evidence Cards:", not subject_in_evidence)
