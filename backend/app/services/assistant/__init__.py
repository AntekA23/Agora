"""Assistant service module - intelligent intent detection and routing."""

from app.services.assistant.router import (
    AssistantRouter,
    Intent,
    IntentResult,
    QuickAction,
    assistant_router,
    get_quick_actions,
)

__all__ = [
    "AssistantRouter",
    "Intent",
    "IntentResult",
    "QuickAction",
    "assistant_router",
    "get_quick_actions",
]
