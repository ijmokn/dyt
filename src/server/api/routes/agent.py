# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Agent information routes."""

import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from azure.ai.projects.models import AgentVersionDetails

from api.dependencies import get_app_settings, get_agent_version_details
from util import encode_project_resource_id


logger = logging.getLogger("azureaiapp")
router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("")
async def get_agent(
    agent: AgentVersionDetails = Depends(get_agent_version_details),
    settings = Depends(get_app_settings)
):
    """Get agent information."""
    agent_name = settings.agent_name
    agent_version = settings.agent_version
    agent_playground_url = f"https://ai.azure.com/nextgen/r/{encode_project_resource_id(settings.AZURE_EXISTING_AIPROJECT_RESOURCE_ID)}/build/agents/{quote(agent_name)}/build?version={agent_version}"
    
    # Filter metadata to only include string values
    filtered_metadata = {}
    if agent.metadata:
        for k, v in agent.metadata.items():
            if v is not None and not isinstance(v, (list, dict)):
                filtered_metadata[k] = str(v)
    
    return JSONResponse(content={
        "name": agent.name, 
        "metadata": filtered_metadata,
        "agentPlaygroundUrl": agent_playground_url
    })
