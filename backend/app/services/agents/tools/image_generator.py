"""Image Generator tool using Together.ai Nano Banana Pro (Gemini 3 Pro Image) for creating visuals."""

import base64
import httpx
from together import Together

from crewai.tools import BaseTool
from pydantic import Field

from app.core.config import settings


class ImageGeneratorTool(BaseTool):
    """Tool for generating images using Nano Banana Pro (Gemini 3 Pro Image).

    Creates professional images for social media posts,
    marketing materials, and other visual content with SOTA text rendering.
    """

    name: str = "image_generator"
    description: str = """Generuje obrazy za pomoca Nano Banana Pro (Gemini). Uzyj tego narzedzia gdy potrzebujesz:
    - Grafiki do posta na social media
    - Obrazu do kampanii marketingowej
    - Wizualizacji produktu lub uslugi
    - Grafiki do reklamy

    Input powinien byc szczegolowym opisem obrazu w jezyku angielskim.
    Przyklad: "Modern minimalist photo of a coffee cup on wooden table, morning light, professional photography"
    """

    client: Together | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TOGETHER_API_KEY:
            self.client = Together(api_key=settings.TOGETHER_API_KEY)

    def _run(self, prompt: str) -> str:
        """Generate image and return URL."""
        if not self.client:
            return "Blad: Brak klucza API Together.ai. Skonfiguruj TOGETHER_API_KEY w .env"

        try:
            response = self.client.images.generate(
                model=settings.TOGETHER_IMAGE_MODEL,
                prompt=self._enhance_prompt(prompt),
                width=1024,
                height=1024,
                steps=28,
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url

                return f"""OBRAZ WYGENEROWANY POMYSLNIE!

URL: {image_url}

Model: {settings.TOGETHER_IMAGE_MODEL}

UWAGA: URL jest wazny przez ograniczony czas. Pobierz obraz jak najszybciej."""
            else:
                return "Blad: Brak danych w odpowiedzi od Together.ai"

        except Exception as e:
            return f"Blad generowania obrazu: {e!s}"

    def _enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt for better results."""
        quality_terms = [
            "professional",
            "high quality",
            "detailed",
            "4k",
            "hd",
        ]

        has_quality = any(term in prompt.lower() for term in quality_terms)

        if not has_quality:
            prompt = f"{prompt}, professional quality, high resolution, detailed"

        return prompt


class SocialMediaImageTool(BaseTool):
    """Specialized tool for generating social media images."""

    name: str = "social_media_image"
    description: str = """Generuje obrazy zoptymalizowane pod social media.
    Automatycznie dobiera styl i format pod platforme.

    Input: opis obrazu + platforma (instagram/facebook/linkedin)
    Przyklad: "Promocja kawy latte, instagram"
    """

    client: Together | None = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if settings.TOGETHER_API_KEY:
            self.client = Together(api_key=settings.TOGETHER_API_KEY)

    def _run(self, input_text: str) -> str:
        """Generate social media optimized image."""
        if not self.client:
            return "Blad: Brak klucza API Together.ai"

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

        enhanced_prompt = f"{input_text}. Style: {style_guide.get(platform, style_guide['instagram'])}, high quality, detailed"

        # Platform-specific dimensions
        dimensions = {
            "instagram": (1024, 1024),  # Square
            "facebook": (1024, 768),    # Landscape
            "linkedin": (1024, 768),    # Landscape
        }
        width, height = dimensions.get(platform, (1024, 1024))

        try:
            response = self.client.images.generate(
                model=settings.TOGETHER_IMAGE_MODEL,
                prompt=enhanced_prompt,
                width=width,
                height=height,
                steps=28,
                n=1,
            )

            if response.data and len(response.data) > 0:
                return f"""OBRAZ DLA {platform.upper()} WYGENEROWANY!

URL: {response.data[0].url}

Platforma: {platform}
Wymiary: {width}x{height}px

Wskazowka: Pobierz obraz i dostosuj do wymagan platformy jesli potrzeba."""
            else:
                return "Blad: Brak danych w odpowiedzi"

        except Exception as e:
            return f"Blad: {e!s}"


class ImageService:
    """Service for image generation operations using Nano Banana Pro (Gemini 3 Pro Image)."""

    def __init__(self):
        self.client = None
        if settings.TOGETHER_API_KEY:
            self.client = Together(api_key=settings.TOGETHER_API_KEY)

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 28,
    ) -> dict:
        """Generate image with Nano Banana Pro (Gemini 3 Pro Image)."""
        if not self.client:
            raise ValueError("Together.ai API key not configured")

        response = self.client.images.generate(
            model=settings.TOGETHER_IMAGE_MODEL,
            prompt=prompt,
            width=width,
            height=height,
            steps=steps,
            n=1,
        )

        if not response.data or len(response.data) == 0:
            raise ValueError("No image data in response")

        return {
            "url": response.data[0].url,
            "revised_prompt": prompt,  # Together.ai doesn't revise prompts like DALL-E
            "width": width,
            "height": height,
            "model": settings.TOGETHER_IMAGE_MODEL,
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

        platform_dimensions = {
            "instagram": (1024, 1024),
            "facebook": (1024, 768),
            "linkedin": (1024, 768),
            "twitter": (1024, 768),
        }

        style = platform_styles.get(platform, platform_styles["instagram"])
        width, height = platform_dimensions.get(platform, (1024, 1024))

        prompt = f"{description}. Style: {style}, high quality, professional photography"
        if brand_style:
            prompt += f". Brand aesthetic: {brand_style}"

        return await self.generate_image(prompt, width=width, height=height)

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
