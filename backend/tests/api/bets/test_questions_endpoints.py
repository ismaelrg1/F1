# backend/tests/test_bet_questions_endpoints.py

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.betting import (
    Bet,
    BetContext,
    BetEditPermission,
    BetException,
    BetPick,
    BetResultsVisibilityPolicy,
    BetScore,
    BetSubmissionRevision,
    BetTemplate,
    BetTemplateItem,
)
from app.db.competition import (
    Circuit,
    Country,
    Driver,
    DriverEntry,
    Engine,
    EventSession,
    RaceEvent,
    Season,
    SeasonDriver,
    TeamF1,
    TestingEvent as CompetitionTestingEvent,
    TestingEventSession as CompetitionTestingEventSession,
)
from app.db.enums import (
    BetContextKind,
    BetResultsVisibilityMode,
    BetTemplateScope,
    BetValueType,
    RaceEventStatus,
    SeasonDriverStatus,
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
    ScoreSession,
    ScoreSessionComponent,
)
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
) -> User:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_group_with_membership(
    db_session,
    *,
    user_id: int,
    name: str,
) -> Group:
    group = Group(
        name=name,
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()

    membership = GroupMembership(
        group_id=group.id,
        user_id=user_id,
        role=GroupRole.MEMBER,
    )
    db_session.add(membership)
    db_session.flush()

    return group


def _create_race_event_roster(db_session, *, season_id: int, race_event: RaceEvent, fp1_session: EventSession) -> None:
    red_bull = TeamF1(code="RBR", name="Red Bull Racing")
    ferrari = TeamF1(code="FER", name="Ferrari")
    honda = Engine(code="HONDA", name="Honda")
    ferrari_engine = Engine(code="FERRARI", name="Ferrari")
    verstappen = Driver(code="VER", name="Max Verstappen")
    leclerc = Driver(code="LEC", name="Charles Leclerc")
    norris = Driver(code="NOR", name="Lando Norris")

    db_session.add_all(
        [red_bull, ferrari, honda, ferrari_engine, verstappen, leclerc, norris]
    )
    db_session.flush()

    db_session.add_all(
        [
            SeasonDriver(
                season_id=season_id,
                driver_id=verstappen.id,
                driver_number=1,
            ),
            SeasonDriver(
                season_id=season_id,
                driver_id=leclerc.id,
                driver_number=16,
            ),
            SeasonDriver(
                season_id=season_id,
                driver_id=norris.id,
                driver_number=4,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DriverEntry(
                season_id=season_id,
                driver_id=verstappen.id,
                team_id=red_bull.id,
                engine_id=honda.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                note=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season_id,
                driver_id=leclerc.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                note=None,
                race_event_id=None,
                event_session_id=None,
            ),
            # GP override: Norris replaces Leclerc for this event.
            DriverEntry(
                season_id=season_id,
                driver_id=norris.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                note="Race weekend substitute",
                race_event_id=race_event.id,
                event_session_id=None,
            ),
            # Session override: Leclerc returns for FP1 only.
            DriverEntry(
                season_id=season_id,
                driver_id=leclerc.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                note="FP1 only",
                race_event_id=None,
                event_session_id=fp1_session.id,
            ),
        ]
    )
    db_session.flush()


def test_get_race_event_bet_questions_requires_authentication(client, db_session) -> None:
    group = Group(
        name=f"group_{uuid4().hex[:8]}",
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()

    response = client.get(
        f"/api/v1/bets/race-events/{uuid4()}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 401


def test_get_race_event_bet_questions_requires_group_membership(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )

    group = Group(
        name=f"group_{uuid4().hex[:8]}",
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{uuid4()}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "access.not_group_member"


def test_get_race_event_bet_questions_returns_event_and_session_questions(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 3, 8, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
        ),
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(race_event)
    db_session.flush()

    fp1_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.FP1)
    race_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.RACE)
    _create_race_event_roster(
        db_session,
        season_id=season.id,
        race_event=race_event,
        fp1_session=fp1_session,
    )

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
        code="SAFETY_CAR",
        label="Safety Car",
        base_points=3,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    fp1_score = BetScore(
        code="FP1_FASTEST",
        label="FP1 Fastest Driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json={"allowed": ["VER", "LEC"]},
    )
    fp1_team_score = BetScore(
        code="FP1_TOP_TEAM",
        label="FP1 Top Team",
        base_points=2,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    race_score = BetScore(
        code="RACE_WINNER",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json={"allowed": ["VER", "LEC", "HAM"]},
    )
    race_position_score = BetScore(
        code="NOR_FINAL_POSITION",
        label="Final position of Lando Norris",
        base_points=3,
        value_type=BetValueType.POSITION,
        constraints_json={"allow_dnf": True},
    )
    db_session.add_all([event_score, fp1_score, fp1_team_score, race_score, race_position_score])
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="GP Event Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    fp1_template = BetTemplate(
        season_id=season.id,
        name="GP FP1 Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.FP1,
    )
    race_template = BetTemplate(
        season_id=season.id,
        name="GP Race Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.RACE,
    )
    db_session.add_all([event_template, fp1_template, race_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=event_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_team_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_position_score.id,
                required=True,
                display_order=1,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=event_score.id,
                override_points=7,
                is_disabled=None,
                override_constraints_json=None,
                note="Event override points",
            ),
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=fp1_session.id,
                bet_score_id=fp1_score.id,
                override_points=None,
                is_disabled=None,
                override_constraints_json={"allowed": ["NOR"]},
                note="FP1 override constraints",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(race_event.public_id)
    assert payload["label"] == "Bahrain GP"

    assert len(payload["event_questions"]) == 1
    assert payload["event_questions"][0]["code"] == "SAFETY_CAR"
    assert payload["event_questions"][0]["base_points"] == 7.0
    assert payload["event_questions"][0]["options"] == [
        {"value": "true", "label": "Yes"},
        {"value": "false", "label": "No"},
    ]

    assert len(payload["sessions"]) == 2
    assert [session["session_type"] for session in payload["sessions"]] == ["FP1", "RACE"]

    fp1_payload = payload["sessions"][0]
    assert fp1_payload["event_session_public_id"] == str(fp1_session.public_id)
    assert len(fp1_payload["questions"]) == 2
    assert fp1_payload["questions"][0]["code"] == "FP1_FASTEST"
    assert fp1_payload["questions"][0]["constraints_json"] == {"allowed": ["NOR"]}
    assert fp1_payload["questions"][0]["options"] == [
        {"value": "LEC", "label": "Charles Leclerc", "meta": {"code": "LEC", "driver_number": 16}},
        {"value": "VER", "label": "Max Verstappen", "meta": {"code": "VER", "driver_number": 1}},
    ]
    assert fp1_payload["questions"][1]["code"] == "FP1_TOP_TEAM"
    assert fp1_payload["questions"][1]["options"] == [
        {"value": "FER", "label": "Ferrari", "meta": {"code": "FER"}},
        {"value": "RBR", "label": "Red Bull Racing", "meta": {"code": "RBR"}},
    ]

    race_payload = payload["sessions"][1]
    assert race_payload["event_session_public_id"] == str(race_session.public_id)
    assert len(race_payload["questions"]) == 2
    assert race_payload["questions"][0]["code"] == "RACE_WINNER"
    assert race_payload["questions"][0]["base_points"] == 10.0
    assert race_payload["questions"][0]["options"] == [
        {"value": "NOR", "label": "Lando Norris", "meta": {"code": "NOR", "driver_number": 4}},
        {"value": "VER", "label": "Max Verstappen", "meta": {"code": "VER", "driver_number": 1}},
    ]
    assert race_payload["questions"][1]["code"] == "NOR_FINAL_POSITION"
    assert "options" not in race_payload["questions"][1]
    assert race_payload["questions"][1]["constraints_json"] == {
        "allow_dnf": True,
        "min": 1,
        "max": 2,
    }


def test_get_race_event_bet_questions_returns_404_when_bet_context_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="ES", name="Spain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="barcelona",
        name="Circuit de Barcelona-Catalunya",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=2,
        name="Spanish Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 6, 12, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc),
    )
    db_session.add(race_event)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 404


import json
import pytest

@pytest.mark.manual
def test_preview_race_event_bet_questions_payload_prints_result(client, db_session) -> None:
    user = _create_user(
        db_session,
        username="bet_questions_manual",
        email="bet_questions_manual@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 3, 8, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
        ),
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(race_event)
    db_session.flush()

    fp1_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.FP1)
    _create_race_event_roster(
        db_session,
        season_id=season.id,
        race_event=race_event,
        fp1_session=fp1_session,
    )

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
        code="SAFETY_CAR",
        label="Safety Car",
        base_points=3,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    fp1_score = BetScore(
        code="FP1_FASTEST",
        label="FP1 Fastest Driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json={"allowed": ["VER", "LEC"]},
    )
    fp1_team_score = BetScore(
        code="FP1_TOP_TEAM",
        label="FP1 Top Team",
        base_points=2,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    race_score = BetScore(
        code="RACE_WINNER",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json={"allowed": ["VER", "LEC", "HAM"]},
    )
    race_position_score = BetScore(
        code="NOR_FINAL_POSITION",
        label="Final position of Lando Norris",
        base_points=3,
        value_type=BetValueType.POSITION,
        constraints_json={"allow_dnf": True},
    )
    db_session.add_all([event_score, fp1_score, fp1_team_score, race_score, race_position_score])
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="GP Event Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    fp1_template = BetTemplate(
        season_id=season.id,
        name="GP FP1 Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.FP1,
    )
    race_template = BetTemplate(
        season_id=season.id,
        name="GP Race Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.RACE,
    )
    db_session.add_all([event_template, fp1_template, race_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=event_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_team_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_position_score.id,
                required=True,
                display_order=1,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=event_score.id,
                override_points=7,
                is_disabled=None,
                override_constraints_json=None,
                note="Event override points",
            ),
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=fp1_session.id,
                bet_score_id=fp1_score.id,
                override_points=None,
                is_disabled=None,
                override_constraints_json={"allowed": ["NOR"]},
                note="FP1 override constraints",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )
    assert response.status_code == 200

    import json

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_get_testing_event_bet_questions_returns_event_and_session_questions(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    red_bull = TeamF1(code="RBR", name="Red Bull Racing")
    ferrari = TeamF1(code="FER", name="Ferrari")
    honda = Engine(code="HONDA", name="Honda")
    ferrari_engine = Engine(code="FERRARI", name="Ferrari Power Unit")
    verstappen = Driver(code="VER", name="Max Verstappen")
    leclerc = Driver(code="LEC", name="Charles Leclerc")
    norris = Driver(code="NOR", name="Lando Norris")
    db_session.add_all(
        [red_bull, ferrari, honda, ferrari_engine, verstappen, leclerc, norris]
    )
    db_session.flush()

    db_session.add_all(
        [
            SeasonDriver(
                season_id=season.id,
                driver_id=verstappen.id,
                driver_number=1,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=leclerc.id,
                driver_number=16,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=norris.id,
                driver_number=4,
                status=SeasonDriverStatus.PRIMARY,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DriverEntry(
                season_id=season.id,
                driver_id=verstappen.id,
                team_id=red_bull.id,
                engine_id=honda.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=leclerc.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=norris.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=2,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
        ]
    )
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing Bahrain",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 2, 13, 17, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 11, 17, 0, tzinfo=timezone.utc),
        ),
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 12, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 12, 17, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(testing_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Bahrain Testing",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    event_score = BetScore(
        code="MOST_KILOMETRAGE_DRIVER",
        label="Driver with most mileage",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    session_score = BetScore(
        code="DAY_WINNER_DRIVER",
        label="Driver topping the day",
        base_points=3,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    position_score = BetScore(
        code="ALO_TEST_POSITION",
        label="Fernando Alonso final testing position",
        base_points=2,
        value_type=BetValueType.POSITION,
        constraints_json={"allow_dnf": False},
    )
    team_score = BetScore(
        code="TOP_TEAM_TESTING",
        label="Top team in testing",
        base_points=2,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    boolean_score = BetScore(
        code="RED_FLAG",
        label="Will there be a red flag?",
        base_points=1,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    db_session.add_all([event_score, session_score, position_score, team_score, boolean_score])
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="Pretesting Event Template",
        context_kind=BetContextKind.PRETESTING,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )

    db_session.add(event_template)
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=event_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=team_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=session_score.id,
                required=True,
                display_order=2,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=position_score.id,
                required=True,
                display_order=3,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=boolean_score.id,
                required=True,
                display_order=4,
            ),
        ]
    )
    db_session.flush()

    db_session.add(
        BetException(
            bet_context_id=bet_context.id,
            event_session_id=None,
            bet_score_id=event_score.id,
            override_points=7,
            is_disabled=None,
            override_constraints_json=None,
            note="Boost event score",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/testing-events/{testing_event.public_id}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "PRETESTING"
    assert payload["testing_event_public_id"] == str(testing_event.public_id)
    assert payload["label"] == "Bahrain Testing"
    assert payload["status"] == "SCHEDULED"

    assert len(payload["event_questions"]) == 5

    assert payload["event_questions"][0]["code"] == "MOST_KILOMETRAGE_DRIVER"
    assert payload["event_questions"][0]["base_points"] == 7.0
    assert payload["event_questions"][0]["options"] == [
        {"value": "LEC", "label": "Charles Leclerc", "meta": {"code": "LEC", "driver_number": 16}},
        {"value": "NOR", "label": "Lando Norris", "meta": {"code": "NOR", "driver_number": 4}},
        {"value": "VER", "label": "Max Verstappen", "meta": {"code": "VER", "driver_number": 1}},
    ]

    assert payload["event_questions"][1]["code"] == "TOP_TEAM_TESTING"
    assert payload["event_questions"][1]["options"] == [
        {"value": "FER", "label": "Ferrari", "meta": {"code": "FER"}},
        {"value": "RBR", "label": "Red Bull Racing", "meta": {"code": "RBR"}},
    ]
    assert payload["event_questions"][2]["code"] == "DAY_WINNER_DRIVER"
    assert payload["event_questions"][3]["code"] == "ALO_TEST_POSITION"
    assert payload["event_questions"][3]["constraints_json"] == {
        "allow_dnf": False,
        "min": 1,
        "max": 3,
    }
    assert "options" not in payload["event_questions"][3]
    assert payload["event_questions"][4]["code"] == "RED_FLAG"
    assert payload["event_questions"][4]["options"] == [
        {"value": "true", "label": "Yes"},
        {"value": "false", "label": "No"},
    ]

    assert len(payload["sessions"]) == 2
    assert [session["session_order"] for session in payload["sessions"]] == [1, 2]

    day_1 = payload["sessions"][0]
    assert day_1["name"] == "Day 1"
    assert len(day_1["questions"]) == 5

    assert day_1["questions"][0]["code"] == "MOST_KILOMETRAGE_DRIVER"
    assert day_1["questions"][1]["code"] == "TOP_TEAM_TESTING"
    assert day_1["questions"][2]["code"] == "DAY_WINNER_DRIVER"
    assert day_1["questions"][2]["options"] == [
        {"value": "LEC", "label": "Charles Leclerc", "meta": {"code": "LEC", "driver_number": 16}},
        {"value": "NOR", "label": "Lando Norris", "meta": {"code": "NOR", "driver_number": 4}},
        {"value": "VER", "label": "Max Verstappen", "meta": {"code": "VER", "driver_number": 1}},
    ]

    assert day_1["questions"][3]["code"] == "ALO_TEST_POSITION"
    assert day_1["questions"][3]["constraints_json"] == {
        "allow_dnf": False,
        "min": 1,
        "max": 3,
    }
    assert "options" not in day_1["questions"][3]

    assert day_1["questions"][4]["code"] == "RED_FLAG"
    assert day_1["questions"][4]["options"] == [
        {"value": "true", "label": "Yes"},
        {"value": "false", "label": "No"},
    ]

    day_2 = payload["sessions"][1]
    assert day_2["name"] == "Day 2"
    assert len(day_2["questions"]) == 5
    assert day_2["questions"][2]["code"] == "DAY_WINNER_DRIVER"


@pytest.mark.manual
def test_preview_testing_event_bet_questions_payload_prints_result(client, db_session) -> None:
    user = _create_user(
        db_session,
        username="testing_bets_manual",
        email="testing_bets_manual@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    red_bull = TeamF1(code="RBR", name="Red Bull Racing")
    ferrari = TeamF1(code="FER", name="Ferrari")
    honda = Engine(code="HONDA", name="Honda")
    ferrari_engine = Engine(code="FERRARI", name="Ferrari Power Unit")
    verstappen = Driver(code="VER", name="Max Verstappen")
    leclerc = Driver(code="LEC", name="Charles Leclerc")
    norris = Driver(code="NOR", name="Lando Norris")
    db_session.add_all(
        [red_bull, ferrari, honda, ferrari_engine, verstappen, leclerc, norris]
    )
    db_session.flush()

    db_session.add_all(
        [
            SeasonDriver(
                season_id=season.id,
                driver_id=verstappen.id,
                driver_number=1,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=leclerc.id,
                driver_number=16,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=norris.id,
                driver_number=4,
                status=SeasonDriverStatus.PRIMARY,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DriverEntry(
                season_id=season.id,
                driver_id=verstappen.id,
                team_id=red_bull.id,
                engine_id=honda.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=leclerc.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=norris.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=2,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
        ]
    )
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing Bahrain",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 2, 13, 17, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 11, 17, 0, tzinfo=timezone.utc),
        ),
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 12, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 12, 17, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(testing_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Bahrain Testing",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    event_score = BetScore(
        code="MOST_KILOMETRAGE_DRIVER",
        label="Driver with most mileage",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    session_score = BetScore(
        code="DAY_WINNER_DRIVER",
        label="Driver topping the day",
        base_points=3,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    position_score = BetScore(
        code="ALO_TEST_POSITION",
        label="Fernando Alonso final testing position",
        base_points=2,
        value_type=BetValueType.POSITION,
        constraints_json={"allow_dnf": False},
    )
    team_score = BetScore(
        code="TOP_TEAM_TESTING",
        label="Top team in testing",
        base_points=2,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    boolean_score = BetScore(
        code="RED_FLAG",
        label="Will there be a red flag?",
        base_points=1,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    engine_score = BetScore(
        code="BEST_ENGINE",
        label="Best engine in testing",
        base_points=2,
        value_type=BetValueType.ENGINE,
        constraints_json=None,
    )
    db_session.add_all(
        [event_score, session_score, position_score, team_score, boolean_score, engine_score]
    )
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="Pretesting Event Template",
        context_kind=BetContextKind.PRETESTING,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add(event_template)
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=event_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=team_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=session_score.id,
                required=True,
                display_order=2,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=position_score.id,
                required=True,
                display_order=3,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=boolean_score.id,
                required=True,
                display_order=4,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=engine_score.id,
                required=False,
                display_order=5,
            ),
        ]
    )
    db_session.flush()

    db_session.add(
        BetException(
            bet_context_id=bet_context.id,
            event_session_id=None,
            bet_score_id=event_score.id,
            override_points=7,
            is_disabled=None,
            override_constraints_json=None,
            note="Boost event score",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/testing-events/{testing_event.public_id}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )
    assert response.status_code == 200

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_get_season_bet_questions_returns_questions(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    db_session.add(season)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.SEASON,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=None,
        label="Season 2026",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    boolean_score = BetScore(
        code="WILL_VER_WIN_TITLE",
        label="Will Verstappen win the title?",
        base_points=5,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    string_score = BetScore(
        code="SEASON_SURPRISE",
        label="Biggest surprise of the season",
        base_points=3,
        value_type=BetValueType.STRING,
        constraints_json={"max_length": 40},
    )
    disabled_score = BetScore(
        code="DISABLED_QUESTION",
        label="Disabled question",
        base_points=2,
        value_type=BetValueType.STRING,
        constraints_json=None,
    )
    db_session.add_all([boolean_score, string_score, disabled_score])
    db_session.flush()

    season_template = BetTemplate(
        season_id=season.id,
        name="Season Template",
        context_kind=BetContextKind.SEASON,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add(season_template)
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=boolean_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=string_score.id,
                required=False,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=disabled_score.id,
                required=True,
                display_order=2,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=boolean_score.id,
                override_points=8,
                is_disabled=None,
                override_constraints_json=None,
                note="Boost title question",
            ),
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=string_score.id,
                override_points=None,
                is_disabled=None,
                override_constraints_json={"max_length": 20},
                note="Tighter text constraint",
            ),
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=disabled_score.id,
                override_points=None,
                is_disabled=True,
                override_constraints_json=None,
                note="Disabled for this group",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/seasons/{season.year}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "SEASON"
    assert payload["season_year"] == 2026
    assert payload["label"] == "Season 2026"

    assert len(payload["questions"]) == 2

    first_question = payload["questions"][0]
    assert first_question["code"] == "WILL_VER_WIN_TITLE"
    assert first_question["base_points"] == 8.0
    assert first_question["options"] == [
        {"value": "true", "label": "Yes"},
        {"value": "false", "label": "No"},
    ]

    second_question = payload["questions"][1]
    assert second_question["code"] == "SEASON_SURPRISE"
    assert second_question["required"] is False
    assert second_question["constraints_json"] == {"max_length": 20}
    assert "options" not in second_question

    returned_codes = [question["code"] for question in payload["questions"]]
    assert "DISABLED_QUESTION" not in returned_codes



@pytest.mark.manual
def test_preview_season_bet_questions_payload_prints_result(client, db_session) -> None:
    user = _create_user(
        db_session,
        username="season_bets_manual",
        email="season_bets_manual@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    db_session.add(season)
    db_session.flush()

    red_bull = TeamF1(code="RBR", name="Red Bull Racing")
    ferrari = TeamF1(code="FER", name="Ferrari")
    honda = Engine(code="HONDA", name="Honda")
    ferrari_engine = Engine(code="FERRARI", name="Ferrari Power Unit")
    verstappen = Driver(code="VER", name="Max Verstappen")
    leclerc = Driver(code="LEC", name="Charles Leclerc")
    norris = Driver(code="NOR", name="Lando Norris")
    db_session.add_all(
        [red_bull, ferrari, honda, ferrari_engine, verstappen, leclerc, norris]
    )
    db_session.flush()

    db_session.add_all(
        [
            SeasonDriver(
                season_id=season.id,
                driver_id=verstappen.id,
                driver_number=1,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=leclerc.id,
                driver_number=16,
                status=SeasonDriverStatus.PRIMARY,
            ),
            SeasonDriver(
                season_id=season.id,
                driver_id=norris.id,
                driver_number=4,
                status=SeasonDriverStatus.PRIMARY,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            DriverEntry(
                season_id=season.id,
                driver_id=verstappen.id,
                team_id=red_bull.id,
                engine_id=honda.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=leclerc.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=1,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
            DriverEntry(
                season_id=season.id,
                driver_id=norris.id,
                team_id=ferrari.id,
                engine_id=ferrari_engine.id,
                seat_index=2,
                active_from=None,
                active_to=None,
                race_event_id=None,
                event_session_id=None,
            ),
        ]
    )
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.SEASON,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=None,
        label="Season 2026",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    boolean_score = BetScore(
        code="WILL_VER_WIN_TITLE",
        label="Will Verstappen win the title?",
        base_points=5,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    string_score = BetScore(
        code="SEASON_SURPRISE",
        label="Biggest surprise of the season",
        base_points=3,
        value_type=BetValueType.STRING,
        constraints_json={"max_length": 40},
    )
    team_score = BetScore(
        code="BEST_TEAM",
        label="Best team of the season",
        base_points=4,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    position_score = BetScore(
        code="ALONSO_FINAL_POSITION",
        label="Final Alonso championship position",
        base_points=4,
        value_type=BetValueType.POSITION,
        constraints_json={"allow_dnf": False},
    )
    driver_score = BetScore(
        code="BEST_DRIVER",
        label="Best driver of the season",
        base_points=6,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    engine_score = BetScore(
        code="BEST_ENGINE",
        label="Best engine of the season",
        base_points=2,
        value_type=BetValueType.ENGINE,
        constraints_json=None,
    )
    db_session.add_all(
        [boolean_score, string_score, team_score, position_score, driver_score, engine_score]
    )
    db_session.flush()

    season_template = BetTemplate(
        season_id=season.id,
        name="Season Template",
        context_kind=BetContextKind.SEASON,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add(season_template)
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=boolean_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=string_score.id,
                required=False,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=team_score.id,
                required=True,
                display_order=2,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=position_score.id,
                required=True,
                display_order=3,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=driver_score.id,
                required=True,
                display_order=4,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=engine_score.id,
                required=False,
                display_order=5,
            ),
        ]
    )
    db_session.flush()

    db_session.add_all(
        [
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=boolean_score.id,
                override_points=8,
                is_disabled=None,
                override_constraints_json=None,
                note="Boost title question",
            ),
            BetException(
                bet_context_id=bet_context.id,
                event_session_id=None,
                bet_score_id=string_score.id,
                override_points=None,
                is_disabled=None,
                override_constraints_json={"max_length": 20},
                note="Tighter text constraint",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/seasons/{season.year}/questions",
        headers={"X-Group-Id": str(group.public_id)},
    )
    assert response.status_code == 200

    payload = response.json()

    assert payload["kind"] == "SEASON"
    assert payload["season_year"] == 2026
    assert len(payload["questions"]) == 6

    by_code = {question["code"]: question for question in payload["questions"]}

    assert by_code["WILL_VER_WIN_TITLE"]["options"] == [
        {"value": "true", "label": "Yes"},
        {"value": "false", "label": "No"},
    ]
    assert by_code["WILL_VER_WIN_TITLE"]["base_points"] == 8.0

    assert by_code["BEST_DRIVER"]["options"] == [
        {"value": "LEC", "label": "Charles Leclerc", "meta": {"code": "LEC", "driver_number": 16}},
        {"value": "NOR", "label": "Lando Norris", "meta": {"code": "NOR", "driver_number": 4}},
        {"value": "VER", "label": "Max Verstappen", "meta": {"code": "VER", "driver_number": 1}},
    ]

    assert by_code["BEST_TEAM"]["options"] == [
        {"value": "FER", "label": "Ferrari", "meta": {"code": "FER"}},
        {"value": "RBR", "label": "Red Bull Racing", "meta": {"code": "RBR"}},
    ]

    assert by_code["BEST_ENGINE"]["options"] == [
        {"value": "FERRARI", "label": "Ferrari Power Unit", "meta": {"code": "FERRARI"}},
        {"value": "HONDA", "label": "Honda", "meta": {"code": "HONDA"}},
    ]

    assert "options" not in by_code["ALONSO_FINAL_POSITION"]
    assert by_code["ALONSO_FINAL_POSITION"]["constraints_json"] == {
        "allow_dnf": False,
        "min": 1,
        "max": 3,
    }

    assert "options" not in by_code["SEASON_SURPRISE"]
    assert by_code["SEASON_SURPRISE"]["constraints_json"] == {"max_length": 20}

    print(json.dumps(payload, indent=2, ensure_ascii=False))



def test_get_race_event_bet_answers_returns_event_and_session_answers(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 3, 8, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 6, 11, 30, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 6, 11, 25, tzinfo=timezone.utc),
        ),
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2026, 3, 8, 16, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(race_event)
    db_session.flush()

    fp1_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.FP1)
    race_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.RACE)

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

    safety_car_score = BetScore(
        code="SAFETY_CAR",
        label="Safety Car",
        base_points=3,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    fp1_fastest_score = BetScore(
        code="FP1_FASTEST",
        label="FP1 Fastest Driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    race_winner_score = BetScore(
        code="RACE_WINNER",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([safety_car_score, fp1_fastest_score, race_winner_score])
    db_session.flush()

    event_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
        locked_at=None,
    )
    fp1_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=fp1_session.id,
        testing_event_session_id=None,
        submitted_at=None,
        locked_at=None,
    )
    race_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=race_session.id,
        testing_event_session_id=None,
        submitted_at=datetime(2026, 3, 8, 15, 30, tzinfo=timezone.utc),
        locked_at=datetime(2026, 3, 8, 15, 55, tzinfo=timezone.utc),
    )
    db_session.add_all([event_bet, fp1_bet, race_bet])
    db_session.flush()

    db_session.add_all(
        [
            BetPick(
                bet_id=event_bet.id,
                bet_score_id=safety_car_score.id,
                value="true",
            ),
            BetPick(
                bet_id=fp1_bet.id,
                bet_score_id=fp1_fastest_score.id,
                value="VER",
            ),
            BetPick(
                bet_id=race_bet.id,
                bet_score_id=race_winner_score.id,
                value="NOR",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(race_event.public_id)
    assert payload["label"] == "Bahrain GP"
    assert payload["submitted_at"] == "2026-03-05T10:00:00Z"

    assert payload["event_answers"] == [
        {
            "bet_score_code": "SAFETY_CAR",
            "value": "true",
        }
    ]

    assert len(payload["sessions"]) == 2
    assert [session["session_type"] for session in payload["sessions"]] == ["FP1", "RACE"]

    fp1_payload = payload["sessions"][0]
    assert fp1_payload["event_session_public_id"] == str(fp1_session.public_id)
    assert "submitted_at" not in fp1_payload
    assert fp1_payload["answers"] == [
        {
            "bet_score_code": "FP1_FASTEST",
            "value": "VER",
        }
    ]

    race_payload = payload["sessions"][1]
    assert race_payload["event_session_public_id"] == str(race_session.public_id)
    assert race_payload["submitted_at"] == "2026-03-08T15:30:00Z"
    assert race_payload["locked_at"] == "2026-03-08T15:55:00Z"
    assert race_payload["answers"] == [
        {
            "bet_score_code": "RACE_WINNER",
            "value": "NOR",
        }
    ]


def test_get_testing_event_bet_answers_returns_event_and_filtered_session_answers(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code="bahrain",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing Bahrain",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2026, 2, 13, 17, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 11, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 11, 17, 0, tzinfo=timezone.utc),
        ),
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(2026, 2, 12, 7, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(2026, 2, 12, 17, 0, tzinfo=timezone.utc),
        ),
    ]
    db_session.add(testing_event)
    db_session.flush()

    day_1 = next(session for session in testing_event.sessions if session.session_order == 1)
    day_2 = next(session for session in testing_event.sessions if session.session_order == 2)

    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Bahrain Testing",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    event_score = BetScore(
        code="TESTING_TOP_TEAM",
        label="Top team in testing",
        base_points=3,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    day_1_score = BetScore(
        code="TESTING_DAY_1_FASTEST",
        label="Day 1 fastest driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    day_2_score = BetScore(
        code="TESTING_DAY_2_FASTEST",
        label="Day 2 fastest driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([event_score, day_1_score, day_2_score])
    db_session.flush()

    event_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
        locked_at=None,
    )
    day_1_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=day_1.id,
        submitted_at=None,
        locked_at=None,
    )
    day_2_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=day_2.id,
        submitted_at=datetime(2026, 2, 12, 6, 30, tzinfo=timezone.utc),
        locked_at=None,
    )
    db_session.add_all([event_bet, day_1_bet, day_2_bet])
    db_session.flush()

    db_session.add_all(
        [
            BetPick(
                bet_id=event_bet.id,
                bet_score_id=event_score.id,
                value="RBR",
            ),
            BetPick(
                bet_id=day_1_bet.id,
                bet_score_id=day_1_score.id,
                value="VER",
            ),
            BetPick(
                bet_id=day_2_bet.id,
                bet_score_id=day_2_score.id,
                value="LEC",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/testing-events/{testing_event.public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "PRETESTING"
    assert payload["testing_event_public_id"] == str(testing_event.public_id)
    assert payload["label"] == "Bahrain Testing"
    assert payload["status"] == "SCHEDULED"
    assert payload["submitted_at"] == "2026-02-10T10:00:00Z"
    assert payload["event_answers"] == [
        {
            "bet_score_code": "TESTING_TOP_TEAM",
            "value": "RBR",
        }
    ]

    assert len(payload["sessions"]) == 2
    assert [session["session_order"] for session in payload["sessions"]] == [1, 2]
    assert payload["sessions"][0]["testing_event_session_public_id"] == str(day_1.public_id)
    assert payload["sessions"][0]["answers"] == [
        {
            "bet_score_code": "TESTING_DAY_1_FASTEST",
            "value": "VER",
        }
    ]
    assert payload["sessions"][1]["testing_event_session_public_id"] == str(day_2.public_id)
    assert payload["sessions"][1]["submitted_at"] == "2026-02-12T06:30:00Z"
    assert payload["sessions"][1]["answers"] == [
        {
            "bet_score_code": "TESTING_DAY_2_FASTEST",
            "value": "LEC",
        }
    ]

    filtered_response = client.get(
        f"/api/v1/bets/testing-events/{testing_event.public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(day_2.public_id)},
    )

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()

    assert filtered_payload["bet_context_public_id"] == str(bet_context.public_id)
    assert filtered_payload["kind"] == "PRETESTING"
    assert filtered_payload["testing_event_public_id"] == str(testing_event.public_id)
    assert filtered_payload["event_answers"] == []
    assert len(filtered_payload["sessions"]) == 1
    assert filtered_payload["sessions"][0]["testing_event_session_public_id"] == str(day_2.public_id)
    assert filtered_payload["sessions"][0]["session_order"] == 2
    assert filtered_payload["sessions"][0]["name"] == "Day 2"
    assert filtered_payload["sessions"][0]["submitted_at"] == "2026-02-12T06:30:00Z"
    assert filtered_payload["sessions"][0]["answers"] == [
        {
            "bet_score_code": "TESTING_DAY_2_FASTEST",
            "value": "LEC",
        }
    ]


def _create_patch_race_event_answers_fixture(db_session, *, user_id: int, group_id: int):
    now = datetime.now(timezone.utc)

    season = Season(year=2026, is_active=True)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"bahrain_{uuid4().hex[:8]}",
        name="Bahrain International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=now + timedelta(days=3),
        scheduled_event_end=now + timedelta(days=5),
        betting_open_at=now - timedelta(hours=1),
        lock_cutoff=now + timedelta(days=2),
        scheduled_lock_cutoff=now + timedelta(days=2),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=now + timedelta(days=1),
            scheduled_start_datetime=now + timedelta(days=1),
            betting_open_at=now - timedelta(hours=1),
            lock_cutoff=now + timedelta(hours=12),
            scheduled_lock_cutoff=now + timedelta(hours=12),
        ),
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=now + timedelta(days=3),
            scheduled_start_datetime=now + timedelta(days=3),
            betting_open_at=now - timedelta(hours=1),
            lock_cutoff=now + timedelta(days=2),
            scheduled_lock_cutoff=now + timedelta(days=2),
        ),
    ]
    db_session.add(race_event)
    db_session.flush()

    fp1_session = next(session for session in race_event.event_sessions if session.session_type == SessionType.FP1)

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Bahrain GP",
        results_published=False,
        results_published_at=None,
        group_id=group_id,
    )
    db_session.add(bet_context)
    db_session.flush()

    safety_car_score = BetScore(
        code=f"SAFETY_CAR_{uuid4().hex[:8].upper()}",
        label="Safety Car",
        base_points=3,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    pole_score = BetScore(
        code=f"POLE_SITTER_{uuid4().hex[:8].upper()}",
        label="Pole sitter",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    fp1_fastest_score = BetScore(
        code=f"FP1_FASTEST_{uuid4().hex[:8].upper()}",
        label="FP1 fastest driver",
        base_points=4,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([safety_car_score, pole_score, fp1_fastest_score])
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="GP Event Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    fp1_template = BetTemplate(
        season_id=season.id,
        name="GP FP1 Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.FP1,
    )
    db_session.add_all([event_template, fp1_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=safety_car_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=pole_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_fastest_score.id,
                required=True,
                display_order=0,
            ),
        ]
    )
    db_session.flush()

    return {
        "race_event": race_event,
        "fp1_session": fp1_session,
        "bet_context": bet_context,
        "safety_car_score": safety_car_score,
        "pole_score": pole_score,
        "fp1_fastest_score": fp1_fastest_score,
    }


def test_patch_race_event_bet_answers_saves_partial_event_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["safety_car_score"].code,
                    "value": "true",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(data["race_event"].public_id)
    assert "submitted_at" not in payload
    assert "locked_at" not in payload
    assert "last_modified_at" in payload
    assert payload["event_answers"] == [
        {
            "bet_score_code": data["safety_car_score"].code,
            "value": "true",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id is None
    )
    assert saved_bet.submitted_at is None
    assert saved_bet.locked_at is None
    assert saved_bet.last_modified_at is not None


def test_patch_race_event_bet_answers_saves_partial_session_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["fp1_session"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["event_answers"] == []
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["event_session_public_id"] == str(data["fp1_session"].public_id)
    assert payload["sessions"][0]["session_type"] == "FP1"
    assert "submitted_at" not in payload["sessions"][0]
    assert "locked_at" not in payload["sessions"][0]
    assert "last_modified_at" in payload["sessions"][0]
    assert payload["sessions"][0]["answers"] == [
        {
            "bet_score_code": data["fp1_fastest_score"].code,
            "value": "VER",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id == data["fp1_session"].id
    )
    assert saved_bet.submitted_at is None
    assert saved_bet.locked_at is None
    assert saved_bet.last_modified_at is not None


def test_patch_race_event_bet_answers_returns_409_when_session_is_closed(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["fp1_session"].lock_cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["fp1_session"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_closed"


def test_patch_race_event_bet_answers_returns_409_when_event_is_not_open(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["race_event"].betting_open_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["safety_car_score"].code,
                    "value": "true",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_not_open"


def test_patch_race_event_bet_answers_returns_400_when_answer_is_not_in_scope(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fp1_fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.answer_question_not_found"


def test_patch_race_event_bet_answers_returns_409_when_bet_is_already_submitted(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["safety_car_score"].code,
                    "value": "true",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.already_submitted"


def _create_submit_race_event_answers_fixture(db_session, *, user_id: int, group_id: int):
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:8].upper()
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    season_year = None
    for candidate_year in range(1950, 2101):
        if db_session.query(Season).filter(Season.year == candidate_year).first() is None:
            season_year = candidate_year
            break
    assert season_year is not None

    country_iso2 = None
    for first in alphabet:
        for second in alphabet:
            candidate_iso2 = f"{first}{second}"
            if db_session.query(Country).filter(Country.iso2 == candidate_iso2).first() is None:
                country_iso2 = candidate_iso2
                break
        if country_iso2 is not None:
            break
    assert country_iso2 is not None

    season = Season(year=season_year, is_active=False)
    country = Country(
        iso2=country_iso2,
        name=f"Submit Country {suffix}",
        flag_asset_url=None,
    )
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"submit_{suffix.lower()}",
        name="Submit Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Submit Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=now + timedelta(days=3),
        scheduled_event_end=now + timedelta(days=5),
        betting_open_at=now - timedelta(hours=1),
        lock_cutoff=now + timedelta(days=2),
        scheduled_lock_cutoff=now + timedelta(days=2),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=now + timedelta(days=1),
            scheduled_start_datetime=now + timedelta(days=1),
            betting_open_at=now - timedelta(hours=1),
            lock_cutoff=now + timedelta(hours=12),
            scheduled_lock_cutoff=now + timedelta(hours=12),
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    fp1_session = race_event.event_sessions[0]

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Submit GP",
        results_published=False,
        results_published_at=None,
        group_id=group_id,
    )
    db_session.add(bet_context)
    db_session.flush()

    safety_car_score = BetScore(
        code=f"SUBMIT_SAFETY_CAR_{suffix}",
        label="Safety Car",
        base_points=3,
        value_type=BetValueType.BOOLEAN,
        constraints_json=None,
    )
    pole_score = BetScore(
        code=f"SUBMIT_POLE_{suffix}",
        label="Pole sitter",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    fp1_score = BetScore(
        code=f"SUBMIT_FP1_FASTEST_{suffix}",
        label="FP1 fastest",
        base_points=4,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([safety_car_score, pole_score, fp1_score])
    db_session.flush()

    event_template = BetTemplate(
        season_id=season.id,
        name="Submit GP Event Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    fp1_template = BetTemplate(
        season_id=season.id,
        name="Submit GP FP1 Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.SESSION,
        session_type=SessionType.FP1,
    )
    db_session.add_all([event_template, fp1_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=safety_car_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=event_template.id,
                bet_score_id=pole_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=fp1_template.id,
                bet_score_id=fp1_score.id,
                required=True,
                display_order=0,
            ),
        ]
    )
    db_session.flush()

    return {
        "race_event": race_event,
        "fp1_session": fp1_session,
        "bet_context": bet_context,
        "safety_car_score": safety_car_score,
        "pole_score": pole_score,
        "fp1_score": fp1_score,
    }


def test_submit_race_event_bet_answers_creates_first_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["safety_car_score"].code,
                    "value": "true",
                },
                {
                    "bet_score_code": data["pole_score"].code,
                    "value": "VER",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(data["race_event"].public_id)
    assert payload["submitted_at"] is not None
    assert payload["last_modified_at"] is not None
    assert answers_by_code == {
        data["safety_car_score"].code: "true",
        data["pole_score"].code: "VER",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id is None
    )
    assert saved_bet.submitted_at is not None
    assert saved_bet.last_modified_at is not None
    assert saved_bet.locked_at is None
    assert saved_bet.submit_order_int is None
    assert len(saved_bet.submission_revisions) == 1
    assert saved_bet.submission_revisions[0].revision_number == 1


def test_submit_race_event_bet_answers_merges_existing_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    draft_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=None,
        locked_at=None,
    )
    db_session.add(draft_bet)
    db_session.flush()
    db_session.add(
        BetPick(
            bet_id=draft_bet.id,
            bet_score_id=data["safety_car_score"].id,
            value="false",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["pole_score"].code,
                    "value": "LEC",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }

    assert payload["submitted_at"] is not None
    assert answers_by_code == {
        data["safety_car_score"].code: "false",
        data["pole_score"].code: "LEC",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id is None
    )
    assert saved_bet.submitted_at is not None
    assert len(saved_bet.submission_revisions) == 1


def test_submit_race_event_session_bet_answers_creates_session_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["fp1_session"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fp1_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["event_answers"] == []
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["event_session_public_id"] == str(data["fp1_session"].public_id)
    assert payload["sessions"][0]["submitted_at"] is not None
    assert payload["sessions"][0]["last_modified_at"] is not None
    assert payload["sessions"][0]["answers"] == [
        {
            "bet_score_code": data["fp1_score"].code,
            "value": "VER",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id == data["fp1_session"].id
    )
    assert saved_bet.submitted_at is not None
    assert len(saved_bet.submission_revisions) == 1


def test_submit_race_event_bet_answers_updates_existing_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    first_submitted_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=first_submitted_at,
        last_modified_at=first_submitted_at,
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()
    db_session.add_all(
        [
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["safety_car_score"].id,
                value="true",
            ),
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["pole_score"].id,
                value="VER",
            ),
            BetSubmissionRevision(
                bet_id=submitted_bet.id,
                revision_number=1,
                submitted_at=first_submitted_at,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["pole_score"].code,
                    "value": "LEC",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }

    assert payload["submitted_at"] is not None
    assert answers_by_code[data["pole_score"].code] == "LEC"

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id is None
    )
    assert saved_bet.submitted_at == first_submitted_at
    assert saved_bet.last_modified_at > first_submitted_at
    assert len(saved_bet.submission_revisions) == 2
    assert sorted(revision.revision_number for revision in saved_bet.submission_revisions) == [1, 2]


def test_submit_race_event_bet_answers_returns_400_when_required_answer_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["safety_car_score"].code,
                    "value": "true",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.required_answer_missing"


def test_submit_race_event_bet_answers_allows_modification_with_active_permission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    first_submitted_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    data["race_event"].lock_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=first_submitted_at,
        last_modified_at=first_submitted_at,
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()
    db_session.add_all(
        [
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["safety_car_score"].id,
                value="true",
            ),
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["pole_score"].id,
                value="VER",
            ),
            BetSubmissionRevision(
                bet_id=submitted_bet.id,
                revision_number=1,
                submitted_at=first_submitted_at,
            ),
            BetEditPermission(
                bet_context_id=data["bet_context"].id,
                event_session_id=None,
                testing_event_session_id=None,
                applies_to_all=True,
                starts_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                ends_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                max_modifications=1,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["pole_score"].code,
                    "value": "LEC",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }
    assert answers_by_code[data["pole_score"].code] == "LEC"

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.event_session_id is None
    )
    assert len(saved_bet.submission_revisions) == 2


def test_submit_race_event_bet_answers_returns_409_when_modification_limit_is_reached(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_submit_race_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    first_submitted_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    second_submitted_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    data["race_event"].lock_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=first_submitted_at,
        last_modified_at=second_submitted_at,
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()
    db_session.add_all(
        [
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["safety_car_score"].id,
                value="true",
            ),
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["pole_score"].id,
                value="VER",
            ),
            BetSubmissionRevision(
                bet_id=submitted_bet.id,
                revision_number=1,
                submitted_at=first_submitted_at,
            ),
            BetSubmissionRevision(
                bet_id=submitted_bet.id,
                revision_number=2,
                submitted_at=second_submitted_at,
            ),
            BetEditPermission(
                bet_context_id=data["bet_context"].id,
                event_session_id=None,
                testing_event_session_id=None,
                applies_to_all=True,
                starts_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                ends_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                max_modifications=1,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/race-events/{data['race_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["pole_score"].code,
                    "value": "LEC",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.modification_limit_reached"


def _create_patch_testing_event_answers_fixture(db_session, *, user_id: int, group_id: int):
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:8].upper()
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    season_year = None
    for candidate_year in range(1950, 2101):
        if db_session.query(Season).filter(Season.year == candidate_year).first() is None:
            season_year = candidate_year
            break
    assert season_year is not None

    country_iso2 = None
    for first in alphabet:
        for second in alphabet:
            candidate_iso2 = f"{first}{second}"
            if db_session.query(Country).filter(Country.iso2 == candidate_iso2).first() is None:
                country_iso2 = candidate_iso2
                break
        if country_iso2 is not None:
            break
    assert country_iso2 is not None

    season = Season(
        year=season_year,
        is_active=False,
    )
    country = Country(
        iso2=country_iso2,
        name=f"Testing Country {suffix}",
        flag_asset_url=None,
    )
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"testing_{suffix.lower()}",
        name="Testing Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=now + timedelta(days=3),
        scheduled_event_end=now + timedelta(days=5),
        betting_open_at=now - timedelta(hours=1),
        lock_cutoff=now + timedelta(days=2),
        scheduled_lock_cutoff=now + timedelta(days=2),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=8),
            scheduled_start_datetime=now + timedelta(days=1),
            scheduled_end_datetime=now + timedelta(days=1, hours=8),
            betting_open_at=now - timedelta(hours=1),
            lock_cutoff=now + timedelta(hours=12),
            scheduled_lock_cutoff=now + timedelta(hours=12),
        ),
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=2),
            end_datetime=now + timedelta(days=2, hours=8),
            scheduled_start_datetime=now + timedelta(days=2),
            scheduled_end_datetime=now + timedelta(days=2, hours=8),
            betting_open_at=now - timedelta(hours=1),
            lock_cutoff=now + timedelta(days=1, hours=12),
            scheduled_lock_cutoff=now + timedelta(days=1, hours=12),
        ),
    ]
    db_session.add(testing_event)
    db_session.flush()

    day_1 = next(session for session in testing_event.sessions if session.session_order == 1)

    bet_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Bahrain Testing",
        results_published=False,
        results_published_at=None,
        group_id=group_id,
    )
    db_session.add(bet_context)
    db_session.flush()

    top_team_score = BetScore(
        code=f"TESTING_TOP_TEAM_{suffix}",
        label="Top testing team",
        base_points=3,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    fastest_score = BetScore(
        code=f"TESTING_FASTEST_{suffix}",
        label="Fastest testing driver",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    race_only_score = BetScore(
        code=f"RACE_ONLY_{suffix}",
        label="Race only score",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([top_team_score, fastest_score, race_only_score])
    db_session.flush()

    testing_template = BetTemplate(
        season_id=season.id,
        name="Testing Event Template",
        context_kind=BetContextKind.PRETESTING,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    race_template = BetTemplate(
        season_id=season.id,
        name="GP Race Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add_all([testing_template, race_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=testing_template.id,
                bet_score_id=top_team_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=testing_template.id,
                bet_score_id=fastest_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_only_score.id,
                required=True,
                display_order=0,
            ),
        ]
    )
    db_session.flush()

    return {
        "testing_event": testing_event,
        "day_1": day_1,
        "bet_context": bet_context,
        "top_team_score": top_team_score,
        "fastest_score": fastest_score,
        "race_only_score": race_only_score,
    }


def test_patch_testing_event_bet_answers_saves_partial_event_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "PRETESTING"
    assert payload["testing_event_public_id"] == str(data["testing_event"].public_id)
    assert payload["label"] == "Bahrain Testing"
    assert payload["status"] == "SCHEDULED"
    assert "submitted_at" not in payload
    assert "locked_at" not in payload
    assert "last_modified_at" in payload
    assert payload["event_answers"] == [
        {
            "bet_score_code": data["top_team_score"].code,
            "value": "RBR",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.testing_event_session_id is None
    )
    assert saved_bet.event_session_id is None
    assert saved_bet.submitted_at is None
    assert saved_bet.locked_at is None
    assert saved_bet.last_modified_at is not None


def test_patch_testing_event_bet_answers_saves_partial_session_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["day_1"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["event_answers"] == []
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["testing_event_session_public_id"] == str(data["day_1"].public_id)
    assert payload["sessions"][0]["session_order"] == 1
    assert payload["sessions"][0]["name"] == "Day 1"
    assert "submitted_at" not in payload["sessions"][0]
    assert "locked_at" not in payload["sessions"][0]
    assert "last_modified_at" in payload["sessions"][0]
    assert payload["sessions"][0]["answers"] == [
        {
            "bet_score_code": data["fastest_score"].code,
            "value": "VER",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.testing_event_session_id == data["day_1"].id
    )
    assert saved_bet.event_session_id is None
    assert saved_bet.submitted_at is None
    assert saved_bet.locked_at is None
    assert saved_bet.last_modified_at is not None


def test_patch_testing_event_bet_answers_returns_409_when_session_is_closed(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["day_1"].lock_cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["day_1"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_closed"


def test_patch_testing_event_bet_answers_returns_409_when_event_is_not_open(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["testing_event"].betting_open_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_not_open"


def test_patch_testing_event_bet_answers_returns_400_when_answer_is_not_in_scope(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["race_only_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.answer_question_not_found"


def test_patch_testing_event_bet_answers_returns_409_when_bet_is_already_submitted(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.already_submitted"


def test_submit_testing_event_bet_answers_creates_first_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                },
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "VER",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "PRETESTING"
    assert payload["testing_event_public_id"] == str(data["testing_event"].public_id)
    assert payload["label"] == "Bahrain Testing"
    assert payload["status"] == "SCHEDULED"
    assert payload["submitted_at"] is not None
    assert payload["last_modified_at"] is not None
    assert answers_by_code == {
        data["top_team_score"].code: "RBR",
        data["fastest_score"].code: "VER",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.testing_event_session_id is None
    )
    assert saved_bet.event_session_id is None
    assert saved_bet.submitted_at is not None
    assert saved_bet.last_modified_at is not None
    assert saved_bet.locked_at is None
    assert saved_bet.submit_order_int is None
    assert len(saved_bet.submission_revisions) == 1
    assert saved_bet.submission_revisions[0].revision_number == 1


def test_submit_testing_event_bet_answers_merges_existing_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    draft_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=None,
        locked_at=None,
    )
    db_session.add(draft_bet)
    db_session.flush()
    db_session.add(
        BetPick(
            bet_id=draft_bet.id,
            bet_score_id=data["top_team_score"].id,
            value="FER",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["event_answers"]
    }

    assert payload["submitted_at"] is not None
    assert answers_by_code == {
        data["top_team_score"].code: "FER",
        data["fastest_score"].code: "VER",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.testing_event_session_id is None
    )
    assert saved_bet.submitted_at is not None
    assert len(saved_bet.submission_revisions) == 1


def test_submit_testing_event_session_bet_answers_creates_session_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(data["day_1"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                },
                {
                    "bet_score_code": data["fastest_score"].code,
                    "value": "VER",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["event_answers"] == []
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["testing_event_session_public_id"] == str(data["day_1"].public_id)
    assert payload["sessions"][0]["session_order"] == 1
    assert payload["sessions"][0]["name"] == "Day 1"
    assert payload["sessions"][0]["submitted_at"] is not None
    assert payload["sessions"][0]["last_modified_at"] is not None
    session_answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["sessions"][0]["answers"]
    }
    assert session_answers_by_code == {
        data["top_team_score"].code: "RBR",
        data["fastest_score"].code: "VER",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id and bet.testing_event_session_id == data["day_1"].id
    )
    assert saved_bet.event_session_id is None
    assert saved_bet.submitted_at is not None
    assert len(saved_bet.submission_revisions) == 1


def test_submit_testing_event_bet_answers_returns_400_when_required_answer_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_testing_event_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/testing-events/{data['testing_event'].public_id}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["top_team_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.required_answer_missing"


def _create_patch_season_answers_fixture(db_session, *, user_id: int, group_id: int):
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:8].upper()

    season_year = None
    for candidate_year in range(1950, 2101):
        if db_session.query(Season).filter(Season.year == candidate_year).first() is None:
            season_year = candidate_year
            break
    assert season_year is not None

    season = Season(
        year=season_year,
        is_active=False,
        betting_open_at=now - timedelta(hours=1),
        lock_cutoff=now + timedelta(days=30),
        scheduled_lock_cutoff=now + timedelta(days=30),
    )
    db_session.add(season)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.SEASON,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=None,
        label=f"{season.year} Season",
        results_published=False,
        results_published_at=None,
        group_id=group_id,
    )
    db_session.add(bet_context)
    db_session.flush()

    champion_score = BetScore(
        code=f"DRIVERS_CHAMPION_{suffix}",
        label="Drivers champion",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    constructors_score = BetScore(
        code=f"CONSTRUCTORS_CHAMPION_{suffix}",
        label="Constructors champion",
        base_points=8,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    race_only_score = BetScore(
        code=f"RACE_ONLY_SEASON_{suffix}",
        label="Race-only score",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([champion_score, constructors_score, race_only_score])
    db_session.flush()

    season_template = BetTemplate(
        season_id=season.id,
        name="Season Template",
        context_kind=BetContextKind.SEASON,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    race_template = BetTemplate(
        season_id=season.id,
        name="GP Template",
        context_kind=BetContextKind.GP,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add_all([season_template, race_template])
    db_session.flush()

    db_session.add_all(
        [
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=champion_score.id,
                required=True,
                display_order=0,
            ),
            BetTemplateItem(
                template_id=season_template.id,
                bet_score_id=constructors_score.id,
                required=True,
                display_order=1,
            ),
            BetTemplateItem(
                template_id=race_template.id,
                bet_score_id=race_only_score.id,
                required=True,
                display_order=0,
            ),
        ]
    )
    db_session.flush()

    return {
        "season": season,
        "bet_context": bet_context,
        "champion_score": champion_score,
        "constructors_score": constructors_score,
        "race_only_score": race_only_score,
    }


def test_patch_season_bet_answers_saves_partial_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "SEASON"
    assert payload["season_year"] == data["season"].year
    assert payload["label"] == f"{data['season'].year} Season"
    assert "submitted_at" not in payload
    assert "locked_at" not in payload
    assert "last_modified_at" in payload
    assert payload["answers"] == [
        {
            "bet_score_code": data["champion_score"].code,
            "value": "VER",
        }
    ]

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id
        and bet.event_session_id is None
        and bet.testing_event_session_id is None
    )
    assert saved_bet.submitted_at is None
    assert saved_bet.locked_at is None
    assert saved_bet.last_modified_at is not None


def test_patch_season_bet_answers_returns_409_when_season_is_closed(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["season"].lock_cutoff = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_closed"


def test_patch_season_bet_answers_returns_409_when_season_is_not_open(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    data["season"].betting_open_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.answers_not_open"


def test_patch_season_bet_answers_returns_400_when_answer_is_not_in_scope(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["race_only_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.answer_question_not_found"


def test_patch_season_bet_answers_returns_409_when_bet_is_already_submitted(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "bets.already_submitted"


def test_submit_season_bet_answers_creates_first_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                },
                {
                    "bet_score_code": data["constructors_score"].code,
                    "value": "RBR",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["answers"]
    }

    assert payload["bet_context_public_id"] == str(data["bet_context"].public_id)
    assert payload["kind"] == "SEASON"
    assert payload["season_year"] == data["season"].year
    assert payload["label"] == f"{data['season'].year} Season"
    assert payload["submitted_at"] is not None
    assert payload["last_modified_at"] is not None
    assert answers_by_code == {
        data["champion_score"].code: "VER",
        data["constructors_score"].code: "RBR",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id
        and bet.event_session_id is None
        and bet.testing_event_session_id is None
    )
    assert saved_bet.submitted_at is not None
    assert saved_bet.last_modified_at is not None
    assert saved_bet.locked_at is None
    assert saved_bet.submit_order_int is None
    assert len(saved_bet.submission_revisions) == 1
    assert saved_bet.submission_revisions[0].revision_number == 1


def test_submit_season_bet_answers_merges_existing_draft(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    draft_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=None,
        locked_at=None,
    )
    db_session.add(draft_bet)
    db_session.flush()
    db_session.add(
        BetPick(
            bet_id=draft_bet.id,
            bet_score_id=data["champion_score"].id,
            value="VER",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["constructors_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["answers"]
    }

    assert payload["submitted_at"] is not None
    assert answers_by_code == {
        data["champion_score"].code: "VER",
        data["constructors_score"].code: "RBR",
    }

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id
        and bet.event_session_id is None
        and bet.testing_event_session_id is None
    )
    assert saved_bet.submitted_at is not None
    assert len(saved_bet.submission_revisions) == 1


def test_submit_season_bet_answers_updates_existing_submission(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    first_submitted_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    submitted_bet = Bet(
        user_id=user.id,
        bet_context_id=data["bet_context"].id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=first_submitted_at,
        last_modified_at=first_submitted_at,
        locked_at=None,
    )
    db_session.add(submitted_bet)
    db_session.flush()
    db_session.add_all(
        [
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["champion_score"].id,
                value="VER",
            ),
            BetPick(
                bet_id=submitted_bet.id,
                bet_score_id=data["constructors_score"].id,
                value="FER",
            ),
            BetSubmissionRevision(
                bet_id=submitted_bet.id,
                revision_number=1,
                submitted_at=first_submitted_at,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["constructors_score"].code,
                    "value": "RBR",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    answers_by_code = {
        answer["bet_score_code"]: answer["value"]
        for answer in payload["answers"]
    }

    assert payload["submitted_at"] is not None
    assert answers_by_code[data["constructors_score"].code] == "RBR"

    db_session.expire_all()
    saved_bet = next(
        bet
        for bet in data["bet_context"].bets
        if bet.user_id == user.id
        and bet.event_session_id is None
        and bet.testing_event_session_id is None
    )
    assert saved_bet.submitted_at == first_submitted_at
    assert saved_bet.last_modified_at > first_submitted_at
    assert len(saved_bet.submission_revisions) == 2
    assert sorted(revision.revision_number for revision in saved_bet.submission_revisions) == [1, 2]


def test_submit_season_bet_answers_returns_400_when_required_answer_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    data = _create_patch_season_answers_fixture(
        db_session,
        user_id=user.id,
        group_id=group.id,
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["champion_score"].code,
                    "value": "VER",
                }
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "bets.required_answer_missing"


def test_get_season_bet_answers_returns_answers(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    db_session.add(season)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.SEASON,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=None,
        label="2026 Season",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    champion_score = BetScore(
        code="DRIVERS_CHAMPION",
        label="Drivers champion",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    constructors_score = BetScore(
        code="CONSTRUCTORS_CHAMPION",
        label="Constructors champion",
        base_points=8,
        value_type=BetValueType.TEAM,
        constraints_json=None,
    )
    db_session.add_all([champion_score, constructors_score])
    db_session.flush()

    season_bet = Bet(
        user_id=user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
        locked_at=None,
    )
    db_session.add(season_bet)
    db_session.flush()

    db_session.add_all(
        [
            BetPick(
                bet_id=season_bet.id,
                bet_score_id=champion_score.id,
                value="VER",
            ),
            BetPick(
                bet_id=season_bet.id,
                bet_score_id=constructors_score.id,
                value="RBR",
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/seasons/{season.year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "SEASON"
    assert payload["season_year"] == 2026
    assert payload["label"] == "2026 Season"
    assert payload["submitted_at"] == "2026-02-01T12:00:00Z"
    assert payload["answers"] == [
        {
            "bet_score_code": "CONSTRUCTORS_CHAMPION",
            "value": "RBR",
        },
        {
            "bet_score_code": "DRIVERS_CHAMPION",
            "value": "VER",
        },
    ]


def test_get_season_bet_answers_returns_404_when_season_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        "/api/v1/bets/seasons/2099/answers",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "bets.season_not_found"


def test_get_season_bet_answers_returns_404_when_bet_context_is_missing(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=user.id,
        name=f"group_{uuid4().hex[:8]}",
    )

    season = Season(year=2026, is_active=True)
    db_session.add(season)
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/seasons/{season.year}/answers",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "bets.bet_context_not_found_for_season"


def test_get_race_event_bet_results_returns_group_event_results_when_always_visible(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_{uuid4().hex[:8]}",
        email=f"viewer_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    other_user = _create_user(
        db_session,
        username=f"other_{uuid4().hex[:8]}",
        email=f"other_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=viewer.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    db_session.add(
        GroupMembership(
            group_id=group.id,
            user_id=other_user.id,
            role=GroupRole.MEMBER,
        )
    )
    db_session.flush()

    season = Season(year=2031, is_active=True)
    country = Country(iso2="QA", name="Qatar", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"lusail_{uuid4().hex[:8]}",
        name="Lusail International Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Qatar Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        event_start=datetime(2031, 3, 10, 16, 0, tzinfo=timezone.utc),
        scheduled_event_start=datetime(2031, 3, 10, 16, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2031, 3, 10, 18, 0, tzinfo=timezone.utc),
        lock_cutoff=datetime(2031, 3, 10, 15, 55, tzinfo=timezone.utc),
        scheduled_lock_cutoff=datetime(2031, 3, 10, 15, 55, tzinfo=timezone.utc),
    )
    db_session.add(race_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Qatar GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    race_winner_score = BetScore(
        code=f"RACE_WINNER_{uuid4().hex[:8].upper()}",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([bet_context, race_winner_score])
    db_session.flush()

    db_session.add_all(
        [
            BetResultsVisibilityPolicy(
                bet_context_id=bet_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                visibility_mode=BetResultsVisibilityMode.ALWAYS_VISIBLE,
            ),
            OfficialResult(
                bet_context_id=bet_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                bet_score_id=race_winner_score.id,
                value="VER",
                source=SourceType.MANUAL,
            ),
            ResultPublication(
                bet_context_id=bet_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                published_by_user_id=viewer.id,
            ),
        ]
    )
    db_session.flush()

    submitted_at = datetime(2031, 3, 10, 15, 30, tzinfo=timezone.utc)
    bet = Bet(
        user_id=other_user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=submitted_at,
        last_modified_at=submitted_at,
        locked_at=None,
    )
    db_session.add(bet)
    db_session.flush()

    db_session.add(
        BetPick(
            bet_id=bet.id,
            bet_score_id=race_winner_score.id,
            value="VER",
        )
    )
    score = Score(
        user_id=other_user.id,
        bet_context_id=bet_context.id,
        base_points=10,
        total_points=12,
        computed_at=datetime(2031, 3, 10, 18, 10, tzinfo=timezone.utc),
    )
    db_session.add(score)
    db_session.flush()
    db_session.add_all(
        [
            ScoreComponent(
                score_id=score.id,
                component_type=ScoreComponentType.BASE,
                code="RACE_WINNER_BASE",
                points=10,
                details_json={
                    "applies_to": {
                        "level": "QUESTION",
                        "bet_score_code": race_winner_score.code,
                    },
                    "matched": True,
                },
            ),
            ScoreComponent(
                score_id=score.id,
                component_type=ScoreComponentType.EXTRA,
                code="FIRST_SUBMIT",
                points=2,
                details_json={"applies_to": {"level": "EVENT"}},
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": viewer.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/results",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(race_event.public_id)
    assert payload["label"] == "Qatar GP"

    event_results = payload["event_results"]
    assert event_results["scope"] == {
        "type": "EVENT",
        "race_event_public_id": str(race_event.public_id),
    }
    assert event_results["visibility"]["mode"] == "ALWAYS_VISIBLE"
    assert event_results["visibility"]["can_view_group_results"] is True
    assert event_results["visibility"]["reason"] == "ALWAYS_VISIBLE"
    assert event_results["visibility"]["viewer_submitted"] is False
    assert event_results["visibility"]["results_published"] is True

    assert event_results["official_results"] == [
        {
            "bet_score_code": race_winner_score.code,
            "label": "Race Winner",
            "value": "VER",
            "source": "MANUAL",
            "created_at": event_results["official_results"][0]["created_at"],
        }
    ]

    assert len(event_results["entries"]) == 1
    entry = event_results["entries"][0]
    assert entry["user"]["public_id"] == str(other_user.public_id)
    assert entry["user"]["username"] == other_user.username
    assert entry["submitted_at"] == "2031-03-10T15:30:00Z"
    assert entry["answers"] == [
        {
            "bet_score_code": race_winner_score.code,
            "label": "Race Winner",
            "value": "VER",
            "is_invalid": False,
            "official_value": "VER",
            "is_correct": True,
            "points": {
                "base": 10.0,
                "powerup": 0.0,
                "extra": 0.0,
                "penalty": 0.0,
                "total": 10.0,
            },
            "components": [
                {
                    "type": "BASE",
                    "code": "RACE_WINNER_BASE",
                    "points": 10.0,
                    "applies_to": {
                        "level": "QUESTION",
                        "bet_score_code": race_winner_score.code,
                    },
                    "details": {
                        "applies_to": {
                            "level": "QUESTION",
                            "bet_score_code": race_winner_score.code,
                        },
                        "matched": True,
                    },
                }
            ],
        }
    ]
    assert entry["score"]["points"] == {
        "base": 10.0,
        "powerup": 0.0,
        "extra": 2.0,
        "penalty": 0.0,
        "total": 12.0,
    }
    assert entry["score"]["components"] == [
        {
            "type": "EXTRA",
            "code": "FIRST_SUBMIT",
            "points": 2.0,
            "applies_to": {"level": "EVENT"},
            "details": {"applies_to": {"level": "EVENT"}},
        }
    ]
    assert payload["sessions"] == []


def test_get_race_event_bet_results_with_session_id_returns_only_session_results(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_{uuid4().hex[:8]}",
        email=f"viewer_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    other_user = _create_user(
        db_session,
        username=f"other_{uuid4().hex[:8]}",
        email=f"other_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=viewer.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    db_session.add(
        GroupMembership(
            group_id=group.id,
            user_id=other_user.id,
            role=GroupRole.MEMBER,
        )
    )
    db_session.flush()

    season = Season(year=2032, is_active=True)
    country = Country(iso2="JP", name="Japan", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"suzuka_{uuid4().hex[:8]}",
        name="Suzuka Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=2,
        name="Japanese Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(2032, 4, 4, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2032, 4, 4, 10, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.QUALY,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.COMPLETED,
            start_datetime=datetime(2032, 4, 3, 7, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(2032, 4, 3, 7, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(2032, 4, 3, 6, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(2032, 4, 3, 6, 55, tzinfo=timezone.utc),
        )
    ]
    db_session.add(race_event)
    db_session.flush()
    session = race_event.event_sessions[0]

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Japanese GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    pole_score = BetScore(
        code=f"POLE_{uuid4().hex[:8].upper()}",
        label="Pole Position",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([bet_context, pole_score])
    db_session.flush()

    db_session.add_all(
        [
            BetResultsVisibilityPolicy(
                bet_context_id=bet_context.id,
                event_session_id=session.id,
                testing_event_session_id=None,
                visibility_mode=BetResultsVisibilityMode.ALWAYS_VISIBLE,
            ),
            OfficialResult(
                bet_context_id=bet_context.id,
                event_session_id=session.id,
                testing_event_session_id=None,
                bet_score_id=pole_score.id,
                value="LEC",
                source=SourceType.FASTF1,
            ),
        ]
    )
    db_session.flush()

    submitted_at = datetime(2032, 4, 3, 6, 40, tzinfo=timezone.utc)
    bet = Bet(
        user_id=other_user.id,
        bet_context_id=bet_context.id,
        event_session_id=session.id,
        testing_event_session_id=None,
        submitted_at=submitted_at,
        last_modified_at=submitted_at,
        locked_at=None,
    )
    db_session.add(bet)
    db_session.flush()
    db_session.add(
        BetPick(
            bet_id=bet.id,
            bet_score_id=pole_score.id,
            value="VER",
        )
    )
    score_session = ScoreSession(
        user_id=other_user.id,
        bet_context_id=bet_context.id,
        event_session_id=session.id,
        testing_event_session_id=None,
        base_points=0,
        total_points=0,
        computed_at=datetime(2032, 4, 3, 8, 0, tzinfo=timezone.utc),
    )
    db_session.add(score_session)
    db_session.flush()
    db_session.add(
        ScoreSessionComponent(
            score_session_id=score_session.id,
            component_type=ScoreComponentType.BASE,
            code="POLE_BASE",
            points=0,
            details_json={
                "applies_to": {
                    "level": "QUESTION",
                    "bet_score_code": pole_score.code,
                },
                "matched": False,
            },
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": viewer.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/results",
        headers={"X-Group-Id": str(group.public_id)},
        params={"session_id": str(session.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()

    assert "event_results" not in payload
    assert "sessions" not in payload
    assert payload["bet_context_public_id"] == str(bet_context.public_id)
    assert payload["kind"] == "GP"
    assert payload["race_event_public_id"] == str(race_event.public_id)
    assert payload["label"] == "Japanese GP"
    assert payload["scope"] == {
        "type": "SESSION",
        "race_event_public_id": str(race_event.public_id),
        "event_session_public_id": str(session.public_id),
        "session_type": "QUALY",
    }
    assert payload["visibility"]["can_view_group_results"] is True
    assert payload["official_results"][0]["bet_score_code"] == pole_score.code
    assert payload["official_results"][0]["value"] == "LEC"
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["answers"][0]["value"] == "VER"
    assert payload["entries"][0]["answers"][0]["official_value"] == "LEC"
    assert payload["entries"][0]["answers"][0]["is_correct"] is False
    assert payload["entries"][0]["score"]["points"] == {
        "base": 0.0,
        "powerup": 0.0,
        "extra": 0.0,
        "penalty": 0.0,
        "total": 0.0,
    }


def test_get_race_event_bet_results_hides_group_entries_when_submit_required_and_viewer_has_not_submitted(
    client,
    db_session,
) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_{uuid4().hex[:8]}",
        email=f"viewer_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    other_user = _create_user(
        db_session,
        username=f"other_{uuid4().hex[:8]}",
        email=f"other_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    group = _create_group_with_membership(
        db_session,
        user_id=viewer.id,
        name=f"group_{uuid4().hex[:8]}",
    )
    db_session.add(
        GroupMembership(
            group_id=group.id,
            user_id=other_user.id,
            role=GroupRole.MEMBER,
        )
    )
    db_session.flush()

    season = Season(year=2033, is_active=True)
    country = Country(iso2="AU", name="Australia", flag_asset_url=None)
    db_session.add_all([season, country])
    db_session.flush()

    circuit = Circuit(
        code=f"melbourne_{uuid4().hex[:8]}",
        name="Albert Park Circuit",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=3,
        name="Australian Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        event_start=datetime(2033, 3, 20, 6, 0, tzinfo=timezone.utc),
        scheduled_event_start=datetime(2033, 3, 20, 6, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2033, 3, 20, 8, 0, tzinfo=timezone.utc),
        lock_cutoff=datetime(2033, 3, 20, 5, 55, tzinfo=timezone.utc),
        scheduled_lock_cutoff=datetime(2033, 3, 20, 5, 55, tzinfo=timezone.utc),
    )
    db_session.add(race_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Australian GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    winner_score = BetScore(
        code=f"AUS_WINNER_{uuid4().hex[:8].upper()}",
        label="Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([bet_context, winner_score])
    db_session.flush()

    submitted_at = datetime(2033, 3, 20, 5, 30, tzinfo=timezone.utc)
    bet = Bet(
        user_id=other_user.id,
        bet_context_id=bet_context.id,
        event_session_id=None,
        testing_event_session_id=None,
        submitted_at=submitted_at,
        last_modified_at=submitted_at,
        locked_at=None,
    )
    db_session.add(bet)
    db_session.flush()
    db_session.add(
        BetPick(
            bet_id=bet.id,
            bet_score_id=winner_score.id,
            value="VER",
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": viewer.username, "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get(
        f"/api/v1/bets/race-events/{race_event.public_id}/results",
        headers={"X-Group-Id": str(group.public_id)},
    )

    assert response.status_code == 200
    payload = response.json()
    visibility = payload["event_results"]["visibility"]

    assert visibility["mode"] == "SUBMIT_REQUIRED"
    assert visibility["can_view_group_results"] is False
    assert visibility["reason"] == "SUBMIT_REQUIRED_NOT_SUBMITTED"
    assert visibility["is_locked"] is False
    assert visibility["viewer_submitted"] is False
    assert visibility["results_published"] is False
    assert payload["event_results"]["entries"] == []
    assert payload["event_results"]["official_results"] == []
