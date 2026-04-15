from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminCountryRepository,
    SqlAlchemyCountryRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale
from app.core.permissions import COMPETITION_MANAGE
from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateCountry,
)
from app.domain.countries import ListCountries
from app.models.countries import (
    CountryCreateRequest,
    CountryCreateResponse,
    CountryListResponse,
    CountryRead,
)

router = APIRouter()


@router.post(
    "/countries",
    response_model=CountryCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_country(
    data: CountryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
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


@router.get(
    "/countries",
    response_model=CountryListResponse,
)
def list_countries(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> CountryListResponse:
    repository = SqlAlchemyCountryRepository(db)
    use_case = ListCountries(repository)

    countries = use_case.execute()

    return CountryListResponse(
        items=[CountryRead.model_validate(country) for country in countries]
    )
