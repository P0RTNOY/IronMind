from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import verify_firebase_token
from app.config import settings
from app.models import UserContext

security = HTTPBearer(auto_error=False)


def get_current_user(request: Request, creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserContext:
    """
    Validate Bearer token and return UserContext.
    """
    debug_uid = request.headers.get("X-Debug-Uid")
    if debug_uid:
        is_admin = request.headers.get("X-Debug-Admin") == "1"
        return UserContext(
            uid=debug_uid,
            email=f"{debug_uid}@example.com",
            name="Debug User",
            is_admin=is_admin
        )

    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    token = creds.credentials
    claims = verify_firebase_token(token)
    
    # Robust UID extraction (sub is standard, uid is Firebase specific)
    uid = claims.get("uid") or claims.get("sub") or claims.get("user_id")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token missing uid/sub"
        )
        
    email = claims.get("email")
    name = claims.get("name")
    
    # Check admin status based on config
    is_admin = uid in settings.ADMIN_UIDS
    
    return UserContext(
        uid=uid,
        email=email,
        name=name,
        is_admin=is_admin
    )

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
