"""Speech-to-Text Service using OpenAI Whisper API."""

import io
from typing import Any, BinaryIO

from openai import AsyncOpenAI

from app.core.config import settings


class SpeechToTextService:
    """Service for converting speech to text using Whisper."""

    def __init__(self):
        """Initialize the service."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "whisper-1"

    async def transcribe(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
        language: str = "pl",
        prompt: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Transcribe audio to text.

        Args:
            audio_file: Audio file (file-like object)
            filename: Filename with extension (determines format)
            language: Language code (pl, en, etc.)
            prompt: Optional prompt to guide transcription
            response_format: json, text, srt, verbose_json, vtt
            temperature: Sampling temperature (0-1)

        Returns:
            Dictionary with transcription result
        """
        try:
            # Prepare file for upload
            audio_data = audio_file.read()
            file_tuple = (filename, io.BytesIO(audio_data))

            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=file_tuple,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
            )

            if response_format == "json" or response_format == "verbose_json":
                return {
                    "success": True,
                    "text": response.text,
                    "language": language,
                }
            else:
                return {
                    "success": True,
                    "text": response,
                    "language": language,
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def transcribe_with_timestamps(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
        language: str = "pl",
    ) -> dict[str, Any]:
        """Transcribe audio with word-level timestamps.

        Args:
            audio_file: Audio file
            filename: Filename with extension
            language: Language code

        Returns:
            Dictionary with transcription and timestamps
        """
        try:
            audio_data = audio_file.read()
            file_tuple = (filename, io.BytesIO(audio_data))

            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=file_tuple,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )

            return {
                "success": True,
                "text": response.text,
                "language": response.language,
                "duration": response.duration,
                "words": [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                    }
                    for w in (response.words or [])
                ],
                "segments": [
                    {
                        "id": s.id,
                        "text": s.text,
                        "start": s.start,
                        "end": s.end,
                    }
                    for s in (response.segments or [])
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def translate_to_english(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Translate audio in any language to English text.

        Args:
            audio_file: Audio file
            filename: Filename with extension
            prompt: Optional prompt

        Returns:
            Dictionary with English translation
        """
        try:
            audio_data = audio_file.read()
            file_tuple = (filename, io.BytesIO(audio_data))

            response = await self.client.audio.translations.create(
                model=self.model,
                file=file_tuple,
                prompt=prompt,
            )

            return {
                "success": True,
                "text": response.text,
                "target_language": "en",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats."""
        return [
            "flac",
            "m4a",
            "mp3",
            "mp4",
            "mpeg",
            "mpga",
            "oga",
            "ogg",
            "wav",
            "webm",
        ]

    def get_supported_languages(self) -> dict[str, str]:
        """Get list of supported languages."""
        return {
            "pl": "Polski",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "es": "Español",
            "it": "Italiano",
            "pt": "Português",
            "nl": "Nederlands",
            "ru": "Русский",
            "uk": "Українська",
            "cs": "Čeština",
            "sk": "Slovenčina",
            # ... more languages supported by Whisper
        }
