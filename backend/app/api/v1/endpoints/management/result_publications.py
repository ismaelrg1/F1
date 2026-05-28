from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy.management.result_publication_repository import (
    SqlAlchemyResultPublicationRepository,
)
from app.api.deps import (
    get_current_user,
    resolve_management_group_id,
    _translate_management_error,
)
from app.api.error_translators import get_preferred_locale
from app.db.auth import User
from app.db.session import get_db
from app.domain.management import ManagementError
from app.domain.management.result_publications import (
    PublishRaceEventResults,
    PublishSeasonResults,
    PublishTestingEventResults,
    UnpublishRaceEventResults,
    UnpublishSeasonResults,
    UnpublishTestingEventResults,
    ResultPublicationForbiddenGroupError,
)
from app.models.management_result_publications import (
    ResultPublicationDeleteResponse,
    ResultPublicationRead,
    ResultPublicationWriteRequest,
)

router = APIRouter()


@router.post(
    "/result-publications/race-events/{race_event_public_id}",
    response_model=ResultPublicationRead,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def publish_race_event_results(
    race_event_public_id: UUID,
    payload: ResultPublicationWriteRequest,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationRead:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )
    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = PublishRaceEventResults(repository)

    try:
        result = use_case.execute(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
            event_session_public_id=session_id,
            published_by_user_id=user.id,
            note=payload.note,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_response(result)


@router.delete(
    "/result-publications/race-events/{race_event_public_id}",
    response_model=ResultPublicationDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def unpublish_race_event_results(
    race_event_public_id: UUID,
    request: Request,
    session_id: UUID | None = Query(default=None),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationDeleteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )

    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = UnpublishRaceEventResults(repository)

    try:
        use_case.execute(
            group_id=group_id,
            race_event_public_id=race_event_public_id,
            event_session_public_id=session_id,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ResultPublicationDeleteResponse(deleted=True)


@router.post(
    "/result-publications/testing-events/{testing_event_public_id}",
    response_model=ResultPublicationRead,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def publish_testing_event_results(
    testing_event_public_id: UUID,
    payload: ResultPublicationWriteRequest,
    request: Request,
    session_id: UUID = Query(...),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationRead:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )
    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = PublishTestingEventResults(repository)

    try:
        result = use_case.execute(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
            published_by_user_id=user.id,
            note=payload.note,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_response(result)


@router.delete(
    "/result-publications/testing-events/{testing_event_public_id}",
    response_model=ResultPublicationDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def unpublish_testing_event_results(
    testing_event_public_id: UUID,
    request: Request,
    session_id: UUID = Query(...),
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationDeleteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )
    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = UnpublishTestingEventResults(repository)

    try:
        use_case.execute(
            group_id=group_id,
            testing_event_public_id=testing_event_public_id,
            testing_event_session_public_id=session_id,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ResultPublicationDeleteResponse(deleted=True)


@router.post(
    "/result-publications/seasons/{season_year}",
    response_model=ResultPublicationRead,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def publish_season_results(
    season_year: int,
    payload: ResultPublicationWriteRequest,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationRead:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )

    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = PublishSeasonResults(repository)

    try:
        result = use_case.execute(
            group_id=group_id,
            season_year=season_year,
            published_by_user_id=user.id,
            note=payload.note,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return _map_response(result)


@router.delete(
    "/result-publications/seasons/{season_year}",
    response_model=ResultPublicationDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def unpublish_season_results(
    season_year: int,
    request: Request,
    x_group_id: UUID | None = Header(default=None, alias="X-Group-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResultPublicationDeleteResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)
    group_id = resolve_management_group_id(
        db=db,
        user=user,
        x_group_id=x_group_id,
        locale=locale,
        forbidden_error=ResultPublicationForbiddenGroupError(),
    )

    repository = SqlAlchemyResultPublicationRepository(db)
    use_case = UnpublishSeasonResults(repository)

    try:
        use_case.execute(
            group_id=group_id,
            season_year=season_year,
        )
        db.commit()
    except ManagementError as exc:
        db.rollback()
        raise _translate_management_error(exc, locale=locale) from exc

    return ResultPublicationDeleteResponse(deleted=True)


def _map_response(result) -> ResultPublicationRead:
    return ResultPublicationRead(
        race_event_public_id=result.race_event_public_id,
        event_session_public_id=result.event_session_public_id,
        testing_event_public_id=result.testing_event_public_id,
        testing_event_session_public_id=result.testing_event_session_public_id,
        season_year=result.season_year,
        published_at=result.published_at,
        note=result.note,
    )
