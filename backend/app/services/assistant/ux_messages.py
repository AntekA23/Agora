"""UX Messages and Progress Indicators for better user experience.

This module provides:
1. Friendly error messages in Polish
2. Progress indicators for long operations
3. Helpful suggestions and tips
4. Feedback collection utilities
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime, timezone


class ErrorType(str, Enum):
    """Types of errors that can occur."""

    UNKNOWN_INTENT = "unknown_intent"
    MISSING_REQUIRED = "missing_required"
    INVALID_PARAM = "invalid_param"
    EXECUTION_FAILED = "execution_failed"
    LLM_UNAVAILABLE = "llm_unavailable"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ProgressStage(str, Enum):
    """Stages of task execution for progress tracking."""

    UNDERSTANDING = "understanding"  # Analyzing request
    GATHERING = "gathering"  # Collecting parameters
    CONFIRMING = "confirming"  # Waiting for confirmation
    PREPARING = "preparing"  # Setting up task
    EXECUTING = "executing"  # Running agent
    GENERATING = "generating"  # Creating content
    FINALIZING = "finalizing"  # Finishing up
    COMPLETED = "completed"  # Done


@dataclass
class ProgressUpdate:
    """Progress update for long-running operations."""

    stage: ProgressStage
    message: str
    percentage: int  # 0-100
    details: str | None = None
    estimated_seconds: int | None = None


# Friendly error messages in Polish
ERROR_MESSAGES: dict[ErrorType, dict[str, str]] = {
    ErrorType.UNKNOWN_INTENT: {
        "title": "Nie rozumiem",
        "message": (
            "Nie jestem pewien czego potrzebujesz. "
            "Możesz opisać to inaczej?"
        ),
        "suggestions": [
            "Stwórz post na Instagram o...",
            "Napisz tekst reklamowy dla...",
            "Wygeneruj fakturę dla...",
            "Przeanalizuj przepływy finansowe",
        ],
    },
    ErrorType.MISSING_REQUIRED: {
        "title": "Brakuje informacji",
        "message": "Potrzebuję więcej szczegółów, żeby wykonać to zadanie.",
        "suggestions": [],
    },
    ErrorType.INVALID_PARAM: {
        "title": "Nieprawidłowa wartość",
        "message": "Podana wartość jest nieprawidłowa. Spróbuj jeszcze raz.",
        "suggestions": [],
    },
    ErrorType.EXECUTION_FAILED: {
        "title": "Coś poszło nie tak",
        "message": (
            "Wystąpił problem podczas wykonywania zadania. "
            "Spróbuj ponownie za chwilę."
        ),
        "suggestions": [
            "Spróbuj ponownie",
            "Zmień parametry",
            "Skontaktuj się z pomocą techniczną",
        ],
    },
    ErrorType.LLM_UNAVAILABLE: {
        "title": "Usługa chwilowo niedostępna",
        "message": (
            "Nasz asystent AI jest chwilowo przeciążony. "
            "Spróbuj ponownie za kilka sekund."
        ),
        "suggestions": ["Odczekaj chwilę i spróbuj ponownie"],
    },
    ErrorType.RATE_LIMITED: {
        "title": "Zbyt wiele zapytań",
        "message": (
            "Wysłałeś zbyt wiele zapytań. "
            "Poczekaj chwilę przed następnym."
        ),
        "suggestions": [],
    },
    ErrorType.VALIDATION_ERROR: {
        "title": "Błąd walidacji",
        "message": "Podane dane są nieprawidłowe.",
        "suggestions": [],
    },
    ErrorType.TIMEOUT: {
        "title": "Przekroczono limit czasu",
        "message": (
            "Operacja trwała zbyt długo. "
            "Spróbuj z prostszym zapytaniem."
        ),
        "suggestions": [],
    },
    ErrorType.CANCELLED: {
        "title": "Anulowano",
        "message": "Zadanie zostało anulowane.",
        "suggestions": ["Zacznij od nowa", "Jak mogę Ci pomóc?"],
    },
}

# Progress messages for each stage
PROGRESS_MESSAGES: dict[ProgressStage, dict[str, Any]] = {
    ProgressStage.UNDERSTANDING: {
        "message": "Analizuję Twoje zapytanie...",
        "icon": "🔍",
        "percentage": 10,
    },
    ProgressStage.GATHERING: {
        "message": "Zbieram potrzebne informacje...",
        "icon": "📝",
        "percentage": 25,
    },
    ProgressStage.CONFIRMING: {
        "message": "Czekam na potwierdzenie...",
        "icon": "✋",
        "percentage": 40,
    },
    ProgressStage.PREPARING: {
        "message": "Przygotowuję zadanie...",
        "icon": "⚙️",
        "percentage": 50,
    },
    ProgressStage.EXECUTING: {
        "message": "Pracuję nad tym...",
        "icon": "🤖",
        "percentage": 65,
    },
    ProgressStage.GENERATING: {
        "message": "Generuję treść...",
        "icon": "✨",
        "percentage": 80,
    },
    ProgressStage.FINALIZING: {
        "message": "Kończę...",
        "icon": "🎯",
        "percentage": 95,
    },
    ProgressStage.COMPLETED: {
        "message": "Gotowe!",
        "icon": "✅",
        "percentage": 100,
    },
}

# Task-specific progress messages
TASK_PROGRESS_MESSAGES: dict[str, dict[ProgressStage, str]] = {
    "social_media_post": {
        ProgressStage.EXECUTING: "Tworzę post na social media...",
        ProgressStage.GENERATING: "Generuję treść i hashtagi...",
    },
    "marketing_copy": {
        ProgressStage.EXECUTING: "Piszę tekst reklamowy...",
        ProgressStage.GENERATING: "Dopracowuję przekaz...",
    },
    "invoice": {
        ProgressStage.EXECUTING: "Przygotowuję fakturę...",
        ProgressStage.GENERATING: "Obliczam kwoty i VAT...",
    },
    "cashflow_analysis": {
        ProgressStage.EXECUTING: "Analizuję przepływy...",
        ProgressStage.GENERATING: "Przygotowuję raport...",
    },
    "job_posting": {
        ProgressStage.EXECUTING: "Tworzę ogłoszenie...",
        ProgressStage.GENERATING: "Dopracowuję treść...",
    },
}


class UXHelper:
    """Helper class for UX-related operations."""

    @staticmethod
    def get_error_response(
        error_type: ErrorType,
        details: str | None = None,
        param_name: str | None = None,
    ) -> dict[str, Any]:
        """Get a friendly error response.

        Args:
            error_type: Type of error
            details: Additional error details
            param_name: Parameter name for context

        Returns:
            Dictionary with error info for the user
        """
        error_info = ERROR_MESSAGES.get(
            error_type,
            ERROR_MESSAGES[ErrorType.EXECUTION_FAILED]
        )

        message = error_info["message"]

        # Customize message for specific errors
        if error_type == ErrorType.MISSING_REQUIRED and param_name:
            message = f"Potrzebuję informacji o: **{param_name}**"
        elif error_type == ErrorType.INVALID_PARAM and param_name:
            message = f"Wartość dla **{param_name}** jest nieprawidłowa."

        if details:
            message += f"\n\n_{details}_"

        return {
            "type": "error",
            "error_type": error_type.value,
            "title": error_info["title"],
            "message": message,
            "suggestions": error_info.get("suggestions", []),
            "recoverable": error_type not in [
                ErrorType.RATE_LIMITED,
                ErrorType.LLM_UNAVAILABLE,
            ],
        }

    @staticmethod
    def get_progress_update(
        stage: ProgressStage,
        task_type: str | None = None,
        custom_message: str | None = None,
    ) -> ProgressUpdate:
        """Get a progress update for the current stage.

        Args:
            stage: Current progress stage
            task_type: Type of task for customized messages
            custom_message: Optional custom message

        Returns:
            ProgressUpdate with stage info
        """
        base_info = PROGRESS_MESSAGES.get(
            stage,
            PROGRESS_MESSAGES[ProgressStage.EXECUTING]
        )

        # Get task-specific message if available
        message = custom_message
        if not message and task_type:
            task_messages = TASK_PROGRESS_MESSAGES.get(task_type, {})
            message = task_messages.get(stage)

        if not message:
            message = f"{base_info['icon']} {base_info['message']}"
        else:
            message = f"{base_info['icon']} {message}"

        return ProgressUpdate(
            stage=stage,
            message=message,
            percentage=base_info["percentage"],
        )

    @staticmethod
    def get_help_message(context: str | None = None) -> str:
        """Get a helpful message about available capabilities.

        Args:
            context: Optional context for targeted help

        Returns:
            Help message in Polish
        """
        base_help = """
**Jak mogę Ci pomóc?**

📱 **Marketing**
• Stwórz post na Instagram/Facebook/LinkedIn
• Napisz tekst reklamowy
• Zaplanuj kampanię marketingową

💰 **Finanse**
• Wygeneruj fakturę
• Przeanalizuj przepływy finansowe

👥 **HR**
• Stwórz ogłoszenie o pracę
• Przygotuj pytania rekrutacyjne
• Zaplanuj onboarding

📋 **Prawne**
• Sprawdź umowę
• Stwórz regulamin
• Weryfikacja RODO

💬 **Wsparcie**
• Odpowiedz na zgłoszenie
• Stwórz FAQ
• Analiza opinii klientów

**Wskazówka:** Po prostu opisz czego potrzebujesz, a ja zadam doprecyzujące pytania!
"""
        return base_help.strip()

    @staticmethod
    def format_confirmation_message(
        task_type: str,
        params: dict[str, Any],
    ) -> str:
        """Format a clear confirmation message.

        Args:
            task_type: Type of task
            params: Parameters to confirm

        Returns:
            Formatted confirmation message
        """
        task_names = {
            "social_media_post": "Post na social media",
            "marketing_copy": "Tekst reklamowy",
            "campaign": "Kampania marketingowa",
            "invoice": "Faktura",
            "cashflow_analysis": "Analiza cashflow",
            "job_posting": "Ogłoszenie o pracę",
            "interview_questions": "Pytania rekrutacyjne",
            "onboarding": "Plan onboardingu",
            "contract_review": "Analiza umowy",
            "privacy_policy": "Polityka prywatności",
            "terms_of_service": "Regulamin",
            "gdpr_check": "Weryfikacja RODO",
            "ticket_response": "Odpowiedź na zgłoszenie",
            "faq": "FAQ",
            "sentiment_analysis": "Analiza sentymentu",
        }

        param_labels = {
            "topic": "Temat",
            "brief": "Opis",
            "platform": "Platforma",
            "tone": "Ton",
            "target_audience": "Grupa docelowa",
            "post_type": "Typ posta",
            "copy_type": "Typ tekstu",
            "client_name": "Klient",
            "items": "Pozycje",
            "due_date": "Termin płatności",
            "payment_terms": "Warunki płatności",
            "position": "Stanowisko",
            "requirements": "Wymagania",
            "salary_range": "Wynagrodzenie",
            "location": "Lokalizacja",
            "remote_option": "Praca zdalna",
        }

        task_name = task_names.get(task_type, task_type)

        lines = [f"**{task_name}**", "", "📋 Parametry:"]

        for key, value in params.items():
            if value and key in param_labels:
                display_value = value
                if isinstance(value, str) and len(value) > 60:
                    display_value = value[:60] + "..."
                elif isinstance(value, list):
                    display_value = f"{len(value)} pozycji"

                lines.append(f"• {param_labels[key]}: {display_value}")

        lines.extend([
            "",
            "---",
            "✅ **Wykonaj** | ✏️ **Zmień** | ❌ **Anuluj**",
        ])

        return "\n".join(lines)

    @staticmethod
    def get_success_message(task_type: str) -> str:
        """Get a success message for completed task.

        Args:
            task_type: Type of completed task

        Returns:
            Success message
        """
        messages = {
            "social_media_post": "✅ Post został wygenerowany!",
            "marketing_copy": "✅ Tekst reklamowy jest gotowy!",
            "campaign": "✅ Kampania została zaplanowana!",
            "invoice": "✅ Faktura została wygenerowana!",
            "cashflow_analysis": "✅ Analiza cashflow jest gotowa!",
            "job_posting": "✅ Ogłoszenie o pracę jest gotowe!",
            "interview_questions": "✅ Pytania rekrutacyjne są gotowe!",
            "onboarding": "✅ Plan onboardingu jest gotowy!",
            "contract_review": "✅ Analiza umowy jest gotowa!",
            "privacy_policy": "✅ Polityka prywatności jest gotowa!",
            "terms_of_service": "✅ Regulamin jest gotowy!",
            "gdpr_check": "✅ Weryfikacja RODO zakończona!",
            "ticket_response": "✅ Odpowiedź na zgłoszenie jest gotowa!",
            "faq": "✅ FAQ zostało wygenerowane!",
            "sentiment_analysis": "✅ Analiza sentymentu jest gotowa!",
        }

        return messages.get(task_type, "✅ Zadanie zostało wykonane!")


@dataclass
class FeedbackEntry:
    """Entry for user feedback collection."""

    task_id: str
    task_type: str
    rating: int  # 1-5
    comment: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    params_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at,
            "params_used": self.params_used,
        }


class FeedbackCollector:
    """Collects and manages user feedback."""

    def __init__(self, db=None):
        """Initialize feedback collector.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def submit_feedback(
        self,
        company_id: str,
        task_id: str,
        task_type: str,
        rating: int,
        comment: str | None = None,
        params_used: dict[str, Any] | None = None,
    ) -> bool:
        """Submit user feedback for a task.

        Args:
            company_id: Company ID
            task_id: Task ID
            task_type: Type of task
            rating: Rating 1-5
            comment: Optional comment
            params_used: Parameters used for the task

        Returns:
            True if feedback was saved
        """
        if not self.db:
            return False

        feedback = FeedbackEntry(
            task_id=task_id,
            task_type=task_type,
            rating=rating,
            comment=comment,
            params_used=params_used or {},
        )

        try:
            await self.db.feedback.insert_one({
                "company_id": company_id,
                **feedback.to_dict(),
            })
            return True
        except Exception:
            return False

    async def get_task_feedback_prompt(self) -> dict[str, Any]:
        """Get the feedback prompt to show after task completion.

        Returns:
            Feedback prompt structure
        """
        return {
            "type": "feedback_request",
            "message": "Jak oceniasz wynik?",
            "options": [
                {"value": 1, "label": "😞", "description": "Słabo"},
                {"value": 2, "label": "😐", "description": "Mogło być lepiej"},
                {"value": 3, "label": "🙂", "description": "OK"},
                {"value": 4, "label": "😊", "description": "Dobrze"},
                {"value": 5, "label": "🤩", "description": "Świetnie!"},
            ],
            "allow_comment": True,
            "comment_placeholder": "Dodatkowe uwagi (opcjonalnie)",
        }


# Singleton helper instance
ux_helper = UXHelper()
