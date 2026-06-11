# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Chat-related Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message to send to the agent",
        examples=["你好,我想了解一下这个产品的主要功能有哪些?"]
    )
    
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID. If None or empty, creates a new conversation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好,我想了解一下这个产品的主要功能有哪些?",
                "conversation_id": None
            }
        }


class MessageAnnotation(BaseModel):
    """Annotation for a message (e.g., file citations)."""
    
    label: str = Field(..., description="Label or title of the annotation")
    index: int = Field(..., description="Index position in the message")


class ChatMessage(BaseModel):
    """Individual chat message."""
    
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Message content")
    annotations: List[MessageAnnotation] = Field(default_factory=list, description="Message annotations")
    created_at: str = Field(default="", description="Message creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "assistant",
                "content": "根据产品手册,该产品的主要特点包括:智能对话、多语言支持、上下文记忆等功能。",
                "annotations": [
                    {
                        "label": "产品手册.pdf",
                        "index": 0
                    }
                ],
                "created_at": "2026-05-12T14:30:25.654321+00:00"
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    
    messages: List[ChatMessage] = Field(default_factory=list, description="List of chat messages")
    conversation_id: str = Field(..., description="Conversation ID")
    agent_id: str = Field(..., description="Agent ID")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_20260512143022_1",
                "agent_id": "asst_abc123xyz",
                "messages": [
                    {
                        "role": "user",
                        "content": "你好,我想了解一下产品功能",
                        "annotations": [],
                        "created_at": "2026-05-12T14:30:22.123456+00:00"
                    },
                    {
                        "role": "assistant",
                        "content": "您好!很高兴为您服务。我们的产品主要包含以下核心功能:\n\n1. 智能对话 - 基于大语言模型的自然交互\n2. 多语言支持 - 支持中文、英文、日语等\n3. 上下文记忆 - 记住整个对话历史\n4. 文件引用 - 可以引用和分析文档内容\n\n请问您对哪方面比较感兴趣?",
                        "annotations": [
                            {
                                "label": "产品手册.pdf",
                                "index": 0
                            }
                        ],
                        "created_at": "2026-05-12T14:30:25.654321+00:00"
                    },
                    {
                        "role": "user",
                        "content": "支持哪些语言模型?",
                        "annotations": [],
                        "created_at": "2026-05-12T14:31:10.123456+00:00"
                    },
                    {
                        "role": "assistant",
                        "content": "我们支持多种主流的语言模型,包括:\n\n• GPT-4 Turbo - 最强大的推理能力\n• GPT-3.5 Turbo - 高性价比选择\n• Claude 3 Opus - Anthropic 的旗舰模型\n• 本地部署模型 - 支持私有化部署\n\n您可以根据具体场景选择合适的模型。",
                        "annotations": [],
                        "created_at": "2026-05-12T14:31:13.987654+00:00"
                    }
                ]
            }
        }


class StreamEvent(BaseModel):
    """Server-Sent Event for streaming responses."""
    
    type: str = Field(..., description="Event type: message, completed_message, stream_end")
    content: Optional[str] = Field(None, description="Event content")
    annotations: Optional[List[MessageAnnotation]] = Field(default_factory=list, description="Annotations")

