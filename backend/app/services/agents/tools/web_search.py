"""Tavily web search tool for AI agents.

Tavily is optimized for LLM/AI applications, providing clean, structured
search results with relevance scoring and optional answer extraction.
"""

from crewai.tools import BaseTool
from pydantic import Field
from tavily import TavilyClient

from app.core.config import settings


class TavilySearchTool(BaseTool):
    """Web search tool using Tavily API.

    Provides real-time web search capabilities for agents to:
    - Research trends and current events
    - Find competitor information
    - Discover trending hashtags
    - Get market data and statistics
    """

    name: str = "tavily_search"
    description: str = """Wyszukuje informacje w internecie. Uzyj tego narzedzia gdy potrzebujesz:
    - Aktualnych trendow i wiadomosci
    - Informacji o konkurencji
    - Danych rynkowych i statystyk
    - Trending hashtagow i popularnych tematow
    - Sprawdzenia aktualnych cen, przepisow, wydarzen

    Input powinien byc zapytaniem wyszukiwania w jezyku polskim lub angielskim."""

    client: TavilyClient | None = Field(default=None, exclude=True)
    search_depth: str = Field(default="advanced")
    max_results: int = Field(default=5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TAVILY_API_KEY:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        self.search_depth = settings.TAVILY_SEARCH_DEPTH
        self.max_results = settings.TAVILY_MAX_RESULTS

    def _run(self, query: str) -> str:
        """Execute web search and return formatted results."""
        if not self.client:
            return "Blad: Brak klucza API Tavily. Skonfiguruj TAVILY_API_KEY w .env"

        try:
            response = self.client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=self.max_results,
                include_answer=True,
                include_raw_content=False,
            )

            return self._format_response(response)

        except Exception as e:
            return f"Blad wyszukiwania: {e!s}"

    def _format_response(self, response: dict) -> str:
        """Format Tavily response for agent consumption."""
        output_parts = []

        # Include AI-generated answer if available
        if response.get("answer"):
            output_parts.append(f"ODPOWIEDZ: {response['answer']}\n")

        # Format search results
        results = response.get("results", [])
        if results:
            output_parts.append("WYNIKI WYSZUKIWANIA:")
            for i, result in enumerate(results, 1):
                title = result.get("title", "Brak tytulu")
                content = result.get("content", "")[:500]  # Limit content length
                url = result.get("url", "")
                score = result.get("score", 0)

                output_parts.append(
                    f"\n{i}. {title}\n"
                    f"   Relevance: {score:.2f}\n"
                    f"   {content}\n"
                    f"   URL: {url}"
                )

        return "\n".join(output_parts) if output_parts else "Brak wynikow wyszukiwania."


class TavilyTrendsTool(BaseTool):
    """Specialized tool for finding trending topics and hashtags."""

    name: str = "tavily_trends"
    description: str = """Wyszukuje aktualne trendy i popularne hashtagi.
    Uzyj tego narzedzia do:
    - Znalezienia trending hashtagow na Instagram/social media
    - Odkrycia popularnych tematow w danej branzy
    - Sprawdzenia co jest viralowe

    Input: temat lub branza (np. 'fitness', 'marketing', 'ecommerce')"""

    client: TavilyClient | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TAVILY_API_KEY:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def _run(self, topic: str) -> str:
        """Search for trending topics and hashtags."""
        if not self.client:
            return "Blad: Brak klucza API Tavily. Skonfiguruj TAVILY_API_KEY w .env"

        try:
            # Search for trends
            trends_query = f"trending {topic} 2025 popular hashtags social media"
            response = self.client.search(
                query=trends_query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )

            output_parts = []

            if response.get("answer"):
                output_parts.append(f"TRENDY DLA '{topic.upper()}':\n{response['answer']}\n")

            results = response.get("results", [])
            if results:
                output_parts.append("ZRODLA:")
                for result in results[:3]:
                    title = result.get("title", "")
                    url = result.get("url", "")
                    output_parts.append(f"- {title}: {url}")

            return "\n".join(output_parts) if output_parts else f"Nie znaleziono trendow dla: {topic}"

        except Exception as e:
            return f"Blad wyszukiwania trendow: {e!s}"


class TavilyCompetitorTool(BaseTool):
    """Specialized tool for competitor analysis."""

    name: str = "tavily_competitor"
    description: str = """Analizuje konkurencje i znajduje informacje o firmach.
    Uzyj tego narzedzia do:
    - Zbadania co robi konkurencja
    - Znalezienia strategii marketingowych konkurentow
    - Porownania ofert na rynku

    Input: nazwa firmy lub branza (np. 'konkurencja fitness studio Warszawa')"""

    client: TavilyClient | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TAVILY_API_KEY:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def _run(self, query: str) -> str:
        """Search for competitor information."""
        if not self.client:
            return "Blad: Brak klucza API Tavily. Skonfiguruj TAVILY_API_KEY w .env"

        try:
            search_query = f"{query} marketing strategy social media presence Poland"
            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )

            output_parts = []

            if response.get("answer"):
                output_parts.append(f"ANALIZA KONKURENCJI:\n{response['answer']}\n")

            results = response.get("results", [])
            if results:
                output_parts.append("SZCZEGOLY:")
                for i, result in enumerate(results[:3], 1):
                    title = result.get("title", "")
                    content = result.get("content", "")[:300]
                    output_parts.append(f"\n{i}. {title}\n   {content}")

            return "\n".join(output_parts) if output_parts else f"Nie znaleziono informacji dla: {query}"

        except Exception as e:
            return f"Blad analizy konkurencji: {e!s}"


class TavilyMarketDataTool(BaseTool):
    """Specialized tool for market data and financial information."""

    name: str = "tavily_market"
    description: str = """Wyszukuje dane rynkowe i informacje finansowe.
    Uzyj tego narzedzia do:
    - Znalezienia benchmarkow branzowych
    - Sprawdzenia srednich cen na rynku
    - Danych o trendach ekonomicznych

    Input: zapytanie o dane rynkowe (np. 'srednie wynagrodzenia IT Polska 2025')"""

    client: TavilyClient | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TAVILY_API_KEY:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    def _run(self, query: str) -> str:
        """Search for market data and statistics."""
        if not self.client:
            return "Blad: Brak klucza API Tavily. Skonfiguruj TAVILY_API_KEY w .env"

        try:
            search_query = f"{query} statistics data Poland market 2025"
            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )

            output_parts = []

            if response.get("answer"):
                output_parts.append(f"DANE RYNKOWE:\n{response['answer']}\n")

            results = response.get("results", [])
            if results:
                output_parts.append("ZRODLA DANYCH:")
                for i, result in enumerate(results[:3], 1):
                    title = result.get("title", "")
                    content = result.get("content", "")[:300]
                    url = result.get("url", "")
                    output_parts.append(f"\n{i}. {title}\n   {content}\n   Zrodlo: {url}")

            return "\n".join(output_parts) if output_parts else f"Nie znaleziono danych dla: {query}"

        except Exception as e:
            return f"Blad wyszukiwania danych rynkowych: {e!s}"


# Factory function for getting tools
def get_tavily_tool(tool_type: str = "search") -> BaseTool:
    """Get a Tavily tool instance by type.

    Args:
        tool_type: Type of tool - 'search', 'trends', 'competitor', 'market'

    Returns:
        Configured Tavily tool instance
    """
    tools = {
        "search": TavilySearchTool,
        "trends": TavilyTrendsTool,
        "competitor": TavilyCompetitorTool,
        "market": TavilyMarketDataTool,
    }

    tool_class = tools.get(tool_type, TavilySearchTool)
    return tool_class()


def get_marketing_tools() -> list[BaseTool]:
    """Get all tools useful for marketing agents."""
    return [
        TavilySearchTool(),
        TavilyTrendsTool(),
        TavilyCompetitorTool(),
    ]


def get_finance_tools() -> list[BaseTool]:
    """Get all tools useful for finance agents."""
    return [
        TavilySearchTool(),
        TavilyMarketDataTool(),
    ]
