from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings

COLLECTION_NAME = "agent_memory"
VECTOR_SIZE = 1536  # OpenAI ada-002 embedding size


class QdrantService:
    """Qdrant vector database service for agent memory."""

    client: QdrantClient | None = None

    async def connect(self) -> None:
        """Connect to Qdrant."""
        self.client = QdrantClient(url=settings.QDRANT_URL)
        await self._ensure_collection()

    async def _ensure_collection(self) -> None:
        """Ensure the agent memory collection exists."""
        if not self.client:
            return

        try:
            self.client.get_collection(COLLECTION_NAME)
        except (UnexpectedResponse, Exception):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )

    def disconnect(self) -> None:
        """Disconnect from Qdrant."""
        if self.client:
            self.client.close()
            self.client = None

    def get_client(self) -> QdrantClient:
        """Get Qdrant client instance."""
        if self.client is None:
            raise RuntimeError("Qdrant not connected. Call connect() first.")
        return self.client


qdrant_service = QdrantService()


async def get_qdrant() -> QdrantClient:
    """Dependency to get Qdrant client."""
    return qdrant_service.get_client()
