from app.models.bets import BetCreate


class CreateBet:
    def execute(self, user_id: int, payload: BetCreate) -> dict:
        return {
            "user_id": user_id,
            "bet_context_id": payload.context_id,
            "event_session_id": payload.event_session_id,
        }
