import logging
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, EmailStr
from google.cloud import firestore

from app.deps import get_current_user_cookie, get_db
from app.models import UserContext
from app.config import settings
from app.services.email_service import send_magic_link_email
from app.security.rate_limit import create_rate_limiter_ip

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Models ---

class AuthRequest(BaseModel):
    email: EmailStr

class AuthSessionResponse(BaseModel):
    uid: str
    email: str
    isAdmin: bool

# --- Constants ---

MAGIC_LINK_TTL = 15 * 60  # 15 minutes
SESSION_TTL = 7 * 24 * 60 * 60  # 7 days
COOKIE_NAME = "ironmind_session"

# --- Endpoints ---

@router.post("/auth/request", status_code=204, dependencies=[Depends(create_rate_limiter_ip("auth_req", 5, 60))])
async def request_magic_link(
    req: AuthRequest,
    db: firestore.Client = Depends(get_db)
):
    """
    Generate a magic link and simulate sending it (log to console for dev).
    """
    email = req.email.lower().strip()
    
    # Generate token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=MAGIC_LINK_TTL)
    
    # Store hash in Firestore
    # Collection: auth_magic_links
    link_data = {
        "email": email,
        "tokenHash": token_hash,
        "expiresAt": expires_at,
        "createdAt": now,
        "used": False
    }
    
    # Use token_hash as ID or random ID? 
    # Let's use random ID and query by hash or just use hash as ID for simplicity?
    # Using hash as ID is safe if high entropy.
    db.collection("auth_magic_links").document(token_hash).set(link_data)
    
    # Construct Link
    # In Prod: Use settings.FRONTEND_ORIGIN
    origin = settings.FRONTEND_ORIGIN or "http://localhost:3000"
    
    # If using Vite proxy or a deployment where the API sits behind /api
    prefix = "/api" if settings.ENV == "dev" else "" 
    link = f"{origin}{prefix}/auth/verify?token={token}"
    
    # Send email (Mailpit in dev, Resend in prod)
    logger.info(f"MAGIC LINK for {email}: {link}")
    try:
        send_magic_link_email(email, link)
    except Exception as e:
        logger.error(f"Failed to send magic link email: {e}")
        # Still log the link so dev can grab it from logs as fallback
        print(f"MAGIC LINK for {email}: {link}")
    
    return Response(status_code=204)


@router.get("/auth/verify")
async def verify_magic_link(
    token: str,
    response: Response,
    db: firestore.Client = Depends(get_db)
):
    """
    Validate token, create session, set cookie, redirect to app.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    doc_ref = db.collection("auth_magic_links").document(token_hash)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    
    data = doc.to_dict()
    if data.get("used"):
        raise HTTPException(status_code=400, detail="Link already used")
        
    now = datetime.now(timezone.utc)
    # Firestore returns datetime with timezone, ensure comp is valid
    # Depending on firestore lib version, might be naive or aware.
    # Safe to convert data['expiresAt'] to aware if naive.
    expires_at = data.get("expiresAt")
    if not expires_at:
         raise HTTPException(status_code=400, detail="Invalid link data")

    # Handle Firestore datetime (sometimes naive UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if now > expires_at:
        raise HTTPException(status_code=400, detail="Link expired")
        
    email = data.get("email")
    
    # Mark used
    doc_ref.update({"used": True, "usedAt": now})
    
    # Find or Create User
    users_ref = db.collection("users")
    # Query by email is problematic without index if large, but email is unique?
    # We don't enforce unique email in 'users' collection with raw firestore easily without exact ID match.
    # Strategy: Use deterministic ID? uid = uuid5(namespace, email)?
    # Or query. For MVP, query is fine.
    
    # Note: User requirements say "uid can be deterministic... or random".
    # Let's search for existing user with this email.
    user_query = users_ref.where("email", "==", email).limit(1).stream()
    existing_user = next(user_query, None)
    
    if existing_user:
        uid = existing_user.id
        # Update lastSeen
        users_ref.document(uid).update({"lastSeenAt": now})
    else:
        # Create new user
        uid = str(uuid.uuid4())
        initial_user = {
            "uid": uid,
            "email": email,
            "createdAt": now,
            "lastSeenAt": now,
            "name": email.split("@")[0] # Default name
        }
        users_ref.document(uid).set(initial_user)
        logger.info(f"Created new user {uid} for {email}")

    # Create Session
    session_id = secrets.token_urlsafe(32)
    session_expires = now + timedelta(seconds=SESSION_TTL)
    
    session_data = {
        "sessionId": session_id,
        "uid": uid,
        "email": email,
        "createdAt": now,
        "expiresAt": session_expires,
        "ip": "unknown" # Could populate from request
    }
    
    db.collection("sessions").document(session_id).set(session_data)
    
    # Set Cookie
    # Secure=True in Prod (implied by settings or generic boolean), HttpOnly=True, SameSite=Lax
    is_secure = settings.ENV == "prod"
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        max_age=SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=is_secure
    )
    
    # Redirect to Frontend
    # If dev/local, settings.FRONTEND_ORIGIN is http://localhost:3000
    redirect_url = f"{settings.FRONTEND_ORIGIN or 'http://localhost:3000'}/#/me"
    response.status_code = 302
    response.headers["Location"] = redirect_url
    return response


@router.get("/auth/session", response_model=AuthSessionResponse)
async def get_session(
    user: UserContext = Depends(get_current_user_cookie)
):
    """
    Return current user from cookie session.
    """
    return AuthSessionResponse(
        uid=user.uid,
        email=user.email or "",
        isAdmin=user.is_admin
    )


@router.post("/auth/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: firestore.Client = Depends(get_db)
):
    """
    Clear cookie and delete session doc.
    """
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        db.collection("sessions").document(session_id).delete()
        
    response.delete_cookie(key=COOKIE_NAME)
    return Response(status_code=204)
