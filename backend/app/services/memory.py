import hashlib
from datetime import datetime
from typing import Any
from uuid import uuid4

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

COLLECTION_NAME = "agent_memory"


class AgentMemory:
    """Service for storing and retrieving agent memory using Qdrant."""

    def __init__(self, qdrant_client: QdrantClient):
        self.qdrant = qdrant_client
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI."""
        response = self.openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
        )
        return response.data[0].embedding

    def _generate_id(self, company_id: str, content: str) -> str:
        """Generate deterministic ID for memory entry."""
        hash_input = f"{company_id}:{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def store_memory(
        self,
        company_id: str,
        content: str,
        memory_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a memory entry for a company."""
        embedding = self._get_embedding(content)
        point_id = str(uuid4())

        payload = {
            "company_id": company_id,
            "content": content,
            "memory_type": memory_type,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        self.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return point_id

    async def search_memory(
        self,
        company_id: str,
        query: str,
        memory_type: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for relevant memories."""
        embedding = self._get_embedding(query)

        filter_conditions = [
            models.FieldCondition(
                key="company_id",
                match=models.MatchValue(value=company_id),
            )
        ]

        if memory_type:
            filter_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value=memory_type),
                )
            )

        results = self.qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            query_filter=models.Filter(must=filter_conditions),
            limit=limit,
        )

        return [
            {
                "id": str(result.id),
                "content": result.payload.get("content", ""),
                "memory_type": result.payload.get("memory_type", ""),
                "score": result.score,
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k not in ["company_id", "content", "memory_type"]
                },
            }
            for result in results
        ]

    async def store_task_result(
        self,
        company_id: str,
        task_type: str,
        input_brief: str,
        output_content: str,
        agent: str,
    ) -> str:
        """Store a task result as memory for future context."""
        content = f"Zadanie: {task_type}\nBrief: {input_brief}\nWynik: {output_content[:500]}"

        return await self.store_memory(
            company_id=company_id,
            content=content,
            memory_type="task_result",
            metadata={
                "task_type": task_type,
                "agent": agent,
            },
        )

    async def get_relevant_context(
        self,
        company_id: str,
        brief: str,
        limit: int = 3,
    ) -> str:
        """Get relevant context from past tasks for a new brief."""
        memories = await self.search_memory(
            company_id=company_id,
            query=brief,
            memory_type="task_result",
            limit=limit,
        )

        if not memories:
            return ""

        context_parts = []
        for memory in memories:
            if memory["score"] > 0.7:  # Only include relevant memories
                context_parts.append(memory["content"])

        if not context_parts:
            return ""

        return "Kontekst z poprzednich zadan:\n" + "\n---\n".join(context_parts)

    async def store_company_context(
        self,
        company_id: str,
        context_type: str,
        content: str,
    ) -> str:
        """Store company-specific context (brand guidelines, etc.)."""
        return await self.store_memory(
            company_id=company_id,
            content=content,
            memory_type=f"company_{context_type}",
        )

    async def delete_company_memories(self, company_id: str) -> int:
        """Delete all memories for a company."""
        result = self.qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="company_id",
                            match=models.MatchValue(value=company_id),
                        )
                    ]
                )
            ),
        )
        return result.status
