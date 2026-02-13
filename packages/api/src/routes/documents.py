"""
Document routes - upload, list, download, and delete documents for applications.
"""

import uuid as uuid_mod
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Application, Document, User, get_db

from ..core.security import TokenUser, get_current_user
from ..services.storage import delete_file, generate_presigned_url, upload_file
from ..worker.tasks.document_processing import process_document
from ..schemas.documents import (
    DocumentDownloadResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
)

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
}

ALLOWED_DOCUMENT_TYPES = {
    "government_id",
    "pay_stub",
    "w2",
    "tax_return",
    "bank_statement",
    "employment_letter",
    "proof_of_assets",
    "purchase_agreement",
    "rental_history",
    "other",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _verify_application_access(
    application_id: UUID,
    user: TokenUser,
    session: AsyncSession,
    require_owner: bool = False,
    require_draft: bool = False,
) -> Application:
    """Verify the user has access to the application."""
    result = await session.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Check ownership for applicants
    if user.is_applicant and not user.is_loan_servicer and not user.is_admin:
        user_result = await session.execute(
            select(User).where(User.keycloak_id == user.keycloak_id)
        )
        db_user = user_result.scalar_one_or_none()
        if db_user is None or app.applicant_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this application",
            )

    if require_owner:
        user_result = await session.execute(
            select(User).where(User.keycloak_id == user.keycloak_id)
        )
        db_user = user_result.scalar_one_or_none()
        if db_user is None or app.applicant_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the applicant can perform this action",
            )

    if require_draft and app.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents can only be managed while the application is in draft status",
        )

    return app


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    application_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: str = Form(None),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a document for an application."""
    app = await _verify_application_access(
        application_id, user, session, require_owner=True
    )

    # Validate document type
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES))}",
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: PDF, PNG, JPG, TIFF",
        )

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Generate storage key
    file_ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    storage_key = f"applications/{app.id}/documents/{uuid_mod.uuid4()}.{file_ext}"

    # Upload to MinIO
    uploaded = upload_file(
        storage_key=storage_key,
        data=contents,
        content_type=file.content_type or "application/octet-stream",
    )
    if not uploaded:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store document. Please try again.",
        )

    doc = Document(
        application_id=application_id,
        document_type=document_type,
        filename=storage_key.split("/")[-1],
        original_filename=file.filename or "unnamed",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(contents),
        storage_key=storage_key,
        status="uploaded",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    # Trigger async document processing
    process_document.delay(str(doc.id))

    return DocumentUploadResponse(
        id=str(doc.id),
        application_id=str(doc.application_id),
        document_type=doc.document_type,
        filename=doc.original_filename,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents for an application."""
    await _verify_application_access(application_id, user, session)

    result = await session.execute(
        select(Document)
        .where(Document.application_id == application_id)
        .order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()

    count_result = await session.execute(
        select(func.count())
        .select_from(Document)
        .where(Document.application_id == application_id)
    )
    total = count_result.scalar() or 0

    return DocumentListResponse(
        items=[
            DocumentListItem(
                id=str(doc.id),
                document_type=doc.document_type,
                filename=doc.original_filename,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                status=doc.status,
                extracted_data=doc.extracted_data,
                extraction_confidence=float(doc.extraction_confidence) if doc.extraction_confidence else None,
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
            )
            for doc in docs
        ],
        total=total,
    )


@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def download_document(
    application_id: UUID,
    document_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentDownloadResponse:
    """Get a pre-signed download URL for a document."""
    await _verify_application_access(application_id, user, session)

    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.application_id == application_id,
        )
    )
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Generate pre-signed URL from MinIO
    download_url = generate_presigned_url(doc.storage_key, expires=900)
    if download_url is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL",
        )

    return DocumentDownloadResponse(
        download_url=download_url,
        expires_in_seconds=900,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    application_id: UUID,
    document_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document from an application (only while in draft status)."""
    await _verify_application_access(
        application_id, user, session, require_owner=True, require_draft=True
    )

    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.application_id == application_id,
        )
    )
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete from MinIO
    delete_file(doc.storage_key)

    await session.delete(doc)
    await session.commit()
