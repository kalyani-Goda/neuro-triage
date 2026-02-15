"""Qdrant vector database client."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import logging
import uuid

from src.config import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manager for Qdrant vector database operations."""

    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.collection_name = "medical_knowledge"

    def initialize_collection(self, vector_size: int = 1536):
        """Initialize or get medical knowledge collection."""
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception:
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created collection '{self.collection_name}'")

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> bool:
        """Add documents with embeddings to Qdrant."""
        try:
            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=doc,
                )
                for vector, doc in zip(vectors, documents)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Added {len(documents)} documents to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in Qdrant."""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=None,
                limit=limit,
                score_threshold=score_threshold,
            )

            documents = [
                {
                    "id": str(result.id),
                    "score": result.score,
                    **result.payload,
                }
                for result in results
            ]
            return documents
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def health_check(self) -> bool:
        """Check Qdrant connection health."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant manager instance
qdrant_manager = QdrantManager()
