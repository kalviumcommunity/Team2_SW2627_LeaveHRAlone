import logging
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorDBService:
    """Manages Qdrant vector database connection, indexing, and querying."""

    def __init__(self, url: Optional[str] = None, collection_name: Optional[str] = None):
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.client: QdrantClient = self._init_client()

    def _init_client(self) -> QdrantClient:
        """Initialize Qdrant client. Supports in-memory ':memory:' or remote server URL."""
        if self.url == ":memory:":
            logger.info("Using in-memory Qdrant instance")
            return QdrantClient(":memory:")

        try:
            client = QdrantClient(url=self.url, timeout=5.0)
            # Test connectivity
            client.get_collections()
            logger.info("Connected to Qdrant at %s", self.url)
            return client
        except Exception as e:
            if settings.app_env.lower() == "test":
                logger.warning("Could not connect to Qdrant (%s). Using :memory: for test suite.", e)
                return QdrantClient(":memory:")
            logger.error("Failed to connect to Qdrant vector database at %s: %s", self.url, e)
            raise RuntimeError(f"Qdrant connection failed at {self.url}. Ensure the Qdrant service is running.") from e

    def ensure_collection(self, dimension: Optional[int] = None) -> None:
        """Create collection and metadata payload indexes if they do not exist."""
        dim = dimension or settings.embedding_dimension
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection: %s (dim=%d)", self.collection_name, dim)
        else:
            # Check dimension compatibility
            col_info = self.client.get_collection(self.collection_name)
            current_size = col_info.config.params.vectors.size
            if current_size != dim:
                logger.warning(
                    "Collection dimension mismatch: collection=%d, configured=%d. Reindex may be required.",
                    current_size,
                    dim,
                )

        # Create payload indexes for metadata filtering
        index_fields = [
            "region",
            "status",
            "category",
            "document_id",
            "employee_type",
            "effective_date",
            "expiration_date",
            "version",
        ]
        for field in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
            except Exception as e:
                logger.debug("Payload index notice for %s: %s", field, e)

    def upsert_chunks(self, points: List[Dict[str, Any]]) -> None:
        """Upsert embedded chunks into Qdrant collection."""
        self.ensure_collection()
        qdrant_points = []
        for p in points:
            point_id = str(p.get("id") or uuid.uuid4())
            qdrant_points.append(
                models.PointStruct(
                    id=point_id,
                    vector=p["vector"],
                    payload=p["payload"],
                )
            )

        if qdrant_points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points,
            )

    def count(self) -> int:
        """Return total number of points in the collection."""
        self.ensure_collection()
        try:
            res = self.client.count(collection_name=self.collection_name)
            return res.count
        except Exception:
            return 0

    def search(
        self,
        query_vector: List[float],
        region: str,
        category: Optional[str] = None,
        status: str = "active",
        employee_type: Optional[str] = None,
        limit: int = 5,
        allowed_regions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with region isolation and metadata filtering."""
        self.ensure_collection()

        filter_conditions = []

        # Region filtering: Never leak another region's policy
        # If allowed_regions specified, use that; otherwise allow [region, 'Global']
        target_regions = allowed_regions or [region, "Global"]
        filter_conditions.append(
            models.FieldCondition(
                key="region",
                match=models.MatchAny(any=target_regions),
            )
        )

        # Status filtering (default 'active')
        if status:
            filter_conditions.append(
                models.FieldCondition(
                    key="status",
                    match=models.MatchValue(value=status),
                )
            )

        # Employee type filtering (match specific type or 'All')
        if employee_type and employee_type != "All":
            filter_conditions.append(
                models.FieldCondition(
                    key="employee_type",
                    match=models.MatchAny(any=[employee_type, "All"]),
                )
            )

        # Category filtering if provided
        if category:
            filter_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category),
                )
            )

        search_filter = models.Filter(must=filter_conditions)

        # Execute search
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload,
            }
            for r in response.points
        ]

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunk points belonging to a specific document."""
        self.ensure_collection()
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )

    def set_document_status(self, document_id: str, new_status: str) -> None:
        """Update the status payload for all chunks of a document (e.g. 'inactive')."""
        self.update_document_metadata(document_id, {"status": new_status})

    def update_document_metadata(self, document_id: str, payload_updates: Dict[str, Any]) -> None:
        """Update payload fields for all chunks belonging to a document."""
        self.ensure_collection()
        self.client.set_payload(
            collection_name=self.collection_name,
            payload=payload_updates,
            points=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )


vector_db = VectorDBService()
