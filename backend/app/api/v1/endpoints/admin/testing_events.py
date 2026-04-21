from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyAdminTestingEventRepository
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE
from app.db.auth import User
from app.db.enums import SourceProvider, TestingEventStatus
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateTestingEvent,
    ListTestingEvents,
    UpdateTestingEvent,
)
from app.domain.admin.testing_events.models import AdminTestingEventSessionWrite
from app.models.admin_event_reads import (
    AdminTestingEventListResponse,
    AdminTestingEventRead,
    AdminTestingEventSessionRead,
)
from app.models.testing_events import (
    TestingEventCreateRequest,
    TestingEventCreateResponse,
    TestingEventSessionCreateResponse,
)

router = APIRouter()

@router.get(
    "/testing-events",
    response_model=AdminTestingEventListResponse,
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
)
def list_testing_events(
    season_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> AdminTestingEventListResponse:
    repository = SqlAlchemyAdminTestingEventRepository(db)
    use_case = ListTestingEvents(repository)

    testing_events = use_case.execute(season_year=season_year)

    return AdminTestingEventListResponse(
        items=[
            AdminTestingEventRead(
                id=testing_event.id,
                season_year=testing_event.season_year,
                circuit_code=testing_event.circuit_code,
                name=testing_event.name,
                source_provider=SourceProvider(testing_event.source_provider),
                source_key=testing_event.source_key,
                event_start=testing_event.event_start,
                event_end=testing_event.event_end,
                scheduled_event_start=testing_event.scheduled_event_start,
                scheduled_event_end=testing_event.scheduled_event_end,
                status=TestingEventStatus(testing_event.status),
                status_reason=testing_event.status_reason,
                sessions=[
                    AdminTestingEventSessionRead(
                        id=session.id,
                        session_order=session.session_order,
                        name=session.name,
                        source_provider=SourceProvider(session.source_provider),
                        source_key=session.source_key,
                        start_datetime=session.start_datetime,
                        end_datetime=session.end_datetime,
                        scheduled_start_datetime=session.scheduled_start_datetime,
                        scheduled_end_datetime=session.scheduled_end_datetime,
                    )
                    for session in testing_event.sessions
                ],
            )
            for testing_event in testing_events
        ]
    )


@router.post(
    "/testing-events",
    response_model=TestingEventCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_testing_event(
    data: TestingEventCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> TestingEventCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminTestingEventRepository(db)
    use_case = CreateTestingEvent(repository)

    try:
        testing_event = use_case.execute(
            season_year=data.season_year,
            circuit_code=data.circuit_code,
            name=data.name,
            source_provider=data.source_provider.value,
            source_key=data.source_key,
            event_start=data.event_start,
            event_end=data.event_end,
            scheduled_event_start=data.scheduled_event_start,
            scheduled_event_end=data.scheduled_event_end,
            status=data.status.value if data.status is not None else None,
            status_reason=data.status_reason,
            sessions=[
                AdminTestingEventSessionWrite(
                    session_order=session.session_order,
                    name=session.name,
                    source_provider=session.source_provider.value,
                    source_key=session.source_key,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in data.sessions
            ],
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return TestingEventCreateResponse(
        public_id=testing_event.public_id,
        season_year=testing_event.season_year,
        circuit_code=testing_event.circuit_code,
        name=testing_event.name,
        source_provider=SourceProvider(testing_event.source_provider),
        source_key=testing_event.source_key,
        event_start=testing_event.event_start,
        event_end=testing_event.event_end,
        scheduled_event_start=testing_event.scheduled_event_start,
        scheduled_event_end=testing_event.scheduled_event_end,
        status=TestingEventStatus(testing_event.status),
        status_reason=testing_event.status_reason,
        sessions=[
            TestingEventSessionCreateResponse(
                public_id=session.public_id,
                session_order=session.session_order,
                name=session.name,
                source_provider=SourceProvider(session.source_provider),
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in testing_event.sessions
        ],
    )


@router.patch(
    "/testing-events/{testing_event_id}",
    response_model=TestingEventCreateResponse,
    status_code=status.HTTP_200_OK,
)
def update_testing_event(
    testing_event_id: int,
    data: TestingEventCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> TestingEventCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminTestingEventRepository(db)
    use_case = UpdateTestingEvent(repository)

    try:
        testing_event = use_case.execute(
            testing_event_id=testing_event_id,
            season_year=data.season_year,
            circuit_code=data.circuit_code,
            name=data.name,
            source_provider=data.source_provider.value,
            source_key=data.source_key,
            event_start=data.event_start,
            event_end=data.event_end,
            scheduled_event_start=data.scheduled_event_start,
            scheduled_event_end=data.scheduled_event_end,
            status=data.status.value if data.status is not None else None,
            status_reason=data.status_reason,
            sessions=[
                AdminTestingEventSessionWrite(
                    session_order=session.session_order,
                    name=session.name,
                    source_provider=session.source_provider.value,
                    source_key=session.source_key,
                    start_datetime=session.start_datetime,
                    end_datetime=session.end_datetime,
                    scheduled_start_datetime=session.scheduled_start_datetime,
                    scheduled_end_datetime=session.scheduled_end_datetime,
                )
                for session in data.sessions
            ],
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return TestingEventCreateResponse(
        public_id=testing_event.public_id,
        season_year=testing_event.season_year,
        circuit_code=testing_event.circuit_code,
        name=testing_event.name,
        source_provider=SourceProvider(testing_event.source_provider),
        source_key=testing_event.source_key,
        event_start=testing_event.event_start,
        event_end=testing_event.event_end,
        scheduled_event_start=testing_event.scheduled_event_start,
        scheduled_event_end=testing_event.scheduled_event_end,
        status=TestingEventStatus(testing_event.status),
        status_reason=testing_event.status_reason,
        sessions=[
            TestingEventSessionCreateResponse(
                public_id=session.public_id,
                session_order=session.session_order,
                name=session.name,
                source_provider=SourceProvider(session.source_provider),
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in testing_event.sessions
        ],
    )