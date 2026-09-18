"""Evidence ranking module utilizing BGE-M3 semantic similarity scoring.

Ranks candidate passages against the user claim to extract the top-K
most relevant evidence items while reducing noise for the LLM.
"""

import logging
import math
from typing import List, Dict, Any
from .config import config
from .schemas import EvidenceItem, SourceTier

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Cache for local sentence transformer if initialized
_LOCAL_MODEL = None


def get_local_embedder():
    """Loads a fast, local sentence-transformer model if available."""
    global _LOCAL_MODEL
    if _LOCAL_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use compact, fast BGE model for CPU efficiency or bge-m3 if specified
            model_name = "BAAI/bge-small-en-v1.5"
            logger.info(f"Loading local embedder {model_name}...")
            _LOCAL_MODEL = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning(f"Could not load local SentenceTransformer: {e}")
            _LOCAL_MODEL = None
    return _LOCAL_MODEL


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def compute_lexical_similarity(claim: str, passage: str) -> float:
    """Fast fallback lexical overlap & term frequency similarity."""
    claim_words = set(re_tokenize(claim))
    passage_words = re_tokenize(passage)
    if not claim_words or not passage_words:
        return 0.0

    def word_match(pw: str, cw: str) -> bool:
        if pw == cw:
            return True
        if len(pw) >= 3 and len(cw) >= 3:
            if pw.startswith(cw) or cw.startswith(pw):
                return True
            if len(pw) >= 4 and len(cw) >= 4 and pw[:4] == cw[:4]:
                return True
        return False

    hit_count = sum(1 for pw in passage_words if any(word_match(pw, cw) for cw in claim_words))
    # Jaccard / frequency score normalized
    overlap = hit_count / (len(claim_words) + math.log1p(len(passage_words)))
    return min(max(overlap, 0.0), 1.0)


def re_tokenize(text: str) -> List[str]:
    import re
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
    stop_words = {"the", "and", "for", "that", "this", "with", "from", "have", "are", "was", "were", "been"}
    return [t for t in tokens if t not in stop_words]


def get_hf_embeddings(texts: List[str], token: str, model_id: str = "BAAI/bge-m3") -> List[List[float]]:
    """Fetches embeddings via Hugging Face Inference API."""
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=token)
        # feature_extraction returns embeddings
        vectors = client.feature_extraction(texts, model=model_id)
        if isinstance(vectors, list):
            return vectors
        return vectors.tolist()
    except Exception as e:
        logger.warning(f"HF Inference feature_extraction failed: {e}")
        return []


def rank_evidence_chunks(
    claim: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[EvidenceItem]:
    """Ranks extracted passage chunks based on semantic similarity to the claim.
    
    Returns top_k EvidenceItem instances sorted by relevance score.
    """
    if not chunks:
        return []

    passages = [c["passage"] for c in chunks]
    similarity_scores: List[float] = []

    # Method 1: Hugging Face Inference API (if token provided)
    if config.has_hf_token:
        try:
            batch = [claim] + passages[:30] # Limit batch size for serverless API
            embs = get_hf_embeddings(batch, token=config.hf_token, model_id=config.hf_embedding_model)
            if len(embs) == len(batch):
                claim_vec = embs[0]
                similarity_scores = [cosine_similarity(claim_vec, p_vec) for p_vec in embs[1:]]
        except Exception as ex:
            logger.warning(f"HF embedding scoring error: {ex}")

    # Method 2: Local SentenceTransformer embedder fallback (only if NOT in low_memory_mode)
    if not similarity_scores or len(similarity_scores) != len(chunks):
        if not config.low_memory_mode:
            local_model = get_local_embedder()
            if local_model is not None:
                try:
                    claim_vec = local_model.encode(claim).tolist()
                    chunk_vecs = local_model.encode(passages).tolist()
                    similarity_scores = [cosine_similarity(claim_vec, v) for v in chunk_vecs]
                except Exception as ex:
                    logger.warning(f"Local embedder scoring error: {ex}")

    # Method 3: Lightweight lexical overlap fallback (0 MB RAM overhead)
    if not similarity_scores or len(similarity_scores) != len(chunks):
        similarity_scores = [compute_lexical_similarity(claim, p) for p in passages]

    # Combine similarity with source tier weight
    scored_items: List[EvidenceItem] = []
    for idx, chunk in enumerate(chunks):
        base_sim = similarity_scores[idx] if idx < len(similarity_scores) else 0.0
        tier = chunk["source_tier"]

        # Tier weighting
        tier_multiplier = 1.05 if tier == SourceTier.PRIMARY else (1.0 if tier == SourceTier.SECONDARY else 0.8)
        final_score = round(base_sim * tier_multiplier, 4)

        scored_items.append(EvidenceItem(
            id=f"ev_{idx+1}",
            url=chunk["url"],
            title=chunk["title"],
            domain=chunk["domain"],
            source_tier=tier,
            passage=chunk["passage"],
            similarity_score=final_score,
            stance=None,
        ))

    # Sort descending by similarity score
    scored_items.sort(key=lambda item: item.similarity_score, reverse=True)

    # Deduplicate items by URL so we have variety in sources
    unique_by_url: List[EvidenceItem] = []
    seen_urls = set()
    for item in scored_items:
        if item.url not in seen_urls:
            unique_by_url.append(item)
            seen_urls.add(item.url)
        elif len(unique_by_url) < top_k:
            unique_by_url.append(item)

        if len(unique_by_url) >= top_k:
            break

    return unique_by_url


def score_image_relevance(claim: str, image_dict: Dict[str, Any]) -> float:
    """Computes generic semantic relevance score (0.0 - 1.0) between claim and real textual image metadata.

    Only uses real textual metadata fields ('title', 'alt', 'page_title').
    Raw image URLs and source URLs are NOT used as semantic evidence text.
    """
    if not claim or not isinstance(image_dict, dict):
        return 0.0

    meta_parts = []
    title_val = image_dict.get("title")
    alt_val = image_dict.get("alt")
    page_title_val = image_dict.get("page_title")

    if title_val and str(title_val).strip():
        meta_parts.append(str(title_val).strip())
    if alt_val and str(alt_val).strip():
        meta_parts.append(str(alt_val).strip())
    if page_title_val and str(page_title_val).strip():
        meta_parts.append(str(page_title_val).strip())

    meta_text = " ".join(meta_parts).strip()
    if not meta_text:
        return 0.0

    sim_score = 0.0
    if config.has_hf_token:
        try:
            embs = get_hf_embeddings([claim, meta_text], token=config.hf_token, model_id=config.hf_embedding_model)
            if len(embs) == 2:
                sim_score = cosine_similarity(embs[0], embs[1])
        except Exception:
            pass

    if sim_score == 0.0 and not config.low_memory_mode:
        local_model = get_local_embedder()
        if local_model is not None:
            try:
                c_vec = local_model.encode(claim).tolist()
                m_vec = local_model.encode(meta_text).tolist()
                sim_score = cosine_similarity(c_vec, m_vec)
            except Exception:
                pass

    if sim_score == 0.0:
        sim_score = compute_lexical_similarity(claim, meta_text)

    claim_terms = re_tokenize(claim)
    meta_terms = set(re_tokenize(meta_text))
    if claim_terms:
        matches = sum(1 for t in claim_terms if t in meta_terms)
        ratio = matches / len(claim_terms)
    else:
        ratio = 1.0

    if len(claim_terms) >= 3 and ratio < 0.35:
        sim_score = sim_score * (0.3 + 0.7 * ratio)

    return round(sim_score, 4)


def rank_and_filter_images(
    claim: str,
    raw_images: List[Dict[str, Any]],
    top_k: int = 2,
    min_threshold: float = 0.45,
) -> List[Any]:
    """Ranks candidate images by semantic relevance and filters out irrelevant images.

    Returns up to top_k RelevantImage instances that pass min_threshold.
    Returns [] if zero candidates satisfy the threshold.
    """
    from .schemas import RelevantImage
    from .source_filter import classify_source

    if not raw_images or not claim:
        return []

    scored: List[tuple[float, RelevantImage]] = []
    seen_urls = set()

    for img in raw_images:
        if not isinstance(img, dict):
            continue
        img_url = img.get("image_url")
        if not img_url or img_url in seen_urls:
            continue
        seen_urls.add(img_url)

        base_score = score_image_relevance(claim, img)
        if base_score <= 0.0:
            continue

        source_val = str(img.get("source_url")).strip() if img.get("source_url") else None

        # Generic source quality weighting using existing classify_source
        if source_val:
            _, _, authority_weight = classify_source(source_val)
            final_score = round(base_score * (0.8 + 0.2 * authority_weight), 4)
        else:
            final_score = base_score

        if final_score >= min_threshold:
            title_val = str(img.get("title")).strip() if img.get("title") else None
            thumb_val = str(img.get("thumbnail_url")).strip() if img.get("thumbnail_url") else None

            scored.append((
                final_score,
                RelevantImage(
                    title=title_val,
                    image_url=str(img_url),
                    thumbnail_url=thumb_val,
                    source_url=source_val,
                    relevance_score=final_score,
                )
            ))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


