from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_all
from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import PublishResults

router = APIRouter()


@router.post("/results/publish")
def publish_results(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("RESULTS_PUBLISH")),
):
    return PublishResults().execute(user.id)
