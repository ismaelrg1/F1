from app.models.powerups import UsePowerupRequest


class ListAssignmentsForSeason:
    def execute(self, season_id: int) -> dict:
        return {"season_id": season_id, "items": []}


class UsePowerup:
    def execute(self, payload: UsePowerupRequest) -> dict:
        return {
            "ok": True,
            "bet_context_id": payload.bet_context_id,
            "event_session_id": payload.event_session_id,
            "powerup_code": payload.powerup_code,
            "targets_count": len(payload.targets),
        }
