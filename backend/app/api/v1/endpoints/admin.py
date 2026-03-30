from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminCountryRepository,
    SqlAlchemyAdminSeasonRepository,
    SqlAlchemyAdminCircuitRepository,
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
)
from app.models.seasons import SeasonCreateRequest, SeasonCreateResponse
from app.models.countries import CountryCreateRequest, CountryCreateResponse
from app.models.circuits import CircuitCreateRequest, CircuitCreateResponse


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
            country_id=data.country_id,
            map_asset_url=data.map_asset_url,
            image_asset_url=data.image_asset_url,
        )
    except AdminError as exc:
        raise _translate_admin_error(exc, locale=locale) from exc
    
    return CircuitCreateResponse.model_validate(circuit)