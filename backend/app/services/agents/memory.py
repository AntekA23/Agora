"""Agent Memory Service - wektorowa pamięć dla agentów AI.

Umożliwia agentom:
- Zapamiętywanie udanych zadań i ich wyników
- Uczenie się z feedbacku użytkowników
- Dostęp do historii i kontekstu firmy
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

from app.core.config import settings

COLLECTION_NAME = "agent_memory"
VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small


class MemoryType:
    """Types of memories stored."""
    TASK_SUCCESS = "task_success"  # Udane zadanie z wysokim feedbackiem
    TASK_FAILURE = "task_failure"  # Nieudane zadanie do unikania
    COMPANY_FACT = "company_fact"  # Fakt o firmie
    BRAND_STYLE = "brand_style"  # Styl komunikacji marki
    USER_PREFERENCE = "user_preference"  # Preferencje użytkownika


class AgentMemoryService:
    """Service for managing agent memories in Qdrant vector database."""

    def __init__(self):
        self.client: QdrantClient | None = None
        self.openai: OpenAI | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connections to Qdrant and OpenAI."""
        if self._initialized:
            return

        try:
            self.client = QdrantClient(url=settings.QDRANT_URL)
            self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
            await self._ensure_collection()
            self._initialized = True
        except Exception as e:
            print(f"Memory service initialization failed: {e}")
            self._initialized = False

    async def _ensure_collection(self) -> None:
        """Ensure the memory collection exists with proper schema."""
        if not self.client:
            return

        try:
            self.client.get_collection(COLLECTION_NAME)
        except Exception:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
            # Create payload indexes for filtering
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="company_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="memory_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="agent",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using OpenAI."""
        if not self.openai:
            raise RuntimeError("OpenAI client not initialized")

        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def _generate_id(self, content: str, company_id: str) -> str:
        """Generate deterministic ID for deduplication."""
        hash_input = f"{company_id}:{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def store_memory(
        self,
        company_id: str,
        content: str,
        memory_type: str,
        agent: str = "",
        metadata: dict[str, Any] | None = None,
        rating: int | None = None,
    ) -> str:
        """Store a memory in the vector database.

        Args:
            company_id: ID firmy
            content: Treść do zapamiętania
            memory_type: Typ pamięci (MemoryType)
            agent: Nazwa agenta który stworzył pamięć
            metadata: Dodatkowe dane
            rating: Ocena (1-5) jeśli dotyczy

        Returns:
            ID zapisanej pamięci
        """
        if not self._initialized:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Memory service not available")

        # Generate embedding
        embedding = self._get_embedding(content)

        # Generate ID (for deduplication)
        memory_id = self._generate_id(content, company_id)

        # Prepare payload
        payload = {
            "company_id": company_id,
            "content": content,
            "memory_type": memory_type,
            "agent": agent,
            "rating": rating,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        # Upsert point
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return memory_id

    async def recall_memories(
        self,
        company_id: str,
        query: str,
        memory_types: list[str] | None = None,
        agent: str | None = None,
        limit: int = 5,
        min_score: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Recall relevant memories for a query.

        Args:
            company_id: ID firmy
            query: Zapytanie do wyszukania
            memory_types: Filtruj po typach pamięci
            agent: Filtruj po agencie
            limit: Maksymalna liczba wyników
            min_score: Minimalny próg podobieństwa

        Returns:
            Lista pasujących pamięci z ich treścią i metadanymi
        """
        if not self._initialized:
            await self.initialize()

        if not self.client:
            return []

        # Generate query embedding
        query_embedding = self._get_embedding(query)

        # Build filter conditions
        must_conditions = [
            FieldCondition(key="company_id", match=MatchValue(value=company_id))
        ]

        if memory_types:
            must_conditions.append(
                FieldCondition(
                    key="memory_type",
                    match=models.MatchAny(any=memory_types),
                )
            )

        if agent:
            must_conditions.append(
                FieldCondition(key="agent", match=MatchValue(value=agent))
            )

        # Search
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=Filter(must=must_conditions),
            limit=limit,
            score_threshold=min_score,
        )

        # Format results
        memories = []
        for hit in results:
            memories.append({
                "id": hit.id,
                "content": hit.payload.get("content", ""),
                "memory_type": hit.payload.get("memory_type", ""),
                "agent": hit.payload.get("agent", ""),
                "rating": hit.payload.get("rating"),
                "score": hit.score,
                "created_at": hit.payload.get("created_at"),
                "metadata": {
                    k: v for k, v in hit.payload.items()
                    if k not in ["content", "memory_type", "agent", "rating", "created_at", "company_id"]
                },
            })

        return memories

    async def store_successful_task(
        self,
        company_id: str,
        agent: str,
        task_input: dict[str, Any],
        task_output: dict[str, Any],
        rating: int,
    ) -> str:
        """Store a successful task for future reference.

        Zapisuje udane zadania z wysoką oceną (4-5) aby agent mógł
        się z nich uczyć przy podobnych zadaniach w przyszłości.
        """
        if rating < 4:
            # Only store highly rated tasks as successes
            return ""

        # Create content for embedding
        content = f"""
Zadanie: {task_input.get('brief', '')}
Typ: {task_input.get('type', task_input.get('post_type', ''))}
Wynik: {task_output.get('content', task_output.get('post_text', str(task_output)[:500]))}
"""

        metadata = {
            "task_input": task_input,
            "task_output_summary": str(task_output)[:1000],
        }

        return await self.store_memory(
            company_id=company_id,
            content=content,
            memory_type=MemoryType.TASK_SUCCESS,
            agent=agent,
            metadata=metadata,
            rating=rating,
        )

    async def get_similar_successful_tasks(
        self,
        company_id: str,
        brief: str,
        agent: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Get similar successful tasks for inspiration.

        Zwraca podobne zadania z wysoką oceną aby agent mógł
        się nimi inspirować przy tworzeniu nowego contentu.
        """
        return await self.recall_memories(
            company_id=company_id,
            query=brief,
            memory_types=[MemoryType.TASK_SUCCESS],
            agent=agent,
            limit=limit,
            min_score=0.6,
        )

    async def store_company_knowledge(
        self,
        company_id: str,
        knowledge_type: str,
        content: str,
    ) -> str:
        """Store company-specific knowledge for agents.

        Args:
            company_id: ID firmy
            knowledge_type: Typ wiedzy (product, service, brand, etc.)
            content: Treść do zapamiętania
        """
        return await self.store_memory(
            company_id=company_id,
            content=content,
            memory_type=MemoryType.COMPANY_FACT,
            metadata={"knowledge_type": knowledge_type},
        )

    async def get_company_context(
        self,
        company_id: str,
        query: str,
        limit: int = 5,
    ) -> str:
        """Get relevant company context for a query.

        Zwraca sformatowany kontekst o firmie do użycia przez agenta.
        """
        memories = await self.recall_memories(
            company_id=company_id,
            query=query,
            memory_types=[MemoryType.COMPANY_FACT, MemoryType.BRAND_STYLE],
            limit=limit,
            min_score=0.5,
        )

        if not memories:
            return ""

        context_parts = ["KONTEKST FIRMY:"]
        for mem in memories:
            context_parts.append(f"- {mem['content']}")

        return "\n".join(context_parts)

    async def delete_company_memories(self, company_id: str) -> int:
        """Delete all memories for a company (e.g., when company is deleted)."""
        if not self._initialized:
            await self.initialize()

        if not self.client:
            return 0

        result = self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="company_id", match=MatchValue(value=company_id))
                    ]
                )
            ),
        )

        return getattr(result, 'deleted_count', 0)


# Singleton instance
memory_service = AgentMemoryService()


async def get_memory_service() -> AgentMemoryService:
    """Get the memory service instance."""
    if not memory_service._initialized:
        await memory_service.initialize()
    return memory_service
