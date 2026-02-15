"""
Chat routes - conversational mortgage application via LLM chatbot.

All endpoints use session-based auth (no Keycloak required to start chatting).
"""

import json
import logging
import uuid as uuid_mod
from uuid import UUID

from db import Application, Conversation, Document, Message, User, get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.security import TokenUser, get_current_user
from ..schemas.chat import (
    ChatFileUploadResponse,
    ChatHistoryResponse,
    ChatLinkResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
)
from ..services import session_manager
from ..services.chat_agent import handle_chat_message
from ..services.storage import upload_file
from ..worker.tasks.document_processing import process_document

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    db: AsyncSession = Depends(get_db),
):
    """Create a new anonymous chat session."""
    # Create Redis session
    redis_session = session_manager.create_session()

    # Create conversation in DB
    conversation = Conversation(
        session_id=redis_session.session_id,
        status="active",
        current_phase="greeting",
        collected_data={},
    )
    db.add(conversation)
    await db.flush()

    # Link Redis session to conversation
    redis_session.conversation_id = str(conversation.id)
    session_manager.update_session(redis_session)

    # Add welcome system message
    welcome_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=(
            "Hi there! Welcome to MortgageAI. I'm here to help you find "
            "the right home loan and guide you through the application process. "
            "What brings you in today? Are you looking to purchase a home, "
            "refinance an existing mortgage, or just exploring your options?"
        ),
        message_type="text",
    )
    db.add(welcome_msg)
    await db.commit()

    return ChatSessionResponse(
        session_id=redis_session.session_id,
        conversation_id=str(conversation.id),
    )


@router.post("/sessions/{session_id}/messages")
async def send_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get a streaming SSE response."""
    # Validate session
    redis_session = session_manager.get_session(session_id)
    if redis_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    # Load conversation
    result = await db.execute(select(Conversation).where(Conversation.session_id == session_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # Sync user_id from Redis session (in case it was linked)
    if redis_session.user_id and not conversation.user_id:
        conversation.user_id = UUID(redis_session.user_id)
        await db.flush()

    # Process message with chat agent
    events = await handle_chat_message(conversation, request.content, db)
    await db.commit()

    # Stream events as SSE
    async def event_generator():
        for event in events:
            data = json.dumps(event.data)
            yield f"event: {event.event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/files", response_model=ChatFileUploadResponse)
async def upload_chat_file(
    session_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document within a chat session."""
    # Validate session
    redis_session = session_manager.get_session(session_id)
    if redis_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    # Load conversation
    result = await db.execute(select(Conversation).where(Conversation.session_id == session_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if not conversation.application_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No application exists yet. Continue chatting to create one first.",
        )

    # Validate file
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 10 MB limit.",
        )

    # Upload to MinIO
    ext = (file.filename or "file").rsplit(".", 1)[-1] if file.filename else "pdf"
    stored_filename = f"{uuid_mod.uuid4()}.{ext}"
    storage_key = f"applications/{conversation.application_id}/documents/{stored_filename}"
    upload_file(storage_key, contents, file.content_type or "application/octet-stream")

    # Create document record
    doc = Document(
        application_id=conversation.application_id,
        document_type=document_type,
        filename=stored_filename,
        original_filename=file.filename or "uploaded_file",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(contents),
        storage_key=storage_key,
        status="uploaded",
    )
    db.add(doc)

    # Add a file upload message to chat
    file_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=f"Uploaded document: {file.filename} ({document_type})",
        message_type="file_upload",
        metadata_={
            "document_id": str(doc.id),
            "filename": file.filename,
            "document_type": document_type,
        },
    )
    db.add(file_msg)
    await db.commit()

    # Trigger async document processing
    try:
        process_document.apply_async(args=[str(doc.id)], queue="documents")
    except Exception as e:
        logger.warning(f"Failed to queue document processing: {e}")

    return ChatFileUploadResponse(
        document_id=str(doc.id),
        filename=file.filename or "uploaded_file",
        document_type=document_type,
        status="uploaded",
    )


@router.post("/sessions/{session_id}/link", response_model=ChatLinkResponse)
async def link_session_to_user(
    session_id: str,
    user: TokenUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link an anonymous chat session to an authenticated user."""
    redis_session = session_manager.get_session(session_id)
    if redis_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    # Get or create local user
    result = await db.execute(select(User).where(User.keycloak_id == user.keycloak_id))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        db_user = User(
            keycloak_id=user.keycloak_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.primary_role,
        )
        db.add(db_user)
        await db.flush()

    # Update conversation
    result = await db.execute(select(Conversation).where(Conversation.session_id == session_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    conversation.user_id = db_user.id

    # Update application ownership if exists
    app_id_str = None
    if conversation.application_id:
        result = await db.execute(
            select(Application).where(Application.id == conversation.application_id)
        )
        app = result.scalar_one_or_none()
        if app:
            app.applicant_id = db_user.id
            app_id_str = str(app.id)

    # Update Redis session
    session_manager.link_session_to_user(session_id, str(db_user.id))

    await db.commit()

    return ChatLinkResponse(
        linked=True,
        user_id=str(db_user.id),
        application_id=app_id_str,
    )


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get conversation message history for resuming a chat."""
    redis_session = session_manager.get_session(session_id)
    if redis_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # Only return user and assistant text messages (not tool messages)
    visible_messages = [
        ChatMessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            message_type=m.message_type,
            metadata=m.metadata_,
            created_at=m.created_at,
        )
        for m in conversation.messages
        if m.role in ("user", "assistant") and not (m.metadata_ and m.metadata_.get("tool_calls"))
    ]

    return ChatHistoryResponse(
        session_id=session_id,
        conversation_id=str(conversation.id),
        current_phase=conversation.current_phase,
        messages=visible_messages,
    )
