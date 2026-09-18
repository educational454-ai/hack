import logging
from core.retriever import retrieve_relevant_images
from core.ranker import get_local_embedder, cosine_similarity, re_tokenize, get_hf_embeddings
from core.config import config

logging.basicConfig(level=logging.INFO)

def score_image(claim: str, title: str, source_url: str) -> float:
    meta_parts = []
    if title:
        meta_parts.append(title)
    if source_url:
        meta_parts.append(source_url)
    meta = " ".join(meta_parts).strip()
    
    if not meta:
        return 0.0

    sim_score = 0.0
    if config.has_hf_token:
        try:
            embs = get_hf_embeddings([claim, meta], token=config.hf_token, model_id=config.hf_embedding_model)
            if len(embs) == 2:
                sim_score = cosine_similarity(embs[0], embs[1])
        except Exception:
            pass

    if sim_score == 0.0:
        model = get_local_embedder()
        if model:
            c_vec = model.encode(claim).tolist()
            m_vec = model.encode(meta).tolist()
            sim_score = cosine_similarity(c_vec, m_vec)

    claim_terms = re_tokenize(claim)
    meta_terms = set(re_tokenize(meta))
    if claim_terms:
        matches = sum(1 for t in claim_terms if t in meta_terms)
        ratio = matches / len(claim_terms)
    else:
        ratio = 1.0

    if len(claim_terms) >= 3 and ratio < 0.35:
        sim_score = sim_score * (0.3 + 0.7 * ratio)

    return round(sim_score, 4)

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
    
    accepted = []
    for idx, r in enumerate(raw, 1):
        t = r.get("title")
        s_url = r.get("source_url")
        score = score_image(claim, t, s_url)
        status = "ACCEPTED" if score >= 0.45 else "REJECTED"
        print(f"[{idx}] Status: {status:<8} | Score: {score:.4f} | Title: {t} | Source: {s_url}")
        if score >= 0.45:
            accepted.append((score, r))

    print(f"--> Total Accepted: {len(accepted)} (Top 2 will render, rest discarded)")
