from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyOfficialResultRepository
from app.api.deps import get_current_user, _translate_management_error
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.db.enums import RoleName
from app.domain.management import ManagementError, CreateOfficialResults, UpdateOfficialResults
from app.domain.management.official_results.models import OfficialResultInput

from app.domain.management.official_results.errors import (
    OfficialResultsBetContextNotFoundError,
    OfficialResultsForbiddenGroupError,
)

from app.models.management_official_results import (
    OfficialResultRead,
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
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyOfficialResultRepository(db)
    use_case = CreateOfficialResults(repository)

    try:
        _ensure_can_manage_official_results_scope(
            repository=repository,
            user=user,
            bet_context_public_id=data.bet_context_public_id,
        )

        results = use_case.execute(
            bet_context_public_id=data.bet_context_public_id,
            event_session_public_id=data.event_session_public_id,
            testing_event_session_public_id=data.testing_event_session_public_id,
            source=data.source,
            results=[
                OfficialResultInput(
                    bet_score_code=item.bet_score_code,
                    value=item.value,
                )
                for item in data.results
            ],
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_write_response(results)


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
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyOfficialResultRepository(db)
    use_case = UpdateOfficialResults(repository)

    try:
        _ensure_can_manage_official_results_scope(
            repository=repository,
            user=user,
            bet_context_public_id=data.bet_context_public_id,
        )

        results = use_case.execute(
            bet_context_public_id=data.bet_context_public_id,
            event_session_public_id=data.event_session_public_id,
            testing_event_session_public_id=data.testing_event_session_public_id,
            source=data.source,
            results=[
                OfficialResultInput(
                    bet_score_code=item.bet_score_code,
                    value=item.value,
                )
                for item in data.results
            ],
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_write_response(results)

def _ensure_can_manage_official_results_scope(
    *,
    repository: SqlAlchemyOfficialResultRepository,
    user: User,
    bet_context_public_id,
) -> None:
    is_admin = any(role.name == RoleName.ADMIN for role in user.roles)
    if is_admin:
        return

    group_id = repository.get_bet_context_group_id(
        bet_context_public_id=bet_context_public_id,
    )
    if group_id is None:
        raise OfficialResultsBetContextNotFoundError()

    role = repository.get_group_role(
        user_id=user.id,
        group_id=group_id,
    )
    if role not in {"OWNER", "MODERATOR"}:
        raise OfficialResultsForbiddenGroupError()


def _map_write_response(results) -> OfficialResultsWriteResponse:
    return OfficialResultsWriteResponse(
        items=[
            OfficialResultRead(
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