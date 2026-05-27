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
    RoleName,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.scoring import OfficialResult, ResultPublication
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
    role_name: RoleName | None = None,
) -> User:
    hasher = PasslibPasswordHasher()
    roles = []

    if role_name is not None:
        role = db_session.execute(
            select(Role).where(Role.name == role_name)
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name, description=role_name.value.title())
            db_session.add(role)
            db_session.flush()
        roles = [role]

    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
        roles=roles,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_group(db_session, *, name: str) -> Group:
    group = Group(
        name=name,
        join_code=None,
        is_private=False,
        teams_enabled=False,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()
    return group


def _add_membership(
    db_session,
    *,
    user_id: int,
    group_id: int,
    role: GroupRole,
) -> None:
    db_session.add(
        GroupMembership(
            user_id=user_id,
            group_id=group_id,
            role=role,
        )
    )
    db_session.flush()


def _create_management_calendar_fixture(db_session, *, season_year: int | None = None):
    year = season_year or 2100 + int(uuid4().hex[:3], 16) % 500
    season = Season(year=year, is_active=True)
    country = Country(
        iso2=uuid4().hex[:2].upper(),
        name=f"Country {uuid4().hex[:8]}",
        flag_asset_url=f"flags/{uuid4().hex[:8]}.svg",
    )
    db_session.add_all([season, country])
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

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
        scheduled_event_start=datetime(year, 3, 1, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(year, 3, 3, 18, 0, tzinfo=timezone.utc),
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.SCHEDULED,
            start_datetime=datetime(year, 3, 1, 10, 0, tzinfo=timezone.utc),
            scheduled_start_datetime=datetime(year, 3, 1, 10, 0, tzinfo=timezone.utc),
            lock_cutoff=datetime(year, 3, 1, 9, 55, tzinfo=timezone.utc),
            scheduled_lock_cutoff=datetime(year, 3, 1, 9, 55, tzinfo=timezone.utc),
        )
    ]
    db_session.add(race_event)
    db_session.flush()

    testing_event = CompetitionTestingEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing",
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
        scheduled_event_start=datetime(year, 2, 10, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(year, 2, 12, 18, 0, tzinfo=timezone.utc),
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=datetime(year, 2, 10, 8, 0, tzinfo=timezone.utc),
            scheduled_end_datetime=datetime(year, 2, 10, 18, 0, tzinfo=timezone.utc),
        )
    ]
    db_session.add(testing_event)
    db_session.flush()

    managed_group = _create_group(db_session, name=f"managed_{uuid4().hex[:8]}")
    empty_group = _create_group(db_session, name=f"empty_{uuid4().hex[:8]}")

    race_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Bahrain GP",
        results_published=False,
        results_published_at=None,
        group_id=managed_group.id,
    )
    testing_context = BetContext(
        kind=BetContextKind.PRETESTING,
        season_id=season.id,
        race_event_id=None,
        testing_event_id=testing_event.id,
        label="Pre-Season Testing",
        results_published=False,
        results_published_at=None,
        group_id=managed_group.id,
    )
    db_session.add_all([race_context, testing_context])
    db_session.flush()

    race_score = BetScore(
        code=f"RACE_WINNER_{uuid4().hex[:8].upper()}",
        label="Race Winner",
        base_points=10,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    testing_score = BetScore(
        code=f"DAY1_FASTEST_{uuid4().hex[:8].upper()}",
        label="Day 1 Fastest",
        base_points=5,
        value_type=BetValueType.DRIVER,
        constraints_json=None,
    )
    db_session.add_all([race_score, testing_score])
    db_session.flush()

    db_session.add_all(
        [
            OfficialResult(
                bet_context_id=race_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                bet_score_id=race_score.id,
                value="VER",
                source=SourceType.MANUAL,
            ),
            ResultPublication(
                bet_context_id=race_context.id,
                event_session_id=None,
                testing_event_session_id=None,
                published_by_user_id=None,
                note=None,
            ),
            OfficialResult(
                bet_context_id=testing_context.id,
                event_session_id=None,
                testing_event_session_id=testing_event.sessions[0].id,
                bet_score_id=testing_score.id,
                value="NOR",
                source=SourceType.MANUAL,
            ),
        ]
    )
    db_session.flush()

    return {
        "season": season,
        "country": country,
        "race_event": race_event,
        "race_session": race_event.event_sessions[0],
        "testing_event": testing_event,
        "testing_session": testing_event.sessions[0],
        "managed_group": managed_group,
        "empty_group": empty_group,
    }


def _login(client, user: User) -> None:
    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": user.username, "password": "secret123"},
    )
    assert response.status_code == 200


def test_get_management_calendar_requires_authentication(client) -> None:
    response = client.get("/api/v1/management/calendar")

    assert response.status_code == 401


def test_get_management_calendar_requires_group_header(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"user_{uuid4().hex[:8]}",
        email=f"user_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    _login(client, user)

    response = client.get("/api/v1/management/calendar")

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "management.group_required"


def test_get_management_calendar_returns_events_and_management_flags_for_admin(client, db_session) -> None:
    admin = _create_user(
        db_session,
        username=f"admin_{uuid4().hex[:8]}",
        email=f"admin_{uuid4().hex[:8]}@example.com",
        password="secret123",
        role_name=RoleName.ADMIN,
    )
    data = _create_management_calendar_fixture(db_session)
    _login(client, admin)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["managed_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2

    testing_item = payload["items"][0]
    race_item = payload["items"][1]

    assert testing_item["type"] == "TESTING"
    assert testing_item["public_id"] == str(data["testing_event"].public_id)
    assert "round_number" not in testing_item
    assert testing_item["name"] == "Pre-Season Testing"
    assert testing_item["country"] == {
        "name": data["country"].name,
        "flag_asset_url": data["country"].flag_asset_url,
    }
    assert testing_item["has_bet_context"] is True
    assert testing_item["has_official_results"] is False
    assert testing_item["results_published"] is False
    assert testing_item["sessions"] == [
        {
            "public_id": str(data["testing_session"].public_id),
            "name": "Day 1",
            "type": "TESTING",
            "has_official_results": True,
            "results_published": False,
        }
    ]

    assert race_item["type"] == "RACE"
    assert race_item["public_id"] == str(data["race_event"].public_id)
    assert race_item["season_year"] == data["season"].year
    assert race_item["round_number"] == 1
    assert race_item["name"] == "Bahrain Grand Prix"
    assert race_item["has_bet_context"] is True
    assert race_item["has_official_results"] is True
    assert race_item["results_published"] is True
    assert race_item["sessions"] == [
        {
            "public_id": str(data["race_session"].public_id),
            "name": "FP1",
            "type": "FP1",
            "has_official_results": False,
            "results_published": False,
        }
    ]


def test_get_management_calendar_marks_events_without_group_context(client, db_session) -> None:
    admin = _create_user(
        db_session,
        username=f"admin_{uuid4().hex[:8]}",
        email=f"admin_{uuid4().hex[:8]}@example.com",
        password="secret123",
        role_name=RoleName.ADMIN,
    )
    data = _create_management_calendar_fixture(db_session)
    _login(client, admin)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["empty_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert all(item["has_bet_context"] is False for item in payload["items"])
    assert all(item["has_official_results"] is False for item in payload["items"])
    assert all(item["results_published"] is False for item in payload["items"])
    assert all(
        session["has_official_results"] is False and session["results_published"] is False
        for item in payload["items"]
        for session in item["sessions"]
    )


def test_get_management_calendar_allows_group_owner(client, db_session) -> None:
    owner = _create_user(
        db_session,
        username=f"owner_{uuid4().hex[:8]}",
        email=f"owner_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    data = _create_management_calendar_fixture(db_session)
    _add_membership(
        db_session,
        user_id=owner.id,
        group_id=data["managed_group"].id,
        role=GroupRole.OWNER,
    )
    _login(client, owner)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["managed_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_management_calendar_allows_group_moderator(client, db_session) -> None:
    moderator = _create_user(
        db_session,
        username=f"moderator_{uuid4().hex[:8]}",
        email=f"moderator_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    data = _create_management_calendar_fixture(db_session)
    _add_membership(
        db_session,
        user_id=moderator.id,
        group_id=data["managed_group"].id,
        role=GroupRole.MODERATOR,
    )
    _login(client, moderator)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["managed_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_management_calendar_forbids_group_member(client, db_session) -> None:
    member = _create_user(
        db_session,
        username=f"member_{uuid4().hex[:8]}",
        email=f"member_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    data = _create_management_calendar_fixture(db_session)
    _add_membership(
        db_session,
        user_id=member.id,
        group_id=data["managed_group"].id,
        role=GroupRole.MEMBER,
    )
    _login(client, member)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["managed_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.forbidden_group"


def test_get_management_calendar_forbids_user_from_other_group(client, db_session) -> None:
    user = _create_user(
        db_session,
        username=f"outsider_{uuid4().hex[:8]}",
        email=f"outsider_{uuid4().hex[:8]}@example.com",
        password="secret123",
    )
    data = _create_management_calendar_fixture(db_session)
    other_group = _create_group(db_session, name=f"other_{uuid4().hex[:8]}")
    _add_membership(
        db_session,
        user_id=user.id,
        group_id=other_group.id,
        role=GroupRole.OWNER,
    )
    _login(client, user)

    response = client.get(
        "/api/v1/management/calendar",
        headers={"X-Group-Id": str(data["managed_group"].public_id)},
        params={"season_year": data["season"].year},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "management.forbidden_group"
