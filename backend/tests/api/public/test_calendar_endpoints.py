from datetime import UTC, datetime, timedelta

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
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
    RaceEventStatus,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)


def _create_user(
    db_session,
    *,
    username: str,
    password: str,
) -> None:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()


def test_get_calendar_requires_authentication(client) -> None:
    response = client.get("/api/v1/calendar")

    assert response.status_code == 401


def test_get_calendar_returns_single_ordered_list_with_testing_first(client, db_session) -> None:
    now = datetime.now(UTC)

    _create_user(
        db_session,
        username="calendar_reader",
        password="secret123",
    )

    active_season = Season(year=2026, is_active=True)
    inactive_season = Season(year=2025, is_active=False)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([active_season, inactive_season, country])
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
        season_id=active_season.id,
        circuit_id=circuit.id,
        name="Pre-Season Testing 1",
        scheduled_event_start=now + timedelta(days=1),
        scheduled_event_end=now + timedelta(days=3),
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=now + timedelta(days=2),
            scheduled_end_datetime=now + timedelta(days=2, hours=8),
        ),
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=now + timedelta(days=1),
            scheduled_end_datetime=now + timedelta(days=1, hours=8),
        ),
    ]

    race_event = RaceEvent(
        season_id=active_season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        scheduled_event_start=now + timedelta(days=10),
        scheduled_event_end=now + timedelta(days=12),
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=12, hours=5),
            scheduled_start_datetime=now + timedelta(days=12, hours=5),
            lock_cutoff=now + timedelta(days=12, hours=4, minutes=55),
            scheduled_lock_cutoff=now + timedelta(days=12, hours=4, minutes=55),
            status=RaceEventStatus.SCHEDULED,
        ),
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=10, hours=3),
            scheduled_start_datetime=now + timedelta(days=10, hours=3),
            lock_cutoff=now + timedelta(days=10, hours=2, minutes=55),
            scheduled_lock_cutoff=now + timedelta(days=10, hours=2, minutes=55),
            status=RaceEventStatus.SCHEDULED,
        ),
    ]

    inactive_race_event = RaceEvent(
        season_id=inactive_season.id,
        circuit_id=circuit.id,
        round_number=99,
        name="Old Grand Prix",
        scheduled_event_start=now + timedelta(days=20),
        scheduled_event_end=now + timedelta(days=22),
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
    )

    db_session.add_all([testing_event, race_event, inactive_race_event])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "calendar_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/calendar")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 2
    assert [item["kind"] for item in payload["items"]] == ["TESTING", "RACE"]

    testing_item = payload["items"][0]
    assert "season_year" not in testing_item
    assert "round_number" not in testing_item
    assert testing_item["name"] == "Pre-Season Testing 1"
    assert testing_item["is_up_next"] is True
    assert [session["session_order"] for session in testing_item["testing_sessions"]] == [1, 2]
    assert testing_item["race_sessions"] == []

    race_item = payload["items"][1]
    assert "season_year" not in race_item
    assert race_item["round_number"] == 1
    assert race_item["name"] == "Bahrain Grand Prix"
    assert race_item["is_up_next"] is False
    assert race_item["testing_sessions"] == []
    assert [session["session_type"] for session in race_item["race_sessions"]] == ["FP1", "RACE"]


def test_get_calendar_returns_requested_season_when_year_is_provided(client, db_session) -> None:
    now = datetime.now(UTC)

    _create_user(
        db_session,
        username="calendar_year_reader",
        password="secret123",
    )

    season_2026 = Season(year=2026, is_active=True)
    season_2027 = Season(year=2027, is_active=False)
    country = Country(iso2="BH", name="Bahrain", flag_asset_url=None)
    db_session.add_all([season_2026, season_2027, country])
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

    db_session.add_all(
        [
            CompetitionTestingEvent(
                season_id=season_2026.id,
                circuit_id=circuit.id,
                name="Testing 2026",
                scheduled_event_start=now + timedelta(days=1),
                scheduled_event_end=now + timedelta(days=3),
                source_provider=SourceProvider.MANUAL,
                status=CompetitionTestingEventStatus.SCHEDULED,
            ),
            CompetitionTestingEvent(
                season_id=season_2027.id,
                circuit_id=circuit.id,
                name="Testing 2027",
                scheduled_event_start=now + timedelta(days=30),
                scheduled_event_end=now + timedelta(days=32),
                source_provider=SourceProvider.MANUAL,
                status=CompetitionTestingEventStatus.SCHEDULED,
            ),
            RaceEvent(
                season_id=season_2027.id,
                circuit_id=circuit.id,
                round_number=1,
                name="Bahrain Grand Prix 2027",
                scheduled_event_start=now + timedelta(days=40),
                scheduled_event_end=now + timedelta(days=42),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.SCHEDULED,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "calendar_year_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/calendar?season_year=2027")

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["items"]) == 2
    assert all("season_year" not in item for item in payload["items"])
    assert [item["kind"] for item in payload["items"]] == ["TESTING", "RACE"]
    assert payload["items"][0]["name"] == "Testing 2027"
    assert payload["items"][1]["name"] == "Bahrain Grand Prix 2027"

import json
import pytest

@pytest.mark.manual
def test_preview_calendar_payload_prints_result(client, db_session) -> None:
    now = datetime.now(UTC)

    _create_user(
        db_session,
        username="calendar_manual",
        password="secret123",
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
        name="Pre-Season Testing 1",
        scheduled_event_start=now + timedelta(days=1),
        scheduled_event_end=now + timedelta(days=3),
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
    )
    testing_event.sessions = [
        CompetitionTestingEventSession(
            session_order=1,
            name="Day 1",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=now + timedelta(days=1),
            scheduled_end_datetime=now + timedelta(days=1, hours=8),
        ),
        CompetitionTestingEventSession(
            session_order=2,
            name="Day 2",
            source_provider=SourceProvider.MANUAL,
            scheduled_start_datetime=now + timedelta(days=2),
            scheduled_end_datetime=now + timedelta(days=2, hours=8),
        ),
    ]

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Bahrain Grand Prix",
        scheduled_event_start=now + timedelta(days=10),
        scheduled_event_end=now + timedelta(days=12),
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.SCHEDULED,
    )
    race_event.event_sessions = [
        EventSession(
            session_type=SessionType.FP1,
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=10, hours=3),
            scheduled_start_datetime=now + timedelta(days=10, hours=3),
            lock_cutoff=now + timedelta(days=10, hours=2, minutes=55),
            scheduled_lock_cutoff=now + timedelta(days=10, hours=2, minutes=55),
            status=RaceEventStatus.SCHEDULED,
        ),
        EventSession(
            session_type=SessionType.RACE,
            source_provider=SourceProvider.MANUAL,
            start_datetime=now + timedelta(days=12, hours=5),
            scheduled_start_datetime=now + timedelta(days=12, hours=5),
            lock_cutoff=now + timedelta(days=12, hours=4, minutes=55),
            scheduled_lock_cutoff=now + timedelta(days=12, hours=4, minutes=55),
            status=RaceEventStatus.SCHEDULED,
        ),
    ]

    db_session.add_all([testing_event, race_event])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "calendar_manual", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/calendar")
    assert response.status_code == 200

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
