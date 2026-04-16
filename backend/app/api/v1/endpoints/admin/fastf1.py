from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.adapters.fastf1 import FastF1AdminRepository
from app.api.deps import require_permissions_all
from app.core.permissions import COMPETITION_MANAGE

from app.db.auth import User
from app.db.session import get_db
from app.domain.admin import (
    ListFastF1RaceEventPreviews,
    ListFastF1TestingEventPreviews,

)

from app.models.admin_fastf1 import (
    FastF1RaceEventPreviewListResponse,
    FastF1RaceEventPreview,
    FastF1SessionPreview,
    FastF1TestingEventPreviewListResponse,
    FastF1TestingEventPreview,
    FastF1TestingSessionPreview,
)

router = APIRouter()

@router.get(
    "/fastf1/race-events/{year}",
    response_model=FastF1RaceEventPreviewListResponse,
    status_code=status.HTTP_200_OK,
)
def list_fastf1_race_events(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> FastF1RaceEventPreviewListResponse:
    repository = FastF1AdminRepository(db)
    use_case = ListFastF1RaceEventPreviews(repository)

    items = use_case.execute(year=year)

    return FastF1RaceEventPreviewListResponse(
        items=[
            FastF1RaceEventPreview(
                season_year=item.season_year,
                round_number=item.round_number,
                country_name=item.country_name,
                country_iso2_suggestion=item.country_iso2_suggestion,
                event_name=item.event_name,
                official_event_name=item.official_event_name,
                location=item.location,
                event_format=item.event_format,
                source_provider=item.source_provider,
                source_key=item.source_key,
                circuit_code_suggestion=item.circuit_code_suggestion,
                scheduled_event_end_utc=item.scheduled_event_end_utc,
                sessions=[
                    FastF1SessionPreview(
                        order=session.order,
                        fastf1_name=session.fastf1_name,
                        session_type=session.session_type,
                        source_provider=session.source_provider,
                        source_key=session.source_key,
                        scheduled_start_utc=session.scheduled_start_utc,
                    )
                    for session in item.sessions
                ],
            )
            for item in items
        ]
    )


@router.get(
    "/fastf1/testing-events/{year}",
    response_model=FastF1TestingEventPreviewListResponse,
    status_code=status.HTTP_200_OK,
)
def list_fastf1_testing_events(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions_all(COMPETITION_MANAGE)),
) -> FastF1TestingEventPreviewListResponse:
    repository = FastF1AdminRepository(db)
    use_case = ListFastF1TestingEventPreviews(repository)

    items = use_case.execute(year=year)

    return FastF1TestingEventPreviewListResponse(
        items=[
            FastF1TestingEventPreview(
                season_year=item.season_year,
                country_name=item.country_name,
                country_iso2_suggestion=item.country_iso2_suggestion,
                event_name=item.event_name,
                official_event_name=item.official_event_name,
                location=item.location,
                event_format=item.event_format,
                source_provider=item.source_provider,
                source_key=item.source_key,
                circuit_code_suggestion=item.circuit_code_suggestion,
                scheduled_event_end_utc=item.scheduled_event_end_utc,
                sessions=[
                    FastF1TestingSessionPreview(
                        order=session.order,
                        fastf1_name=session.fastf1_name,
                        source_provider=session.source_provider,
                        source_key=session.source_key,
                        scheduled_start_utc=session.scheduled_start_utc,
                    )
                    for session in item.sessions
                ],
            )
            for item in items
        ]
    )