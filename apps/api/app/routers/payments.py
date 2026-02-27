from fastapi import APIRouter, Depends, HTTPException
from app.models import UserContext, PaymentIntentPublic
from app.deps import get_current_user
from app.payments.repo import get_repos

router = APIRouter()

@router.get("/intents/{intent_id}", response_model=PaymentIntentPublic)
async def get_payment_intent(intent_id: str, current_user: UserContext = Depends(get_current_user)):
    repos = get_repos()
    intent_record = repos.intents.get_intent(intent_id)
    
    if intent_record is None:
        raise HTTPException(status_code=404, detail="Not Found")
        
    if current_user.uid != intent_record.uid and not current_user.is_admin:
        # User requested 404 instead of 403 to prevent intent ID leakage
        raise HTTPException(status_code=404, detail="Not Found")
        
    return PaymentIntentPublic(
        id=intent_record.id,
        kind=intent_record.kind,
        scope=intent_record.scope,
        courseId=intent_record.courseId,
        status=intent_record.status,
        updatedAt=intent_record.updatedAt
    )
