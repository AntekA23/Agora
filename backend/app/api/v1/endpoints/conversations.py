"""Conversations API - Full chat interface with AI agents.

This endpoint provides a conversational interface where users can
chat naturally with Agora agents, maintaining context across messages.
"""

from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.conversation_service import conversation_service
from app.services.task_queue import get_task_queue
from app.services.assistant.router import assistant_router
from app.services.assistant.agent_state import AgentState
from app.services.assistant.user_preferences import UserPreferences, PreferencesService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _format_params_preview(params: dict) -> str:
    """Format extracted parameters for user preview."""
    if not params:
        return ""

    # Map param keys to Polish labels
    labels = {
        "topic": "Temat",
        "brief": "Temat",
        "post_type": "Typ",
        "platform": "Platforma",
        "copy_type": "Rodzaj tekstu",
        "client_name": "Klient",
        "style": "Styl",
        "tone": "Ton",
        "target_audience": "Grupa docelowa",
        "campaign_goal": "Cel kampanii",
        "salary_range": "Wynagrodzenie",
        "location": "Lokalizacja",
        "remote_option": "Praca zdalna",
        "due_date": "Termin płatności",
        "payment_terms": "Warunki płatności",
        "key_benefits": "Główne korzyści",
        "urgency": "Pilność",
    }

    # Map param values to Polish
    value_labels = {
        "post": "post",
        "story": "story",
        "reel": "reel",
        "carousel": "karuzela",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "ad": "reklama",
        "email": "email",
        "description": "opis produktu",
        "profesjonalny": "profesjonalny",
        "casualowy": "casualowy",
        "zabawny": "zabawny",
        "formalny": "formalny",
        "ogólna": "ogólna",
        "młodzi": "młodzi",
        "dorośli": "dorośli",
        "firmy": "firmy",
    }

    lines = ["📋 **Parametry:**"]
    for key, value in params.items():
        if value and key in labels:
            display_value = value_labels.get(value, value) if isinstance(value, str) else value
            lines.append(f"• {labels[key]}: {display_value}")

    return "\n".join(lines) if len(lines) > 1 else ""


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class MessageInput(BaseModel):
    """Input for sending a message."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Treść wiadomości",
    )
    use_state_machine: bool = Field(
        default=True,
        description="Use Phase 2 state machine flow (recommended)",
    )


class ActionInput(BaseModel):
    """Input for executing an action from a message."""

    action_id: str = Field(..., description="ID akcji do wykonania")
    params: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Response message from assistant."""

    id: str
    role: str
    content: str
    message_type: str = "text"
    actions: list[dict[str, str]] = Field(default_factory=list)
    task_id: str | None = None
    task_status: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Full conversation response."""

    id: str
    title: str
    status: str
    messages: list[MessageResponse]
    task_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    last_message_at: datetime | None


class ConversationListItem(BaseModel):
    """Conversation list item."""

    id: str
    title: str
    status: str
    message_count: int
    last_message_at: datetime | None
    created_at: datetime


class ConversationListResponse(BaseModel):
    """List of conversations."""

    conversations: list[ConversationListItem]
    total: int


class SendMessageResponse(BaseModel):
    """Response after sending a message."""

    user_message: MessageResponse
    assistant_message: MessageResponse
    tasks_created: list[str] = Field(default_factory=list)


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nowa rozmowa",
)
async def create_conversation(
    current_user: CurrentUser,
    db: Database,
) -> ConversationResponse:
    """Create a new conversation session."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    now = datetime.utcnow()
    conversation_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "title": "Nowa rozmowa",
        "status": "active",
        "messages": [],
        "context": {},
        "task_ids": [],
        "created_at": now,
        "updated_at": now,
        "last_message_at": None,
    }

    result = await db.conversations.insert_one(conversation_doc)

    return ConversationResponse(
        id=str(result.inserted_id),
        title="Nowa rozmowa",
        status="active",
        messages=[],
        task_ids=[],
        created_at=now,
        last_message_at=None,
    )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="Lista rozmów",
)
async def list_conversations(
    current_user: CurrentUser,
    db: Database,
    limit: int = 20,
    offset: int = 0,
) -> ConversationListResponse:
    """Get list of user's conversations."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    query = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "status": "active",
    }

    total = await db.conversations.count_documents(query)

    cursor = db.conversations.find(query).sort("updated_at", -1).skip(offset).limit(limit)
    conversations = await cursor.to_list(length=limit)

    return ConversationListResponse(
        conversations=[
            ConversationListItem(
                id=str(conv["_id"]),
                title=conv.get("title", "Rozmowa"),
                status=conv.get("status", "active"),
                message_count=len(conv.get("messages", [])),
                last_message_at=conv.get("last_message_at"),
                created_at=conv["created_at"],
            )
            for conv in conversations
        ],
        total=total,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Szczegóły rozmowy",
)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    db: Database,
) -> ConversationResponse:
    """Get a specific conversation with all messages."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    try:
        conv = await db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "company_id": current_user.company_id,
            "user_id": current_user.id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = [
        MessageResponse(
            id=msg.get("id", str(i)),
            role=msg["role"],
            content=msg["content"],
            message_type=msg.get("message_type", "text"),
            actions=msg.get("actions", []),
            task_id=msg.get("task_id"),
            task_status=msg.get("task_status"),
            created_at=msg.get("created_at", conv["created_at"]),
        )
        for i, msg in enumerate(conv.get("messages", []))
    ]

    return ConversationResponse(
        id=str(conv["_id"]),
        title=conv.get("title", "Rozmowa"),
        status=conv.get("status", "active"),
        messages=messages,
        task_ids=conv.get("task_ids", []),
        created_at=conv["created_at"],
        last_message_at=conv.get("last_message_at"),
    )


async def _process_with_state_machine(
    conv: dict,
    message: str,
    user_message: dict,
    company_context: dict,
    current_user: Any,
    db: Any,
    conversation_id: str,
) -> SendMessageResponse:
    """Process message using the Phase 2 state machine flow.

    Args:
        conv: Conversation document from MongoDB
        message: User's message content
        user_message: Pre-built user message dict
        company_context: Company info
        current_user: Current user
        db: Database connection
        conversation_id: Conversation ID

    Returns:
        SendMessageResponse
    """
    now = datetime.utcnow()
    context = conv.get("context", {})

    # Load or create agent state
    agent_state = AgentState.from_dict(conv.get("agent_state"))

    # Load user preferences for smart defaults (Phase 3)
    prefs_service = PreferencesService(db)
    user_preferences = await prefs_service.get_preferences(current_user.company_id)

    # Build conversation context with company knowledge for intelligent agent
    conversation_context = {
        "messages": conv.get("messages", [])[-10:],
        "extracted_params": context.get("extracted_params", {}),
        "last_intent": context.get("last_intent"),
        # Level 1 Intelligence: Include company context for LLM
        "company_context": company_context.get("formatted", ""),
    }

    # Process with state machine and preferences
    response, updated_state = await conversation_service.process_message_with_state(
        message=message,
        agent_state=agent_state,
        conversation_context=conversation_context,
        company_context=company_context,
        user_preferences=user_preferences,
    )

    # Update conversation title if first message
    title = conv.get("title", "Nowa rozmowa")
    if title == "Nowa rozmowa" and len(conv.get("messages", [])) == 0:
        title = conversation_service.generate_title(message)

    created_task_ids: list[str] = []
    assistant_msg_id = str(ObjectId())

    # Handle task execution if ready
    if response.get("can_execute") and response.get("tasks_to_create"):
        for task_info in response.get("tasks_to_create", []):
            task_doc = {
                "company_id": current_user.company_id,
                "user_id": current_user.id,
                "department": task_info.get("department", "marketing"),
                "agent": task_info.get("agent", ""),
                "type": task_info.get("type", ""),
                "input": task_info.get("input", {}),
                "output": None,
                "status": "pending",
                "error": None,
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
                "conversation_id": conversation_id,
            }

            result = await db.tasks.insert_one(task_doc)
            task_id = str(result.inserted_id)
            created_task_ids.append(task_id)

            # Enqueue task
            try:
                pool = await get_task_queue()
                agent = task_info.get("agent", "")
                if agent == "instagram_specialist":
                    await pool.enqueue_job("process_instagram_task", task_id, task_info.get("input", {}))
                elif agent == "copywriter":
                    await pool.enqueue_job("process_copywriter_task", task_id, task_info.get("input", {}))
            except Exception:
                pass

        # Update agent state to executing
        updated_state.task_ids = created_task_ids
        updated_state.transition("confirmed")

        # Record task completion to learn user preferences (Phase 3)
        params = response.get("extracted_params", {})
        if params:
            await prefs_service.record_task_completion(current_user.company_id, params)

        assistant_message = {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": response["content"],
            "message_type": "task_created",
            "task_id": created_task_ids[0] if created_task_ids else None,
            "task_status": "pending",
            "actions": [],
            "created_at": now,
        }
    else:
        # Normal response - gathering info or confirming
        assistant_message = {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": response["content"],
            "message_type": "text",
            "actions": response.get("actions", []),
            "created_at": now,
        }

    # Update conversation with new state
    update_data: dict[str, Any] = {
        "$push": {
            "messages": {"$each": [user_message, assistant_message]},
        },
        "$set": {
            "updated_at": now,
            "last_message_at": now,
            "title": title,
            # Save agent state to MongoDB
            "agent_state": updated_state.to_dict(),
            # Also update legacy context for compatibility
            "context.extracted_params": response.get("extracted_params", {}),
            "context.last_intent": response.get("intent"),
            "context.awaiting_recommendations": response.get("awaiting_recommendations", False),
        },
    }

    if created_task_ids:
        update_data["$push"]["task_ids"] = {"$each": created_task_ids}

    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        update_data,
    )

    return SendMessageResponse(
        user_message=MessageResponse(
            id=user_message["id"],
            role="user",
            content=message,
            message_type="text",
            actions=[],
            task_id=None,
            task_status=None,
            created_at=now,
        ),
        assistant_message=MessageResponse(
            id=assistant_msg_id,
            role="assistant",
            content=assistant_message["content"],
            message_type=assistant_message.get("message_type", "text"),
            actions=assistant_message.get("actions", []),
            task_id=created_task_ids[0] if created_task_ids else None,
            task_status="pending" if created_task_ids else None,
            created_at=now,
        ),
        tasks_created=created_task_ids,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    summary="Wyślij wiadomość",
)
async def send_message(
    conversation_id: str,
    data: MessageInput,
    current_user: CurrentUser,
    db: Database,
) -> SendMessageResponse:
    """Send a message in a conversation and get a response."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get conversation
    try:
        conv = await db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "company_id": current_user.company_id,
            "user_id": current_user.id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Get comprehensive company context for intelligent agent
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    company_context = {}
    company_context_str = ""  # Formatted string for LLM

    if company:
        company_context = {
            "name": company.get("name", ""),
            "industry": company.get("industry", ""),
            "knowledge": company.get("knowledge", {}),
        }

        # Build formatted context string for intelligent agent
        context_parts = []
        if company.get("name"):
            context_parts.append(f"Firma: {company['name']}")
        if company.get("description"):
            context_parts.append(f"Opis: {company['description']}")
        if company.get("industry"):
            context_parts.append(f"Branża: {company['industry']}")

        # Brand settings
        brand = company.get("brand_settings", {})
        if brand:
            if brand.get("tone"):
                context_parts.append(f"Ton komunikacji: {brand['tone']}")
            if brand.get("target_audience"):
                context_parts.append(f"Grupa docelowa: {brand['target_audience']}")
            if brand.get("values") and isinstance(brand["values"], list):
                context_parts.append(f"Wartości: {', '.join(brand['values'])}")

        # Knowledge
        knowledge = company.get("knowledge", {})
        if knowledge:
            products = knowledge.get("products", [])
            if products:
                product_names = [p.get("name", "") for p in products[:5] if p.get("name")]
                if product_names:
                    context_parts.append(f"Produkty: {', '.join(product_names)}")

            services = knowledge.get("services", [])
            if services:
                service_names = [s.get("name", "") for s in services[:5] if s.get("name")]
                if service_names:
                    context_parts.append(f"Usługi: {', '.join(service_names)}")

        company_context_str = "\n".join(context_parts) if context_parts else ""
        company_context["formatted"] = company_context_str

    now = datetime.utcnow()

    # Create user message
    user_msg_id = str(ObjectId())
    user_message = {
        "id": user_msg_id,
        "role": "user",
        "content": data.content,
        "message_type": "text",
        "created_at": now,
    }

    # Use state machine flow (Phase 2) if enabled
    if data.use_state_machine:
        return await _process_with_state_machine(
            conv=conv,
            message=data.content,
            user_message=user_message,
            company_context=company_context,
            current_user=current_user,
            db=db,
            conversation_id=conversation_id,
        )

    # Legacy flow (Phase 1) - kept for backward compatibility
    # Build conversation context from previous messages
    # CRITICAL: Include all fields needed by interpret() for context preservation
    context = conv.get("context", {})
    awaiting_recommendations = context.get("awaiting_recommendations", False)

    conversation_context = {
        "messages": conv.get("messages", [])[-10:],  # Last 10 messages
        "extracted_params": context.get("extracted_params", {}),
        "recommendations_answered": context.get("recommendations_answered", False),
        # CRITICAL for followup detection in interpret():
        "last_intent": context.get("last_intent"),
        "awaiting_recommendations": awaiting_recommendations,
    }

    # Check if user clicked "use_defaults" button
    use_defaults = data.content.strip().lower() in ["[użyj domyślnych]", "użyj domyślnych"]

    if awaiting_recommendations:
        # User is responding to recommendation questions
        conversation_context["recommendations_answered"] = True

        last_intent = context.get("last_intent")

        if use_defaults:
            # User wants to skip recommendations - apply defaults
            if last_intent:
                from app.services.assistant import Intent
                try:
                    intent_enum = Intent(last_intent)
                    default_params = assistant_router.get_default_params(intent_enum)
                    # Merge defaults with existing params
                    conversation_context["extracted_params"] = {
                        **conversation_context["extracted_params"],
                        **default_params,
                    }
                except ValueError:
                    pass
        else:
            # User provided actual answer - extract params from their response
            if last_intent:
                from app.services.assistant import Intent
                try:
                    intent_enum = Intent(last_intent)
                    # Extract new params from user's response (e.g., "casualowy")
                    # Pass is_followup=True to skip topic extraction for short responses
                    new_params = assistant_router.extract_params_from_message(
                        data.content, intent_enum, is_followup=True
                    )
                    # Merge with existing params - user's response takes priority
                    conversation_context["extracted_params"] = {
                        **conversation_context["extracted_params"],
                        **new_params,
                    }
                except ValueError:
                    pass

        # CRITICAL: Tell conversation service to preserve the original intent
        conversation_context["preserve_intent"] = True
        conversation_context["original_intent"] = last_intent

    # Process message with conversation service
    response = await conversation_service.process_message(
        message=data.content,
        conversation_context=conversation_context,
        company_context=company_context,
    )

    # QUICK FIX: If we were awaiting recommendations and interpreter lost context,
    # restore it from conversation context
    if awaiting_recommendations and not use_defaults:
        last_intent = context.get("last_intent")
        if last_intent:
            # Check if interpret() lost the context (low confidence or unknown intent)
            response_intent = response.get("intent", "unknown")
            response_confidence = response.get("confidence", 0)

            if response_intent == "unknown" or response_confidence < 0.5:
                from app.services.assistant import Intent

                # Restore original intent and merged params
                response["intent"] = last_intent
                response["extracted_params"] = conversation_context["extracted_params"]
                response["can_execute"] = True  # We have all we need
                response["awaiting_recommendations"] = False

                # Build tasks to create based on restored intent
                try:
                    intent_enum = Intent(last_intent)
                    # Create a mock IntentResult-like object
                    class MockIntentResult:
                        def __init__(self, intent, confidence):
                            self.intent = intent
                            self.confidence = confidence

                    mock_result = MockIntentResult(intent_enum, 1.0)
                    exec_response = conversation_service._build_execution_response(
                        mock_result,
                        response["extracted_params"],
                        company_context,
                    )
                    response["tasks_to_create"] = exec_response.get("tasks_to_create", [])
                except (ValueError, Exception):
                    response["tasks_to_create"] = []

    # Update conversation title if first message
    title = conv.get("title", "Nowa rozmowa")
    if title == "Nowa rozmowa" and len(conv.get("messages", [])) == 0:
        title = conversation_service.generate_title(data.content)

    created_task_ids: list[str] = []
    assistant_msg_id = str(ObjectId())

    # AUTO-EXECUTE: If we can execute, create tasks immediately
    if response.get("can_execute") and response.get("tasks_to_create"):
        pending_tasks = response.get("tasks_to_create", [])

        # Create tasks
        for task_info in pending_tasks:
            task_doc = {
                "company_id": current_user.company_id,
                "user_id": current_user.id,
                "department": task_info.get("department", "marketing"),
                "agent": task_info.get("agent", ""),
                "type": task_info.get("type", ""),
                "input": task_info.get("input", {}),
                "output": None,
                "status": "pending",
                "error": None,
                "created_at": now,
                "updated_at": now,
                "completed_at": None,
                "conversation_id": conversation_id,
            }

            result = await db.tasks.insert_one(task_doc)
            task_id = str(result.inserted_id)
            created_task_ids.append(task_id)

            # Enqueue task
            try:
                pool = await get_task_queue()
                agent = task_info.get("agent", "")
                if agent == "instagram_specialist":
                    await pool.enqueue_job("process_instagram_task", task_id, task_info.get("input", {}))
                elif agent == "copywriter":
                    await pool.enqueue_job("process_copywriter_task", task_id, task_info.get("input", {}))
            except Exception:
                pass

        # Build response with params preview
        params = response.get("extracted_params", {})
        params_preview = _format_params_preview(params)

        content = f"Rozumiem! Zaczynam generowanie.\n\n{params_preview}\n\n⏳ Zadanie w toku..."

        assistant_message = {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": content,
            "message_type": "task_created",
            "task_id": created_task_ids[0] if created_task_ids else None,
            "task_status": "pending",
            "actions": [],  # No actions needed - auto-executing
            "created_at": now,
        }

        # Update conversation - clear pending tasks since we executed
        update_data: dict[str, Any] = {
            "$push": {
                "messages": {"$each": [user_message, assistant_message]},
                "task_ids": {"$each": created_task_ids},
            },
            "$set": {
                "updated_at": now,
                "last_message_at": now,
                "title": title,
                "context.extracted_params": {},
                "context.last_intent": response.get("intent"),
                "context.can_execute": False,
                "context.pending_tasks": [],
            },
        }
    else:
        # Normal response - need more info or just chatting
        assistant_message = {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": response["content"],
            "message_type": "text",
            "actions": response.get("actions", []),
            "created_at": now,
        }

        # If response is awaiting recommendations, save flag
        # If we previously answered, keep that flag True
        recommendations_answered = (
            conversation_context.get("recommendations_answered", False)
            or (awaiting_recommendations and not response.get("awaiting_recommendations", False))
        )

        update_data = {
            "$push": {"messages": {"$each": [user_message, assistant_message]}},
            "$set": {
                "updated_at": now,
                "last_message_at": now,
                "title": title,
                "context.extracted_params": response.get("extracted_params", {}),
                "context.last_intent": response.get("intent"),
                "context.can_execute": response.get("can_execute", False),
                "context.pending_tasks": response.get("tasks_to_create", []),
                "context.awaiting_recommendations": response.get("awaiting_recommendations", False),
                "context.recommendations_answered": recommendations_answered,
            },
        }

    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        update_data,
    )

    return SendMessageResponse(
        user_message=MessageResponse(
            id=user_msg_id,
            role="user",
            content=data.content,
            message_type="text",
            actions=[],
            task_id=None,
            task_status=None,
            created_at=now,
        ),
        assistant_message=MessageResponse(
            id=assistant_msg_id,
            role="assistant",
            content=assistant_message["content"],
            message_type=assistant_message.get("message_type", "text"),
            actions=assistant_message.get("actions", []),
            task_id=created_task_ids[0] if created_task_ids else None,
            task_status="pending" if created_task_ids else None,
            created_at=now,
        ),
        tasks_created=created_task_ids,
    )


@router.post(
    "/{conversation_id}/execute",
    response_model=SendMessageResponse,
    summary="Wykonaj zaplanowane zadania",
)
async def execute_pending_tasks(
    conversation_id: str,
    current_user: CurrentUser,
    db: Database,
) -> SendMessageResponse:
    """Execute the pending tasks in the conversation."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get conversation
    try:
        conv = await db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "company_id": current_user.company_id,
            "user_id": current_user.id,
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    context = conv.get("context", {})
    pending_tasks = context.get("pending_tasks", [])

    if not pending_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brak zadań do wykonania",
        )

    now = datetime.utcnow()
    created_task_ids = []

    # Create tasks
    for task_info in pending_tasks:
        task_doc = {
            "company_id": current_user.company_id,
            "user_id": current_user.id,
            "department": task_info.get("department", "marketing"),
            "agent": task_info.get("agent", ""),
            "type": task_info.get("type", ""),
            "input": task_info.get("input", {}),
            "output": None,
            "status": "pending",
            "error": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "conversation_id": conversation_id,
        }

        result = await db.tasks.insert_one(task_doc)
        task_id = str(result.inserted_id)
        created_task_ids.append(task_id)

        # Enqueue task
        try:
            pool = await get_task_queue()
            agent = task_info.get("agent", "")
            if agent == "instagram_specialist":
                await pool.enqueue_job("process_instagram_task", task_id, task_info.get("input", {}))
            elif agent == "copywriter":
                await pool.enqueue_job("process_copywriter_task", task_id, task_info.get("input", {}))
        except Exception:
            pass  # Task will be processed later

    # Create assistant message about task creation
    assistant_msg_id = str(ObjectId())
    task_count = len(created_task_ids)
    content = f"Generuję {'zadanie' if task_count == 1 else f'{task_count} zadania'}... ⏳\n\nMożesz śledzić postęp w zakładce Zadania."

    assistant_message = {
        "id": assistant_msg_id,
        "role": "assistant",
        "content": content,
        "message_type": "task_created",
        "task_ids": created_task_ids,
        "actions": [
            {"id": "view_tasks", "label": "Zobacz zadania", "type": "primary"},
        ],
        "created_at": now,
    }

    # Update conversation
    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {"messages": assistant_message, "task_ids": {"$each": created_task_ids}},
            "$set": {
                "updated_at": now,
                "last_message_at": now,
                "context.pending_tasks": [],
                "context.can_execute": False,
            },
        },
    )

    return SendMessageResponse(
        user_message=MessageResponse(
            id=str(ObjectId()),
            role="user",
            content="[Wykonaj]",
            message_type="action",
            actions=[],
            task_id=None,
            task_status=None,
            created_at=now,
        ),
        assistant_message=MessageResponse(
            id=assistant_msg_id,
            role="assistant",
            content=content,
            message_type="task_created",
            actions=[{"id": "view_tasks", "label": "Zobacz zadania", "type": "primary"}],
            task_id=created_task_ids[0] if created_task_ids else None,
            task_status="pending",
            created_at=now,
        ),
        tasks_created=created_task_ids,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Usuń rozmowę",
)
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser,
    db: Database,
) -> None:
    """Archive/delete a conversation."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    result = await db.conversations.update_one(
        {
            "_id": ObjectId(conversation_id),
            "company_id": current_user.company_id,
            "user_id": current_user.id,
        },
        {"$set": {"status": "archived", "updated_at": datetime.utcnow()}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
