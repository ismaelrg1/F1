from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAdminBetContextRepository
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE
from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import AdminError, GenerateBetContexts
from app.models.bet_contexts import (
    AdminBetContextGenerateRequest,
    AdminBetContextGenerateResponse,
)

router = APIRouter()


@router.post(
    "/bet-contexts/generate",
    response_model=AdminBetContextGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_bet_contexts(
    data: AdminBetContextGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> AdminBetContextGenerateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminBetContextRepository(db)
    use_case = GenerateBetContexts(repository)

    try:
        result = use_case.execute(
            season_id=data.season_id,
            group_id=data.group_id,
            include_season=data.include_season,
            include_race_events=data.include_race_events,
            include_testing_events=data.include_testing_events,
        )
        db.commit()
    except AdminError as exc:
        db.rollback()
        raise _translate_admin_error(exc, locale=locale) from exc

    return AdminBetContextGenerateResponse(
        groups_processed=result.groups_processed,
        created=result.created,
        existing=result.existing,
        season_contexts_created=result.season_contexts_created,
        race_event_contexts_created=result.race_event_contexts_created,
        testing_event_contexts_created=result.testing_event_contexts_created,
    )