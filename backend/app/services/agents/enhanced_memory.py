"""Enhanced Memory System - Advanced RAG for AI Agents.

Combines multiple sources for comprehensive context:
- Qdrant (vector memory) - semantic search
- MongoDB (company data) - structured knowledge
- Tavily (web search) - real-time information
- Task history - learning from past successes
"""

from datetime import datetime, timedelta
from typing import Any

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.agents.memory import memory_service, MemoryType
from app.services.agents.tools.web_search import search_tool


class ContextSource(BaseModel):
    """Source of context information."""
    source_type: str  # vector, database, web, history
    content: str
    relevance_score: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnhancedContext(BaseModel):
    """Combined context from multiple sources."""
    query: str
    company_id: str
    sources: list[ContextSource] = Field(default_factory=list)
    formatted_context: str = ""
    total_sources: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


def _get_llm():
    """Get LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,
    )


class EnhancedMemoryService:
    """Enhanced RAG service combining multiple context sources."""

    def __init__(self, db):
        """Initialize with database connection."""
        self.db = db

    async def get_comprehensive_context(
        self,
        company_id: str,
        query: str,
        agent: str = "",
        include_web: bool = True,
        include_history: bool = True,
        include_company: bool = True,
        max_sources: int = 10,
    ) -> EnhancedContext:
        """Get comprehensive context from all available sources.

        Args:
            company_id: Company ID
            query: Query/task description
            agent: Agent name for filtering
            include_web: Include web search results
            include_history: Include task history
            include_company: Include company data
            max_sources: Maximum total sources

        Returns:
            EnhancedContext with all relevant information
        """
        context = EnhancedContext(query=query, company_id=company_id)
        sources = []

        # 1. Vector Memory (Qdrant) - similar tasks and company facts
        vector_sources = await self._get_vector_context(
            company_id=company_id,
            query=query,
            agent=agent,
            limit=3,
        )
        sources.extend(vector_sources)

        # 2. Company Knowledge Base (MongoDB)
        if include_company:
            company_sources = await self._get_company_context(
                company_id=company_id,
                query=query,
            )
            sources.extend(company_sources)

        # 3. Task History (MongoDB)
        if include_history:
            history_sources = await self._get_history_context(
                company_id=company_id,
                agent=agent,
                limit=3,
            )
            sources.extend(history_sources)

        # 4. Web Search (Tavily)
        if include_web and settings.TAVILY_API_KEY:
            web_sources = await self._get_web_context(
                query=query,
                limit=2,
            )
            sources.extend(web_sources)

        # Sort by relevance and limit
        sources.sort(key=lambda x: x.relevance_score, reverse=True)
        sources = sources[:max_sources]

        context.sources = sources
        context.total_sources = len(sources)
        context.formatted_context = self._format_context(sources)

        return context

    async def _get_vector_context(
        self,
        company_id: str,
        query: str,
        agent: str = "",
        limit: int = 3,
    ) -> list[ContextSource]:
        """Get context from vector memory."""
        sources = []

        try:
            if not memory_service._initialized:
                await memory_service.initialize()

            # Get similar successful tasks
            memories = await memory_service.recall_memories(
                company_id=company_id,
                query=query,
                memory_types=[MemoryType.TASK_SUCCESS, MemoryType.COMPANY_FACT],
                agent=agent if agent else None,
                limit=limit,
                min_score=0.5,
            )

            for mem in memories:
                sources.append(ContextSource(
                    source_type="vector",
                    content=mem["content"],
                    relevance_score=mem["score"],
                    metadata={
                        "memory_type": mem["memory_type"],
                        "agent": mem.get("agent", ""),
                        "rating": mem.get("rating"),
                    },
                ))

        except Exception as e:
            print(f"Vector memory error: {e}")

        return sources

    async def _get_company_context(
        self,
        company_id: str,
        query: str,
    ) -> list[ContextSource]:
        """Get context from company knowledge base."""
        sources = []

        try:
            company = await self.db.companies.find_one({"_id": company_id})
            if not company:
                return sources

            # Company basic info
            if company.get("name") or company.get("description"):
                sources.append(ContextSource(
                    source_type="database",
                    content=f"Firma: {company.get('name', '')}. {company.get('description', '')}",
                    relevance_score=0.9,
                    metadata={"type": "company_info"},
                ))

            # Brand settings
            brand = company.get("brand_settings", {})
            if brand:
                brand_info = []
                if brand.get("tone"):
                    brand_info.append(f"Ton komunikacji: {brand['tone']}")
                if brand.get("values"):
                    brand_info.append(f"Wartości: {', '.join(brand['values'])}")
                if brand.get("target_audience"):
                    brand_info.append(f"Grupa docelowa: {brand['target_audience']}")

                if brand_info:
                    sources.append(ContextSource(
                        source_type="database",
                        content="MARKA:\n" + "\n".join(brand_info),
                        relevance_score=0.85,
                        metadata={"type": "brand_settings"},
                    ))

            # Knowledge base
            knowledge = company.get("knowledge", {})
            if knowledge:
                # Products
                products = knowledge.get("products", [])
                if products:
                    products_text = "PRODUKTY:\n" + "\n".join(
                        f"- {p.get('name', '')}: {p.get('description', '')}"
                        for p in products[:5]
                    )
                    sources.append(ContextSource(
                        source_type="database",
                        content=products_text,
                        relevance_score=0.8,
                        metadata={"type": "products"},
                    ))

                # Services
                services = knowledge.get("services", [])
                if services:
                    services_text = "USŁUGI:\n" + "\n".join(
                        f"- {s.get('name', '')}: {s.get('description', '')}"
                        for s in services[:5]
                    )
                    sources.append(ContextSource(
                        source_type="database",
                        content=services_text,
                        relevance_score=0.8,
                        metadata={"type": "services"},
                    ))

                # USPs
                usps = knowledge.get("unique_selling_points", [])
                if usps:
                    sources.append(ContextSource(
                        source_type="database",
                        content="PRZEWAGI KONKURENCYJNE:\n" + "\n".join(f"- {u}" for u in usps),
                        relevance_score=0.75,
                        metadata={"type": "usps"},
                    ))

        except Exception as e:
            print(f"Company context error: {e}")

        return sources

    async def _get_history_context(
        self,
        company_id: str,
        agent: str = "",
        limit: int = 3,
    ) -> list[ContextSource]:
        """Get context from recent task history."""
        sources = []

        try:
            query = {"company_id": company_id, "status": "completed"}
            if agent:
                query["agent"] = agent

            # Get recent successful tasks with high ratings
            tasks = []
            cursor = self.db.tasks.find(query).sort("completed_at", -1).limit(limit * 2)
            async for task in cursor:
                if task.get("feedback", {}).get("rating", 0) >= 4:
                    tasks.append(task)
                    if len(tasks) >= limit:
                        break

            for task in tasks:
                content = f"Poprzednie zadanie ({task.get('agent', 'unknown')}):\n"
                content += f"Brief: {task.get('input', {}).get('brief', 'N/A')[:200]}\n"
                output = task.get("output", {})
                if isinstance(output, dict):
                    content += f"Wynik: {str(output)[:300]}"

                sources.append(ContextSource(
                    source_type="history",
                    content=content,
                    relevance_score=0.7,
                    metadata={
                        "task_id": str(task.get("_id")),
                        "agent": task.get("agent"),
                        "rating": task.get("feedback", {}).get("rating"),
                    },
                ))

        except Exception as e:
            print(f"History context error: {e}")

        return sources

    async def _get_web_context(
        self,
        query: str,
        limit: int = 2,
    ) -> list[ContextSource]:
        """Get context from web search."""
        sources = []

        try:
            # Use Tavily search
            from langchain_community.tools.tavily_search import TavilySearchResults

            tavily = TavilySearchResults(
                max_results=limit,
                search_depth="basic",
            )

            results = tavily.invoke(query)

            if isinstance(results, list):
                for r in results:
                    if isinstance(r, dict):
                        content = r.get("content", "")
                        if content:
                            sources.append(ContextSource(
                                source_type="web",
                                content=content[:500],
                                relevance_score=0.6,
                                metadata={
                                    "url": r.get("url", ""),
                                    "title": r.get("title", ""),
                                },
                            ))

        except Exception as e:
            print(f"Web context error: {e}")

        return sources

    def _format_context(self, sources: list[ContextSource]) -> str:
        """Format all sources into a single context string."""
        if not sources:
            return ""

        sections = {
            "database": [],
            "vector": [],
            "history": [],
            "web": [],
        }

        for source in sources:
            sections.get(source.source_type, []).append(source.content)

        formatted = []

        if sections["database"]:
            formatted.append("=" * 40)
            formatted.append("WIEDZA O FIRMIE:")
            formatted.extend(sections["database"])

        if sections["vector"]:
            formatted.append("=" * 40)
            formatted.append("POWIĄZANE DOŚWIADCZENIA:")
            formatted.extend(sections["vector"])

        if sections["history"]:
            formatted.append("=" * 40)
            formatted.append("POPRZEDNIE UDANE ZADANIA:")
            formatted.extend(sections["history"])

        if sections["web"]:
            formatted.append("=" * 40)
            formatted.append("AKTUALNE INFORMACJE Z INTERNETU:")
            formatted.extend(sections["web"])

        return "\n".join(formatted)

    async def synthesize_context(
        self,
        company_id: str,
        query: str,
        agent: str = "",
    ) -> dict[str, Any]:
        """Get context and synthesize it into actionable insights.

        Uses LLM to analyze context and extract key points.
        """
        # Get comprehensive context
        context = await self.get_comprehensive_context(
            company_id=company_id,
            query=query,
            agent=agent,
        )

        if not context.sources:
            return {
                "success": True,
                "has_context": False,
                "insights": {},
                "formatted_context": "",
            }

        # Use LLM to synthesize
        llm = _get_llm()

        synthesizer = Agent(
            role="Context Synthesizer",
            goal="Wyciągać kluczowe informacje z kontekstu",
            backstory="""Jesteś ekspertem od analizy informacji.
            Potrafisz szybko wyciągnąć najważniejsze punkty z różnych źródeł.""",
            tools=[],
            llm=llm,
            verbose=False,
        )

        task = Task(
            description=f"""
            Przeanalizuj kontekst i wyciągnij kluczowe informacje dla zadania:

            ZADANIE: {query}

            KONTEKST:
            {context.formatted_context}

            Zwróć w formacie JSON:
            {{
                "key_facts": ["najważniejsze fakty"],
                "brand_guidelines": ["wytyczne marki do zastosowania"],
                "past_successes": ["co działało wcześniej"],
                "current_trends": ["aktualne trendy (jeśli dostępne)"],
                "recommendations": ["rekomendacje jak podejść do zadania"],
                "warnings": ["na co uważać"]
            }}
            """,
            agent=synthesizer,
            expected_output="Synthesized context in JSON format",
        )

        crew = Crew(
            agents=[synthesizer],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        import json
        import re

        result_text = str(result)
        json_match = re.search(r'\{[\s\S]*\}', result_text)

        insights = {}
        if json_match:
            try:
                insights = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "success": True,
            "has_context": True,
            "insights": insights,
            "formatted_context": context.formatted_context,
            "sources_count": context.total_sources,
            "source_types": list(set(s.source_type for s in context.sources)),
        }
