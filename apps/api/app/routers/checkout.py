import logging
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, model_validator
from app.deps import get_current_user
from app.models import UserContext
from app.payments import service as payments_service

logger = logging.getLogger(__name__)

router = APIRouter()

class CheckoutRequest(BaseModel):
    type: Literal["one_time", "subscription"]
    courseId: Optional[str] = None

    @model_validator(mode='after')
    def check_course_id(self):
        if self.type == "one_time" and not self.courseId:
            raise ValueError("courseId is required for one_time purchases")
        return self

class CheckoutResponse(BaseModel):
    url: str

@router.post("/checkout/session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user: UserContext = Depends(get_current_user)
):
    """
    Create a checkout session via the active payment provider.
    """
    # Map checkout type to payment domain
    scope = "course" if request.type == "one_time" else "membership"

    try:
        result = payments_service.create_checkout(
            uid=user.uid,
            kind=request.type,
            scope=scope,
            courseId=request.courseId,
        )

        logger.info(
            "Checkout session created",
            extra={
                "uid": user.uid,
                "kind": request.type,
                "scope": scope,
                "course_id": request.courseId,
            }
        )

        return CheckoutResponse(url=result["url"])

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
