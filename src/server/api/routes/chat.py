# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Chat routes - 使用 Azure SDK + ORM 数据库"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails
from sqlalchemy.orm import Session

from api.dependencies import (
    get_app_settings,
    get_project_client,
    get_agent_version_details,
    get_conversation_id_from_cookie,
    verify_credentials
)
from core.database import get_db
from models import Conversation as DBConversation, Message as DBMessage
from schemas.chat import ChatRequest
from core.security import verify_basic_auth
from services.chat_service import ChatService
from services.user_service import get_or_create_user

logger = logging.getLogger("azureaiapp")
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    user_email: str = Header(..., alias="X-User-Email", description="User email address"),
    project_client: AIProjectClient = Depends(get_project_client),
    agent: AgentVersionDetails = Depends(get_agent_version_details),
    conversation_id: Optional[str] = Depends(get_conversation_id_from_cookie),
    db: Session = Depends(get_db),
    _auth = Depends(verify_basic_auth) if get_app_settings().basic_auth_enabled else None,
):
    """
    Chat endpoint - 使用 Azure SDK 流式响应，ORM 数据库保存
    
    Args:
        request: FastAPI request
        chat_request: Chat request body
        user_email: User email from X-User-Email header
        project_client: Azure AI Project client
        agent: Agent version details
        conversation_id: Conversation ID from cookie (optional)
        db: Database session
    
    Returns:
        StreamingResponse: Server-Sent Events stream
    """
    logger.info(f"Chat request from user: {user_email}")
    
    # 优先使用请求体中的 conversation_id，如果没有则使用 cookie 中的
    # 这样可以正确处理"新对话"场景（前端传 null）
    effective_conversation_id = chat_request.conversation_id if chat_request.conversation_id else conversation_id
    logger.info(f"Effective conversation_id: {effective_conversation_id} (from body: {chat_request.conversation_id}, from cookie: {conversation_id})")
    
    # 准备 trace context
    carrier = {}
    TraceContextTextMapPropagator().inject(carrier)
    
    # 使用 Azure 的 conversation management
    async with project_client.get_openai_client() as openai_client:
        azure_conversation = None
        
        # 如果有 conversation_id，尝试获取现有 conversation
        # 注意：不依赖 agent_id cookie，因为前端"新对话"操作会清除 cookie
        if effective_conversation_id:
            try:
                logger.info(f"Attempting to retrieve existing conversation: {effective_conversation_id}")
                azure_conversation = await openai_client.conversations.retrieve(
                    conversation_id=effective_conversation_id
                )
                logger.info(f"Retrieved existing Azure conversation: {azure_conversation.id}")
            except Exception as e:
                logger.warning(f"Failed to retrieve Azure conversation {effective_conversation_id}: {e}")
        
        # 如果没有获取到，创建新的 Azure conversation
        if not azure_conversation:
            try:
                logger.info("Creating new Azure conversation")
                azure_conversation = await openai_client.conversations.create()
                logger.info(f"Created new Azure conversation: {azure_conversation.id}")
                # 统一使用 Azure 生成的 conversation ID
                effective_conversation_id = azure_conversation.id
            except Exception as e:
                logger.error(f"Failed to create conversation: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create conversation: {e}")
    
    # effective_conversation_id 此时必定有值（要么来自前端，要么 Azure 新建）
    assert effective_conversation_id is not None, "conversation_id must not be None"
    
    # 在数据库中创建或更新 conversation 记录
    is_new_conversation = False
    try:
        user_id = get_or_create_user(db, user_email)
        
        db_conversation = db.query(DBConversation).filter(
            DBConversation.id == effective_conversation_id
        ).first()
        
        if not db_conversation:
            # 创建新的 conversation
            title = chat_request.message[:50] if len(chat_request.message) > 50 else chat_request.message
            now = datetime.now(timezone.utc)
            
            db_conversation = DBConversation(
                id=effective_conversation_id,
                user_id=user_id,
                agent_id=agent.id,
                title=title,
                last_message=chat_request.message[:200],
                message_count=0,
                status="active",
                created_at=now,
                updated_at=now
            )
            db.add(db_conversation)
            db.commit()
            is_new_conversation = True
            logger.info(f"Created conversation in database: {effective_conversation_id}")
        else:
            logger.info(f"Using existing conversation: {effective_conversation_id}")
    
    except Exception as e:
        logger.error(f"Failed to ensure conversation in database: {e}")
        db.rollback()
    
    # 设置 SSE headers
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "X-Conversation-Id": effective_conversation_id,
        "X-Agent-Id": agent.id
    }
    
    logger.info(f"Starting streaming response for conversation {effective_conversation_id}")
    
    # 创建流式响应
    response = StreamingResponse(
        ChatService.stream_agent_response(
            agent=agent,
            conversation_id=effective_conversation_id,
            user_message=chat_request.message,
            project_client=project_client,
            carrier=carrier,
            db=db
        ),
        headers=headers
    )
    
    # 设置 cookies
    response.set_cookie("conversation_id", effective_conversation_id)
    response.set_cookie("agent_id", agent.id)
    
    return response
