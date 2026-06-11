# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class AIAgentException(Exception):
    """Base exception for AI Agent application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(AIAgentException):
    """Configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class AgentNotFoundError(AIAgentException):
    """Agent not found error."""
    
    def __init__(self, agent_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Agent '{agent_id}' not found"
        super().__init__(message, status_code=404, details=details)


class ConversationError(AIAgentException):
    """Conversation-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class ConversationNotFoundError(AIAgentException):
    """Conversation not found error."""
    
    def __init__(self, conversation_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Conversation '{conversation_id}' not found"
        super().__init__(message, status_code=404, details=details)


class AuthenticationError(AIAgentException):
    """Authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class ValidationError(AIAgentException):
    """Input validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class ExternalServiceError(AIAgentException):
    """External service errors (Azure AI, OpenAI, etc.)."""
    
    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"Error from {service_name}: {message}"
        super().__init__(full_message, status_code=502, details=details)
