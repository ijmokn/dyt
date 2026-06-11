# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""Security utilities for authentication and authorization."""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import Settings, get_settings
from .exceptions import AuthenticationError


security = HTTPBasic()


def verify_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
    settings: Settings = Depends(get_settings)
) -> None:
    """
    Verify HTTP Basic Authentication credentials.
    
    Args:
        credentials: HTTP Basic credentials from request
        settings: Application settings
        
    Raises:
        HTTPException: If authentication fails
    """
    if not settings.basic_auth_enabled:
        # Authentication not configured, allow access
        return
    
    correct_username = secrets.compare_digest(
        credentials.username,
        settings.WEB_APP_USERNAME or ""
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        settings.WEB_APP_PASSWORD or ""
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def get_optional_auth(settings: Settings = Depends(get_settings)):
    """
    Get optional authentication dependency.
    
    Returns None if auth is not enabled, otherwise returns the auth dependency.
    """
    if settings.basic_auth_enabled:
        return Depends(verify_basic_auth)
    return None
