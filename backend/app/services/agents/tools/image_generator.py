"""Image Generator tool using OpenAI DALL-E for creating visuals."""

import base64
import httpx
from openai import OpenAI

from crewai.tools import BaseTool
from pydantic import Field

from app.core.config import settings


class ImageGeneratorTool(BaseTool):
    """Tool for generating images using DALL-E 3.

    Creates professional images for social media posts,
    marketing materials, and other visual content.
    """

    name: str = "image_generator"
    description: str = """Generuje obrazy za pomoca DALL-E 3. Uzyj tego narzedzia gdy potrzebujesz:
    - Grafiki do posta na social media
    - Obrazu do kampanii marketingowej
    - Wizualizacji produktu lub uslugi
    - Grafiki do reklamy

    Input powinien byc szczegolowym opisem obrazu w jezyku angielskim.
    Przyklad: "Modern minimalist photo of a coffee cup on wooden table, morning light, professional photography"
    """

    client: OpenAI | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _run(self, prompt: str) -> str:
        """Generate image and return URL."""
        if not self.client:
            return "Blad: Brak klucza API OpenAI. Skonfiguruj OPENAI_API_KEY w .env"

        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=self._enhance_prompt(prompt),
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            return f"""OBRAZ WYGENEROWANY POMYSLNIE!

URL: {image_url}

Zmodyfikowany prompt: {revised_prompt}

UWAGA: URL jest wazny przez ograniczony czas. Pobierz obraz jak najszybciej."""

        except Exception as e:
            return f"Blad generowania obrazu: {e!s}"

    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt for better results."""
        # Add quality modifiers if not present
        quality_terms = [
            "professional",
            "high quality",
            "detailed",
            "4k",
            "hd",
        ]

        has_quality = any(term in prompt.lower() for term in quality_terms)

        if not has_quality:
            prompt = f"{prompt}, professional quality, high resolution"

        return prompt


class SocialMediaImageTool(BaseTool):
    """Specialized tool for generating social media images."""

    name: str = "social_media_image"
    description: str = """Generuje obrazy zoptymalizowane pod social media.
    Automatycznie dobiera styl i format pod platforme.

    Input: opis obrazu + platforma (instagram/facebook/linkedin)
    Przyklad: "Promocja kawy latte, instagram"
    """

    client: OpenAI | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _run(self, input_text: str) -> str:
        """Generate social media optimized image."""
        if not self.client:
            return "Blad: Brak klucza API OpenAI"

        # Parse platform from input
        input_lower = input_text.lower()
        platform = "instagram"  # default

        if "linkedin" in input_lower:
            platform = "linkedin"
            input_text = input_text.replace("linkedin", "").strip(", ")
        elif "facebook" in input_lower:
            platform = "facebook"
            input_text = input_text.replace("facebook", "").strip(", ")
        elif "instagram" in input_lower:
            platform = "instagram"
            input_text = input_text.replace("instagram", "").strip(", ")

        # Platform-specific styling
        style_guide = {
            "instagram": "vibrant colors, lifestyle photography, engaging, modern aesthetic, square format friendly",
            "facebook": "clear and readable, professional but approachable, eye-catching, horizontal friendly",
            "linkedin": "professional, corporate style, clean design, business-appropriate, trustworthy",
        }

        enhanced_prompt = f"{input_text}. Style: {style_guide.get(platform, style_guide['instagram'])}"

        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            return f"""OBRAZ DLA {platform.upper()} WYGENEROWANY!

URL: {response.data[0].url}

Platforma: {platform}
Sugerowany format: {"1080x1080px (kwadrat)" if platform == "instagram" else "1200x630px (prostokat)"}

Wskazowka: Pobierz obraz i dostosuj rozmiar do wymagan platformy."""

        except Exception as e:
            return f"Blad: {e!s}"


class ImageService:
    """Service for image generation operations."""

    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural",
    ) -> dict:
        """Generate image with DALL-E 3."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )

        return {
            "url": response.data[0].url,
            "revised_prompt": response.data[0].revised_prompt,
            "size": size,
            "quality": quality,
        }

    async def generate_post_image(
        self,
        description: str,
        brand_style: str = "",
        platform: str = "instagram",
    ) -> dict:
        """Generate image optimized for social media post."""
        platform_styles = {
            "instagram": "vibrant, lifestyle, modern, engaging, square composition",
            "facebook": "clear, shareable, eye-catching, horizontal composition",
            "linkedin": "professional, corporate, trustworthy, clean design",
            "twitter": "bold, attention-grabbing, clear message",
        }

        style = platform_styles.get(platform, platform_styles["instagram"])

        prompt = f"{description}. Style: {style}"
        if brand_style:
            prompt += f". Brand aesthetic: {brand_style}"

        return await self.generate_image(prompt)

    async def download_image(self, url: str) -> bytes:
        """Download image from URL and return bytes."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def image_to_base64(self, url: str) -> str:
        """Download image and convert to base64."""
        image_bytes = await self.download_image(url)
        return base64.b64encode(image_bytes).decode("utf-8")


# Singleton
image_service = ImageService()


def get_image_tools() -> list[BaseTool]:
    """Get all image generation tools."""
    return [
        ImageGeneratorTool(),
        SocialMediaImageTool(),
    ]
