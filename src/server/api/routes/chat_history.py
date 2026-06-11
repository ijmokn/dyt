# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Chat history routes for conversation management."""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails

from schemas.chat import ChatMessage, ChatHistoryResponse, MessageAnnotation
from schemas.chat_history import (
    ConversationListItem,
    ConversationCreateResponse,
    MessageSaveRequest,
    SuccessResponse
)
from core.config import Settings
from core.security import verify_basic_auth
from core.database import get_db
from api.dependencies import (
    get_app_settings,
    get_project_client,
    get_agent_version_details
)
from models import User, Conversation, Message
from services.user_service import get_or_create_user

logger = logging.getLogger("azureaiapp")
router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "",
    response_model=List[ConversationListItem],
    summary="Get conversations list",
    description="Retrieve list of conversations for the current user"
)
async def get_conversations(
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Search query"),
    settings: Settings = Depends(get_app_settings),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
    db: Session = Depends(get_db)
) -> List[ConversationListItem]:
    """Get list of conversations for a user."""
    
    # Query with ORM
    query = db.query(Conversation).join(User).filter(User.email == user_email)
    
    # Add search filter if provided
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            (Conversation.title.ilike(search_pattern)) | 
            (Conversation.last_message.ilike(search_pattern))
        )
    
    # Apply ordering and pagination
    conversations = (
        query.order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to response model
    return [
        ConversationListItem(
            id=conv.id,  # type: ignore
            agent_id=conv.agent_id,  # type: ignore
            title=conv.title or "Untitled",  # type: ignore
            last_message=conv.last_message or "",  # type: ignore
            message_count=conv.message_count or 0,  # type: ignore
            status=conv.status or "active",  # type: ignore
            created_at=conv.created_at.isoformat() if conv.created_at is not None else None,  # type: ignore
            updated_at=conv.updated_at.isoformat() if conv.updated_at is not None else None,  # type: ignore
        )
        for conv in conversations
    ]


@router.get(
    "/{conversation_id}",
    response_model=ChatHistoryResponse,
    summary="Get conversation details",
    description="Retrieve complete message history for a specific conversation"
)
async def get_conversation_detail(
    conversation_id: str,
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    settings: Settings = Depends(get_app_settings),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
    db: Session = Depends(get_db)
):
    """Get detailed message history for a conversation."""
    
    # Check if user owns this conversation
    conversation = (
        db.query(Conversation)
        .join(User)
        .filter(User.email == user_email, Conversation.id == conversation_id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(
            status_code=403, 
            detail="Access denied: User does not own this conversation"
        )
    
    # Get messages with pagination
    messages_query = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    
    messages = messages_query.all()
    
    # Convert to response model
    chat_messages = []
    for msg in messages:
        annotations = []
        # Check if annotations exist and is a list
        if msg.annotations is not None and isinstance(msg.annotations, list):  # type: ignore
            annotations = [
                MessageAnnotation(**ann) 
                for ann in msg.annotations  # type: ignore
                if isinstance(ann, dict)
            ]
        
        chat_messages.append(ChatMessage(
            role=msg.role,  # type: ignore
            content=msg.content,  # type: ignore
            annotations=annotations,
            created_at=msg.created_at.isoformat() if msg.created_at is not None else ""  # type: ignore
        ))
    
    return ChatHistoryResponse(
        conversation_id=conversation_id,
        agent_id=conversation.agent_id,  # type: ignore
        messages=chat_messages
    )


@router.post(
    "",
    response_model=ConversationCreateResponse,
    summary="Create new conversation",
    description="Create a new conversation for the current user"
)
async def create_conversation(
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    title: str = Query(default="New Conversation", description="Conversation title"),
    agent_id: str = Query(default="", description="Agent ID"),
    settings: Settings = Depends(get_app_settings),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
    project_client: AIProjectClient = Depends(get_project_client),
    agent: AgentVersionDetails = Depends(get_agent_version_details),
    db: Session = Depends(get_db)
) -> ConversationCreateResponse:
    """Create a new conversation."""
    
    # Get or create user
    user_id = get_or_create_user(db, user_email)
    
    # 使用 Azure 创建 conversation，获得真正的 Azure conversation ID
    async with project_client.get_openai_client() as openai_client:
        azure_conversation = await openai_client.conversations.create()
        conversation_id = azure_conversation.id
        logger.info(f"Created Azure conversation: {conversation_id}")
    
    now = datetime.now(timezone.utc)
    new_conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        agent_id=agent.id,
        title=title,
        last_message="",
        message_count=0,
        status="active",
        created_at=now,
        updated_at=now
    )
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return ConversationCreateResponse(
        id=new_conversation.id,  # type: ignore
        title=new_conversation.title or title,  # type: ignore
        created_at=new_conversation.created_at.isoformat() if new_conversation.created_at is not None else None,  # type: ignore
        updated_at=new_conversation.updated_at.isoformat() if new_conversation.updated_at is not None else None,  # type: ignore
    )


@router.post(
    "/{conversation_id}/message",
    response_model=SuccessResponse,
    summary="Save message to conversation",
    description="Save a message to the conversation history"
)
async def save_message(
    conversation_id: str,
    message_data: MessageSaveRequest,
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    settings: Settings = Depends(get_app_settings),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Save a message to conversation history."""
    
    # Check if user owns this conversation
    conversation = (
        db.query(Conversation)
        .join(User)
        .filter(User.email == user_email, Conversation.id == conversation_id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create new message
    now = datetime.now(timezone.utc)
    new_message = Message(
        conversation_id=conversation_id,
        role=message_data.role,
        content=message_data.content,
        annotations=message_data.annotations if message_data.annotations else [],
        created_at=now,
        updated_at=now
    )
    
    db.add(new_message)
    
    # Update conversation
    conversation.last_message = message_data.content[:200]  # type: ignore
    conversation.message_count = conversation.message_count + 1  # type: ignore
    conversation.updated_at = now  # type: ignore
    
    db.commit()
    
    return SuccessResponse(message="Message saved successfully")


@router.delete(
    "/{conversation_id}",
    response_model=SuccessResponse,
    summary="Delete conversation",
    description="Delete a conversation and all its messages"
)
async def delete_conversation(
    conversation_id: str,
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    settings: Settings = Depends(get_app_settings),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete a conversation."""
    
    # Check if user owns this conversation
    conversation = (
        db.query(Conversation)
        .join(User)
        .filter(User.email == user_email, Conversation.id == conversation_id)
        .first()
    )
    
    if not conversation:
        raise HTTPException(
            status_code=404, 
            detail="Conversation not found or access denied"
        )
    
    # Delete conversation (cascade will delete messages)
    db.delete(conversation)
    db.commit()
    
    return SuccessResponse(message="Conversation deleted successfully")
