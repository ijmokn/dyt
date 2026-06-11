# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""FastAPI application factory and lifecycle management."""

import contextlib
import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.telemetry import AIProjectInstrumentor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from starlette.types import ASGIApp, Scope, Receive, Send

from core.config import get_settings
from core.exceptions import AIAgentException
from core.exception_handlers import (
    ai_agent_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from logging_config import configure_logging
from util import get_env_file_path

logger = logging.getLogger("azureaiapp")
env_file = None


class CorsPreflightMiddleware:
    """Handle CORS preflight (OPTIONS) requests at the ASGI level.

    This middleware intercepts OPTIONS requests and returns proper CORS headers
    before any other middleware processes them. This works around issues with
    VS Code dev tunnels and other reverse proxies that may not properly forward
    OPTIONS preflight requests to the application's CORSMiddleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Extract relevant headers from the preflight request
        origin = None
        request_headers = None
        request_method = None
        for header_name, header_value in scope.get("headers", []):
            name_lower = header_name.lower()
            if name_lower == b"origin":
                origin = header_value
            elif name_lower == b"access-control-request-headers":
                request_headers = header_value
            elif name_lower == b"access-control-request-method":
                request_method = header_value

        # Build response headers
        response_headers = [
            (b"access-control-max-age", b"600"),
        ]

        # Reflect or echo request headers (must be explicit when credentials are used)
        if request_headers:
            response_headers.append((b"access-control-allow-headers", request_headers))
        else:
            response_headers.append((b"access-control-allow-headers", b"*"))

        if request_method:
            response_headers.append((b"access-control-allow-methods", request_method))
        else:
            response_headers.append((b"access-control-allow-methods", b"GET, POST, PUT, DELETE, PATCH, OPTIONS"))

        if origin:
            # Reflect the origin (required when allow_credentials is true)
            response_headers.append((b"access-control-allow-origin", origin))
            response_headers.append((b"access-control-allow-credentials", b"true"))
            response_headers.append((b"vary", b"Origin"))
        else:
            response_headers.append((b"access-control-allow-origin", b"*"))

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": response_headers,
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })


async def setup_tracing(project_client: AIProjectClient, settings):
    """Set up Azure Monitor tracing if enabled."""
    if not settings.ENABLE_AZURE_MONITOR_TRACING:
        logger.info("Tracing is not enabled")
        return None
    
    logger.info("Tracing is enabled")
    
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
    except ModuleNotFoundError:
        logger.error("Required libraries for tracing not installed.")
        return None
    
    try:
        connection_string = await project_client.telemetry.get_application_insights_connection_string()
        
        if not connection_string:
            logger.error("Application Insights was not enabled for this project.")
            logger.error("Enable it via the 'Tracing' tab in your AI Foundry project page.")
            return None
        
        configure_azure_monitor(connection_string=connection_string)
        AIProjectInstrumentor().instrument(True)
        logger.info("Configured Application Insights for tracing.")
        return connection_string
    
    except Exception as e:
        logger.error(f"Failed to configure Application Insights: {e}")
        return None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - 直接使用 Azure SDK"""
    settings = get_settings()
    proj_endpoint = settings.AZURE_EXISTING_AIPROJECT_ENDPOINT
    agent_id = settings.AZURE_EXISTING_AGENT_ID
    agent_version_details = None
    
    try:
        async with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=proj_endpoint, credential=credential) as project_client,
        ):
            logger.info("Created AIProjectClient")

            # 设置监控
            connection_string = await setup_tracing(project_client, settings)
            if connection_string:
                app.state.application_insights_connection_string = connection_string

            # 获取 Agent 信息
            if agent_id:
                if agent_id.count(":") != 1:
                    raise RuntimeError(
                        "AZURE_EXISTING_AGENT_ID must be in the format 'agent_name:agent_version'."
                    )
                try: 
                    agent_name = agent_id.split(":")[0]
                    agent_version = agent_id.split(":")[1]
                    agent_version_details = await project_client.agents.get_version(
                        agent_name, 
                        agent_version
                    )
                    logger.info(f"Fetched agent, agent ID: {agent_version_details.id}")
                except Exception as e:
                    logger.error(f"Error fetching agent: {e}", exc_info=True)
                    raise

            if not agent_version_details:
                raise RuntimeError("Failed to fetch agent.")

            # 存储到 app.state
            app.state.ai_project = project_client
            app.state.agent_version_details = agent_version_details
            
            logger.info("Application startup complete")
            yield

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise RuntimeError(f"Error during startup: {e}")

    finally:
        logger.info("Closed AIProjectClient")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Initialize logging
    global logger, env_file
    settings = get_settings()
    logger = configure_logging(settings.APP_LOG_FILE)
    
    # Load environment variables
    env_file = get_env_file_path()
    load_dotenv(env_file)
    
    if env_file:
        logger.info(f"Loaded environment variables from {env_file}")
    else:
        logger.info("Loaded environment variables from default location")
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan
    )
    
    # Configure CORS - 允许所有来源
    # 同时使用 allow_origins 和 allow_origin_regex 以确保兼容性
    # allow_origins 中对特定域名做显式放行，allow_origin_regex 作为兜底
    cors_origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Conversation-Id", "X-Agent-Id", "X-User-Email"],
    )
    
    # Add CORS preflight middleware as the OUTERMOST layer
    # This ensures OPTIONS requests are handled even when dev tunnels
    # or reverse proxies interfere with standard CORS processing
    app.add_middleware(CorsPreflightMiddleware)
    
    # Register exception handlers
    app.add_exception_handler(AIAgentException, ai_agent_exception_handler) # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler) # type: ignore
    app.add_exception_handler(Exception, global_exception_handler)
    
    # Include API routes
    from api.routes import api_router
    app.include_router(api_router)
    
    logger.info("Application configuration complete")
    
    return app


app = create_app()
