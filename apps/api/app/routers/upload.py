import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import UserContext, UploadSignRequest, UploadSignResponse
from app.deps import require_admin
from app.services import storage

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "cover": ["image/jpeg", "image/png", "image/webp"],
    "plan_pdf": ["application/pdf"]
}

@router.post("/uploads/sign", response_model=UploadSignResponse)
async def sign_upload(
    request: UploadSignRequest,
    admin: UserContext = Depends(require_admin)
):
    """
    Generate a signed URL for uploading a file to GCS.
    Enforces strict content-type validation.
    """
    # 1. Validate Content-Type against Kind
    allowed_types = ALLOWED_CONTENT_TYPES.get(request.kind)
    if not allowed_types:
        raise HTTPException(status_code=400, detail="Invalid upload kind")
    
    if request.contentType not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid content type for {request.kind}. Allowed: {allowed_types}"
        )

    # 2. Start constructing the path
    # Structure: <kind>s/<uuid>-<sanitized_filename>
    # Note: Pluralizing kind for folder name (cover -> covers)
    folder = f"{request.kind}s"
    
    # 3. Sanitize filename (basic) and generate UUID
    # We use UUID as the prefix to ensure uniqueness and prevent overwrites
    file_id = str(uuid.uuid4())
    safe_filename = "".join(c for c in request.filename if c.isalnum() or c in "._-")
    blob_name = f"{folder}/{file_id}-{safe_filename}"
    
    # 4. Generate Signed URL
    try:
        upload_url = storage.generate_signed_upload_url(
            blob_name=blob_name,
            content_type=request.contentType
        )
        
        public_url = storage.get_public_url(blob_name)
        
        return UploadSignResponse(
            uploadUrl=upload_url,
            publicUrl=public_url,
            objectPath=blob_name
        )
    except RuntimeError as e:
        # GCS might not be configured
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate signed URL")
