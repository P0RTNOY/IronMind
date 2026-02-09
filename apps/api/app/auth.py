import base64
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from app.config import settings

def init_firebase_admin():
    """Initialize Firebase Admin SDK exactly once."""
    if firebase_admin._apps:
        return

    # options = {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None
    # Simplified: rely on default project discovery or credentials unless explicit override needed
    
    if settings.FIREBASE_ADMIN_SDK_JSON_BASE64:
        try:
            # Decode base64 service account JSON
            creds_json = base64.b64decode(settings.FIREBASE_ADMIN_SDK_JSON_BASE64).decode("utf-8")
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            # Raise RuntimeError to ensure 500 equivalent rather than raw ValueError
            raise RuntimeError(f"Failed to initialize Firebase Admin with provided base64 credentials: {e}") from e
    else:
        # Use Application Default Credentials (ADC)
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)

def verify_firebase_token(id_token: str) -> dict:
    """Verify Firebase ID token and return decoded claims."""
    init_firebase_admin()
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        # In a real app we might log specific auth errors (expired, invalid signature)
        # For security, we return a generic 401 to the client
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
