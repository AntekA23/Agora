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

router = APIRouter(prefix="/conversations", tags=["conversations"])


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

    # Get company context
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    company_context = {}
    if company:
        company_context = {
            "name": company.get("name", ""),
            "industry": company.get("industry", ""),
            "knowledge": company.get("knowledge", {}),
        }

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

    # Build conversation context from previous messages
    conversation_context = {
        "messages": conv.get("messages", [])[-10:],  # Last 10 messages
        "extracted_params": conv.get("context", {}).get("extracted_params", {}),
    }

    # Process message with conversation service
    response = await conversation_service.process_message(
        message=data.content,
        conversation_context=conversation_context,
        company_context=company_context,
    )

    # Create assistant message
    assistant_msg_id = str(ObjectId())
    assistant_message = {
        "id": assistant_msg_id,
        "role": "assistant",
        "content": response["content"],
        "message_type": "text",
        "actions": response.get("actions", []),
        "created_at": now,
    }

    # Update conversation title if first message
    title = conv.get("title", "Nowa rozmowa")
    if title == "Nowa rozmowa" and len(conv.get("messages", [])) == 0:
        title = conversation_service.generate_title(data.content)

    # Update conversation
    update_data: dict[str, Any] = {
        "$push": {"messages": {"$each": [user_message, assistant_message]}},
        "$set": {
            "updated_at": now,
            "last_message_at": now,
            "title": title,
            "context.extracted_params": response.get("extracted_params", {}),
            "context.last_intent": response.get("intent"),
            "context.can_execute": response.get("can_execute", False),
            "context.pending_tasks": response.get("tasks_to_create", []),
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
            content=response["content"],
            message_type="text",
            actions=response.get("actions", []),
            task_id=None,
            task_status=None,
            created_at=now,
        ),
        tasks_created=[],
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
