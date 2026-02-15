"""
Chat session and message Pydantic schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSessionResponse(BaseModel):
    """Response when creating a new chat session."""

    session_id: str
    conversation_id: str


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., min_length=1, max_length=5000)
    file_ids: list[str] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    """A single chat message in the conversation."""

    id: str
    role: str
    content: str
    message_type: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Response containing conversation history."""

    session_id: str
    conversation_id: str
    current_phase: str
    messages: list[ChatMessageResponse]


class ChatFileUploadResponse(BaseModel):
    """Response after uploading a file in chat."""

    document_id: str
    filename: str
    document_type: str
    status: str


class ChatLinkRequest(BaseModel):
    """Request to link an anonymous session to an authenticated user."""

    pass  # Auth comes from the Bearer token


class ChatLinkResponse(BaseModel):
    """Response after linking a session."""

    linked: bool
    user_id: str
    application_id: str | None = None
