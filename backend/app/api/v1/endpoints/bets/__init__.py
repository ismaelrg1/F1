from fastapi import APIRouter

from . import race_events, seasons, testing_events

router = APIRouter()
router.include_router(race_events.router)
router.include_router(seasons.router)
router.include_router(testing_events.router)

__all__ = [
    "router",
    "race_events",
    "seasons",
    "testing_events",
]