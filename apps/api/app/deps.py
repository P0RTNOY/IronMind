from typing import Optional
from fastapi import Depends, HTTPException, status, Request
# removed HTTPBearer
from app.config import settings
from app.models import UserContext
from google.cloud import firestore

# We no longer use Firebase Auth tokens in the backend.
# We use:
# 1. Dev: X-Debug-Uid header
# 2. Prod: ironmind_session cookie

def get_db():
    from app.repos.firestore import get_db as _get_db
    return _get_db()

async def get_current_user_cookie(
    request: Request, 
    db: firestore.Client = Depends(get_db)
) -> UserContext:
    """
    Validate Session Cookie (Prod) or Debug Header (Dev).
    """
    # 1. Dev Override
    debug_uid = request.headers.get("X-Debug-Uid")
    if debug_uid:
        is_admin = request.headers.get("X-Debug-Admin") == "1"
        return UserContext(
            uid=debug_uid,
            email=f"{debug_uid}@example.com",
            name="Debug User",
            is_admin=is_admin
        )

    # 2. Cookie Auth
    session_id = request.cookies.get("ironmind_session")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session cookie"
        )

    # 3. Validate Session from Firestore
    session_ref = db.collection("sessions").document(session_id)
    session_doc = session_ref.get()
    
    if not session_doc.exists:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    session_data = session_doc.to_dict()
    
    # Check Expiry
    # Assuming firestore returns aware datetime
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    expires_at = session_data.get("expiresAt")
    
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if not expires_at or now > expires_at:
        raise HTTPException(status_code=401, detail="Session expired")
        
    uid = session_data.get("uid")
    email = session_data.get("email")
    
    # Check Admin (Env based source of truth for Prod)
    # or we could store isAdmin in the user doc/session.
    # For now, let's keep using ADMIN_UIDS env for safety.
    is_admin = uid in settings.ADMIN_UIDS
    
    return UserContext(
        uid=uid,
        email=email,
        name=email.split("@")[0] if email else "User",
        is_admin=is_admin
    )

# Alias for compatibility if needed, or we just update imports
get_current_user = get_current_user_cookie

def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    """
    Dependency to ensure the user is an admin.
    Returns 403 Forbidden if not.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user
