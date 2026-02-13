"""
Celery tasks for document processing.

Handles asynchronous document data extraction after upload.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select

from db import Document

from ..celery_app import celery_app
from ..db import get_sync_session
from ...services.document_extraction import extract_document_data
from ...services.storage import download_file
from ...services.websocket_manager import publish_event_sync

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="src.worker.tasks.document_processing.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document(self, document_id: str) -> dict:
    """Process an uploaded document: download, extract data, update record.

    Args:
        document_id: UUID string of the document to process.

    Returns:
        Dict with processing result summary.
    """
    logger.info(f"Processing document {document_id}")

    with get_sync_session() as session:
        # Fetch the document record
        result = session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()

        if doc is None:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "error": "Document not found"}

        if doc.status == "processed":
            logger.info(f"Document {document_id} already processed, skipping")
            return {"status": "skipped", "reason": "already_processed"}

        # Update status to processing
        doc.status = "processing"
        session.commit()

    # Download file from MinIO (outside session to avoid long-held connections)
    file_data = download_file(doc.storage_key)
    if file_data is None:
        with get_sync_session() as session:
            result = session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "error"
                doc.processing_error = "Failed to download file from storage"
                session.commit()
        logger.error(f"Failed to download document {document_id} from storage")
        return {"status": "error", "error": "Failed to download file"}

    # Extract data from the document
    try:
        extracted_data, confidence = extract_document_data(
            document_type=doc.document_type,
            file_data=file_data,
            mime_type=doc.mime_type,
            filename=doc.original_filename,
        )
    except Exception as exc:
        with get_sync_session() as session:
            result = session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "error"
                doc.processing_error = f"Extraction failed: {str(exc)[:500]}"
                session.commit()

        logger.error(f"Extraction failed for document {document_id}: {exc}")
        # Retry on transient failures
        raise self.retry(exc=exc)

    # Update the document record with extracted data
    with get_sync_session() as session:
        result = session.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return {"status": "error", "error": "Document disappeared during processing"}

        doc.extracted_data = extracted_data
        doc.extraction_confidence = confidence
        doc.status = "processed"
        doc.processed_at = datetime.now(UTC)
        doc.processing_error = None
        session.commit()

    logger.info(
        f"Document {document_id} processed successfully "
        f"(type={doc.document_type}, confidence={confidence:.2f})"
    )

    # Notify via WebSocket
    publish_event_sync(f"application:{doc.application_id}", {
        "type": "document_processed",
        "data": {
            "document_id": document_id,
            "document_type": doc.document_type,
            "status": "processed",
            "confidence": confidence,
        },
    })

    return {
        "status": "success",
        "document_id": document_id,
        "document_type": doc.document_type,
        "confidence": confidence,
        "fields_detected": len(extracted_data.get("fields_detected", [])),
    }


@celery_app.task(
    name="src.worker.tasks.document_processing.process_application_documents",
    acks_late=True,
)
def process_application_documents(application_id: str) -> dict:
    """Process all unprocessed documents for an application.

    Called when an application is submitted to ensure all documents are processed.

    Args:
        application_id: UUID string of the application.

    Returns:
        Dict with counts of queued documents.
    """
    logger.info(f"Queuing document processing for application {application_id}")

    with get_sync_session() as session:
        result = session.execute(
            select(Document).where(
                Document.application_id == application_id,
                Document.status == "uploaded",
            )
        )
        docs = result.scalars().all()

        queued = 0
        for doc in docs:
            process_document.delay(str(doc.id))
            queued += 1

    logger.info(f"Queued {queued} documents for application {application_id}")
    return {"application_id": application_id, "documents_queued": queued}
