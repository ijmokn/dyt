# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Application startup and resource initialization."""

import asyncio
import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

from logging_config import configure_logging
from util import get_env_file_path
from services.agent_creation_service import AgentCreationService
from services.evaluation_service import EvaluationService


# Load environment variables
env_file = get_env_file_path()
load_dotenv(env_file)

logger = configure_logging(os.getenv("APP_LOG_FILE", ""))

if env_file:
    logger.info(f"Loaded environment variables from {env_file}")
else:
    logger.info("Loaded environment variables from default location")


async def initialize_resources() -> None:
    """
    Initialize Azure AI resources on application startup.
    
    This function:
    1. Creates/retrieves the AI agent
    2. Sets up continuous evaluation
    3. Updates environment variables with agent ID
    
    Raises:
        RuntimeError: If resource initialization fails
    """
    proj_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    
    if not proj_endpoint:
        raise RuntimeError("AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable not set")
    
    try:
        async with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=proj_endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            # Get or create agent
            logger.info("Initializing agent...")
            agent_version_details = await AgentCreationService.get_or_create_agent(
                project_client,
                openai_client,
                credential
            )
            
            # Update environment variable
            os.environ["AZURE_EXISTING_AGENT_ID"] = agent_version_details.id
            logger.info(f"Agent ready (ID: {agent_version_details.id})")
            
            # Initialize continuous evaluation
            logger.info("Initializing continuous evaluation...")
            await EvaluationService.initialize_continuous_evaluation(
                project_client,
                openai_client,
                agent_version_details,
                credential
            )
            logger.info("Continuous evaluation initialized")
            
            logger.info("✓ All resources initialized successfully")
    
    except Exception as e:
        logger.error(f"Error initializing resources: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize resources: {e}")


def run_initialization() -> None:
    """
    Synchronous wrapper for resource initialization.
    
    Used by Gunicorn's on_starting hook.
    """
    try:
        asyncio.get_event_loop().run_until_complete(initialize_resources())
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise


if __name__ == "__main__":
    # For direct testing
    logger.info("Running resource initialization directly...")
    asyncio.run(initialize_resources())
    logger.info("Initialization complete")
