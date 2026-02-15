import logging
import datetime
from typing import Optional
from google.cloud import storage
from app.config import settings

logger = logging.getLogger(__name__)

_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is None:
        try:
            _storage_client = storage.Client()
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}")
            return None
    return _storage_client

def generate_signed_upload_url(
    blob_name: str, 
    content_type: str, 
    bucket_name: Optional[str] = None
) -> str:
    """
    Generate a V4 signed URL for uploading a file to GCS.
    """
    bucket_name = bucket_name or settings.GCS_BUCKET_NAME
    if not bucket_name:
        raise RuntimeError("GCS_BUCKET_NAME is not configured")

    client = get_storage_client()
    if not client:
        raise RuntimeError("GCS client not initialized")

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
    )
    
    return url

def get_public_url(blob_name: str) -> str:
    """
    Return the public URL for a blob. 
    Assumes the bucket/object is publicly readable.
    """
    bucket_name = settings.GCS_BUCKET_NAME
    # Use the configured public base URL (e.g. https://storage.googleapis.com)
    # Pattern: https://storage.googleapis.com/<bucket>/<blob>
    return f"{settings.GCS_PUBLIC_BASE_URL}/{bucket_name}/{blob_name}"
