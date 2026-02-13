"""
Document Pydantic schemas.
"""

from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    id: str
    application_id: str
    document_type: str
    filename: str
    file_size: int
    mime_type: str
    status: str
    uploaded_at: datetime | None = None


class DocumentListItem(BaseModel):
    """Document item for list views."""

    id: str
    document_type: str
    filename: str
    file_size: int
    mime_type: str
    status: str
    extracted_data: dict | None = None
    extraction_confidence: float | None = None
    uploaded_at: datetime | None = None
    processed_at: datetime | None = None


class DocumentListResponse(BaseModel):
    """List of documents for an application."""

    items: list[DocumentListItem]
    total: int


class DocumentDownloadResponse(BaseModel):
    """Pre-signed download URL for a document."""

    download_url: str
    expires_in_seconds: int = 900
