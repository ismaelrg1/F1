from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import (
    SqlAlchemyAdminCircuitRepository,
)
from app.api.deps import require_permissions_all, _translate_admin_error
from app.api.error_translators import get_preferred_locale

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    AdminError,
    CreateCircuit,
)

from app.models.circuits import CircuitCreateRequest, CircuitCreateResponse

router = APIRouter()

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