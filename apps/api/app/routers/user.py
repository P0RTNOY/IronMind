from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models import UserContext

router = APIRouter()

@router.get("/me", response_model=UserContext)
async def get_me(user: UserContext = Depends(get_current_user)):
    """
    Return current user profile and admin status.
    """
    return user
