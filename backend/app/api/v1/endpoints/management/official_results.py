from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAccessRepository, SqlAlchemyOfficialResultRepository
from app.api.deps import get_current_user, _translate_management_error
from app.api.error_translators import get_preferred_locale
from app.core.config import settings
from app.db.auth import User
from app.db.enums import RoleName
from app.db.session import get_db
from app.db.social.group_membership import GroupRole
from app.domain.access import ResolveCurrentGroup
from app.domain.management import ManagementError
from app.domain.management.official_results.answers import (
    CreateOfficialResults,
    OfficialResultInput,
    UpdateOfficialResults,
)
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
    "/official-results/race-events/{race_event_public_id}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_race_event_official_results(
    race_event_public_id: UUID,
    data: OfficialResultsWriteRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_race_bet_context_public_id(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
    )

    return _create_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
        event_session_public_id=session_id,
    )


@router.patch(
    "/official-results/race-events/{race_event_public_id}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
def update_race_event_official_results(
    race_event_public_id: UUID,
    data: OfficialResultsWriteRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_race_bet_context_public_id(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
        )
    )

    return _update_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
        event_session_public_id=session_id,
    )


@router.post(
    "/official-results/testing-events/{testing_event_public_id}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_testing_event_official_results(
    testing_event_public_id: UUID,
    data: OfficialResultsWriteRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_testing_bet_context_public_id(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
    )

    return _create_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
        testing_event_session_public_id=session_id,
    )


@router.patch(
    "/official-results/testing-events/{testing_event_public_id}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
def update_testing_event_official_results(
    testing_event_public_id: UUID,
    data: OfficialResultsWriteRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_testing_bet_context_public_id(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
        )
    )

    return _update_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
        testing_event_session_public_id=session_id,
    )


@router.post(
    "/official-results/seasons/{season_year}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_season_official_results(
    season_year: int,
    data: OfficialResultsWriteRequest,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_season_bet_context_public_id(
            group_id=group_id,
            season_year=season_year,
        )
    )

    return _create_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
    )


@router.patch(
    "/official-results/seasons/{season_year}",
    response_model=OfficialResultsWriteResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
def update_season_official_results(
    season_year: int,
    data: OfficialResultsWriteRequest,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfficialResultsWriteResponse:
    repository = SqlAlchemyOfficialResultRepository(db)
    group_id = _resolve_management_group_id(db=db, user=user, x_group_id=x_group_id)
    bet_context_public_id = _require_bet_context_public_id(
        repository.get_season_bet_context_public_id(
            group_id=group_id,
            season_year=season_year,
        )
    )

    return _update_results_for_scope(
        data=data,
        request=request,
        db=db,
        bet_context_public_id=bet_context_public_id,
    )


def _resolve_management_group_id(
    *,
    db: Session,
    user: User,
    x_group_id: UUID | None,
) -> int:
    if x_group_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "management.group_required",
                    "message": "X-Group-Id is required.",
                }
            },
        )

    access_repository = SqlAlchemyAccessRepository(db)
    group_ref = ResolveCurrentGroup(
        access_repository,
        default_group_id=settings.default_group_id,
        default_group_public_id=getattr(settings, "default_group_public_id", None),
    ).execute(str(x_group_id))

    is_admin = any(role.name == RoleName.ADMIN for role in user.roles)
    if is_admin:
        return group_ref.id

    group_role = access_repository.get_group_role(
        user_id=user.id,
        group_id=group_ref.id,
    )
    if group_role not in {GroupRole.OWNER, GroupRole.MODERATOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "management.official_results.forbidden_group",
                    "message": "You are not allowed to manage official results for this group.",
                }
            },
        )

    return group_ref.id


def _create_results_for_scope(
    *,
    data: OfficialResultsWriteRequest,
    request: Request,
    db: Session,
    bet_context_public_id: UUID,
    event_session_public_id: UUID | None = None,
    testing_event_session_public_id: UUID | None = None,
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyOfficialResultRepository(db)
    use_case = CreateOfficialResults(repository)

    try:
        results = use_case.execute(
            bet_context_public_id=bet_context_public_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
            source=data.source,
            results=_map_inputs(data),
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_write_response(results)


def _update_results_for_scope(
    *,
    data: OfficialResultsWriteRequest,
    request: Request,
    db: Session,
    bet_context_public_id: UUID,
    event_session_public_id: UUID | None = None,
    testing_event_session_public_id: UUID | None = None,
) -> OfficialResultsWriteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    repository = SqlAlchemyOfficialResultRepository(db)
    use_case = UpdateOfficialResults(repository)

    try:
        results = use_case.execute(
            bet_context_public_id=bet_context_public_id,
            event_session_public_id=event_session_public_id,
            testing_event_session_public_id=testing_event_session_public_id,
            source=data.source,
            results=_map_inputs(data),
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_write_response(results)


def _map_inputs(data: OfficialResultsWriteRequest) -> list[OfficialResultInput]:
    return [
        OfficialResultInput(
            bet_score_code=item.bet_score_code,
            value=item.value,
        )
        for item in data.results
    ]


def _require_bet_context_public_id(value: UUID | None) -> UUID:
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "management.official_results.bet_context_not_found",
                    "message": "Bet context not found.",
                }
            },
        )
    return value


def _map_write_response(results) -> OfficialResultsWriteResponse:
    return OfficialResultsWriteResponse(
        items=[
            OfficialResultRead(
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
