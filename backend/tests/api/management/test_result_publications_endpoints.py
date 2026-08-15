from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Role, User
from app.db.betting import BetContext, BetScore
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
    RankingEventType,
    RoleName,
    ScoreComponentType,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.scoring import (
    OfficialResult,
    ResultPublication,
    Score,
    ScoreComponent,
    ScoreSeasonAggregate,
    ScoreSession,
    ScoreSessionComponent,
)
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_admin_user(
    db_session,
    *,
    username: str,
    password: str,
) -> User:
    hasher = PasslibPasswordHasher()
    role = db_session.execute(
        select(Role).where(Role.name == RoleName.ADMIN)
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=RoleName.ADMIN, description="Admin")
        db_session.add(role)
        db_session.flush()

    user = User(
        username=username,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[role],
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_local_user(
    db_session,
    *,
    username: str,
    password: str,
) -> User:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=[],
    )
    db_session.add(user)
    db_session.flush()
    return user


def _add_group_membership(
    db_session,
    *,
    group_id: int,
    user_id: int,
    role: GroupRole,
) -> None:
    db_session.add(
        GroupMembership(
            group_id=group_id,
            user_id=user_id,
            role=role,
        )
    )
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
    return 3000 + int(uuid4().hex[:3], 16) % 900


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


def _add_calculated_score(
    db_session,
    *,
    bet_context_id: int,
    user_id: int,
    base_points: int | float = 1,
    total_points: int | float = 1,
) -> Score:
    row = Score(
        bet_context_id=bet_context_id,
        user_id=user_id,
        base_points=base_points,
        total_points=total_points,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _add_calculated_session_score(
    db_session,
    *,
    bet_context_id: int,
    user_id: int,
    event_session_id: int | None = None,
    testing_event_session_id: int | None = None,
    base_points: int | float = 1,
    total_points: int | float = 1,
) -> ScoreSession:
    row = ScoreSession(
        bet_context_id=bet_context_id,
        user_id=user_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
        base_points=base_points,
        total_points=total_points,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _add_score_component(
    db_session,
    *,
    score_id: int,
    component_type: ScoreComponentType,
    code: str,
    points: int | float,
) -> ScoreComponent:
    row = ScoreComponent(
        score_id=score_id,
        component_type=component_type,
        code=code,
        points=points,
        details_json=None,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _add_score_session_component(
    db_session,
    *,
    score_session_id: int,
    component_type: ScoreComponentType,
    code: str,
    points: int | float,
) -> ScoreSessionComponent:
    row = ScoreSessionComponent(
        score_session_id=score_session_id,
        component_type=component_type,
        code=code,
        points=points,
        details_json=None,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _create_race_context_for_existing_group(
    db_session,
    *,
    season: Season,
    group: Group,
    round_number: int,
    name: str,
):
    _, circuit = _create_country_and_circuit(db_session)
    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=round_number,
        name=name,
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 4, round_number, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 4, round_number, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 4, round_number, 14, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 4, round_number, 14, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 4, round_number, 13, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 4, round_number, 13, 55, tzinfo=timezone.utc),
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label=name,
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    score = BetScore(
        code=f"RACE_WINNER_{uuid4().hex[:8].upper()}",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add(score)
    db_session.flush()

    return {
        "race_event": race_event,
        "session": race_event.event_sessions[0],
        "bet_context": bet_context,
        "score": score,
    }


def _login(client, username: str) -> None:
    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": "secret123"},
    )
    assert response.status_code == 200


def test_publish_race_event_results_creates_publication(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_race_event",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        user_id=admin.id,
    )
    _login(client, "admin_publish_race_event")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={"note": "Ready to publish"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["race_event_public_id"] == str(data["race_event"].public_id)
    assert "event_session_public_id" not in payload
    assert payload["note"] == "Ready to publish"
    assert payload["published_at"] is not None

    row = db_session.execute(
        select(ResultPublication).where(
            ResultPublication.bet_context_id == data["bet_context"].id,
            ResultPublication.event_session_id.is_(None),
            ResultPublication.testing_event_session_id.is_(None),
        )
    ).scalar_one()
    assert row.note == "Ready to publish"


def test_publish_race_session_results_creates_publication(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_race_session",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        event_session_id=data["session"].id,
        bet_score_id=data["session_score"].id,
    )
    _add_calculated_session_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        event_session_id=data["session"].id,
        user_id=admin.id,
    )
    _login(client, "admin_publish_race_session")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        params={"session_id": str(data["session"].public_id)},
        json={},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["race_event_public_id"] == str(data["race_event"].public_id)
    assert payload["event_session_public_id"] == str(data["session"].public_id)

    row = db_session.execute(
        select(ResultPublication).where(
            ResultPublication.bet_context_id == data["bet_context"].id,
            ResultPublication.event_session_id == data["session"].id,
            ResultPublication.testing_event_session_id.is_(None),
        )
    ).scalar_one()
    assert row.event_session_id == data["session"].id


def test_publish_testing_session_results_creates_publication(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_testing_session",
        password="secret123",
    )
    data = _create_testing_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        testing_event_session_id=data["session"].id,
        bet_score_id=data["score"].id,
    )
    _add_calculated_session_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        testing_event_session_id=data["session"].id,
        user_id=admin.id,
    )
    _login(client, "admin_publish_testing_session")

    response = client.post(
        f"/api/v1/management/result-publications/testing-events/{data['testing_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        params={"session_id": str(data["session"].public_id)},
        json={},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["testing_event_public_id"] == str(data["testing_event"].public_id)
    assert payload["testing_event_session_public_id"] == str(data["session"].public_id)

    row = db_session.execute(
        select(ResultPublication).where(
            ResultPublication.bet_context_id == data["bet_context"].id,
            ResultPublication.event_session_id.is_(None),
            ResultPublication.testing_event_session_id == data["session"].id,
        )
    ).scalar_one()
    assert row.testing_event_session_id == data["session"].id


def test_publish_testing_event_results_creates_context_publication_without_session_id(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_testing_context",
        password="secret123",
    )
    data = _create_testing_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        user_id=admin.id,
    )
    _login(client, "admin_publish_testing_context")

    response = client.post(
        f"/api/v1/management/result-publications/testing-events/{data['testing_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={"note": "Testing context published"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["testing_event_public_id"] == str(data["testing_event"].public_id)
    assert "testing_event_session_public_id" not in payload
    assert payload["note"] == "Testing context published"

    row = db_session.execute(
        select(ResultPublication).where(
            ResultPublication.bet_context_id == data["bet_context"].id,
            ResultPublication.event_session_id.is_(None),
            ResultPublication.testing_event_session_id.is_(None),
        )
    ).scalar_one()
    assert row.note == "Testing context published"


def test_publish_season_results_creates_publication(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_season",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        user_id=admin.id,
    )
    _login(client, "admin_publish_season")

    response = client.post(
        f"/api/v1/management/result-publications/seasons/{data['season'].year}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={"note": "Season published"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["season_year"] == data["season"].year
    assert payload["note"] == "Season published"

    row = db_session.execute(
        select(ResultPublication).where(
            ResultPublication.bet_context_id == data["bet_context"].id,
            ResultPublication.event_session_id.is_(None),
            ResultPublication.testing_event_session_id.is_(None),
        )
    ).scalar_one()
    assert row.note == "Season published"


def test_unpublish_race_event_results_deletes_publication(client, db_session) -> None:
    _create_admin_user(
        db_session,
        username="admin_unpublish_race_event",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    publication = ResultPublication(
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
    )
    db_session.add(publication)
    db_session.flush()
    _login(client, "admin_unpublish_race_event")

    response = client.delete(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    assert db_session.execute(
        select(ResultPublication).where(ResultPublication.id == publication.id)
    ).scalar_one_or_none() is None


def test_publish_results_returns_conflict_when_official_results_do_not_exist(client, db_session) -> None:
    _create_admin_user(
        db_session,
        username="admin_publish_without_results",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _login(client, "admin_publish_without_results")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "management.result_publications.official_results_not_found"


def test_publish_results_returns_conflict_when_scores_are_not_calculated(client, db_session) -> None:
    _create_admin_user(
        db_session,
        username="admin_publish_without_scoring",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _login(client, "admin_publish_without_scoring")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "management.result_publications.scoring_required"


def test_publish_results_returns_conflict_when_publication_exists(client, db_session) -> None:
    _create_admin_user(
        db_session,
        username="admin_publish_duplicate",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    db_session.add(
        ResultPublication(
            bet_context_id=data["bet_context"].id,
            event_session_id=None,
            testing_event_session_id=None,
        )
    )
    db_session.flush()
    _login(client, "admin_publish_duplicate")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "management.result_publications.already_exists"


def test_unpublish_results_returns_not_found_when_publication_does_not_exist(client, db_session) -> None:
    _create_admin_user(
        db_session,
        username="admin_unpublish_missing",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _login(client, "admin_unpublish_missing")

    response = client.delete(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "management.result_publications.not_found"


def test_publish_results_allows_group_owner(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="owner_publish_results",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=user.id,
        role=GroupRole.OWNER,
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        user_id=user.id,
    )
    _login(client, "owner_publish_results")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 201
    assert response.json()["race_event_public_id"] == str(data["race_event"].public_id)


def test_publish_results_forbids_group_member(client, db_session) -> None:
    user = _create_local_user(
        db_session,
        username="member_publish_results",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=user.id,
        role=GroupRole.MEMBER,
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    _login(client, "member_publish_results")

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.result_publications.forbidden_group"


def test_publish_results_recalculates_season_aggregate_for_published_scores(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_publish_aggregate",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_publish_aggregate",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["event_score"].id,
    )
    score = _add_calculated_score(
        db_session,
        bet_context_id=data["bet_context"].id,
        user_id=player.id,
        base_points=10,
        total_points=12,
    )
    _add_score_component(
        db_session,
        score_id=score.id,
        component_type=ScoreComponentType.EXTRA,
        code="BONUS_EXTRA",
        points=2,
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/result-publications/race-events/{data['race_event'].public_id}",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={},
    )

    assert response.status_code == 201
    aggregate = db_session.execute(
        select(ScoreSeasonAggregate).where(
            ScoreSeasonAggregate.group_id == data["group"].id,
            ScoreSeasonAggregate.season_id == data["season"].id,
            ScoreSeasonAggregate.user_id == player.id,
        )
    ).scalar_one()
    assert aggregate.total_points == 12
    assert aggregate.race_points == 12
    assert aggregate.testing_points == 0
    assert aggregate.season_points == 0
    assert aggregate.extra_points == 2
    assert aggregate.penalty_points == 0
    assert aggregate.position == 1
    assert aggregate.previous_position is None
    assert aggregate.last_event_type == RankingEventType.RACE_EVENT
    assert aggregate.last_event_label == data["bet_context"].label
    assert aggregate.last_event_order == data["race_event"].round_number


def test_unpublish_results_recalculates_aggregate_excluding_unpublished_scope(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_unpublish_aggregate",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_unpublish_aggregate",
        password="secret123",
    )
    first = _create_race_fixture(db_session)
    second = _create_race_context_for_existing_group(
        db_session,
        season=first["season"],
        group=first["group"],
        round_number=2,
        name="Saudi Arabian GP",
    )
    _add_calculated_score(
        db_session,
        bet_context_id=first["bet_context"].id,
        user_id=player.id,
        base_points=10,
        total_points=10,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=second["bet_context"].id,
        user_id=player.id,
        base_points=7,
        total_points=7,
    )
    db_session.add_all(
        [
            ResultPublication(bet_context_id=first["bet_context"].id),
            ResultPublication(bet_context_id=second["bet_context"].id),
        ]
    )
    db_session.flush()
    from app.adapters.sqlalchemy.management.result_publication_repository import (
        SqlAlchemyResultPublicationRepository,
    )

    SqlAlchemyResultPublicationRepository(db_session).recalculate_season_aggregates_for_bet_context(
        bet_context_id=first["bet_context"].id,
    )
    aggregate_before = db_session.execute(
        select(ScoreSeasonAggregate).where(
            ScoreSeasonAggregate.group_id == first["group"].id,
            ScoreSeasonAggregate.season_id == first["season"].id,
            ScoreSeasonAggregate.user_id == player.id,
        )
    ).scalar_one()
    assert aggregate_before.total_points == 17

    _login(client, admin.username)
    response = client.delete(
        f"/api/v1/management/result-publications/race-events/{second['race_event'].public_id}",
        headers={"X-Group-Id": str(first["group"].public_id)},
    )

    assert response.status_code == 200
    aggregate_after = db_session.execute(
        select(ScoreSeasonAggregate).where(
            ScoreSeasonAggregate.group_id == first["group"].id,
            ScoreSeasonAggregate.season_id == first["season"].id,
            ScoreSeasonAggregate.user_id == player.id,
        )
    ).scalar_one()
    assert aggregate_after.total_points == 10
    assert aggregate_after.race_points == 10
    assert aggregate_after.previous_position == 1
    assert aggregate_after.last_event_label == first["bet_context"].label
    assert aggregate_after.last_event_order == first["race_event"].round_number


def test_published_aggregate_last_event_uses_calendar_order_not_publication_order(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calendar_order_aggregate",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calendar_order_aggregate",
        password="secret123",
    )
    first = _create_race_fixture(db_session)
    second = _create_race_context_for_existing_group(
        db_session,
        season=first["season"],
        group=first["group"],
        round_number=2,
        name="Saudi Arabian GP",
    )
    _add_official_result(
        db_session,
        bet_context_id=first["bet_context"].id,
        bet_score_id=first["event_score"].id,
    )
    _add_official_result(
        db_session,
        bet_context_id=second["bet_context"].id,
        bet_score_id=second["score"].id,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=first["bet_context"].id,
        user_id=player.id,
        base_points=5,
        total_points=5,
    )
    _add_calculated_score(
        db_session,
        bet_context_id=second["bet_context"].id,
        user_id=player.id,
        base_points=7,
        total_points=7,
    )
    _login(client, admin.username)

    second_response = client.post(
        f"/api/v1/management/result-publications/race-events/{second['race_event'].public_id}",
        headers={"X-Group-Id": str(first["group"].public_id)},
        json={},
    )
    first_response = client.post(
        f"/api/v1/management/result-publications/race-events/{first['race_event'].public_id}",
        headers={"X-Group-Id": str(first["group"].public_id)},
        json={},
    )

    assert second_response.status_code == 201
    assert first_response.status_code == 201
    aggregate = db_session.execute(
        select(ScoreSeasonAggregate).where(
            ScoreSeasonAggregate.group_id == first["group"].id,
            ScoreSeasonAggregate.season_id == first["season"].id,
            ScoreSeasonAggregate.user_id == player.id,
        )
    ).scalar_one()
    assert aggregate.total_points == 12
    assert aggregate.last_event_type == RankingEventType.RACE_EVENT
    assert aggregate.last_event_label == second["bet_context"].label
    assert aggregate.last_event_order == 2
