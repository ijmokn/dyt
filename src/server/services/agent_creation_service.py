# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Agent creation and management service."""

import logging
import os
from typing import List, Optional

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    AgentVersionDetails,
    Tool,
    FileSearchTool,
    AzureAISearchTool,
)
from azure.core.credentials_async import AsyncTokenCredential
from openai import AsyncOpenAI


logger = logging.getLogger("azureaiapp")


class AgentCreationService:
    """Service for creating and managing AI agents."""
    
    @staticmethod
    def _get_file_path(file_name: str) -> str:
        """
        Get absolute file path for files directory.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Absolute path to the file
        """
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'product_info', file_name)
        )
    
    @staticmethod
    def list_files_in_files_directory() -> List[str]:
        """
        List all files in the files directory.
        
        Returns:
            List of file names
        """
        files_directory = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'product_info')
        )
        
        try:
            files = [
                f for f in os.listdir(files_directory)
                if os.path.isfile(os.path.join(files_directory, f))
            ]
            return files
        except FileNotFoundError:
            logger.warning(f"Files directory not found: {files_directory}")
            return []
    
    @staticmethod
    async def create_file_search_tool(openai_client: AsyncOpenAI) -> Optional[FileSearchTool]:
        """
        Create File Search tool by uploading files to vector store.
        
        Args:
            openai_client: OpenAI client
            
        Returns:
            FileSearchTool or None if failed
        """
        file_names = AgentCreationService.list_files_in_files_directory()
        
        if not file_names:
            logger.warning("No files found in files directory.")
            return None
        
        try:
            # Open file streams
            file_streams = [
                open(AgentCreationService._get_file_path(file_name), "rb")
                for file_name in file_names
            ]
            
            # Create vector store and upload files
            vector_store = await openai_client.vector_stores.create()
            await openai_client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=file_streams
            )
            
            logger.info(f"Files uploaded to vector store (id: {vector_store.id})")
            logger.info("File Search tool ready")
            
            return FileSearchTool(vector_store_ids=[vector_store.id])
        
        except FileNotFoundError as e:
            logger.error(f"Asset file not found: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize File Search tool: {e}")
            return None
    
    @staticmethod
    async def get_available_tool(
        project_client: AIProjectClient,
        openai_client: AsyncOpenAI,
        credentials: AsyncTokenCredential
    ) -> Optional[Tool]:
        """
        Get the appropriate tool for the agent (AI Search or File Search).
        
        Args:
            project_client: AI Project client
            openai_client: OpenAI client
            credentials: Azure credentials
            
        Returns:
            Tool or None
        """
        use_ai_search = os.environ.get('USE_AZURE_AI_SEARCH_SERVICE', 'false').lower() == 'true'
        conn_id = os.environ.get('SEARCH_CONNECTION_ID')
        search_index_name = os.environ.get('AZURE_AI_SEARCH_INDEX_NAME')
        
        # If AI Search is explicitly required
        if use_ai_search:
            if not search_index_name or not conn_id:
                logger.warning(
                    "USE_AZURE_AI_SEARCH_SERVICE is set to 'true' but required environment "
                    "variables are missing. Please ensure SEARCH_CONNECTION_ID and "
                    "AZURE_AI_SEARCH_INDEX_NAME are configured. Creating agent without search tool."
                )
                return None
            
            logger.info("AI Search is required. Attempting to create AI Search tool...")
            
            # Import here to avoid circular dependency
            from .search_tool_service import SearchToolService
            
            ai_search_tool = await SearchToolService.create_ai_search_tool(
                project_client,
                credentials
            )
            
            if ai_search_tool:
                return ai_search_tool
            else:
                logger.warning(
                    "AI Search initialization failed. Please check the logs above for details. "
                    "Creating agent without search tool."
                )
                return None
        
        # If AI Search is not required, use File Search
        logger.info("AI Search is not enabled. Using File Search tool.")
        return await AgentCreationService.create_file_search_tool(openai_client)
    
    @staticmethod
    async def create_agent(
        ai_project: AIProjectClient,
        openai_client: AsyncOpenAI,
        credentials: AsyncTokenCredential
    ) -> AgentVersionDetails:
        """
        Create a new AI agent with appropriate tools.
        
        Args:
            ai_project: AI Project client
            openai_client: OpenAI client
            credentials: Azure credentials
            
        Returns:
            AgentVersionDetails: Created agent
        """
        logger.info("Creating new agent with resources")
        
        tool = await AgentCreationService.get_available_tool(
            ai_project,
            openai_client,
            credentials
        )
        
        # Configure instructions based on tool type
        instructions = "You are a helpful assistant."
        tools: List[Tool] = []
        
        if tool:
            tools = [tool]
            if isinstance(tool, AzureAISearchTool):
                instructions = (
                    "Use AI Search always. "
                    "You must always provide citations for answers using the tool and "
                    "render them as: `【message_idx:search_idx†source】`. "
                    "Avoid to use base knowledge."
                )
            else:
                instructions = (
                    "Use File Search always with citations. Avoid to use base knowledge."
                )
        else:
            logger.warning("No search tool available. Creating agent without search tool.")
        
        # Create agent
        agent = await ai_project.agents.create_version(
            agent_name=os.environ["AZURE_AI_AGENT_NAME"],
            definition=PromptAgentDefinition(
                model=os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"],
                instructions=instructions,
                tools=tools,
            ),
        )
        
        logger.info(f"Created agent, agent ID: {agent.id}")
        return agent
    
    @staticmethod
    async def get_or_create_agent(
        project_client: AIProjectClient,
        openai_client: AsyncOpenAI,
        credentials: AsyncTokenCredential
    ) -> AgentVersionDetails:
        """
        Get existing agent or create a new one.
        
        Args:
            project_client: AI Project client
            openai_client: OpenAI client
            credentials: Azure credentials
            
        Returns:
            AgentVersionDetails: Agent details
        """
        agent_version_details: Optional[AgentVersionDetails] = None
        agent_name = None
        # Try to get by ID
        agent_id = os.environ.get("AZURE_EXISTING_AGENT_ID")
        if agent_id:
            try:
                agent_name = agent_id.split(":")[0]
                agent_version = agent_id.split(":")[1]
                agent_version_details = await project_client.agents.get_version(
                    agent_name,
                    agent_version
                )
                logger.info(f"Found agent by ID: {agent_version_details.id}")
                return agent_version_details
            except Exception as e:
                logger.warning(f"Could not retrieve agent by ID {agent_id}: {e}")
        
        # Try to get by name
        if not agent_version_details:
            try:
                agent_name = os.environ["AZURE_AI_AGENT_NAME"]
                logger.info(f"Retrieving agent by name: {agent_name}")
                agents = await project_client.agents.get(agent_name)
                agent_version_details = agents.versions.latest
                logger.info(f"Agent retrieved with ID: {agent_version_details.id}")
                return agent_version_details
            except Exception as e:
                logger.info(f"Agent name {agent_name} not found.")
        
        # Create new agent
        if not agent_version_details:
            agent_version_details = await AgentCreationService.create_agent(
                project_client,
                openai_client,
                credentials
            )
            # Update environment variable
            os.environ["AZURE_EXISTING_AGENT_ID"] = agent_version_details.id
        
        return agent_version_details
