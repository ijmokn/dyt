# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Chat service - 使用 Azure SDK 流式处理 + ORM 数据库保存"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Optional, List, Any

from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry import trace
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails
from sqlalchemy.orm import Session

from models import Conversation as DBConversation, Message as DBMessage

logger = logging.getLogger("azureaiapp")
tracer = trace.get_tracer(__name__)


class ChatService:
    """Chat service - 使用 Azure SDK 处理对话流"""
    
    @staticmethod
    def generate_conversation_id() -> str:
        """生成新的 conversation ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def _serialize_stream_event(event_type: str, content: Any, annotations: Optional[List[Dict]] = None) -> str:
        """序列化流事件为 JSON"""
        data = {
            'type': event_type,
            'content': content
        }
        if annotations:
            data['annotations'] = annotations
        return json.dumps(data)
    
    @staticmethod
    async def _extract_message_and_annotations(event) -> Dict:
        """从 Azure SDK 事件中提取消息和注释"""
        annotations = []
        text = ""
        
        if not event or not hasattr(event, 'content') or not event.content:
            return {'content': text, 'annotations': annotations}
        
        try:
            content = event.content[0]
            
            # 提取文本
            if hasattr(content, 'type'):
                if content.type == "output_text" or content.type == "input_text":
                    text = content.text if hasattr(content, 'text') else ""
            
            # 提取注释
            if hasattr(content, 'type') and content.type == "output_text":
                if hasattr(content, 'annotations'):
                    for annotation in content.annotations:
                        if annotation.type == "file_citation":
                            ann = {
                                'label': annotation.filename,
                                'index': annotation.index
                            }
                            annotations.append(ann)
                        elif annotation.type == "url_citation":
                            ann = {
                                'label': annotation.title,
                                'index': annotation.start_index
                            }
                            annotations.append(ann)
        except Exception as e:
            logger.warning(f"Failed to extract annotations: {e}")
        
        return {'content': text, 'annotations': annotations}
    
    @staticmethod
    async def stream_agent_response(
        agent: AgentVersionDetails,
        conversation_id: str,
        user_message: str,
        project_client: AIProjectClient,
        carrier: Dict[str, str],
        db: Optional[Session] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式处理 Agent 响应 - 使用 Azure SDK + ORM 数据库
        
        Args:
            agent: Azure Agent version details
            conversation_id: Azure conversation ID
            user_message: 用户消息
            project_client: Azure AI Project client
            carrier: Trace context carrier
            db: Database session
            
        Yields:
            SSE formatted strings
        """
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        assistant_message = ""
        assistant_annotations = []
        
        with tracer.start_as_current_span('stream_agent_response', context=ctx):
            logger.info(f"Streaming response for conversation={conversation_id}")
            
            try:
                # 保存用户消息到数据库
                if db:
                    try:
                        now = datetime.now(timezone.utc)
                        user_msg = DBMessage(
                            conversation_id=conversation_id,
                            role="user",
                            content=user_message,
                            annotations=[],
                            created_at=now,
                            updated_at=now
                        )
                        db.add(user_msg)
                        db.commit()
                        logger.info(f"Saved user message to database")
                    except Exception as e:
                        logger.warning(f"Failed to save user message to database: {e}")
                        db.rollback()
                
                # 调用 Azure OpenAI API
                async with project_client.get_openai_client() as openai_client:
                    logger.info(f"Creating Azure response for conversation: {conversation_id}")
                    
                    response = await openai_client.responses.create(
                        conversation=conversation_id,
                        input=user_message,
                        extra_body={
                            "agent_reference": {
                                "name": agent.name,
                                "type": "agent_reference"
                            }
                        },
                        stream=True
                    )
                    
                    logger.info("Successfully created stream; starting to process events")
                    
                    # 处理流式事件
                    async for event in response:
                        if event.type == "response.created":
                            logger.info(f"Stream response created with ID: {event.response.id}")
                        
                        elif event.type == "response.output_text.delta":
                            logger.debug(f"Delta: {event.delta}")
                            if event.delta:
                                assistant_message += event.delta
                                yield f"data: {ChatService._serialize_stream_event('message', event.delta)}\n\n"
                        
                        elif event.type == "response.output_item.done" and event.item.type == "message":
                            stream_data = await ChatService._extract_message_and_annotations(event.item)
                            if stream_data['content']:
                                assistant_message = stream_data['content']
                            if stream_data['annotations']:
                                assistant_annotations = stream_data['annotations']
                            yield f"data: {ChatService._serialize_stream_event('completed_message', assistant_message, assistant_annotations)}\n\n"
                        
                        elif event.type == "response.completed":
                            logger.info(f"Response completed")
            
            except Exception as e:
                logger.exception(f"Exception in stream_agent_response: {e}")
                assistant_message = str(e)
                yield f"data: {ChatService._serialize_stream_event('completed_message', str(e), [])}\n\n"
            
            finally:
                # 保存助手消息到数据库
                if db and assistant_message:
                    try:
                        now = datetime.now(timezone.utc)
                        
                        # 保存助手消息
                        assistant_msg = DBMessage(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=assistant_message,
                            annotations=assistant_annotations,
                            created_at=now,
                            updated_at=now
                        )
                        db.add(assistant_msg)
                        
                        # 更新 conversation 统计信息
                        db_conversation = db.query(DBConversation).filter(
                            DBConversation.id == conversation_id
                        ).first()
                        
                        if db_conversation:
                            db_conversation.last_message = assistant_message[:200]  # type: ignore
                            db_conversation.message_count = db_conversation.message_count + 2  # type: ignore
                            db_conversation.updated_at = now  # type: ignore
                        
                        db.commit()
                        logger.info(f"Saved assistant message to database")
                    
                    except Exception as e:
                        logger.error(f"Failed to save assistant message: {e}")
                        db.rollback()
                
                # 发送流结束事件
                yield f"data: {ChatService._serialize_stream_event('stream_end', '')}\n\n"
