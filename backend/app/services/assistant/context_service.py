"""Context Service - Assembles full context for intelligent responses.

Integrates:
- Conversation memory (Qdrant)
- Company knowledge (MongoDB + RAG)
- Task history
- User preferences

Provides rich context to the Intelligent Agent.
"""

import logging
from typing import Any
from datetime import datetime, timedelta

from app.services.memory import AgentMemory
from app.services.database.qdrant import qdrant_service

logger = logging.getLogger(__name__)


class ContextService:
    """Service for assembling comprehensive context for AI responses."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db
        self._memory = None

    @property
    def memory(self) -> AgentMemory:
        """Get memory service instance."""
        if self._memory is None:
            client = qdrant_service.get_client()
            self._memory = AgentMemory(client)
        return self._memory

    async def get_full_context(
        self,
        company_id: str,
        user_id: str,
        current_message: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive context for intelligent response generation.

        Args:
            company_id: Company ID
            user_id: User ID
            current_message: Current user message
            conversation_id: Optional conversation ID

        Returns:
            Dictionary with:
            - company_context: Formatted company knowledge
            - relevant_memories: Past relevant interactions
            - user_preferences: User's detected preferences
            - conversation_history: Recent messages
        """
        context = {
            "company_context": "",
            "relevant_memories": [],
            "user_preferences": {},
            "conversation_history": [],
            "brand_guidelines": "",
        }

        try:
            # 1. Get company knowledge
            company_context = await self._get_company_knowledge(company_id)
            context["company_context"] = company_context["formatted"]
            context["brand_guidelines"] = company_context.get("brand", "")

            # 2. Get relevant memories from past interactions
            memories = await self._get_relevant_memories(
                company_id=company_id,
                query=current_message,
            )
            context["relevant_memories"] = memories

            # 3. Get user preferences
            preferences = await self._get_user_preferences(company_id, user_id)
            context["user_preferences"] = preferences

            # 4. Get conversation history
            if conversation_id:
                history = await self._get_conversation_history(conversation_id)
                context["conversation_history"] = history

        except Exception as e:
            logger.error(f"Error getting context: {e}")

        return context

    async def _get_company_knowledge(self, company_id: str) -> dict[str, Any]:
        """Get all relevant knowledge about the company."""
        result = {
            "formatted": "",
            "brand": "",
            "products": [],
            "services": [],
        }

        try:
            company = await self.db.companies.find_one({"_id": company_id})
            if not company:
                # Try with string ID
                from bson import ObjectId
                company = await self.db.companies.find_one({"_id": ObjectId(company_id)})

            if not company:
                return result

            parts = []

            # Basic info
            if company.get("name"):
                parts.append(f"**Firma:** {company['name']}")
            if company.get("description"):
                parts.append(f"**Opis:** {company['description']}")
            if company.get("industry"):
                parts.append(f"**Branża:** {company['industry']}")

            # Brand settings
            brand = company.get("brand_settings", {})
            if brand:
                brand_parts = []
                if brand.get("tone"):
                    brand_parts.append(f"Ton komunikacji: {brand['tone']}")
                if brand.get("values"):
                    values = brand['values']
                    if isinstance(values, list):
                        brand_parts.append(f"Wartości: {', '.join(values)}")
                if brand.get("target_audience"):
                    brand_parts.append(f"Główna grupa docelowa: {brand['target_audience']}")
                if brand.get("voice"):
                    brand_parts.append(f"Głos marki: {brand['voice']}")

                if brand_parts:
                    result["brand"] = "\n".join(brand_parts)
                    parts.append("\n**Wytyczne marki:**")
                    parts.extend(brand_parts)

            # Knowledge base
            knowledge = company.get("knowledge", {})
            if knowledge:
                # Products
                products = knowledge.get("products", [])
                if products:
                    result["products"] = products
                    parts.append("\n**Produkty:**")
                    for p in products[:5]:
                        name = p.get("name", "")
                        desc = p.get("description", "")[:100]
                        if name:
                            parts.append(f"- {name}: {desc}")

                # Services
                services = knowledge.get("services", [])
                if services:
                    result["services"] = services
                    parts.append("\n**Usługi:**")
                    for s in services[:5]:
                        name = s.get("name", "")
                        desc = s.get("description", "")[:100]
                        if name:
                            parts.append(f"- {name}: {desc}")

                # USPs
                usps = knowledge.get("unique_selling_points", [])
                if usps:
                    parts.append("\n**Przewagi konkurencyjne:**")
                    for usp in usps[:5]:
                        parts.append(f"- {usp}")

            result["formatted"] = "\n".join(parts) if parts else "Brak informacji o firmie."

        except Exception as e:
            logger.error(f"Error getting company knowledge: {e}")
            result["formatted"] = "Błąd pobierania danych firmy."

        return result

    async def _get_relevant_memories(
        self,
        company_id: str,
        query: str,
        limit: int = 5,
    ) -> list[str]:
        """Get relevant memories from past interactions."""
        memories = []

        try:
            results = await self.memory.search_memory(
                company_id=company_id,
                query=query,
                limit=limit,
            )

            for mem in results:
                if mem.get("score", 0) > 0.6:  # Only relevant memories
                    content = mem.get("content", "")
                    memory_type = mem.get("memory_type", "")
                    if content:
                        memories.append(f"[{memory_type}] {content[:300]}")

        except Exception as e:
            logger.warning(f"Error getting memories: {e}")

        return memories

    async def _get_user_preferences(
        self,
        company_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Get user's detected preferences."""
        preferences = {
            "preferred_tone": None,
            "preferred_platform": None,
            "auto_approve": False,
            "skip_recommendations": False,
        }

        try:
            # Get from user preferences collection
            user_prefs = await self.db.user_preferences.find_one({
                "company_id": company_id,
                "user_id": user_id,
            })

            if user_prefs:
                preferences.update({
                    "preferred_tone": user_prefs.get("preferred_tone"),
                    "preferred_platform": user_prefs.get("preferred_platform"),
                    "auto_approve": user_prefs.get("auto_approve", False),
                    "skip_recommendations": user_prefs.get("skip_recommendations", False),
                })

        except Exception as e:
            logger.warning(f"Error getting user preferences: {e}")

        return preferences

    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        """Get recent conversation history."""
        history = []

        try:
            from bson import ObjectId

            conv = await self.db.conversations.find_one(
                {"_id": ObjectId(conversation_id)}
            )

            if conv and conv.get("messages"):
                messages = conv["messages"][-limit:]
                for msg in messages:
                    history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")[:500],
                    })

        except Exception as e:
            logger.warning(f"Error getting conversation history: {e}")

        return history

    async def store_interaction(
        self,
        company_id: str,
        interaction_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Store an interaction in memory for future reference.

        Args:
            company_id: Company ID
            interaction_type: Type of interaction (task_result, preference, etc.)
            content: Content to store
            metadata: Additional metadata

        Returns:
            Memory ID if successful
        """
        try:
            return await self.memory.store_memory(
                company_id=company_id,
                content=content,
                memory_type=interaction_type,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            return None

    async def store_successful_task(
        self,
        company_id: str,
        task_type: str,
        input_brief: str,
        output_content: str,
        agent: str,
        rating: int | None = None,
    ) -> str | None:
        """Store a successful task for learning.

        Args:
            company_id: Company ID
            task_type: Type of task
            input_brief: Original request/brief
            output_content: Generated output
            agent: Agent that performed the task
            rating: Optional user rating

        Returns:
            Memory ID if successful
        """
        try:
            content = f"Zadanie: {task_type}\nZlecenie: {input_brief}\nWynik: {output_content[:500]}"

            metadata = {
                "task_type": task_type,
                "agent": agent,
            }
            if rating:
                metadata["rating"] = rating

            return await self.memory.store_memory(
                company_id=company_id,
                content=content,
                memory_type="task_success",
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error storing task: {e}")
            return None

    async def learn_preference(
        self,
        company_id: str,
        user_id: str,
        preference_type: str,
        value: Any,
    ) -> None:
        """Learn and store a user preference.

        Args:
            company_id: Company ID
            user_id: User ID
            preference_type: Type of preference (tone, platform, etc.)
            value: Preference value
        """
        try:
            await self.db.user_preferences.update_one(
                {"company_id": company_id, "user_id": user_id},
                {
                    "$set": {
                        f"preferred_{preference_type}": value,
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Error learning preference: {e}")
