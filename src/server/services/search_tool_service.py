# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Azure AI Search tool service."""

import logging
import os
from typing import Dict, List, Optional, Callable

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    Tool,
    AzureAISearchTool,
    AzureAISearchToolResource,
    AISearchIndexResource,
    ConnectionType,
)
from azure.core.credentials_async import AsyncTokenCredential
from openai import AsyncAzureOpenAI


logger = logging.getLogger("azureaiapp")


class ResourceStatus:
    """Resource status enumeration."""
    CREATED = "created"
    EXISTING = "existing"
    FAILED = "failed"


class SearchToolService:
    """Service for creating and managing Azure AI Search tool."""
    
    @staticmethod
    async def _execute_step(
        step_name: str,
        step_func: Callable,
        resources: Dict,
        steps_order: List[str]
    ) -> None:
        """
        Execute a step and check that the prior step succeeded.
        
        Args:
            step_name: Name of the step
            step_func: Async function to execute
            resources: Dictionary to track resource status
            steps_order: List of step names in order
        """
        # Check if prior step failed
        step_index = steps_order.index(step_name)
        if step_index > 0:
            prior_step = steps_order[step_index - 1]
            prior_status = resources.get(prior_step)
            if prior_status == ResourceStatus.FAILED:
                logger.error(
                    f"Skipping step '{step_name}' because prior step '{prior_step}' failed."
                )
                resources[step_name] = ResourceStatus.FAILED
                return
        
        # Execute the step
        try:
            status = await step_func()
            resources[step_name] = status
        except Exception as e:
            logger.error(f"Step '{step_name}' raised exception: {e}")
            resources[step_name] = ResourceStatus.FAILED
    
    @staticmethod
    def _print_summary(resources: Dict, steps_order: List[str]) -> None:
        """
        Print summary of all steps and their status.
        
        Args:
            resources: Dictionary with step names and status
            steps_order: List of step names in order
        """
        logger.info("=" * 80)
        logger.info("Azure AI Search Setup Summary")
        logger.info("=" * 80)
        
        for i, step_name in enumerate(steps_order, 1):
            status = resources.get(step_name)
            if status:
                status_symbol = (
                    "✓" if status == ResourceStatus.CREATED
                    else "ℹ" if status == ResourceStatus.EXISTING
                    else "✗"
                )
                logger.info(f"{i}. {step_name}: {status_symbol} {status}")
            else:
                logger.info(f"{i}. {step_name}: ✗ failed")
        
        logger.info("=" * 80)
    
    @staticmethod
    async def create_ai_search_tool(
        ai_client: AIProjectClient,
        credentials: AsyncTokenCredential
    ) -> Optional[Tool]:
        """
        Create AI Search tool with all required resources.
        
        Args:
            ai_client: AI Project client
            credentials: Azure credentials
            
        Returns:
            AzureAISearchTool or None if failed
        """
        from managers.search_index_manager import SearchIndexManager
        from managers.blob_store_manager import BlobStoreManager
        
        endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')
        embedding = os.getenv('AZURE_AI_EMBED_DEPLOYMENT_NAME')
        container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME', 'documents')
        search_index_name = os.getenv('AZURE_AI_SEARCH_INDEX_NAME', 'index-sample')
        
        if not endpoint or not embedding:
            logger.warning(
                "AI Search endpoint or embedding deployment not configured. "
                "Skipping AI Search setup."
            )
            return None
        
        # Get Azure OpenAI connection
        try:
            aoai_connection = await ai_client.connections.get_default(
                connection_type=ConnectionType.AZURE_OPEN_AI,
                include_credentials=True
            )
        except ValueError as e:
            logger.error(f"Failed to get Azure OpenAI connection: {e}")
            return None
        
        # Create embedding client
        embedding_client = AsyncAzureOpenAI(
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            azure_endpoint=aoai_connection.target,
            azure_ad_token_provider=credentials.get_token
        )
        
        # Initialize SearchIndexManager
        search_mgr = SearchIndexManager(
            endpoint=endpoint,
            credential=credentials,
            index_name=search_index_name,
            dimensions=int(os.getenv('AZURE_AI_EMBED_DIMENSIONS', '1536')),
            model=embedding,
            deployment_name=embedding,
            embedding_endpoint=aoai_connection.target,
            embed_api_key=None,
            embedding_client=embedding_client
        )
        
        # Get storage connection
        try:
            storage_connection = await ai_client.connections.get_default(
                connection_type=ConnectionType.AZURE_STORAGE_ACCOUNT,
                include_credentials=True
            )
            storage_account_endpoint = storage_connection.target
        except ValueError as e:
            logger.error(f"Failed to get Blob Storage connection: {e}")
            return None
        
        # Get storage resource ID
        storage_account_resource_id = os.getenv("STORAGE_ACCOUNT_RESOURCE_ID")
        if not storage_account_resource_id:
            logger.error("Missing required environment variable: STORAGE_ACCOUNT_RESOURCE_ID")
            return None
        
        connection_string = f"ResourceId={storage_account_resource_id};"
        
        # Sanitize names
        sanitized_name = search_index_name.lower().replace("_", "-")
        datasource_name = f"{sanitized_name}-datasource"
        skillset_name = f"{sanitized_name}-skillset"
        
        # Define steps
        steps_order = [
            "blob_container",
            "blob_upload",
            "search_index",
            "search_datasource",
            "search_skillset",
            "indexer_markdown",
            "indexer_documents",
        ]
        
        resources = {}
        
        # Initialize managers
        blob_mgr = BlobStoreManager(
            account_url=storage_account_endpoint,
            credential=credentials
        )
        
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'product_info')
        
        # Execute steps
        await SearchToolService._execute_step(
            "blob_container",
            lambda: blob_mgr.create_blob_container_maybe(container_name),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "blob_upload",
            lambda: blob_mgr.upload_to_blob_store_maybe(container_name, files_dir),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "search_index",
            lambda: search_mgr.create_index_maybe(
                vector_index_dimensions=int(os.getenv('AZURE_AI_EMBED_DIMENSIONS', '1536'))
            ),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "search_datasource",
            lambda: search_mgr.create_datasource_maybe(
                datasource_name=datasource_name,
                container_name=container_name,
                connection_string=connection_string
            ),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "search_skillset",
            lambda: search_mgr.create_skillset_maybe(
                skillset_name=skillset_name,
                target_index_name=search_index_name
            ),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "indexer_markdown",
            lambda: search_mgr.create_indexer_maybe(
                indexer_name=f"{sanitized_name}-markdown-indexer",
                datasource_name=datasource_name,
                target_index_name=search_index_name,
                skillset_name=skillset_name,
                file_extensions=".md",
                parsing_mode="markdown"
            ),
            resources,
            steps_order
        )
        
        await SearchToolService._execute_step(
            "indexer_documents",
            lambda: search_mgr.create_indexer_maybe(
                indexer_name=f"{sanitized_name}-documents-indexer",
                datasource_name=datasource_name,
                target_index_name=search_index_name,
                skillset_name=skillset_name,
                file_extensions=".pdf,.docx,.pptx,.xlsx,.txt",
                parsing_mode="default"
            ),
            resources,
            steps_order
        )
        
        # Check results
        all_succeeded = all(s != ResourceStatus.FAILED for s in resources.values())
        
        # Print summary
        SearchToolService._print_summary(resources, steps_order)
        
        # Return tool if successful
        if all_succeeded:
            logger.info("✓ All AI Search resources created/configured successfully!")
            conn_id = os.environ.get('SEARCH_CONNECTION_ID')
            if conn_id:
                return AzureAISearchTool(
                    azure_ai_search=AzureAISearchToolResource(
                        indexes=[AISearchIndexResource(
                            project_connection_id=conn_id,
                            index_name=search_index_name,
                            query_type="simple"
                        )]
                    )
                )
        else:
            logger.error(
                "✗ Some AI Search resources failed to create/configure. "
                "Falling back to File Search."
            )
            return None
