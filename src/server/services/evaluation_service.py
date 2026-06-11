# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Continuous evaluation service."""

import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AgentVersionDetails,
    EvaluationRule,
    ContinuousEvaluationRuleAction,
    EvaluationRuleFilter,
    EvaluationRuleEventType,
    EvaluationRuleActionType,
)
from azure.core.credentials_async import AsyncTokenCredential
from openai import AsyncOpenAI


logger = logging.getLogger("azureaiapp")


class EvaluationService:
    """Service for managing continuous evaluation."""
    
    @staticmethod
    async def initialize_continuous_evaluation(
        project_client: AIProjectClient,
        openai_client: AsyncOpenAI,
        agent_version_details: AgentVersionDetails,
        credential: AsyncTokenCredential
    ) -> None:
        """
        Initialize continuous evaluation for an agent.
        
        Args:
            project_client: AI Project client
            openai_client: OpenAI client
            agent_version_details: Agent version details
            credential: Azure credentials
        """
        eval_rule_id = f"eval-rule-for-{agent_version_details.name}"
        
        try:
            # Check if rule already exists
            eval_rules = project_client.evaluation_rules.list(
                action_type=EvaluationRuleActionType.CONTINUOUS_EVALUATION,
                agent_name=agent_version_details.name
            )
            rules_list = [rule async for rule in eval_rules]
            
            if len(rules_list) >= 1:
                logger.info(
                    f"Continuous Evaluation Rule for agent {agent_version_details.name} "
                    "already exists"
                )
                return
            
            # Create evaluation with testing criteria
            data_source_config = {
                "type": "azure_ai_source",
                "scenario": "responses"
            }
            
            testing_criteria = [
                {
                    "type": "azure_ai_evaluator",
                    "name": "violence",
                    "evaluator_name": "builtin.violence",
                    "initialization_parameters": {
                        "deployment_name": os.environ["AZURE_AI_AGENT_DEPLOYMENT_NAME"]
                    },
                }
            ]
            
            eval_object = await openai_client.evals.create(
                name=f"{agent_version_details.name} Continuous Evaluation",
                data_source_config=data_source_config,  # type: ignore
                testing_criteria=testing_criteria,  # type: ignore
            )
            
            logger.info(
                f"Evaluation created (id: {eval_object.id}, name: {eval_object.name})"
            )
            
            # Configure rule that triggers evaluation on agent responses
            continuous_eval_rule = await project_client.evaluation_rules.create_or_update(
                id=eval_rule_id,
                evaluation_rule=EvaluationRule(
                    display_name=f"{agent_version_details.name} Continuous Eval Rule",
                    description="An eval rule that runs on agent response completions",
                    action=ContinuousEvaluationRuleAction(
                        eval_id=eval_object.id,
                        max_hourly_runs=5  # Set max eval run limit per hour
                    ),
                    event_type=EvaluationRuleEventType.RESPONSE_COMPLETED,
                    filter=EvaluationRuleFilter(agent_name=agent_version_details.name),
                    enabled=True,
                ),
            )
            
            logger.info(
                f"Continuous Evaluation Rule created "
                f"(id: {continuous_eval_rule.id}, name: {continuous_eval_rule.display_name})"
            )
        
        except Exception as e:
            logger.error(f"Error creating Continuous Evaluation Rule: {e}", exc_info=True)
