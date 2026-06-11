# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""User service for user management operations."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import User


def get_or_create_user(db: Session, email: str) -> int:
    """
    Get existing user ID or create new user.
    
    Args:
        db: Database session
        email: User email address
        
    Returns:
        User ID
    """
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        return user.id
    
    # Create new user
    now = datetime.now(timezone.utc)
    new_user = User(
        email=email,
        created_at=now,
        updated_at=now
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user.id
