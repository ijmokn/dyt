# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Dependency injection for FastAPI routes."""

from typing import Optional

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

from openai import AsyncOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails
from sqlalchemy.orm import Session

from core.config import Settings, get_settings
from core.database import get_db


# ==================== Settings ====================

def get_app_settings() -> Settings:
    """Get application settings."""
    return get_settings()


# ==================== Azure AI Project ====================

def get_project_client(request: Request) -> AIProjectClient:
    """Get Azure AI Projects client from app state."""
    return request.app.state.ai_project


def get_agent_version_details(request: Request) -> AgentVersionDetails:
    """Get agent version details from app state."""
    return request.app.state.agent_version_details


def get_openai_client(request: Request) -> AsyncOpenAI:
    """Get OpenAI client from project client."""
    project_client = get_project_client(request)
    return project_client.get_openai_client()


# ==================== Authentication ====================

security = HTTPBasic()

username = os.getenv("WEB_APP_USERNAME")
password = os.getenv("WEB_APP_PASSWORD")
basic_auth_enabled = username and password


def verify_credentials(
    credentials: Optional[HTTPBasicCredentials] = Depends(security)
) -> None:
    """Verify basic authentication credentials."""
    if not basic_auth_enabled:
        return
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# ==================== Conversation ID ====================

def get_conversation_id_from_cookie(request: Request) -> Optional[str]:
    """
    Extract conversation ID from cookie.
    
    Args:
        request: FastAPI request
    
    Returns:
        Optional[str]: Conversation ID from cookie, or None
    """
    conversation_id = request.cookies.get('conversation_id')
    return conversation_id


# ==================== Database ====================

# Database session dependency is already provided by core.database.get_db
