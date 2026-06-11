# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Health check routes."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.config import get_settings


logger = logging.getLogger("azureaiapp")
router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(request: Request):
    """健康检查端点 - 检查 Azure SDK 连接和 Agent 状态"""
    
    settings = get_settings()
    details = {}
    
    # 检查 Azure Project Client 是否已初始化
    if hasattr(request.app.state, "ai_project"):
        details["ai_project"] = "connected"
    
    # 检查 Agent 是否已加载
    if hasattr(request.app.state, "agent_version_details"):
        details["agent"] = "ready"
    
    # 检查 Application Insights 连接
    if hasattr(request.app.state, "application_insights_connection_string"):
        details["tracing"] = "enabled"
    
    return JSONResponse(
        content={
            "status": "ok",
            "version": settings.APP_VERSION,
            "details": details
        }
    )
