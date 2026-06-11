# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Health check schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Health status: ok, degraded, unhealthy")
    version: Optional[str] = Field(None, description="API version")
    details: Optional[Dict[str, str]] = Field(default_factory=dict, description="Additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "details": {
                    "ai_project": "connected",
                    "agent": "ready"
                }
            }
        }
