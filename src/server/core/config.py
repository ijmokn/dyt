# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Centralized configuration management using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Settings
    APP_NAME: str = Field(default="AI Agent API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix for versioning")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Logging
    APP_LOG_FILE: str = Field(default="", description="Log file path (empty for stdout only)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Azure AI Project
    AZURE_EXISTING_AIPROJECT_ENDPOINT: str = Field(..., description="Azure AI Project endpoint")
    AZURE_EXISTING_AIPROJECT_RESOURCE_ID: str = Field(..., description="Azure AI Project resource ID")
    AZURE_EXISTING_AGENT_ID: str = Field(..., description="Existing Agent ID (format: agent_name:agent_version)")
    
    # Tracing
    ENABLE_AZURE_MONITOR_TRACING: bool = Field(default=False, description="Enable Azure Monitor tracing")
    
    # CORS
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:5174,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:3000,http://127.0.0.1:5174,http://127.0.0.1:8080",
        description="Comma-separated list of allowed CORS origins"
    )
    FRONTEND_URL: Optional[str] = Field(default=None, description="Production frontend URL")
    
    # Authentication
    WEB_APP_USERNAME: Optional[str] = Field(default=None, description="Basic auth username")
    WEB_APP_PASSWORD: Optional[str] = Field(default=None, description="Basic auth password")
    
    # Runtime
    RUNNING_IN_PRODUCTION: bool = Field(default=False, description="Production environment flag")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/chat_history",
        description="PostgreSQL database connection string"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from environment
    )
    
    @field_validator("AZURE_EXISTING_AGENT_ID")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate that agent ID has the correct format."""
        if v and ":" not in v:
            raise ValueError("AZURE_EXISTING_AGENT_ID must be in the format 'agent_name:agent_version'")
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins
    
    @property
    def basic_auth_enabled(self) -> bool:
        """Check if basic authentication is enabled."""
        return bool(self.WEB_APP_USERNAME and self.WEB_APP_PASSWORD)
    
    @property
    def agent_name(self) -> str:
        """Extract agent name from agent ID."""
        return self.AZURE_EXISTING_AGENT_ID.split(":")[0] if self.AZURE_EXISTING_AGENT_ID else ""
    
    @property
    def agent_version(self) -> str:
        """Extract agent version from agent ID."""
        return self.AZURE_EXISTING_AGENT_ID.split(":")[1] if self.AZURE_EXISTING_AGENT_ID else ""


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).
    
    Returns:
        Settings: Application configuration
    """
    global _settings
    if _settings is None:
        # Load environment variables from azd environment folder for local development
        from util import get_env_file_path
        from dotenv import load_dotenv
        
        env_file = get_env_file_path()
        load_dotenv(env_file)
        
        _settings = Settings()
    return _settings
