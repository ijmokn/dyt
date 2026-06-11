# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""API routes."""

from fastapi import APIRouter

from . import health, agent, chat, chat_history
from core.config import get_settings


# Create main API router with /api/v1 prefix
settings = get_settings()
api_router = APIRouter(prefix=settings.API_PREFIX)

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(agent.router)
api_router.include_router(chat.router)
api_router.include_router(chat_history.router)
