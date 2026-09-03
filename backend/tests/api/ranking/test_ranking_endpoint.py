from datetime import datetime, timezone
from uuid import uuid4

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import User
from app.db.betting import BetContext
from app.db.competition import Circuit, Country, EventSession, RaceEvent, Season
from app.db.enums import (
    BetContextKind,
    RaceEventStatus,
    RankingEventType,
    ScoreComponentType,
    SessionType,
    SourceProvider,
)
from app.db.scoring import (
    ResultPublication,
    Score,
    ScoreComponent,
    ScoreSeasonAggregate,
    ScoreSession,
    ScoreSessionComponent,
)
from app.db.social import Group, GroupMembership, GroupSeasonMembership, Team, TeamMembership, TeamSeasonMembership
from app.db.social.group_membership import GroupRole
from app.db.social.group_season_membership import GroupSeasonRole
from app.db.social.team_membership import TeamRole


def _create_user(
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
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_group(
    db_session,
    *,
    name: str,
    teams_enabled: bool = False,
) -> Group:
    group = Group(
        name=name,
        join_code=None,
        is_private=False,
        teams_enabled=teams_enabled,
        max_team_size=None,
    )
    db_session.add(group)
    db_session.flush()
    return group


def _add_group_member(db_session, *, group_id: int, user_id: int) -> None:
    db_session.add(
        GroupMembership(
            group_id=group_id,
            user_id=user_id,
            role=GroupRole.MEMBER,
        )
    )
    db_session.flush()


def _add_group_season_member(
    db_session,
    *,
    group_id: int,
    season_id: int,
    user_id: int,
    role: GroupSeasonRole = GroupSeasonRole.MEMBER,
    is_active: bool = True,
) -> None:
    db_session.add(
        GroupSeasonMembership(
            group_id=group_id,
            season_id=season_id,
            user_id=user_id,
            role=role,
            is_active=is_active,
        )
    )
    db_session.flush()


def _create_published_race_context(
    db_session,
    *,
    season: Season,
    group: Group,
    published_by_user_id: int,
    round_number: int = 1,
) -> tuple[RaceEvent, BetContext]:
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

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=round_number,
        name="Bahrain Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.COMPLETED,
        scheduled_event_start=datetime(2040, 3, 1, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2040, 3, 3, 18, 0, tzinfo=timezone.utc),
    )
    db_session.add(race_event)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Bahrain GP",
        results_published=True,
        results_published_at=datetime(2040, 3, 3, 20, 0, tzinfo=timezone.utc),
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    db_session.add(
        ResultPublication(
            bet_context_id=bet_context.id,
            event_session_id=None,
            testing_event_session_id=None,
            published_by_user_id=published_by_user_id,
            published_at=datetime(2040, 3, 3, 20, 0, tzinfo=timezone.utc),
        )
    )
    db_session.flush()

    return race_event, bet_context


def _login(client, *, username: str, password: str = "secret123") -> None:
    response = client.post(
        "/api/v1/auth/login/local",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200


def test_get_ranking_requires_authentication(client, db_session) -> None:
    group = _create_group(
        db_session,
        name=f"group_{uuid4().hex[:8]}",
    )

    response = client.get(
        "/api/v1/ranking",
        headers={"X-Group-Id": str(group.public_id)},
        params={"season_year": 2040},
    )

    assert response.status_code == 401


def test_get_ranking_returns_user_rows_and_timeline_for_user_group(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_{uuid4().hex[:8]}",
        password="secret123",
    )
    other_user = _create_user(
        db_session,
        username=f"other_{uuid4().hex[:8]}",
        password="secret123",
    )
    zero_user = _create_user(
        db_session,
        username=f"zero_{uuid4().hex[:8]}",
        password="secret123",
    )
    group = _create_group(
        db_session,
        name=f"group_{uuid4().hex[:8]}",
    )
    for user in [viewer, other_user, zero_user]:
        _add_group_member(db_session, group_id=group.id, user_id=user.id)

    season = Season(year=2040, is_active=True)
    db_session.add(season)
    db_session.flush()
    for user in [viewer, other_user, zero_user]:
        _add_group_season_member(
            db_session,
            group_id=group.id,
            season_id=season.id,
            user_id=user.id,
        )

    first_race_event, first_bet_context = _create_published_race_context(
        db_session,
        season=season,
        group=group,
        published_by_user_id=viewer.id,
        round_number=1,
    )
    _, second_bet_context = _create_published_race_context(
        db_session,
        season=season,
        group=group,
        published_by_user_id=viewer.id,
        round_number=2,
    )

    unpublished_race_event = RaceEvent(
        season_id=season.id,
        circuit_id=first_race_event.circuit_id,
        round_number=3,
        name="Unpublished Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.COMPLETED,
        scheduled_event_start=datetime(2040, 3, 10, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2040, 3, 10, 18, 0, tzinfo=timezone.utc),
    )
    db_session.add(unpublished_race_event)
    db_session.flush()

    unpublished_bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=unpublished_race_event.id,
        testing_event_id=None,
        label="Unpublished GP",
        results_published=False,
        results_published_at=None,
        group_id=group.id,
    )
    db_session.add(unpublished_bet_context)
    db_session.flush()

    db_session.add_all(
        [
            Score(
                user_id=viewer.id,
                bet_context_id=first_bet_context.id,
                base_points=5,
                total_points=5,
                computed_at=datetime(2040, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=other_user.id,
                bet_context_id=first_bet_context.id,
                base_points=8,
                total_points=8,
                computed_at=datetime(2040, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=viewer.id,
                bet_context_id=second_bet_context.id,
                base_points=12,
                total_points=12,
                computed_at=datetime(2040, 3, 4, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=other_user.id,
                bet_context_id=second_bet_context.id,
                base_points=0,
                total_points=0,
                computed_at=datetime(2040, 3, 4, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=other_user.id,
                bet_context_id=unpublished_bet_context.id,
                base_points=100,
                total_points=100,
                computed_at=datetime(2040, 3, 5, 20, 5, tzinfo=timezone.utc),
            ),
            ScoreSeasonAggregate(
                user_id=viewer.id,
                group_id=group.id,
                season_id=season.id,
                total_points=999,
                race_points=999,
                testing_points=0,
                season_points=0,
                extra_points=0,
                penalty_points=0,
                position=1,
                previous_position=99,
                last_event_type=RankingEventType.RACE_EVENT,
                last_event_label="Wrong Aggregate Event",
                last_event_order=99,
                last_scored_at=datetime(2040, 3, 5, 20, 5, tzinfo=timezone.utc),
            ),
            ScoreSeasonAggregate(
                user_id=other_user.id,
                group_id=group.id,
                season_id=season.id,
                total_points=1,
                race_points=1,
                testing_points=0,
                season_points=0,
                extra_points=0,
                penalty_points=0,
                position=2,
                previous_position=98,
                last_event_type=RankingEventType.RACE_EVENT,
                last_event_label="Wrong Aggregate Event",
                last_event_order=99,
                last_scored_at=datetime(2040, 3, 5, 20, 5, tzinfo=timezone.utc),
            ),
        ]
    )
    db_session.flush()

    _login(client, username=viewer.username)

    response = client.get(
        "/api/v1/ranking",
        headers={"X-Group-Id": str(group.public_id)},
        params={"season_year": season.year},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["season_year"] == 2040
    assert payload["ranking_mode"] == "USER"
    assert payload["teams"] == []

    assert [row["user"]["username"] for row in payload["users"]] == [
        viewer.username,
        other_user.username,
        zero_user.username,
    ]
    assert [row["position"] for row in payload["users"]] == [1, 2, 3]
    assert payload["users"][0]["previous_position"] == 2
    assert payload["users"][1]["previous_position"] == 1
    assert payload["users"][0]["points"] == {
        "race": 17.0,
        "testing": 0.0,
        "season": 0.0,
        "powerup": 0.0,
        "total": 17.0,
    }
    assert payload["users"][1]["points"]["total"] == 8.0
    assert payload["users"][2]["points"]["total"] == 0.0

    timelines_by_username = {
        item["user"]["username"]: item["points"]
        for item in payload["timeline"]["users"]
    }
    assert timelines_by_username[viewer.username] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 5.0,
        },
        {
            "event_order": 2,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 17.0,
        },
    ]
    assert timelines_by_username[other_user.username] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 8.0,
        },
        {
            "event_order": 2,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 8.0,
        },
    ]
    assert timelines_by_username[zero_user.username] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 0.0,
        },
        {
            "event_order": 2,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 0.0,
        },
    ]
    assert payload["timeline"]["teams"] == []


def test_get_ranking_includes_published_race_session_scores(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_session_{uuid4().hex[:8]}",
        password="secret123",
    )
    group = _create_group(
        db_session,
        name=f"group_{uuid4().hex[:8]}",
    )
    _add_group_member(db_session, group_id=group.id, user_id=viewer.id)

    season = Season(year=2042, is_active=True)
    db_session.add(season)
    db_session.flush()
    _add_group_season_member(
        db_session,
        group_id=group.id,
        season_id=season.id,
        user_id=viewer.id,
    )

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

    race_event = RaceEvent(
        season_id=season.id,
        circuit_id=circuit.id,
        round_number=1,
        name="Session Grand Prix",
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.COMPLETED,
        scheduled_event_start=datetime(2042, 3, 1, 8, 0, tzinfo=timezone.utc),
        scheduled_event_end=datetime(2042, 3, 3, 18, 0, tzinfo=timezone.utc),
    )
    db_session.add(race_event)
    db_session.flush()

    event_session = EventSession(
        race_event_id=race_event.id,
        session_type=SessionType.RACE,
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.COMPLETED,
        start_datetime=datetime(2042, 3, 3, 15, 0, tzinfo=timezone.utc),
        scheduled_start_datetime=datetime(2042, 3, 3, 15, 0, tzinfo=timezone.utc),
        lock_cutoff=datetime(2042, 3, 3, 15, 0, tzinfo=timezone.utc),
        scheduled_lock_cutoff=datetime(2042, 3, 3, 15, 0, tzinfo=timezone.utc),
    )
    db_session.add(event_session)
    db_session.flush()

    bet_context = BetContext(
        kind=BetContextKind.GP,
        season_id=season.id,
        race_event_id=race_event.id,
        testing_event_id=None,
        label="Session GP",
        results_published=True,
        results_published_at=datetime(2042, 3, 3, 20, 0, tzinfo=timezone.utc),
        group_id=group.id,
    )
    db_session.add(bet_context)
    db_session.flush()

    db_session.add_all(
        [
            ResultPublication(
                bet_context_id=bet_context.id,
                event_session_id=event_session.id,
                testing_event_session_id=None,
                published_by_user_id=viewer.id,
                published_at=datetime(2042, 3, 3, 20, 0, tzinfo=timezone.utc),
            ),
            ScoreSession(
                user_id=viewer.id,
                bet_context_id=bet_context.id,
                event_session_id=event_session.id,
                testing_event_session_id=None,
                base_points=12,
                total_points=12,
                computed_at=datetime(2042, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
        ]
    )
    db_session.flush()

    _login(client, username=viewer.username)

    response = client.get(
        "/api/v1/ranking",
        headers={"X-Group-Id": str(group.public_id)},
        params={"season_year": season.year},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["users"][0]["points"] == {
        "race": 12.0,
        "testing": 0.0,
        "season": 0.0,
        "powerup": 0.0,
        "total": 12.0,
    }
    assert payload["timeline"]["users"][0]["points"] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Session GP",
            "published_at": "2042-03-03T20:00:00Z",
            "points": 12.0,
        }
    ]


def test_get_ranking_groups_extras_with_event_points_and_powerups_separately(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_components_{uuid4().hex[:8]}",
        password="secret123",
    )
    group = _create_group(
        db_session,
        name=f"group_{uuid4().hex[:8]}",
    )
    _add_group_member(db_session, group_id=group.id, user_id=viewer.id)

    season = Season(year=2043, is_active=True)
    db_session.add(season)
    db_session.flush()
    _add_group_season_member(
        db_session,
        group_id=group.id,
        season_id=season.id,
        user_id=viewer.id,
    )

    race_event, bet_context = _create_published_race_context(
        db_session,
        season=season,
        group=group,
        published_by_user_id=viewer.id,
        round_number=1,
    )
    event_session = EventSession(
        race_event_id=race_event.id,
        session_type=SessionType.RACE,
        source_provider=SourceProvider.MANUAL,
        status=RaceEventStatus.COMPLETED,
        start_datetime=datetime(2043, 3, 3, 15, 0, tzinfo=timezone.utc),
        scheduled_start_datetime=datetime(2043, 3, 3, 15, 0, tzinfo=timezone.utc),
        lock_cutoff=datetime(2043, 3, 3, 15, 0, tzinfo=timezone.utc),
        scheduled_lock_cutoff=datetime(2043, 3, 3, 15, 0, tzinfo=timezone.utc),
    )
    db_session.add(event_session)
    db_session.flush()

    score = Score(
        user_id=viewer.id,
        bet_context_id=bet_context.id,
        base_points=0,
        total_points=1,
        computed_at=datetime(2043, 3, 3, 20, 5, tzinfo=timezone.utc),
    )
    score_session = ScoreSession(
        user_id=viewer.id,
        bet_context_id=bet_context.id,
        event_session_id=event_session.id,
        testing_event_session_id=None,
        base_points=10,
        total_points=16,
        computed_at=datetime(2043, 3, 3, 20, 5, tzinfo=timezone.utc),
    )
    db_session.add_all([score, score_session])
    db_session.flush()

    db_session.add_all(
        [
            ScoreComponent(
                score_id=score.id,
                component_type=ScoreComponentType.EXTRA,
                code="GP_HITS_BONUS",
                points=1,
                details_json={},
            ),
            ScoreSessionComponent(
                score_session_id=score_session.id,
                component_type=ScoreComponentType.BASE,
                code="WINNER",
                points=10,
                details_json={},
            ),
            ScoreSessionComponent(
                score_session_id=score_session.id,
                component_type=ScoreComponentType.EXTRA,
                code="FIRST_SUBMIT",
                points=2,
                details_json={},
            ),
            ScoreSessionComponent(
                score_session_id=score_session.id,
                component_type=ScoreComponentType.POWERUP,
                code="DOUBLE_POINTS",
                points=5,
                details_json={},
            ),
            ScoreSessionComponent(
                score_session_id=score_session.id,
                component_type=ScoreComponentType.PENALTY,
                code="HALVE_POINTS",
                points=1,
                details_json={},
            ),
        ]
    )
    db_session.flush()

    _login(client, username=viewer.username)

    response = client.get(
        "/api/v1/ranking",
        headers={"X-Group-Id": str(group.public_id)},
        params={"season_year": season.year},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["users"][0]["points"] == {
        "race": 13.0,
        "testing": 0.0,
        "season": 0.0,
        "powerup": 4.0,
        "total": 17.0,
    }
    assert payload["timeline"]["users"][0]["points"] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 17.0,
        }
    ]


def test_get_ranking_returns_team_rows_when_group_uses_teams(client, db_session) -> None:
    viewer = _create_user(
        db_session,
        username=f"viewer_{uuid4().hex[:8]}",
        password="secret123",
    )
    teammate = _create_user(
        db_session,
        username=f"teammate_{uuid4().hex[:8]}",
        password="secret123",
    )
    rival = _create_user(
        db_session,
        username=f"rival_{uuid4().hex[:8]}",
        password="secret123",
    )
    guest_without_team = _create_user(
        db_session,
        username=f"guest_{uuid4().hex[:8]}",
        password="secret123",
    )
    group = _create_group(
        db_session,
        name=f"group_{uuid4().hex[:8]}",
        teams_enabled=True,
    )
    for user in [viewer, teammate, rival, guest_without_team]:
        _add_group_member(db_session, group_id=group.id, user_id=user.id)

    red_team = Team(group_id=group.id, name="Red Team")
    blue_team = Team(group_id=group.id, name="Blue Team")
    empty_team = Team(group_id=group.id, name="Empty Team")
    db_session.add_all([red_team, blue_team, empty_team])
    db_session.flush()

    db_session.add_all(
        [
            TeamMembership(
                group_id=group.id,
                team_id=red_team.id,
                user_id=viewer.id,
                role=TeamRole.CAPTAIN,
            ),
            TeamMembership(
                group_id=group.id,
                team_id=red_team.id,
                user_id=teammate.id,
                role=TeamRole.MEMBER,
            ),
            TeamMembership(
                group_id=group.id,
                team_id=blue_team.id,
                user_id=rival.id,
                role=TeamRole.CAPTAIN,
            ),
        ]
    )
    db_session.flush()

    season = Season(year=2041, is_active=True)
    db_session.add(season)
    db_session.flush()
    for user in [viewer, teammate, rival]:
        _add_group_season_member(
            db_session,
            group_id=group.id,
            season_id=season.id,
            user_id=user.id,
        )
    db_session.add_all(
        [
            TeamSeasonMembership(
                group_id=group.id,
                season_id=season.id,
                team_id=red_team.id,
                user_id=viewer.id,
                role=TeamRole.CAPTAIN,
            ),
            TeamSeasonMembership(
                group_id=group.id,
                season_id=season.id,
                team_id=red_team.id,
                user_id=teammate.id,
                role=TeamRole.MEMBER,
            ),
            TeamSeasonMembership(
                group_id=group.id,
                season_id=season.id,
                team_id=blue_team.id,
                user_id=rival.id,
                role=TeamRole.CAPTAIN,
            ),
        ]
    )
    db_session.flush()

    _, first_bet_context = _create_published_race_context(
        db_session,
        season=season,
        group=group,
        published_by_user_id=viewer.id,
        round_number=1,
    )
    _, second_bet_context = _create_published_race_context(
        db_session,
        season=season,
        group=group,
        published_by_user_id=viewer.id,
        round_number=2,
    )

    db_session.add_all(
        [
            Score(
                user_id=viewer.id,
                bet_context_id=first_bet_context.id,
                base_points=3,
                total_points=3,
                computed_at=datetime(2041, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=teammate.id,
                bet_context_id=first_bet_context.id,
                base_points=2,
                total_points=2,
                computed_at=datetime(2041, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=rival.id,
                bet_context_id=first_bet_context.id,
                base_points=7,
                total_points=7,
                computed_at=datetime(2041, 3, 3, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=viewer.id,
                bet_context_id=second_bet_context.id,
                base_points=10,
                total_points=10,
                computed_at=datetime(2041, 3, 4, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=teammate.id,
                bet_context_id=second_bet_context.id,
                base_points=5,
                total_points=5,
                computed_at=datetime(2041, 3, 4, 20, 5, tzinfo=timezone.utc),
            ),
            Score(
                user_id=rival.id,
                bet_context_id=second_bet_context.id,
                base_points=0,
                total_points=0,
                computed_at=datetime(2041, 3, 4, 20, 5, tzinfo=timezone.utc),
            ),
            ScoreSeasonAggregate(
                user_id=viewer.id,
                group_id=group.id,
                season_id=season.id,
                total_points=999,
                race_points=999,
                testing_points=0,
                season_points=0,
                extra_points=0,
                penalty_points=0,
            ),
            ScoreSeasonAggregate(
                user_id=teammate.id,
                group_id=group.id,
                season_id=season.id,
                total_points=999,
                race_points=999,
                testing_points=0,
                season_points=0,
                extra_points=0,
                penalty_points=0,
            ),
            ScoreSeasonAggregate(
                user_id=rival.id,
                group_id=group.id,
                season_id=season.id,
                total_points=1,
                race_points=1,
                testing_points=0,
                season_points=0,
                extra_points=0,
                penalty_points=0,
            ),
        ]
    )
    db_session.flush()

    _login(client, username=viewer.username)

    response = client.get(
        "/api/v1/ranking",
        headers={"X-Group-Id": str(group.public_id)},
        params={"season_year": season.year},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["ranking_mode"] == "TEAM"
    assert [row["team"]["name"] for row in payload["teams"]] == [
        "Red Team",
        "Blue Team",
    ]
    assert [row["points"]["total"] for row in payload["teams"]] == [20.0, 7.0]
    assert payload["teams"][0]["previous_position"] == 2
    assert payload["teams"][1]["previous_position"] == 1

    user_names = [row["user"]["username"] for row in payload["users"]]
    assert user_names == [viewer.username, rival.username, teammate.username]
    assert guest_without_team.username not in user_names

    red_users = [
        row["user"]
        for row in payload["users"]
        if row["user"]["team_name"] == "Red Team"
    ]
    assert {user["username"] for user in red_users} == {viewer.username, teammate.username}
    assert all(user["team_public_id"] == str(red_team.public_id) for user in red_users)

    team_timelines = {
        item["team"]["name"]: item["points"]
        for item in payload["timeline"]["teams"]
    }
    assert team_timelines["Red Team"] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 5.0,
        },
        {
            "event_order": 2,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 20.0,
        },
    ]
    assert team_timelines["Blue Team"] == [
        {
            "event_order": 1,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 7.0,
        },
        {
            "event_order": 2,
            "event_type": "RACE_EVENT",
            "label": "Bahrain GP",
            "published_at": "2040-03-03T20:00:00Z",
            "points": 7.0,
        },
    ]
