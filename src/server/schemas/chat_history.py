# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Chat history related Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class ConversationListItem(BaseModel):
    """Single conversation item in the list."""
    
    id: str = Field(..., description="Conversation ID")
    agent_id: str = Field(..., description="Agent ID used in this conversation")
    title: str = Field(..., description="Conversation title")
    last_message: str = Field(..., description="Last message preview (truncated to 200 chars)")
    message_count: int = Field(..., description="Total number of messages in the conversation")
    status: str = Field(..., description="Conversation status (active/archived)")
    created_at: Optional[str] = Field(None, description="Creation timestamp in ISO 8601 format")
    updated_at: Optional[str] = Field(None, description="Last update timestamp in ISO 8601 format")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "conv_20260512143022_1",
                    "agent_id": "asst_abc123xyz",
                    "title": "产品功能咨询",
                    "last_message": "我们支持多种主流的语言模型,包括: GPT-4 Turbo、GPT-3.5 Turbo、Claude 3 Opus等。您可以根据具体场景选择合适的模型。",
                    "message_count": 8,
                    "status": "active",
                    "created_at": "2026-05-12T14:30:22.123456+00:00",
                    "updated_at": "2026-05-12T14:35:18.654321+00:00"
                },
                {
                    "id": "conv_20260512120000_1",
                    "agent_id": "asst_abc123xyz",
                    "title": "技术支持",
                    "last_message": "好的,我会继续跟进这个问题。如果您还有其他疑问,随时告诉我。",
                    "message_count": 15,
                    "status": "active",
                    "created_at": "2026-05-12T12:00:00.000000+00:00",
                    "updated_at": "2026-05-12T13:45:30.123456+00:00"
                },
                {
                    "id": "conv_20260511090000_1",
                    "agent_id": "asst_abc123xyz",
                    "title": "定价方案",
                    "last_message": "我们提供三种定价方案:基础版、专业版和企业版。基础版免费,专业版每月99元,企业版根据需求定制。",
                    "message_count": 6,
                    "status": "active",
                    "created_at": "2026-05-11T09:00:00.000000+00:00",
                    "updated_at": "2026-05-11T09:30:45.987654+00:00"
                }
            ]
        }


class ConversationCreateResponse(BaseModel):
    """Response model for creating a conversation."""
    
    id: str = Field(..., description="Newly created conversation ID (format: conv_YYYYMMDDHHmmss_userid)")
    title: str = Field(..., description="Conversation title")
    created_at: Optional[str] = Field(None, description="Creation timestamp in ISO 8601 format")
    updated_at: Optional[str] = Field(None, description="Last update timestamp in ISO 8601 format")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conv_20260512150000_1",
                "title": "新对话",
                "created_at": "2026-05-12T15:00:00.123456+00:00",
                "updated_at": "2026-05-12T15:00:00.123456+00:00"
            }
        }


class MessageSaveRequest(BaseModel):
    """Request model for saving a message."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    annotations: Optional[list] = Field(default=None, description="Optional message annotations (file citations, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "你好,我想了解一下产品的主要功能",
                "annotations": []
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    message: str = Field(..., description="Success message describing the operation result")

    class Config:
        json_schema_extra = {
            "examples": [
                {"message": "Message saved successfully"},
                {"message": "Conversation deleted successfully"}
            ]
        }
