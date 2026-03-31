from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminRaceEventRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateRaceEvent,
    ListRaceEvents,
    UpdateRaceEvent,
)

from app.models.race_events import (
    EventSessionCreateResponse,
    RaceEventCreateRequest,
    RaceEventCreateResponse,
)
from app.models.admin_event_reads import (
    AdminRaceEventListResponse,
    AdminRaceEventRead,
    AdminRaceEventSessionRead,
)

router = APIRouter()

@router.get(
    "/race-events",
    response_model=AdminRaceEventListResponse,
    status_code=status.HTTP_200_OK,
)
def list_race_events(
    season_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> AdminRaceEventListResponse:
    repository = SqlAlchemyAdminRaceEventRepository(db)
    use_case = ListRaceEvents(repository)

    race_events = use_case.execute(season_year=season_year)

    return AdminRaceEventListResponse(
        items=[
            AdminRaceEventRead(
                id=race_event.id,
                season_year=race_event.season.year,
                round_number=race_event.round_number,
                circuit_code=race_event.circuit.code,
                name=race_event.name,
                source_provider=race_event.source_provider,
                source_key=race_event.source_key,
                event_start=race_event.event_start,
                event_end=race_event.event_end,
                scheduled_event_start=race_event.scheduled_event_start,
                scheduled_event_end=race_event.scheduled_event_end,
                status=race_event.status,
                status_reason=race_event.status_reason,
                sessions=[
                    AdminRaceEventSessionRead(
                        id=session.id,
                        session_type=session.session_type,
                        source_provider=session.source_provider,
                        source_key=session.source_key,
                        start_datetime=session.start_datetime,
                        scheduled_start_datetime=session.scheduled_start_datetime,
                        lock_cutoff=session.lock_cutoff,
                        scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                        status=session.status,
                        status_reason=session.status_reason,
                        results_published=session.results_published,
                        results_published_at=session.results_published_at,
                    )
                    for session in sorted(race_event.event_sessions, key=lambda s: s.start_datetime)
                ],
            )
            for race_event in race_events
        ]
    )


@router.patch(
    "/race-events/{race_event_id}",
    response_model=RaceEventCreateResponse,
    status_code=status.HTTP_200_OK,
)
def update_race_event(
    race_event_id: int,
    data: RaceEventCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> RaceEventCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminRaceEventRepository(db)
    use_case = UpdateRaceEvent(repository)

    try:
        race_event = use_case.execute(
            race_event_id=race_event_id,
            season_year=data.season_year,
            round_number=data.round_number,
            circuit_code=data.circuit_code,
            name=data.name,
            source_provider=data.source_provider,
            source_key=data.source_key,
            event_start=data.event_start,
            event_end=data.event_end,
            scheduled_event_start=data.scheduled_event_start,
            scheduled_event_end=data.scheduled_event_end,
            status=data.status,
            status_reason=data.status_reason,
            sessions=[session.model_dump() for session in data.sessions],
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return RaceEventCreateResponse(
        public_id=race_event.public_id,
        season_year=race_event.season.year,
        round_number=race_event.round_number,
        circuit_code=race_event.circuit.code,
        name=race_event.name,
        source_provider=race_event.source_provider,
        source_key=race_event.source_key,
        event_start=race_event.event_start,
        event_end=race_event.event_end,
        scheduled_event_start=race_event.scheduled_event_start,
        scheduled_event_end=race_event.scheduled_event_end,
        status=race_event.status,
        status_reason=race_event.status_reason,
        sessions=[
            EventSessionCreateResponse(
                public_id=session.public_id,
                session_type=session.session_type,
                source_provider=session.source_provider,
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                lock_cutoff=session.lock_cutoff,
                scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                status=session.status,
                status_reason=session.status_reason,
                results_published=session.results_published,
                results_published_at=session.results_published_at,
            )
            for session in sorted(race_event.event_sessions, key=lambda s: s.start_datetime)
        ],
    )


@router.post(
    "/race-events",
    response_model=RaceEventCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_race_event(
    data: RaceEventCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> RaceEventCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminRaceEventRepository(db)
    use_case = CreateRaceEvent(repository)

    try:
        race_event = use_case.execute(
            season_year=data.season_year,
            round_number=data.round_number,
            circuit_code=data.circuit_code,
            name=data.name,
            source_provider=data.source_provider,
            source_key=data.source_key,
            event_start=data.event_start,
            event_end=data.event_end,
            scheduled_event_start=data.scheduled_event_start,
            scheduled_event_end=data.scheduled_event_end,
            status=data.status,
            status_reason=data.status_reason,
            sessions=[session.model_dump() for session in data.sessions],
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return RaceEventCreateResponse(
        public_id=race_event.public_id,
        season_year=race_event.season.year,
        round_number=race_event.round_number,
        circuit_code=race_event.circuit.code,
        name=race_event.name,
        source_provider=race_event.source_provider,
        source_key=race_event.source_key,
        event_start=race_event.event_start,
        event_end=race_event.event_end,
        scheduled_event_start=race_event.scheduled_event_start,
        scheduled_event_end=race_event.scheduled_event_end,
        status=race_event.status,
        status_reason=race_event.status_reason,
        sessions=[
            EventSessionCreateResponse(
                public_id=session.public_id,
                session_type=session.session_type,
                source_provider=session.source_provider,
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                lock_cutoff=session.lock_cutoff,
                scheduled_lock_cutoff=session.scheduled_lock_cutoff,
                status=session.status,
                status_reason=session.status_reason,
                results_published=session.results_published,
                results_published_at=session.results_published_at,
            )
            for session in sorted(race_event.event_sessions, key=lambda s: s.start_datetime)
        ],
    )