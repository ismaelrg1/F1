from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Role, User
from app.db.betting import Bet, BetContext, BetPick, BetScore
from app.db.competition import (
    Circuit,
    Country,
    EventSession,
    RaceEvent,
    Season,
    TestingEvent as CompetitionTestingEvent,
    TestingEventSession as CompetitionTestingEventSession,
)
from app.db.enums import (
    BetContextKind,
    BetValueType,
    RaceEventStatus,
    RoleName,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.scoring import OfficialResult, Score, ScoreComponent, ScoreSession, ScoreSessionComponent
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_admin_user(db_session, *, username: str, email: str, password: str) -> User:
    hasher = PasslibPasswordHasher()
    role = db_session.execute(select(Role).where(Role.name == RoleName.ADMIN)).scalar_one_or_none()
    if role is None:
        role = Role(name=RoleName.ADMIN, description="Admin")
        db_session.add(role)
        db_session.flush()

    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[role],
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_local_user(db_session, *, username: str, email: str, password: str) -> User:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[],
    )
    db_session.add(user)
    db_session.flush()
    return user


def _add_group_membership(db_session, *, group_id: int, user_id: int, role: GroupRole) -> None:
    db_session.add(GroupMembership(group_id=group_id, user_id=user_id, role=role))
    db_session.flush()


def _create_group(db_session) -> Group:
    group = Group(
        name=f"group_{uuid4().hex[:8]}",
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()
    return group


def _unique_year() -> int:
    return 3500 + int(uuid4().hex[:3], 16) % 500


def _create_country_and_circuit(db_session):
    country = Country(
        iso2=uuid4().hex[:2].upper(),
        name=f"Country {uuid4().hex[:8]}",
        flag_asset_url=None,
    )
    db_session.add(country)
    db_session.flush()

    circuit = Circuit(
        code=f"circuit_{uuid4().hex[:8]}",
        name=f"Circuit {uuid4().hex[:8]}",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()
    return country, circuit


def _create_race_fixture(db_session):
    season = Season(year=_unique_year(), is_active=True)
    db_session.add(season)
    db_session.flush()
    _, circuit = _create_country_and_circuit(db_session)

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 3, 3, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 1, 9, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 1, 9, 55, tzinfo=timezone.utc),
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    group = _create_group(db_session)
    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Bahrain GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    event_score = BetScore(
        code=f"RACE_WINNER_{uuid4().hex[:8].upper()}",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    session_score = BetScore(
        code=f"FP1_FASTEST_{uuid4().hex[:8].upper()}",
        label="FP1 Fastest",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([event_score, session_score])
    db_session.flush()

    return {
        "season": season,
        "group": group,
        "race_event": race_event,
        "session": race_event.event_sessions[0],
        "bet_context": bet_context,
        "event_score": event_score,
        "session_score": session_score,
    }


def _create_testing_fixture(db_session):
    season = Season(year=_unique_year(), is_active=True)
    db_session.add(season)
    db_session.flush()
    _, circuit = _create_country_and_circuit(db_session)

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 2, 10, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 2, 12, 18, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 10, 8, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 10, 18, 0, tzinfo=timezone.utc),
        )
    ]
    db_session.add(testing_event)
    db_session.flush()

    group = _create_group(db_session)
    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Pre-Season Testing",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    score = BetScore(
        code=f"DAY1_FASTEST_{uuid4().hex[:8].upper()}",
        label="Day 1 Fastest",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add(score)
    db_session.flush()

    return {
        "season": season,
        "group": group,
        "testing_event": testing_event,
        "session": testing_event.sessions[0],
        "bet_context": bet_context,
        "score": score,
    }


def _create_season_fixture(db_session):
    season = Season(year=_unique_year(), is_active=True)
    db_session.add(season)
    db_session.flush()

    group = _create_group(db_session)
    bet_context = BetContext(
        kind=BetContextKind.SEASON,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=None,
        label=f"Season {season.year}",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    score = BetScore(
        code=f"SEASON_CHAMPION_{uuid4().hex[:8].upper()}",
        label="Season Champion",
        base_points=15,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add(score)
    db_session.flush()

    return {
        "season": season,
        "group": group,
        "bet_context": bet_context,
        "score": score,
    }


def _add_official_result(
    db_session,
    *,
    bet_context_id: int,
    bet_score_id: int,
    value: str = "VER",
    event_session_id: int | None = None,
    testing_event_session_id: int | None = None,
) -> OfficialResult:
    row = OfficialResult(
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
        bet_score_id=bet_score_id,
        value=value,
        source=SourceType.MANUAL,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _add_submitted_bet(
    db_session,
    *,
    user_id: int,
    bet_context_id: int,
    bet_score_id: int,
    value: str = "VER",
    event_session_id: int | None = None,
    testing_event_session_id: int | None = None,
) -> Bet:
    bet = Bet(
        user_id=user_id,
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
        submitted_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        locked_at=None,
        submit_order_int=1,
    )
    db_session.add(bet)
    db_session.flush()

    db_session.add(BetPick(bet_id=bet.id, bet_score_id=bet_score_id, value=value))
    db_session.flush()
    return bet


def _login(client, username: str) -> None:
    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )
    assert response.status_code == 200


def test_calculate_race_event_scoring_creates_context_and_session_scores(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_race",
        email="admin_calc_race@example.com",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_race",
        email="player_calc_race@example.com",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        event_session_id=data["session"].id,
        bet_score_id=data["session_score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=data["session"].id,
        bet_score_id=data["session_score"].id,
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/race-events/{data['race_event'].public_id}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["calculated"] is True
    assert payload["calculated_users"] == 1
    assert payload["score_components_count"] == 1
    assert payload["score_session_components_count"] == 1

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("10.00000000")
    assert score.total_points == Decimal("10.00000000")

    score_component = db_session.execute(
        select(ScoreComponent).where(ScoreComponent.score_id == score.id)
    ).scalar_one()
    assert score_component.points == Decimal("10.00000000")
    assert score_component.details_json["answer"] == "VER"
    assert score_component.details_json["official"] == "VER"

    score_session = db_session.execute(
        select(ScoreSession).where(
            ScoreSession.user_id == player.id,
            ScoreSession.bet_context_id == data["bet_context"].id,
            ScoreSession.event_session_id == data["session"].id,
        )
    ).scalar_one()
    assert score_session.base_points == Decimal("5.0000")
    assert score_session.total_points == Decimal("5.00000000")

    session_component = db_session.execute(
        select(ScoreSessionComponent).where(
            ScoreSessionComponent.score_session_id == score_session.id
        )
    ).scalar_one()
    assert session_component.points == Decimal("5.00000000")


def test_calculate_testing_event_scoring_creates_session_score(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_testing",
        email="admin_calc_testing@example.com",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_testing",
        email="player_calc_testing@example.com",
        password="secret123",
    )
    data = _create_testing_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        testing_event_session_id=data["session"].id,
        bet_score_id=data["score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        testing_event_session_id=data["session"].id,
        bet_score_id=data["score"].id,
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/testing-events/{data['testing_event'].public_id}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["calculated"] is True
    assert payload["calculated_users"] == 1
    assert payload["score_components_count"] == 0
    assert payload["score_session_components_count"] == 1

    score_session = db_session.execute(
        select(ScoreSession).where(
            ScoreSession.user_id == player.id,
            ScoreSession.bet_context_id == data["bet_context"].id,
            ScoreSession.testing_event_session_id == data["session"].id,
        )
    ).scalar_one()
    assert score_session.total_points == Decimal("5.00000000")


def test_calculate_season_scoring_creates_context_score(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_season",
        email="admin_calc_season@example.com",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_season",
        email="player_calc_season@example.com",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["calculated"] is True
    assert payload["calculated_users"] == 1
    assert payload["score_components_count"] == 1
    assert payload["score_session_components_count"] == 0

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.total_points == Decimal("15.00000000")


def test_calculate_scoring_replaces_existing_scores(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_replace",
        email="admin_calc_replace@example.com",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_replace",
        email="player_calc_replace@example.com",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    old_score = Score(
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        base_points=99,
        total_points=99,
    )
    db_session.add(old_score)
    db_session.flush()
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    scores = db_session.scalars(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).all()
    assert len(scores) == 1
    assert scores[0].total_points == Decimal("15.00000000")


def test_calculate_scoring_returns_conflict_without_official_results(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_no_results",
        email="admin_calc_no_results@example.com",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/race-events/{data['race_event'].public_id}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "management.scoring.official_results_required"


def test_calculate_scoring_requires_management_group_header(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_no_group",
        email="admin_calc_no_group@example.com",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/race-events/{data['race_event'].public_id}/calculate",
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "management.group_required"


def test_calculate_scoring_forbids_group_member(client, db_session) -> None:
    member = _create_local_user(
        db_session,
        username="member_calc_scoring",
        email="member_calc_scoring@example.com",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=member.id,
        role=GroupRole.MEMBER,
    )
    _login(client, member.username)

    response = client.post(
        f"/api/v1/management/scoring/race-events/{data['race_event'].public_id}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.forbidden_group"


def test_calculate_scoring_allows_group_owner(client, db_session) -> None:
    owner = _create_local_user(
        db_session,
        username="owner_calc_scoring",
        email="owner_calc_scoring@example.com",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_owner_calc_scoring",
        email="player_owner_calc_scoring@example.com",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=owner.id,
        role=GroupRole.OWNER,
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _login(client, owner.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    assert response.json()["calculated_users"] == 1
