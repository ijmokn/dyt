# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Agent-related Pydantic schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Agent metadata."""
    
    description: Optional[str] = Field(None, description="Agent description")
    version: Optional[str] = Field(None, description="Agent version")


class AgentResponse(BaseModel):
    """Response model for agent details."""
    
    name: str = Field(..., description="Agent name")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Agent metadata")
    agentPlaygroundUrl: str = Field(..., description="URL to agent playground")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ProductAssistant",
                "metadata": {
                    "description": "AI assistant for product information",
                    "version": "1.0"
                },
                "agentPlaygroundUrl": "https://ai.azure.com/..."
            }
        }
