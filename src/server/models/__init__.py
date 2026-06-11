# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

"""SQLAlchemy ORM models for chat history database."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base


class User(Base):
    """User model - stores user information."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Conversation(Base):
    """Conversation model - stores conversation information."""
    
    __tablename__ = "conversations"
    
    id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    last_message = Column(Text, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    status = Column(
        String(50),
        default="active",
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    tags = relationship(
        "ConversationTag",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="check_conversation_status"),
    )
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', user_id={self.user_id}, title='{self.title}')>"


class Message(Base):
    """Message model - stores message content."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(255),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    annotations = Column(JSONB, default=list, nullable=True)
    sequence_number = Column(Integer, nullable=True, index=True)
    message_metadata = Column('metadata', JSONB, default=dict, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system', 'error')", name="check_message_role"),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id='{self.conversation_id}', role='{self.role}')>"


class ConversationTag(Base):
    """Conversation tag model - supports conversation categorization."""
    
    __tablename__ = "conversation_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(255),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_name = Column(String(100), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    conversation = relationship("Conversation", back_populates="tags")
    
    # Constraints
    __table_args__ = (
        Index("uk_conversation_tag", "conversation_id", "tag_name", unique=True),
    )
    
    def __repr__(self):
        return f"<ConversationTag(id={self.id}, conversation_id='{self.conversation_id}', tag='{self.tag_name}')>"


class MessageReference(Base):
    """Message reference model - stores references between messages."""
    
    __tablename__ = "message_references"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reference_type = Column(String(50), default="reply", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        Index("uk_message_reference", "source_message_id", "target_message_id", unique=True),
        CheckConstraint(
            "reference_type IN ('reply', 'quote', 'forward', 'edit')",
            name="check_reference_type"
        ),
    )
    
    def __repr__(self):
        return f"<MessageReference(id={self.id}, source={self.source_message_id}, target={self.target_message_id})>"
