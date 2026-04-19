from datetime import UTC, datetime, timedelta

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.competition import (
    Circuit,
    Country,
    RaceEvent,
    Season,
    TestingEvent as CompetitionTestingEvent,
)
from app.db.enums import (
    RaceEventStatus,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)


def _create_user(
    db_session,
    *,
    username: str,
    email: str,
    password: str,
) -> None:
    hasher = PasslibPasswordHasher()
    user = User(
        username=username,
        email=email,
        password_hash=hasher.hash(password),
        auth_provider="LOCAL",
    )
    db_session.add(user)
    db_session.flush()


def test_get_home_requires_authentication(client) -> None:
    response = client.get("/api/v1/home")

    assert response.status_code == 401


def test_get_home_returns_next_event_of_active_season(client, db_session) -> None:
    now = datetime.now(UTC)
    _create_user(
        db_session,
        username="home_reader",
        email="home_reader@example.com",
        password="secret123",
    )

    active_season = Season(year=2026, is_active=True)
    inactive_season = Season(year=2025, is_active=False)
    country = Country(iso2="AU", name="Australia", flag_asset_url=None)
    db_session.add_all([active_season, inactive_season, country])
    db_session.flush()

    circuit = Circuit(
        code="albert-park",
        name="Albert Park",
        country_id=country.id,
        map_asset_url=None,
        image_asset_url=None,
    )
    db_session.add(circuit)
    db_session.flush()

    db_session.add_all(
        [
            RaceEvent(
                season_id=active_season.id,
                circuit_id=circuit.id,
                round_number=1,
                name="Past Grand Prix",
                scheduled_event_start=now - timedelta(days=10),
                scheduled_event_end=now - timedelta(days=8),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.COMPLETED,
            ),
            CompetitionTestingEvent(
                season_id=active_season.id,
                circuit_id=circuit.id,
                name="Earlier Testing",
                scheduled_event_start=now + timedelta(days=2),
                scheduled_event_end=now + timedelta(days=4),
                source_provider=SourceProvider.MANUAL,
                status=CompetitionTestingEventStatus.SCHEDULED,
            ),
            RaceEvent(
                season_id=active_season.id,
                circuit_id=circuit.id,
                round_number=2,
                name="Cancelled Grand Prix",
                scheduled_event_start=now + timedelta(days=1),
                scheduled_event_end=now + timedelta(days=3),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.CANCELLED,
            ),
            RaceEvent(
                season_id=active_season.id,
                circuit_id=circuit.id,
                round_number=3,
                name="Next Grand Prix",
                scheduled_event_start=now + timedelta(days=5),
                scheduled_event_end=now + timedelta(days=7),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.SCHEDULED,
            ),
            RaceEvent(
                season_id=active_season.id,
                circuit_id=circuit.id,
                round_number=4,
                name="Later Grand Prix",
                scheduled_event_start=now + timedelta(days=12),
                scheduled_event_end=now + timedelta(days=14),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.SCHEDULED,
            ),
            RaceEvent(
                season_id=inactive_season.id,
                circuit_id=circuit.id,
                round_number=1,
                name="Inactive Season Grand Prix",
                scheduled_event_start=now + timedelta(days=2),
                scheduled_event_end=now + timedelta(days=4),
                source_provider=SourceProvider.MANUAL,
                status=RaceEventStatus.SCHEDULED,
            ),
        ]
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "home_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/home")

    assert response.status_code == 200
    payload = response.json()

    assert payload["next_event"] is not None
    assert payload["next_event"]["event_kind"] == "TESTING"
    assert payload["next_event"]["season_year"] == 2026
    assert payload["next_event"]["round_number"] is None
    assert payload["next_event"]["name"] == "Earlier Testing"
    assert payload["next_event"]["circuit_code"] == "albert-park"
    assert payload["next_event"]["circuit_name"] == "Albert Park"
    assert payload["next_event"]["country_name"] == "Australia"
    assert payload["next_event"]["status"] == "SCHEDULED"


def test_get_home_returns_null_when_no_upcoming_event_exists(client, db_session) -> None:
    _create_user(
        db_session,
        username="home_empty_reader",
        email="home_empty_reader@example.com",
        password="secret123",
    )
    active_season = Season(year=2026, is_active=True)
    country = Country(iso2="ES", name="Spain", flag_asset_url=None)
    db_session.add_all([active_season, country])
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

    db_session.add(
        RaceEvent(
            season_id=active_season.id,
            circuit_id=circuit.id,
            round_number=1,
            name="Completed Grand Prix",
            source_provider=SourceProvider.MANUAL,
            status=RaceEventStatus.COMPLETED,
        )
    )
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "home_empty_reader", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/home")

    assert response.status_code == 200
    assert response.json() == {"next_event": None}


import json
import pytest

@pytest.mark.manual
def test_preview_home_payload_prints_result(client, db_session) -> None:
    now = datetime.now(UTC)

    _create_user(
        db_session,
        username="home_manual",
        email="home_manual@example.com",
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
        scheduled_event_start=now + timedelta(days=2),
        scheduled_event_end=now + timedelta(days=4),
        source_provider=SourceProvider.MANUAL,
        status=CompetitionTestingEventStatus.SCHEDULED,
    )

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

    db_session.add_all([testing_event, race_event])
    db_session.flush()

    login_response = client.post(
        "/api/v1/auth/login/local",
        json={"username": "home_manual", "password": "secret123"},
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/home")
    assert response.status_code == 200

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))