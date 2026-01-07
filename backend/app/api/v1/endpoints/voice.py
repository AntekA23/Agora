"""Voice Interface API endpoints."""

from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.voice import (
    SpeechToTextService,
    TextToSpeechService,
    VoiceAgent,
)

router = APIRouter(prefix="/voice", tags=["voice"])


# ============================================================================
# SCHEMAS
# ============================================================================


class TextToSpeechRequest(BaseModel):
    """Request for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=4096)
    voice: str = "nova"
    model: str = "tts-1"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class VoiceConversationRequest(BaseModel):
    """Request for voice conversation."""
    conversation_history: list[dict] | None = None
    company_context: str = ""
    voice: str = "nova"
    return_audio: bool = True


class VoiceCommandResponse(BaseModel):
    """Response for voice command."""
    success: bool
    transcription: str | None = None
    command: dict | None = None
    message: str | None = None


# ============================================================================
# SPEECH-TO-TEXT ENDPOINTS
# ============================================================================


@router.post("/transcribe")
async def transcribe_audio(
    current_user: CurrentUser,
    audio: UploadFile = File(...),
    language: str = Query("pl"),
) -> dict[str, Any]:
    """Transcribe audio to text.

    Supported formats: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm
    """
    # Validate file type
    stt = SpeechToTextService()
    valid_extensions = stt.get_supported_formats()

    filename = audio.filename or "audio.wav"
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    if ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Supported: {', '.join(valid_extensions)}",
        )

    result = await stt.transcribe(
        audio_file=audio.file,
        filename=filename,
        language=language,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Transcription failed"),
        )

    return result


@router.post("/transcribe/timestamps")
async def transcribe_with_timestamps(
    current_user: CurrentUser,
    audio: UploadFile = File(...),
    language: str = Query("pl"),
) -> dict[str, Any]:
    """Transcribe audio with word-level timestamps."""
    stt = SpeechToTextService()

    filename = audio.filename or "audio.wav"

    result = await stt.transcribe_with_timestamps(
        audio_file=audio.file,
        filename=filename,
        language=language,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Transcription failed"),
        )

    return result


@router.post("/translate")
async def translate_audio(
    current_user: CurrentUser,
    audio: UploadFile = File(...),
) -> dict[str, Any]:
    """Translate audio in any language to English text."""
    stt = SpeechToTextService()

    filename = audio.filename or "audio.wav"

    result = await stt.translate_to_english(
        audio_file=audio.file,
        filename=filename,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Translation failed"),
        )

    return result


# ============================================================================
# TEXT-TO-SPEECH ENDPOINTS
# ============================================================================


@router.post("/synthesize")
async def synthesize_speech(
    data: TextToSpeechRequest,
    current_user: CurrentUser,
) -> Response:
    """Convert text to speech. Returns audio file."""
    tts = TextToSpeechService()

    result = await tts.synthesize(
        text=data.text,
        voice=data.voice,
        model=data.model,
        speed=data.speed,
        response_format="mp3",
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Synthesis failed"),
        )

    return Response(
        content=result["audio"],
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'attachment; filename="speech.mp3"',
        },
    )


@router.post("/synthesize/json")
async def synthesize_speech_json(
    data: TextToSpeechRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Convert text to speech. Returns base64 encoded audio."""
    import base64

    tts = TextToSpeechService()

    result = await tts.synthesize(
        text=data.text,
        voice=data.voice,
        model=data.model,
        speed=data.speed,
        response_format="mp3",
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Synthesis failed"),
        )

    return {
        "success": True,
        "audio_base64": base64.b64encode(result["audio"]).decode("utf-8"),
        "format": "mp3",
        "content_type": "audio/mpeg",
        "text_length": len(data.text),
    }


@router.get("/voices")
async def get_available_voices() -> list[dict[str, str]]:
    """Get list of available TTS voices."""
    tts = TextToSpeechService()
    return tts.get_available_voices()


@router.get("/languages")
async def get_supported_languages() -> dict[str, str]:
    """Get list of supported languages for transcription."""
    stt = SpeechToTextService()
    return stt.get_supported_languages()


# ============================================================================
# VOICE AGENT ENDPOINTS
# ============================================================================


@router.post("/agent/conversation")
async def voice_conversation(
    current_user: CurrentUser,
    db: Database,
    audio: UploadFile = File(...),
    voice: str = Query("nova"),
    return_audio: bool = Query(True),
) -> dict[str, Any] | Response:
    """Have a voice conversation with the AI agent.

    Accepts audio input, returns text and optionally audio response.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get company context
    company = await db.companies.find_one({"_id": current_user.company_id})
    company_context = ""
    if company:
        company_context = f"Firma: {company.get('name', '')}. {company.get('description', '')}"

    agent = VoiceAgent()
    filename = audio.filename or "audio.wav"

    result = await agent.process_voice_input(
        audio_file=audio.file,
        filename=filename,
        company_context=company_context,
        voice=voice,
        return_audio=return_audio,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Voice processing failed"),
        )

    # If audio requested and available, return audio file
    if return_audio and "audio" in result:
        import base64

        return {
            "success": True,
            "transcription": result["transcription"],
            "response_text": result["response_text"],
            "audio_base64": base64.b64encode(result["audio"]).decode("utf-8"),
            "audio_format": result.get("audio_format", "mp3"),
        }

    return {
        "success": True,
        "transcription": result["transcription"],
        "response_text": result["response_text"],
    }


@router.post("/agent/command", response_model=VoiceCommandResponse)
async def voice_command(
    current_user: CurrentUser,
    audio: UploadFile = File(...),
) -> VoiceCommandResponse:
    """Process a voice command.

    Interprets quick voice commands like "create post", "check finances", etc.
    """
    agent = VoiceAgent()
    filename = audio.filename or "audio.wav"

    result = await agent.quick_command(
        audio_file=audio.file,
        filename=filename,
    )

    return VoiceCommandResponse(**result)


@router.get("/agent/commands")
async def get_voice_commands() -> list[dict[str, str]]:
    """Get list of available voice commands."""
    agent = VoiceAgent()
    return agent.get_available_commands()
