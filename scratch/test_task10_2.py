import logging
from core.retriever import retrieve_relevant_images
from core.ranker import score_image_relevance, rank_and_filter_images
from core.config import config

logging.basicConfig(level=logging.INFO)

claims = [
    "India banned UPI in 2025",
    "Chandrayaan-3 landed on the Moon in 2023",
    "Earth takes approximately 365 days to orbit the Sun",
]

for claim in claims:
    print("\n==========================================")
    print("CLAIM:", claim)
    print("==========================================")
    raw = retrieve_relevant_images(claim, max_images=8)
    print(f"Retrieved {len(raw)} raw candidates from DDGS.")
    
    filtered = rank_and_filter_images(claim, raw, top_k=2, min_threshold=0.45)
    print(f"--> Total Displayed Images: {len(filtered)}")
    for idx, img in enumerate(filtered, 1):
        print(f"[{idx}] Title: {img.title}")
        print(f"    Source URL: {img.source_url}")
        print(f"    Image URL: {img.image_url}")
        print(f"    Relevance Score: {img.relevance_score}")
