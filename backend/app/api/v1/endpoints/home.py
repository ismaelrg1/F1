from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy import SqlAlchemyHomeRepository
from app.api.deps import get_current_user
from app.db.auth import User
from app.db.session import get_db
from app.domain.home import GetHome
from app.models.home import HomeNextEventRead, HomeResponse

router = APIRouter()


@router.get(
    "/home",
    response_model=HomeResponse,
)
def get_home(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HomeResponse:
    repository = SqlAlchemyHomeRepository(db)
    use_case = GetHome(repository)
    result = use_case.execute()

    if result is None:
        return HomeResponse(next_event=None)

    next_event = result.event

    return HomeResponse(
        next_event=HomeNextEventRead(
            public_id=next_event.public_id,
            event_kind=result.kind,
            season_year=next_event.season.year,
            round_number=getattr(next_event, "round_number", None),
            name=next_event.name,
            circuit_code=next_event.circuit.code,
            circuit_name=next_event.circuit.name,
            country_name=next_event.circuit.country.name,
            event_start=next_event.event_start,
            event_end=next_event.event_end,
            scheduled_event_start=next_event.scheduled_event_start,
            scheduled_event_end=next_event.scheduled_event_end,
            status=next_event.status.value,
        )
    )
