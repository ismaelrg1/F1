from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemySeasonRepository
from app.api.deps import get_current_user
from app.db.auth import User
from app.db.session import get_db
from app.domain.seasons import ListSeasons
from app.models.seasons import SeasonYearRead, SeasonYearsResponse

router = APIRouter()


@router.get(
    "/seasons",
    response_model=SeasonYearsResponse,
)
def get_seasons(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SeasonYearsResponse:
    repository = SqlAlchemySeasonRepository(db)
    use_case = ListSeasons(repository)
    seasons = use_case.execute(is_active=is_active)

    return SeasonYearsResponse(
        items=[SeasonYearRead(year=season.year) for season in seasons]
    )
