"""Voice Agent - Conversational voice interface."""

from typing import Any, BinaryIO

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.voice.speech_to_text import SpeechToTextService
from app.services.voice.text_to_speech import TextToSpeechService


class VoiceAgent:
    """Conversational voice agent combining STT, LLM, and TTS."""

    def __init__(self):
        """Initialize the voice agent."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.stt = SpeechToTextService()
        self.tts = TextToSpeechService()

        # Default system prompt in Polish
        self.system_prompt = """Jesteś pomocnym asystentem biznesowym Agora.
Pomagasz przedsiębiorcom w codziennych zadaniach:
- Marketing i social media
- Finanse i faktury
- HR i rekrutacja
- Obsługa klienta

Odpowiadaj zwięźle, po polsku, przyjaźnie ale profesjonalnie.
Twoje odpowiedzi będą odczytywane na głos, więc używaj naturalnego języka mówionego.
Unikaj skomplikowanych list i formatowania - mów jak człowiek."""

    async def process_voice_input(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
        conversation_history: list[dict] | None = None,
        company_context: str = "",
        voice: str = "nova",
        return_audio: bool = True,
    ) -> dict[str, Any]:
        """Process voice input and return voice response.

        Args:
            audio_file: Input audio file
            filename: Filename with extension
            conversation_history: Previous messages for context
            company_context: Additional context about the company
            voice: Voice for response
            return_audio: Whether to return audio response

        Returns:
            Dictionary with transcription, response text, and audio
        """
        # Step 1: Transcribe audio to text
        transcription = await self.stt.transcribe(
            audio_file=audio_file,
            filename=filename,
            language="pl",
        )

        if not transcription["success"]:
            return {
                "success": False,
                "error": f"Transcription failed: {transcription.get('error')}",
            }

        user_text = transcription["text"]

        # Step 2: Generate response with LLM
        response = await self._generate_response(
            user_message=user_text,
            conversation_history=conversation_history,
            company_context=company_context,
        )

        if not response["success"]:
            return {
                "success": False,
                "error": f"LLM response failed: {response.get('error')}",
                "transcription": user_text,
            }

        assistant_text = response["text"]

        result = {
            "success": True,
            "transcription": user_text,
            "response_text": assistant_text,
        }

        # Step 3: Convert response to speech
        if return_audio:
            audio_result = await self.tts.synthesize(
                text=assistant_text,
                voice=voice,
                model="tts-1",  # Use faster model for real-time
                response_format="mp3",
            )

            if audio_result["success"]:
                result["audio"] = audio_result["audio"]
                result["audio_format"] = "mp3"
                result["audio_content_type"] = "audio/mpeg"
            else:
                result["audio_error"] = audio_result.get("error")

        return result

    async def _generate_response(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        company_context: str = "",
    ) -> dict[str, Any]:
        """Generate LLM response.

        Args:
            user_message: User's message
            conversation_history: Previous messages
            company_context: Additional context

        Returns:
            Dictionary with response text
        """
        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]

            if company_context:
                messages.append({
                    "role": "system",
                    "content": f"Kontekst firmy użytkownika: {company_context}",
                })

            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            # Add current message
            messages.append({"role": "user", "content": user_message})

            # Generate response
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,  # Keep responses concise for voice
                temperature=0.7,
            )

            return {
                "success": True,
                "text": response.choices[0].message.content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def process_text_to_voice(
        self,
        text: str,
        voice: str = "nova",
    ) -> dict[str, Any]:
        """Convert text response to voice.

        Args:
            text: Text to speak
            voice: Voice to use

        Returns:
            Dictionary with audio data
        """
        return await self.tts.synthesize(
            text=text,
            voice=voice,
            model="tts-1",
            response_format="mp3",
        )

    async def quick_command(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.wav",
    ) -> dict[str, Any]:
        """Process a quick voice command.

        Args:
            audio_file: Audio file with command
            filename: Filename

        Returns:
            Dictionary with command interpretation
        """
        # Transcribe
        transcription = await self.stt.transcribe(
            audio_file=audio_file,
            filename=filename,
            language="pl",
        )

        if not transcription["success"]:
            return transcription

        command_text = transcription["text"].lower()

        # Parse command
        command_mapping = {
            "stwórz post": {"action": "create_post", "agent": "instagram"},
            "napisz post": {"action": "create_post", "agent": "instagram"},
            "nowy post": {"action": "create_post", "agent": "instagram"},
            "stwórz fakturę": {"action": "create_invoice", "agent": "invoice"},
            "wystaw fakturę": {"action": "create_invoice", "agent": "invoice"},
            "nowa faktura": {"action": "create_invoice", "agent": "invoice"},
            "sprawdź cashflow": {"action": "check_cashflow", "agent": "finance"},
            "sprawdź finanse": {"action": "check_cashflow", "agent": "finance"},
            "stan konta": {"action": "check_cashflow", "agent": "finance"},
            "pokaż alerty": {"action": "show_alerts", "agent": "monitoring"},
            "moje alerty": {"action": "show_alerts", "agent": "monitoring"},
            "powiadomienia": {"action": "show_alerts", "agent": "monitoring"},
            "napisz email": {"action": "create_email", "agent": "copywriter"},
            "stwórz email": {"action": "create_email", "agent": "copywriter"},
            "nowy email": {"action": "create_email", "agent": "copywriter"},
        }

        detected_command = None
        for phrase, command in command_mapping.items():
            if phrase in command_text:
                detected_command = command
                break

        if detected_command:
            return {
                "success": True,
                "transcription": transcription["text"],
                "command": detected_command,
                "requires_details": True,
                "prompt": f"Rozpoznano komendę: {detected_command['action']}. Podaj więcej szczegółów.",
            }

        return {
            "success": True,
            "transcription": transcription["text"],
            "command": None,
            "message": "Nie rozpoznano komendy. Możesz powiedzieć np. 'stwórz post', 'wystaw fakturę', 'sprawdź finanse'.",
        }

    def set_system_prompt(self, prompt: str) -> None:
        """Set custom system prompt for the agent.

        Args:
            prompt: New system prompt
        """
        self.system_prompt = prompt

    def get_available_commands(self) -> list[dict[str, str]]:
        """Get list of available voice commands."""
        return [
            {"command": "Stwórz post", "description": "Rozpoczyna tworzenie posta na social media"},
            {"command": "Wystaw fakturę", "description": "Rozpoczyna tworzenie faktury"},
            {"command": "Sprawdź finanse", "description": "Pokazuje podsumowanie finansów"},
            {"command": "Pokaż alerty", "description": "Wyświetla aktualne powiadomienia"},
            {"command": "Napisz email", "description": "Rozpoczyna tworzenie emaila"},
        ]
