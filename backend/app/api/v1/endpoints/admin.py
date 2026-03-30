from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.fastf1 import FastF1AdminRepository
from app.adapters.sqlalchemy import (
    SqlAlchemyAdminCountryRepository,
    SqlAlchemyAdminSeasonRepository,
    SqlAlchemyAdminCircuitRepository,
    SqlAlchemyAdminTestingEventRepository,
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
    CreateTestingEvent,
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
            event_start=data.event_start,
            event_end=data.event_end,
            scheduled_event_start=data.scheduled_event_start,
            scheduled_event_end=data.scheduled_event_end,
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
        event_start=testing_event.event_start,
        event_end=testing_event.event_end,
        scheduled_event_start=testing_event.scheduled_event_start,
        scheduled_event_end=testing_event.scheduled_event_end,
        status=testing_event.status.value,
        status_reason=testing_event.status_reason,
        sessions=[
            TestingEventSessionCreateResponse(
                id=session.id,
                session_order=session.session_order,
                name=session.name,
                start_datetime=session.start_datetime,
                end_datetime=session.end_datetime,
                scheduled_start_datetime=session.scheduled_start_datetime,
                scheduled_end_datetime=session.scheduled_end_datetime,
            )
            for session in sorted(testing_event.sessions, key=lambda s: s.session_order)
        ],
    )
