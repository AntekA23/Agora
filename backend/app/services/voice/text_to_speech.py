"""Text-to-Speech Service using OpenAI TTS API."""

import io
from typing import Any, Literal

from openai import AsyncOpenAI

from app.core.config import settings


Voice = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
AudioFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]


class TextToSpeechService:
    """Service for converting text to speech using OpenAI TTS."""

    def __init__(self):
        """Initialize the service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def synthesize(
        self,
        text: str,
        voice: Voice = "nova",
        model: str = "tts-1",
        response_format: AudioFormat = "mp3",
        speed: float = 1.0,
    ) -> dict[str, Any]:
        """Convert text to speech.

        Args:
            text: Text to convert (max 4096 characters)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1 for speed, tts-1-hd for quality)
            response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
            speed: Speech speed (0.25 to 4.0)

        Returns:
            Dictionary with audio data
        """
        if len(text) > 4096:
            return {
                "success": False,
                "error": "Text exceeds maximum length of 4096 characters",
            }

        if speed < 0.25 or speed > 4.0:
            return {
                "success": False,
                "error": "Speed must be between 0.25 and 4.0",
            }

        try:
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
                speed=speed,
            )

            # Get audio data
            audio_data = response.content

            return {
                "success": True,
                "audio": audio_data,
                "format": response_format,
                "voice": voice,
                "model": model,
                "text_length": len(text),
                "content_type": self._get_content_type(response_format),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: Voice = "nova",
        model: str = "tts-1",
        response_format: AudioFormat = "mp3",
        speed: float = 1.0,
    ) -> dict[str, Any]:
        """Convert text to speech and save to file.

        Args:
            text: Text to convert
            output_path: Path to save audio file
            voice: Voice to use
            model: TTS model
            response_format: Audio format
            speed: Speech speed

        Returns:
            Dictionary with result
        """
        result = await self.synthesize(
            text=text,
            voice=voice,
            model=model,
            response_format=response_format,
            speed=speed,
        )

        if not result["success"]:
            return result

        try:
            with open(output_path, "wb") as f:
                f.write(result["audio"])

            return {
                "success": True,
                "file_path": output_path,
                "format": response_format,
                "size_bytes": len(result["audio"]),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save file: {str(e)}",
            }

    async def synthesize_long_text(
        self,
        text: str,
        voice: Voice = "nova",
        model: str = "tts-1",
        response_format: AudioFormat = "mp3",
        speed: float = 1.0,
    ) -> dict[str, Any]:
        """Synthesize text longer than 4096 characters by splitting.

        Args:
            text: Long text to convert
            voice: Voice to use
            model: TTS model
            response_format: Audio format
            speed: Speech speed

        Returns:
            Dictionary with combined audio segments
        """
        # Split text into chunks at sentence boundaries
        chunks = self._split_text(text, max_length=4000)

        audio_segments = []
        for i, chunk in enumerate(chunks):
            result = await self.synthesize(
                text=chunk,
                voice=voice,
                model=model,
                response_format=response_format,
                speed=speed,
            )

            if not result["success"]:
                return {
                    "success": False,
                    "error": f"Failed at chunk {i + 1}: {result.get('error')}",
                }

            audio_segments.append(result["audio"])

        return {
            "success": True,
            "audio_segments": audio_segments,
            "chunks_count": len(chunks),
            "format": response_format,
            "voice": voice,
            "total_length": len(text),
        }

    def _split_text(self, text: str, max_length: int = 4000) -> list[str]:
        """Split text into chunks at sentence boundaries."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences (simple approach)
        sentences = text.replace(".", ".|").replace("!", "!|").replace("?", "?|").split("|")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += (" " + sentence) if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _get_content_type(self, format: AudioFormat) -> str:
        """Get MIME type for audio format."""
        content_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac",
            "wav": "audio/wav",
            "pcm": "audio/pcm",
        }
        return content_types.get(format, "audio/mpeg")

    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available voices with descriptions."""
        return [
            {
                "id": "alloy",
                "name": "Alloy",
                "description": "Neutralny, zrównoważony głos",
                "gender": "neutral",
            },
            {
                "id": "echo",
                "name": "Echo",
                "description": "Męski, głęboki głos",
                "gender": "male",
            },
            {
                "id": "fable",
                "name": "Fable",
                "description": "Ciepły, narracyjny głos",
                "gender": "neutral",
            },
            {
                "id": "onyx",
                "name": "Onyx",
                "description": "Głęboki, autorytatywny głos męski",
                "gender": "male",
            },
            {
                "id": "nova",
                "name": "Nova",
                "description": "Przyjazny, żeński głos",
                "gender": "female",
                "recommended": True,
            },
            {
                "id": "shimmer",
                "name": "Shimmer",
                "description": "Jasny, optymistyczny żeński głos",
                "gender": "female",
            },
        ]

    def get_available_models(self) -> list[dict[str, str]]:
        """Get list of available TTS models."""
        return [
            {
                "id": "tts-1",
                "name": "TTS Standard",
                "description": "Szybki, dobra jakość",
                "recommended_for": "real-time",
            },
            {
                "id": "tts-1-hd",
                "name": "TTS HD",
                "description": "Wyższa jakość, wolniejszy",
                "recommended_for": "pre-recorded",
            },
        ]
