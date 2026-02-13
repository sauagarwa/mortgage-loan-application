"""
MinIO object storage service for document management.
"""

import io
import logging
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from ..core.config import settings

logger = logging.getLogger(__name__)

# Singleton MinIO client
_minio_client: Minio | None = None


def get_minio_client() -> Minio:
    """Get or create the MinIO client singleton."""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        # Ensure bucket exists
        _ensure_bucket(settings.MINIO_BUCKET)
    return _minio_client


def _ensure_bucket(bucket_name: str) -> None:
    """Create the bucket if it doesn't exist."""
    client = _minio_client
    if client is None:
        return
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Created MinIO bucket: {bucket_name}")
    except S3Error as e:
        logger.error(f"Failed to ensure bucket {bucket_name}: {e}")


def upload_file(
    storage_key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    bucket: str | None = None,
) -> bool:
    """Upload a file to MinIO.

    Args:
        storage_key: The object key (path) in the bucket.
        data: File contents as bytes.
        content_type: MIME type of the file.
        bucket: Bucket name (defaults to configured bucket).

    Returns:
        True if upload succeeded, False otherwise.
    """
    client = get_minio_client()
    bucket = bucket or settings.MINIO_BUCKET

    try:
        client.put_object(
            bucket_name=bucket,
            object_name=storage_key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Uploaded {storage_key} to {bucket} ({len(data)} bytes)")
        return True
    except S3Error as e:
        logger.error(f"Failed to upload {storage_key}: {e}")
        return False


def download_file(
    storage_key: str,
    bucket: str | None = None,
) -> bytes | None:
    """Download a file from MinIO.

    Args:
        storage_key: The object key (path) in the bucket.
        bucket: Bucket name (defaults to configured bucket).

    Returns:
        File contents as bytes, or None if download failed.
    """
    client = get_minio_client()
    bucket = bucket or settings.MINIO_BUCKET

    try:
        response = client.get_object(bucket, storage_key)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        logger.error(f"Failed to download {storage_key}: {e}")
        return None


def delete_file(
    storage_key: str,
    bucket: str | None = None,
) -> bool:
    """Delete a file from MinIO.

    Args:
        storage_key: The object key (path) in the bucket.
        bucket: Bucket name (defaults to configured bucket).

    Returns:
        True if deletion succeeded, False otherwise.
    """
    client = get_minio_client()
    bucket = bucket or settings.MINIO_BUCKET

    try:
        client.remove_object(bucket, storage_key)
        logger.info(f"Deleted {storage_key} from {bucket}")
        return True
    except S3Error as e:
        logger.error(f"Failed to delete {storage_key}: {e}")
        return False


def generate_presigned_url(
    storage_key: str,
    bucket: str | None = None,
    expires: int = 900,
) -> str | None:
    """Generate a pre-signed URL for downloading a file.

    Args:
        storage_key: The object key (path) in the bucket.
        bucket: Bucket name (defaults to configured bucket).
        expires: URL expiry time in seconds (default 15 minutes).

    Returns:
        Pre-signed URL string, or None if generation failed.
    """
    client = get_minio_client()
    bucket = bucket or settings.MINIO_BUCKET

    try:
        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=storage_key,
            expires=timedelta(seconds=expires),
        )
        return url
    except S3Error as e:
        logger.error(f"Failed to generate presigned URL for {storage_key}: {e}")
        return None


def file_exists(
    storage_key: str,
    bucket: str | None = None,
) -> bool:
    """Check if a file exists in MinIO.

    Args:
        storage_key: The object key (path) in the bucket.
        bucket: Bucket name (defaults to configured bucket).

    Returns:
        True if the file exists, False otherwise.
    """
    client = get_minio_client()
    bucket = bucket or settings.MINIO_BUCKET

    try:
        client.stat_object(bucket, storage_key)
        return True
    except S3Error:
        return False


async def check_health() -> dict:
    """Check MinIO connectivity and return health status."""
    try:
        client = get_minio_client()
        bucket = settings.MINIO_BUCKET
        exists = client.bucket_exists(bucket)
        return {
            "status": "healthy" if exists else "degraded",
            "bucket": bucket,
            "bucket_exists": exists,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)[:100],
        }
