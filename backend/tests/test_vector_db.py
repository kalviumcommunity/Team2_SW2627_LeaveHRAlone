import uuid
import pytest
from app.rag.embeddings.mock_provider import MockEmbeddingProvider
from app.rag.vector_db import VectorDBService


@pytest.fixture
def test_vector_db():
    # Use isolated collection in-memory
    db = VectorDBService(url=":memory:", collection_name=f"test_coll_{uuid.uuid4().hex[:8]}")
    db.ensure_collection(dimension=64)
    return db


def test_vector_db_upsert_and_filtered_search(test_vector_db: VectorDBService):
    embedder = MockEmbeddingProvider(dimension=64)

    # 1. Upsert an India Leave Policy chunk
    doc1_id = str(uuid.uuid4())
    vec1 = embedder.embed_text("Employees in India receive 24 days annual leave")
    test_vector_db.upsert_chunks([
        {
            "id": str(uuid.uuid4()),
            "vector": vec1,
            "payload": {
                "document_id": doc1_id,
                "document_title": "India Leave Policy",
                "region": "India",
                "category": "Leave",
                "status": "active",
                "version": "2026.1",
                "chunk_text": "Employees in India receive 24 days annual leave",
            },
        }
    ])

    # 2. Upsert a US Leave Policy chunk
    doc2_id = str(uuid.uuid4())
    vec2 = embedder.embed_text("Employees in US receive 15 days PTO")
    test_vector_db.upsert_chunks([
        {
            "id": str(uuid.uuid4()),
            "vector": vec2,
            "payload": {
                "document_id": doc2_id,
                "document_title": "US Leave Policy",
                "region": "US",
                "category": "Leave",
                "status": "active",
                "version": "2026.1",
                "chunk_text": "Employees in US receive 15 days PTO",
            },
        }
    ])

    # 3. Query for India should ONLY return India chunk (Strict Region Isolation)
    query_vec = embedder.embed_text("How many days leave do I get?")
    india_results = test_vector_db.search(query_vec, region="India", limit=5)

    assert len(india_results) == 1
    assert india_results[0]["payload"]["region"] == "India"
    assert "24 days" in india_results[0]["payload"]["chunk_text"]

    # 4. Query for US should ONLY return US chunk
    us_results = test_vector_db.search(query_vec, region="US", limit=5)
    assert len(us_results) == 1
    assert us_results[0]["payload"]["region"] == "US"
    assert "15 days" in us_results[0]["payload"]["chunk_text"]

    # 5. Deactivate doc1 and verify it is not returned when filtering status='active'
    test_vector_db.set_document_status(doc1_id, "inactive")
    active_india_results = test_vector_db.search(query_vec, region="India", status="active", limit=5)
    assert len(active_india_results) == 0

    # 6. Delete doc2 and verify deletion
    test_vector_db.delete_by_document_id(doc2_id)
    us_after_delete = test_vector_db.search(query_vec, region="US", limit=5)
    assert len(us_after_delete) == 0
