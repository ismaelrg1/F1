from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyCountryRepository
from app.api.deps import get_current_user
from app.db.auth import User
from app.db.session import get_db
from app.domain.countries import ListCountries
from app.models.countries import CountryListResponse, CountryRead

router = APIRouter()


@router.get(
    "/",
    response_model=CountryListResponse,    
)
def list_countries(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CountryListResponse:
    repository = SqlAlchemyCountryRepository(db)
    use_case = ListCountries(repository)

    countries = use_case.execute()

    return CountryListResponse(
        items=[CountryRead.model_validate(country) for country in countries]
    )
