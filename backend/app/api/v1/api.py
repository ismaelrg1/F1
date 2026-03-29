from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    bets,
    circuits,
    contexts,
    countries,
    powerups,
    race_events,
    ranking,
    results,
    roster,
    rules,
    seasons,
    stream,
    testing_events,
    admin,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(seasons.router, prefix="/seasons", tags=["seasons"])
api_router.include_router(race_events.router, prefix="/race-events", tags=["race-events"])
api_router.include_router(testing_events.router, prefix="/testing-events", tags=["testing-events"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(circuits.router, prefix="/circuits", tags=["circuits"])
api_router.include_router(contexts.router, prefix="/contexts", tags=["contexts"])
api_router.include_router(bets.router, prefix="/bets", tags=["bets"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["ranking"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(powerups.router, prefix="/powerups", tags=["powerups"])
api_router.include_router(roster.router, prefix="/seasons", tags=["roster"])
api_router.include_router(stream.router, prefix="/contexts", tags=["stream"])


api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
