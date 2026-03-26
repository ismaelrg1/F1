from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.auth import User
from app.db.session import get_db

router = APIRouter()


@router.post("/")
def create_bet(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"created_by": user.id}
