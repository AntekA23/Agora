"""Assistant service module - intelligent intent detection and routing."""

from app.services.assistant.router import (
    AssistantRouter,
    IntentResult,
    QuickAction,
    assistant_router,
    get_quick_actions,
)

__all__ = [
    "AssistantRouter",
    "IntentResult",
    "QuickAction",
    "assistant_router",
    "get_quick_actions",
]
