"""Assistant API - Intelligent intent detection and routing.

This endpoint provides natural language interpretation for the Command Center,
allowing users to describe what they need in plain Polish and get routed
to the appropriate agents.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.assistant import (
    assistant_router,
    get_quick_actions,
    IntentResult,
    QuickAction,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class InterpretRequest(BaseModel):
    """Request to interpret a natural language message."""

    message: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Wiadomosc uzytkownika w naturalnym jezyku",
        examples=["Potrzebuje posta na Instagram o nowym produkcie"],
    )


class InterpretResponse(BaseModel):
    """Response with detected intent and routing information."""

    intent: str = Field(..., description="Wykryty intent (np. social_media_post)")
    confidence: float = Field(..., ge=0, le=1, description="Pewnosc detekcji (0-1)")
    suggested_agents: list[str] = Field(
        default_factory=list,
        description="Sugerowane agenty do wykonania zadania",
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description="Brakujace informacje (nazwy parametrow)",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Pytania do uzytkownika o brakujace dane",
    )
    can_auto_execute: bool = Field(
        ...,
        description="Czy mozna od razu wykonac bez dodatkowych pytan",
    )
    extracted_params: dict = Field(
        default_factory=dict,
        description="Wyodrebnione parametry z wiadomosci",
    )
    quick_action_id: str | None = Field(
        default=None,
        description="ID quick action jesli uzyto",
    )


class QuickActionRequest(BaseModel):
    """Request to interpret a quick action selection."""

    action_id: str = Field(
        ...,
        description="ID wybranej quick action",
        examples=["social_post", "invoice", "campaign"],
    )
    params: dict = Field(
        default_factory=dict,
        description="Dodatkowe parametry",
    )


class QuickActionResponse(BaseModel):
    """Quick action definition."""

    id: str
    label: str
    icon: str
    description: str
    intent: str


class QuickActionsResponse(BaseModel):
    """Response with available quick actions."""

    actions: list[QuickActionResponse]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/interpret",
    response_model=InterpretResponse,
    summary="Interpretuj wiadomosc",
    description="Analizuje wiadomosc uzytkownika i wykrywa intent oraz sugeruje agentow.",
)
async def interpret_message(
    data: InterpretRequest,
    current_user: CurrentUser,
    db: Database,
) -> InterpretResponse:
    """Interpret a natural language message and return routing info.

    This endpoint:
    1. Detects user intent from the message
    2. Identifies which agents should handle the request
    3. Extracts any parameters mentioned in the message
    4. Determines what additional info is needed
    5. Generates follow-up questions in Polish
    """
    result = await assistant_router.interpret(data.message)

    return InterpretResponse(
        intent=result.intent.value,
        confidence=result.confidence,
        suggested_agents=result.suggested_agents,
        missing_info=result.missing_info,
        follow_up_questions=result.follow_up_questions,
        can_auto_execute=result.can_auto_execute,
        extracted_params=result.extracted_params,
        quick_action_id=result.quick_action_id,
    )


@router.post(
    "/quick-action",
    response_model=InterpretResponse,
    summary="Interpretuj quick action",
    description="Przetwarza wybrana szybka akcje i zwraca informacje o routingu.",
)
async def interpret_quick_action(
    data: QuickActionRequest,
    current_user: CurrentUser,
    db: Database,
) -> InterpretResponse:
    """Interpret a quick action selection.

    Quick actions are pre-defined common tasks with high confidence.
    """
    result = await assistant_router.interpret_quick_action(
        action_id=data.action_id,
        params=data.params,
    )

    return InterpretResponse(
        intent=result.intent.value,
        confidence=result.confidence,
        suggested_agents=result.suggested_agents,
        missing_info=result.missing_info,
        follow_up_questions=result.follow_up_questions,
        can_auto_execute=result.can_auto_execute,
        extracted_params=result.extracted_params,
        quick_action_id=result.quick_action_id,
    )


@router.get(
    "/quick-actions",
    response_model=QuickActionsResponse,
    summary="Lista quick actions",
    description="Zwraca liste dostepnych szybkich akcji dla Command Center.",
)
async def list_quick_actions(
    current_user: CurrentUser,
) -> QuickActionsResponse:
    """Get list of available quick actions.

    Quick actions are the main buttons shown in the Command Center
    for common tasks.
    """
    actions = get_quick_actions()

    return QuickActionsResponse(
        actions=[
            QuickActionResponse(
                id=action.id,
                label=action.label,
                icon=action.icon,
                description=action.description,
                intent=action.intent.value,
            )
            for action in actions
        ]
    )
