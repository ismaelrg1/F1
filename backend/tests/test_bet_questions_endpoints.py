# backend/tests/test_bet_questions_endpoints.py

from datetime import datetime, timezone
from uuid import uuid4

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.betting import BetContext, BetException, BetScore, BetTemplate, BetTemplateItem
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
    BetTemplateScope,
    BetValueType,
    RaceEventStatus,
    SeasonDriverStatus,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
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
