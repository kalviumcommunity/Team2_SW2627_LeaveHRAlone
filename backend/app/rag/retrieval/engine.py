from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional
import re

from app.rag.embeddings import get_embedding_provider
from app.rag.vector_db import vector_db


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    region: str
    category: str
    version: str
    page_number: int
    section: str
    chunk_text: str
    similarity_score: float
    effective_date: str


def detect_query_category(query: str) -> Optional[str]:
    """Identify HR policy domain category from user question."""
    q = query.lower()
    if any(k in q for k in ["leave", "holiday", "vacation", "pto", "sick", "casual", "maternity", "paternity", "parental", "bereavement"]):
        return "Leave"
    elif any(k in q for k in ["insurance", "medical", "health", "opd", "dental", "gmc", "wellness", "stipend", "401k", "benefit"]):
        return "Benefits & Insurance"
    elif any(k in q for k in ["remote", "wfh", "work from home", "travel", "relocation"]):
        return "Remote Work"
    elif any(k in q for k in ["conduct", "harassment", "whistleblower", "ethics", "discrimination", "handbook"]):
        return "Workplace Policies"
    return None


def calculate_hybrid_score(chunk: Dict[str, Any], query: str, base_similarity: float) -> float:
    """Compute re-ranked relevance score combining vector cosine similarity and keyword matches."""
    score = base_similarity
    q_words = set(re.findall(r"\w+", query.lower()))

    payload = chunk.get("payload", {})
    text = payload.get("chunk_text", "").lower()
    section = payload.get("section", "").lower()
    title = payload.get("document_title", "").lower()

    # Section match boost
    section_words = set(re.findall(r"\w+", section))
    common_section = q_words.intersection(section_words)
    if common_section:
        score += min(len(common_section) * 0.04, 0.12)

    # Keyword density in chunk text
    text_words = set(re.findall(r"\w+", text))
    overlap_ratio = len(q_words.intersection(text_words)) / max(len(q_words), 1)
    score += overlap_ratio * 0.08

    # Title match boost
    if any(w in title for w in q_words if len(w) > 3):
        score += 0.03

    return round(score, 4)


class RetrievalEngine:
    """Executes 3-tier region-aware retrieval with strict geographical isolation."""

    def __init__(self):
        self.embedder = get_embedding_provider()

    def retrieve(
        self,
        query: str,
        user_region: str,
        employee_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        query_vector = self.embedder.embed_text(query)
        detected_category = detect_query_category(query)

        retrieved_raw: List[Dict[str, Any]] = []

        # ==========================================
        # Tier 1: User Region + Global for Detected Category
        # ==========================================
        if detected_category:
            tier1_results = vector_db.search(
                query_vector=query_vector,
                region=user_region,
                category=detected_category,
                status="active",
                employee_type=employee_type,
                allowed_regions=[user_region, "Global"],
                limit=top_k,
            )
            retrieved_raw.extend(tier1_results)

        # ==========================================
        # Tier 2: User Region + Active (Handbook / All categories)
        # ==========================================
        if len(retrieved_raw) < top_k:
            tier2_results = vector_db.search(
                query_vector=query_vector,
                region=user_region,
                status="active",
                employee_type=employee_type,
                allowed_regions=[user_region],
                limit=top_k,
            )
            seen_ids = {r["id"] for r in retrieved_raw}
            for r in tier2_results:
                if r["id"] not in seen_ids:
                    retrieved_raw.append(r)
                    seen_ids.add(r["id"])

        # ==========================================
        # Tier 3: Global Policies + Active (Fallback)
        # ==========================================
        if len(retrieved_raw) < top_k:
            tier3_results = vector_db.search(
                query_vector=query_vector,
                region="Global",
                status="active",
                employee_type=employee_type,
                allowed_regions=["Global"],
                limit=top_k,
            )
            seen_ids = {r["id"] for r in retrieved_raw}
            for r in tier3_results:
                if r["id"] not in seen_ids:
                    retrieved_raw.append(r)
                    seen_ids.add(r["id"])

        # ==========================================
        # Filter Inactive, Future Effective, & Expired Documents
        # ==========================================
        candidates: List[RetrievedChunk] = []
        today_iso = date.today().isoformat()

        for r in retrieved_raw:
            payload = r.get("payload", {})
            exp_date = payload.get("expiration_date")
            eff_date = payload.get("effective_date")

            # Exclude expired documents
            if exp_date and exp_date < today_iso:
                continue

            # Exclude future effective documents
            if eff_date and eff_date > today_iso:
                continue

            base_score = float(r.get("score", 0.0))
            re_ranked_score = calculate_hybrid_score(r, query, base_score)

            candidates.append(
                RetrievedChunk(
                    chunk_id=r["id"],
                    document_id=payload.get("document_id", ""),
                    document_title=payload.get("document_title", "Unknown Policy"),
                    region=payload.get("region", user_region),
                    category=payload.get("category", "General"),
                    version=payload.get("version", "1.0"),
                    page_number=int(payload.get("page_number", 1)),
                    section=payload.get("section", "General"),
                    chunk_text=payload.get("chunk_text", ""),
                    similarity_score=re_ranked_score,
                    effective_date=payload.get("effective_date", ""),
                )
            )

        # Sort descending by re-ranked score
        candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        return candidates[:top_k]


retrieval_engine = RetrievalEngine()
