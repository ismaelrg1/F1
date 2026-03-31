from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session

from app.adapters.fastf1 import FastF1AdminRepository
from app.adapters.sqlalchemy import (
    SqlAlchemyAdminCountryRepository,
    SqlAlchemyAdminSeasonRepository,
    SqlAlchemyAdminCircuitRepository,
    SqlAlchemyAdminTestingEventRepository,
    SqlAlchemyAdminRaceEventRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    PublishResults,
    AdminError,
    CreateSeason,
    CreateCountry,
    CreateCircuit,
    ListFastF1RaceEventPreviews,
    ListFastF1TestingEventPreviews,
    ListRaceEvents,
    ListTestingEvents,
    CreateTestingEvent,
    CreateRaceEvent,
    UpdateTestingEvent,
    UpdateRaceEvent,
)
from app.models.seasons import SeasonCreateRequest, SeasonCreateResponse
from app.models.countries import CountryCreateRequest, CountryCreateResponse
from app.models.circuits import CircuitCreateRequest, CircuitCreateResponse
from app.models.admin_fastf1 import FastF1RaceEventPreviewListResponse, FastF1TestingEventPreviewListResponse
from app.models.testing_events import (
    TestingEventCreateRequest,
    TestingEventCreateResponse,
    TestingEventSessionCreateResponse,
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
    AdminTestingEventListResponse,
    AdminTestingEventRead,
    AdminTestingEventSessionRead,
)

router = APIRouter()

@router.post("/results/publish")
def publish_results(
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("RESULTS_PUBLISH")),
):
    return PublishResults().execute(user.id)


@router.post(
        "/seasons",
        response_model=SeasonCreateResponse,
        status_code=status.HTTP_201_CREATED
)
def create_season(
    data: SeasonCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE"))

) -> SeasonCreateResponse:
    
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminSeasonRepository(db)
    use_case = CreateSeason(repository)

    try:
        season = use_case.execute(
            year=data.year,
            is_active=data.is_active,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return SeasonCreateResponse.model_validate(season)



@router.post(
    "/countries",
    response_model=CountryCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_country(
    data: CountryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> CountryCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminCountryRepository(db)
    use_case = CreateCountry(repository)

    try:
        country = use_case.execute(
            iso2=data.iso2,
            name=data.name,
            flag_asset_url=data.flag_asset_url,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc

    return CountryCreateResponse.model_validate(country)



@router.post(
    "/circuits",
    response_model=CircuitCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_circuit(
    data: CircuitCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> CircuitCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminCircuitRepository(db)
    use_case = CreateCircuit(repository)

    try:
        circuit = use_case.execute(
            code=data.code,
            name=data.name,
            country_iso2=data.country_iso2,
            map_asset_url=data.map_asset_url,
            image_asset_url=data.image_asset_url,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc
    
    return CircuitCreateResponse(
        id=circuit.id,
        code=circuit.code,
        name=circuit.name,
        country_iso2=circuit.country.iso2,
        map_asset_url=circuit.map_asset_url,
        image_asset_url=circuit.image_asset_url,
    )



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


@router.post(
    "/testing-events",
    response_model=TestingEventCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_testing_event(
    data: TestingEventCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> TestingEventCreateResponse:
    locale = get_preferred_locale(request.headers.get("accept-language") if request else None)

    repository = SqlAlchemyAdminTestingEventRepository(db)
    use_case = CreateTestingEvent(repository)

    try:
        testing_event = use_case.execute(
            season_year=data.season_year,
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

    return TestingEventCreateResponse(
        id=testing_event.id,
        season_year=testing_event.season.year,
        circuit_code=testing_event.circuit.code,
        name=testing_event.name,
        source_provider=testing_event.source_provider,
        source_key=testing_event.source_key,
        event_start=testing_event.event_start,
        event_end=testing_event.event_end,
        scheduled_event_start=testing_event.scheduled_event_start,
        scheduled_event_end=testing_event.scheduled_event_end,
        status=testing_event.status,
        status_reason=testing_event.status_reason,
        sessions=[
            TestingEventSessionCreateResponse(
                id=session.id,
                session_order=session.session_order,
                name=session.name,
                source_provider=session.source_provider,
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in sorted(testing_event.sessions, key=lambda s: s.session_order)
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
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
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

    return TestingEventCreateResponse(
        id=testing_event.id,
        season_year=testing_event.season.year,
        circuit_code=testing_event.circuit.code,
        name=testing_event.name,
        source_provider=testing_event.source_provider,
        source_key=testing_event.source_key,
        event_start=testing_event.event_start,
        event_end=testing_event.event_end,
        scheduled_event_start=testing_event.scheduled_event_start,
        scheduled_event_end=testing_event.scheduled_event_end,
        status=testing_event.status,
        status_reason=testing_event.status_reason,
        sessions=[
            TestingEventSessionCreateResponse(
                id=session.id,
                session_order=session.session_order,
                name=session.name,
                source_provider=session.source_provider,
                source_key=session.source_key,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in sorted(testing_event.sessions, key=lambda s: s.session_order)
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
            EventSessionCreateResponse(
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
            EventSessionCreateResponse(
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


@router.get(
    "/testing-events",
    response_model=AdminTestingEventListResponse,
    status_code=status.HTTP_200_OK,
)
def list_testing_events(
    season_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all("COMPETITION_MANAGE")),
) -> AdminTestingEventListResponse:
    repository = SqlAlchemyAdminTestingEventRepository(db)
    use_case = ListTestingEvents(repository)

    testing_events = use_case.execute(season_year=season_year)

    return AdminTestingEventListResponse(
        items=[
            AdminTestingEventRead(
                id=testing_event.id,
                season_year=testing_event.season.year,
                circuit_code=testing_event.circuit.code,
                name=testing_event.name,
                source_provider=testing_event.source_provider,
                source_key=testing_event.source_key,
                event_start=testing_event.event_start,
                event_end=testing_event.event_end,
                scheduled_event_start=testing_event.scheduled_event_start,
                scheduled_event_end=testing_event.scheduled_event_end,
                status=testing_event.status,
                status_reason=testing_event.status_reason,
                sessions=[
                    AdminTestingEventSessionRead(
                        id=session.id,
                        session_order=session.session_order,
                        name=session.name,
                        source_provider=session.source_provider,
                        source_key=session.source_key,
                        start_datetime=session.start_datetime,
                        end_datetime=session.end_datetime,
                        scheduled_start_datetime=session.scheduled_start_datetime,
                        scheduled_end_datetime=session.scheduled_end_datetime,
                    )
                    for session in sorted(testing_event.sessions, key=lambda s: s.session_order)
                ],
            )
            for testing_event in testing_events
        ]
    )