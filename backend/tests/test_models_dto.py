from app.models.auth import LoginRequest
from app.models.bets import BetCreate
from app.models.seasons import SeasonRead


def test_login_request_validation() -> None:
    payload = LoginRequest(username="alice", password="secret")

    assert payload.username == "alice"
    assert payload.password == "secret"


def test_bet_create_validation() -> None:
    payload = BetCreate(context_id=7, event_session_id=15)

    assert payload.context_id == 7
    assert payload.event_session_id == 15


def test_season_read_from_attributes() -> None:
    class SeasonSource:
        id = 1
        year = 2026
        is_active = True

    season = SeasonRead.model_validate(SeasonSource())

    assert season.year == 2026
    assert season.is_active is True
