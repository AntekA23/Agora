"""Website analyzer service - extracts company info from websites.

Uses Tavily API for web scraping and OpenAI for intelligent extraction
of brand information from company websites.
"""

import re
from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from app.core.config import settings


@dataclass
class ExtractedBrandInfo:
    """Extracted brand information from website."""

    company_name: str
    industry: str
    description: str
    target_audience: str
    brand_voice: str
    products_services: list[str]
    unique_selling_points: list[str]
    suggested_hashtags: list[str]
    confidence_score: float  # 0-1, how confident we are in the extraction


class WebsiteAnalyzer:
    """Service for analyzing company websites and extracting brand info."""

    def __init__(self):
        self._tavily_client: Optional[TavilyClient] = None
        self._llm: Optional[ChatOpenAI] = None

    @property
    def tavily_client(self) -> TavilyClient:
        """Lazy-load Tavily client."""
        if self._tavily_client is None:
            if not settings.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY not configured")
            self._tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        return self._tavily_client

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
            )
        return self._llm

    def normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has a scheme."""
        url = url.strip()
        if not url:
            return ""

        # Remove common prefixes that users might type
        url = re.sub(r'^(https?://)?(www\.)?', '', url, flags=re.IGNORECASE)

        # Add https://
        return f"https://{url}"

    async def fetch_website_content(self, url: str) -> dict:
        """Fetch website content using Tavily.

        Args:
            url: Website URL to analyze

        Returns:
            Dictionary with raw content and metadata
        """
        normalized_url = self.normalize_url(url)

        try:
            # Use Tavily to get website content
            response = self.tavily_client.search(
                query=f"site:{normalized_url} company information about products services",
                search_depth="advanced",
                max_results=5,
                include_raw_content=True,
            )

            # Also try to get the main page
            main_page = self.tavily_client.search(
                query=f"site:{normalized_url}",
                search_depth="basic",
                max_results=1,
                include_raw_content=True,
            )

            # Combine results
            all_content = []
            for result in response.get("results", []) + main_page.get("results", []):
                content = result.get("raw_content") or result.get("content", "")
                if content:
                    all_content.append(content[:2000])  # Limit per result

            return {
                "url": normalized_url,
                "content": "\n\n---\n\n".join(all_content)[:8000],  # Total limit
                "success": len(all_content) > 0,
            }

        except Exception as e:
            return {
                "url": normalized_url,
                "content": "",
                "success": False,
                "error": str(e),
            }

    async def extract_brand_info(
        self,
        url: str,
        company_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ExtractedBrandInfo:
        """Extract brand information from a website.

        Args:
            url: Website URL to analyze
            company_name: Optional company name (if already known)
            description: Optional description (if already known)

        Returns:
            ExtractedBrandInfo with analyzed data
        """
        # Fetch website content
        website_data = await self.fetch_website_content(url)

        if not website_data["success"] or not website_data["content"]:
            # Return minimal info if we couldn't fetch the site
            return ExtractedBrandInfo(
                company_name=company_name or "",
                industry="",
                description=description or "",
                target_audience="",
                brand_voice="profesjonalny",
                products_services=[],
                unique_selling_points=[],
                suggested_hashtags=[],
                confidence_score=0.1,
            )

        # Build prompt for extraction
        extraction_prompt = f"""Przeanalizuj ponizszy tekst ze strony internetowej firmy i wyodrebnij informacje o marce.

TEKST ZE STRONY:
{website_data["content"]}

{"ZNANA NAZWA FIRMY: " + company_name if company_name else ""}
{"ZNANY OPIS: " + description if description else ""}

Odpowiedz w formacie JSON (tylko JSON, bez dodatkowego tekstu):
{{
    "company_name": "nazwa firmy",
    "industry": "branza (np. e-commerce, uslugi IT, gastronomia, moda, kosmetyki)",
    "description": "krotki opis firmy (1-2 zdania)",
    "target_audience": "opis grupy docelowej (wiek, plec, zainteresowania, problemy)",
    "brand_voice": "ton komunikacji (np. profesjonalny, przyjazny, ekspertowy, casualowy)",
    "products_services": ["produkt1", "produkt2", "usluga1"],
    "unique_selling_points": ["USP1", "USP2"],
    "suggested_hashtags": ["#hashtag1", "#hashtag2"],
    "confidence": 0.8
}}

Jesli nie mozesz wyodrebnic jakiejs informacji, uzyj pustego stringa lub pustej listy.
Confidence to liczba 0-1 okreslajaca pewnosc ekstrakcji (1 = bardzo pewny).
"""

        try:
            # Call LLM for extraction
            response = await self.llm.ainvoke(extraction_prompt)
            content = response.content

            # Parse JSON from response
            # Try to find JSON in the response
            import json

            # Clean up response - find JSON object
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")

            return ExtractedBrandInfo(
                company_name=data.get("company_name") or company_name or "",
                industry=data.get("industry", ""),
                description=data.get("description") or description or "",
                target_audience=data.get("target_audience", ""),
                brand_voice=data.get("brand_voice", "profesjonalny"),
                products_services=data.get("products_services", []),
                unique_selling_points=data.get("unique_selling_points", []),
                suggested_hashtags=data.get("suggested_hashtags", []),
                confidence_score=float(data.get("confidence", 0.5)),
            )

        except Exception as e:
            # Return partial info on error
            return ExtractedBrandInfo(
                company_name=company_name or "",
                industry="",
                description=description or "",
                target_audience="",
                brand_voice="profesjonalny",
                products_services=[],
                unique_selling_points=[],
                suggested_hashtags=[],
                confidence_score=0.2,
            )

    async def analyze(
        self,
        url: Optional[str] = None,
        company_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ExtractedBrandInfo:
        """Main analysis method - extracts brand info from available data.

        Args:
            url: Optional website URL
            company_name: Optional company name
            description: Optional description

        Returns:
            ExtractedBrandInfo with best available data
        """
        if url:
            return await self.extract_brand_info(url, company_name, description)

        # If no URL, generate suggestions based on name/description
        if company_name or description:
            return await self._generate_suggestions(company_name, description)

        # Return empty result
        return ExtractedBrandInfo(
            company_name="",
            industry="",
            description="",
            target_audience="",
            brand_voice="profesjonalny",
            products_services=[],
            unique_selling_points=[],
            suggested_hashtags=[],
            confidence_score=0.0,
        )

    async def _generate_suggestions(
        self,
        company_name: Optional[str],
        description: Optional[str],
    ) -> ExtractedBrandInfo:
        """Generate brand suggestions based on name and description only."""
        prompt = f"""Na podstawie ponizszych informacji o firmie, zaproponuj ustawienia marki.

{"NAZWA FIRMY: " + company_name if company_name else ""}
{"OPIS: " + description if description else ""}

Odpowiedz w formacie JSON:
{{
    "industry": "prawdopodobna branza",
    "target_audience": "prawdopodobna grupa docelowa",
    "brand_voice": "sugerowany ton komunikacji",
    "suggested_hashtags": ["#hashtag1", "#hashtag2"],
    "confidence": 0.4
}}
"""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content

            import json
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            return ExtractedBrandInfo(
                company_name=company_name or "",
                industry=data.get("industry", ""),
                description=description or "",
                target_audience=data.get("target_audience", ""),
                brand_voice=data.get("brand_voice", "profesjonalny"),
                products_services=[],
                unique_selling_points=[],
                suggested_hashtags=data.get("suggested_hashtags", []),
                confidence_score=float(data.get("confidence", 0.3)),
            )

        except Exception:
            return ExtractedBrandInfo(
                company_name=company_name or "",
                industry="",
                description=description or "",
                target_audience="",
                brand_voice="profesjonalny",
                products_services=[],
                unique_selling_points=[],
                suggested_hashtags=[],
                confidence_score=0.1,
            )


# Singleton instance
website_analyzer = WebsiteAnalyzer()
