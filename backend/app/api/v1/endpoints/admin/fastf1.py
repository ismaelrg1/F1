from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.fastf1 import FastF1AdminRepository
from app.api.deps import require_permissions_all

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    ListFastF1RaceEventPreviews,
    ListFastF1TestingEventPreviews,

)

from app.models.admin_fastf1 import FastF1RaceEventPreviewListResponse, FastF1TestingEventPreviewListResponse

router = APIRouter()

@router.get(
    "/fastf1/race-events/{year}",
    response_model=FastF1RaceEventPreviewListResponse,
    status_code=status.HTTP_200_OK,
)
def list_fastf1_race_events(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> FastF1RaceEventPreviewListResponse:
    repository = FastF1AdminRepository(db)
    use_case = ListFastF1RaceEventPreviews(repository)

    items = use_case.execute(year=year)

    return FastF1RaceEventPreviewListResponse(items=items)


@router.get(
    "/fastf1/testing-events/{year}",
    response_model=FastF1TestingEventPreviewListResponse,
    status_code=status.HTTP_200_OK,
)
def list_fastf1_testing_events(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> FastF1TestingEventPreviewListResponse:
    repository = FastF1AdminRepository(db)
    use_case = ListFastF1TestingEventPreviews(repository)

    items = use_case.execute(year=year)

    return FastF1TestingEventPreviewListResponse(items=items)