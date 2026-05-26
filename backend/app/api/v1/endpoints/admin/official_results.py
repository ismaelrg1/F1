from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAdminOfficialResultRepository
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import SCORING_MANAGE
from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import AdminError, CreateOfficialResults, UpdateOfficialResults
from app.domain.admin.official_results.models import AdminOfficialResultInput
from app.models.admin_official_results import (
    AdminOfficialResultRead,
    OfficialResultsWriteRequest,
    OfficialResultsWriteResponse,
)

router = APIRouter()


@router.post(
    "/official-results",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_official_results(
    data: OfficialResultsWriteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(SCORING_MANAGE)),
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminOfficialResultRepository(db)
    use_case = CreateOfficialResults(repository)

    try:
        results = use_case.execute(
            bet_context_public_id=data.bet_context_public_id,
            event_session_public_id=data.event_session_public_id,
            testing_event_session_public_id=data.testing_event_session_public_id,
            source=data.source,
            results=[
                AdminOfficialResultInput(
                    bet_score_code=item.bet_score_code,
                    value=item.value,
                )
                for item in data.results
            ],
        )
        db.commit()
    except AdminError as exc:
        db.rollback()
        raise _translate_admin_error(exc, locale=locale) from exc

    return OfficialResultsWriteResponse(
        items=[
            AdminOfficialResultRead(
                bet_context_public_id=item.bet_context_public_id,
                event_session_public_id=item.event_session_public_id,
                testing_event_session_public_id=item.testing_event_session_public_id,
                bet_score_code=item.bet_score_code,
                label=item.label,
                value=item.value,
                source=item.source,
                created_at=item.created_at,
            )
            for item in results
        ]
    )


@router.patch(
    "/official-results",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
def update_official_results(
    data: OfficialResultsWriteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(SCORING_MANAGE)),
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminOfficialResultRepository(db)
    use_case = UpdateOfficialResults(repository)

    try:
        results = use_case.execute(
            bet_context_public_id=data.bet_context_public_id,
            event_session_public_id=data.event_session_public_id,
            testing_event_session_public_id=data.testing_event_session_public_id,
            source=data.source,
            results=[
                AdminOfficialResultInput(
                    bet_score_code=item.bet_score_code,
                    value=item.value,
                )
                for item in data.results
            ],
        )
        db.commit()
    except AdminError as exc:
        db.rollback()
        raise _translate_admin_error(exc, locale=locale) from exc

    return OfficialResultsWriteResponse(
        items=[
            AdminOfficialResultRead(
                bet_context_public_id=item.bet_context_public_id,
                event_session_public_id=item.event_session_public_id,
                testing_event_session_public_id=item.testing_event_session_public_id,
                bet_score_code=item.bet_score_code,
                label=item.label,
                value=item.value,
                source=item.source,
                created_at=item.created_at,
            )
            for item in results
        ]
    )