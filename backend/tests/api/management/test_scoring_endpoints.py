from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.adapters.security import PasslibPasswordHasher
from app.db.auth import Role, User
from app.db.betting import Bet, BetContext, BetPick, BetScore, BetTemplate, BetTemplateItem
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
    BetTemplateScope,
    BetValueType,
    PowerUpTargetType,
    RaceEventStatus,
    RoleName,
    ScoreComponentType,
    ScoringRuleScope,
    SessionType,
    SourceProvider,
    TestingEventStatus as CompetitionTestingEventStatus,
)
from app.db.powerups import PowerUp, PowerUpAssignment, PowerUpRestriction, PowerUpUse, PowerUpUseTarget
from app.db.scoring import OfficialResult, Score, ScoreComponent, ScoreSession, ScoreSessionComponent
from app.db.scoring import ScoringRule
from app.db.scoring.official_result import SourceType
from app.db.social import Group, GroupMembership
from app.db.social.group_membership import GroupRole


def _create_admin_user(db_session, *, username: str, password: str) -> User:
    hasher = PasslibPasswordHasher()
    role = db_session.execute(select(Role).where(Role.name == RoleName.ADMIN)).scalar_one_or_none()
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


def _create_local_user(db_session, *, username: str, password: str) -> User:
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


def _add_bet_pick(
    db_session,
    *,
    bet_id: int,
    bet_score_id: int,
    value: str,
) -> BetPick:
    pick = BetPick(bet_id=bet_id, bet_score_id=bet_score_id, value=value)
    db_session.add(pick)
    db_session.flush()
    return pick


def _add_scoring_rule(
    db_session,
    *,
    season_id: int,
    code: str,
    evaluator_key: str,
    component_type: ScoreComponentType = ScoreComponentType.BASE,
    scope: ScoringRuleScope = ScoringRuleScope.BET_SCORE,
    bet_score_id: int | None = None,
    bet_context_id: int | None = None,
    event_session_id: int | None = None,
    priority: int = 10,
    params_json: dict | None = None,
) -> ScoringRule:
    rule = ScoringRule(
        season_id=season_id,
        scope=scope,
        component_type=component_type,
        code=code,
        evaluator_key=evaluator_key,
        priority=priority,
        is_enabled=True,
        params_json=params_json,
        bet_score_id=bet_score_id,
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
    )
    db_session.add(rule)
    db_session.flush()
    return rule


def _add_season_template(
    db_session,
    *,
    season_id: int,
    bet_score_id: int,
    override_points: Decimal | None = None,
    override_constraints_json: dict | None = None,
) -> BetTemplate:
    template = BetTemplate(
        season_id=season_id,
        name=f"Season template {uuid4().hex[:8]}",
        context_kind=BetContextKind.SEASON,
        scope=BetTemplateScope.EVENT,
        session_type=None,
    )
    db_session.add(template)
    db_session.flush()

    db_session.add(
        BetTemplateItem(
            template_id=template.id,
            bet_score_id=bet_score_id,
            required=True,
            display_order=0,
            override_points=override_points,
            override_constraints_json=override_constraints_json,
        )
    )
    db_session.flush()
    return template


def _add_powerup(db_session, *, code: str, name: str | None = None) -> PowerUp:
    powerup = PowerUp(
        code=code,
        name=name or code.replace("_", " ").title(),
        is_enabled=True,
    )
    db_session.add(powerup)
    db_session.flush()
    return powerup


def _add_powerup_assignment(
    db_session,
    *,
    group_id: int,
    user_id: int,
    bet_context_id: int,
    powerup_id: int,
    quantity: int = 1,
) -> PowerUpAssignment:
    assignment = PowerUpAssignment(
        group_id=group_id,
        user_id=user_id,
        season_id=None,
        bet_context_id=bet_context_id,
        powerup_id=powerup_id,
        quantity=quantity,
        is_active=True,
    )
    db_session.add(assignment)
    db_session.flush()
    return assignment


def _add_powerup_use(
    db_session,
    *,
    user_id: int,
    group_id: int,
    bet_context_id: int,
    powerup_id: int,
    event_session_id: int | None = None,
    testing_event_session_id: int | None = None,
    target_user_id: int | None = None,
    rule_json: dict | None = None,
    used_at: datetime | None = None,
) -> PowerUpUse:
    powerup_use = PowerUpUse(
        user_id=user_id,
        group_id=group_id,
        bet_context_id=bet_context_id,
        event_session_id=event_session_id,
        testing_event_session_id=testing_event_session_id,
        powerup_id=powerup_id,
        rule_json=rule_json,
    )
    if used_at is not None:
        powerup_use.used_at = used_at
    db_session.add(powerup_use)
    db_session.flush()

    if target_user_id is not None:
        db_session.add(
            PowerUpUseTarget(
                powerup_use_id=powerup_use.id,
                target_type=PowerUpTargetType.USER,
                target_user_id=target_user_id,
                target_team_id=None,
                target_group_id=None,
                rule_json=None,
            )
        )
        db_session.flush()

    return powerup_use


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
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_race",
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
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_testing",
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
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_season",
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


def test_calculate_season_scoring_uses_template_item_override_points(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_override_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_override_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_season_template(
        db_session,
        season_id=data["season"].id,
        bet_score_id=data["score"].id,
        override_points=Decimal("7"),
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
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("7.00000000")
    assert score.total_points == Decimal("7.00000000")

    component = db_session.execute(
        select(ScoreComponent).where(ScoreComponent.score_id == score.id)
    ).scalar_one()
    assert component.points == Decimal("7.00000000")


def test_calculate_scoring_replaces_existing_scores(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username="admin_calc_replace",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_calc_replace",
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
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username="player_owner_calc_scoring",
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


def test_calculate_scoring_uses_position_near_evaluator_rule(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_near_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_near_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    data["score"].value_type = BetValueType.POSITION
    data["score"].base_points = 3
    _add_scoring_rule(
        db_session,
        season_id=data["season"].id,
        code=f"near_{uuid4().hex[:8]}",
        evaluator_key="position_exact_or_near",
        bet_score_id=data["score"].id,
        params_json={"points": 3, "near_points": 1, "near_delta": 1},
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
        value="1",
    )
    _add_submitted_bet(
        db_session,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
        value="2",
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.total_points == Decimal("1.00000000")

    component = db_session.execute(
        select(ScoreComponent).where(ScoreComponent.score_id == score.id)
    ).scalar_one()
    assert component.details_json["evaluator_key"] == "position_exact_or_near"
    assert component.details_json["near_hit"] is True


def test_calculate_scoring_applies_double_points_powerup(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_double_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_double_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
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
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("15.00000000")
    assert score.total_points == Decimal("30.00000000")

    powerup_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).scalar_one()
    assert powerup_component.points == Decimal("15.00000000")
    assert powerup_component.details_json["powerup_code"] == "DOUBLE_POINTS"


def test_calculate_race_scoring_applies_context_powerup_to_session_base_points(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_gp_context_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_gp_context_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
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
    assert payload["score_components_count"] == 1
    assert payload["score_session_components_count"] == 1

    score_session = db_session.execute(
        select(ScoreSession).where(
            ScoreSession.user_id == player.id,
            ScoreSession.bet_context_id == data["bet_context"].id,
            ScoreSession.event_session_id == data["session"].id,
        )
    ).scalar_one()
    assert score_session.base_points == Decimal("5.0000")
    assert score_session.total_points == Decimal("5.00000000")

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("0E-8")
    assert score.total_points == Decimal("5.00000000")

    powerup_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).scalar_one()
    assert powerup_component.points == Decimal("5.00000000")
    assert powerup_component.details_json["powerup_code"] == "DOUBLE_POINTS"
    assert Decimal(powerup_component.details_json["base_points"]) == Decimal("5")


def test_calculate_race_scoring_context_powerup_can_apply_only_to_gp_questions(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_gp_only_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_gp_only_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
        rule_json={"apply_to": {"context": True, "session_types": []}},
    )
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

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("10.00000000")
    assert score.total_points == Decimal("20.00000000")

    powerup_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).scalar_one()
    assert powerup_component.points == Decimal("10.00000000")
    assert Decimal(powerup_component.details_json["base_points"]) == Decimal("10")


def test_calculate_race_scoring_context_powerup_can_apply_only_to_selected_sessions(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_gp_session_only_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_gp_session_only_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
        rule_json={"apply_to": {"context": False, "session_types": ["FP1"]}},
    )
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

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("10.00000000")
    assert score.total_points == Decimal("15.00000000")

    powerup_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).scalar_one()
    assert powerup_component.points == Decimal("5.00000000")
    assert Decimal(powerup_component.details_json["base_points"]) == Decimal("5")


def test_calculate_race_scoring_context_penalty_can_apply_to_session_base_points(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_gp_context_penalty_{uuid4().hex[:8]}",
        password="secret123",
    )
    actor = _create_local_user(
        db_session,
        username=f"actor_gp_context_penalty_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_gp_context_penalty_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_race_fixture(db_session)
    powerup = _add_powerup(db_session, code="HALVE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=actor.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
        target_user_id=player.id,
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
        event_session_id=data["session"].id,
        bet_score_id=data["session_score"].id,
    )
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/race-events/{data['race_event'].public_id}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200

    score_session = db_session.execute(
        select(ScoreSession).where(
            ScoreSession.user_id == player.id,
            ScoreSession.bet_context_id == data["bet_context"].id,
            ScoreSession.event_session_id == data["session"].id,
        )
    ).scalar_one()
    assert score_session.total_points == Decimal("2.50000000")

    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("0E-8")
    assert score.total_points == Decimal("0E-8")

    penalty_component = db_session.execute(
        select(ScoreSessionComponent).where(
            ScoreSessionComponent.score_session_id == score_session.id,
            ScoreSessionComponent.component_type == ScoreComponentType.PENALTY,
        )
    ).scalar_one()
    assert penalty_component.points == Decimal("2.50000000")


def test_calculate_scoring_applies_powerup_submitted_with_season_bet(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_submit_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_submit_powerup_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    _add_group_membership(
        db_session,
        group_id=data["group"].id,
        user_id=player.id,
        role=GroupRole.MEMBER,
    )
    _add_season_template(
        db_session,
        season_id=data["season"].id,
        bet_score_id=data["score"].id,
    )
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    assignment = _add_powerup_assignment(
        db_session,
        group_id=data["group"].id,
        user_id=player.id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
    )
    _add_official_result(
        db_session,
        bet_context_id=data["bet_context"].id,
        bet_score_id=data["score"].id,
        value="VER",
    )

    _login(client, player.username)
    submit_response = client.post(
        f"/api/v1/bets/seasons/{data['season'].year}/answers",
        headers={"X-Group-Id": str(data["group"].public_id)},
        json={
            "answers": [
                {
                    "bet_score_code": data["score"].code,
                    "value": "VER",
                }
            ],
            "powerups": [
                {
                    "powerup_code": powerup.code,
                    "targets": [],
                }
            ],
        },
    )
    assert submit_response.status_code == 200
    db_session.refresh(assignment)
    assert assignment.quantity == 0

    _login(client, admin.username)
    calculate_response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert calculate_response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("15.00000000")
    assert score.total_points == Decimal("30.00000000")

    powerup_use = db_session.execute(
        select(PowerUpUse).where(
            PowerUpUse.group_id == data["group"].id,
            PowerUpUse.user_id == player.id,
            PowerUpUse.bet_context_id == data["bet_context"].id,
            PowerUpUse.powerup_id == powerup.id,
        )
    ).scalar_one()
    assert powerup_use.event_session_id is None
    assert powerup_use.testing_event_session_id is None

    powerup_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).scalar_one()
    assert powerup_component.points == Decimal("15.00000000")
    assert powerup_component.details_json["powerup_code"] == "DOUBLE_POINTS"


def test_calculate_scoring_applies_halve_points_penalty_powerup(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_half_{uuid4().hex[:8]}",
        password="secret123",
    )
    actor = _create_local_user(
        db_session,
        username=f"actor_half_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_half_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    powerup = _add_powerup(db_session, code="HALVE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=actor.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
        target_user_id=player.id,
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
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("15.00000000")
    assert score.total_points == Decimal("7.50000000")

    penalty_component = db_session.execute(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.PENALTY,
        )
    ).scalar_one()
    assert penalty_component.points == Decimal("7.50000000")
    assert penalty_component.details_json["powerup_code"] == "HALVE_POINTS"
    assert penalty_component.details_json["target_user_id"] == player.id


def test_calculate_scoring_applies_context_powerups_sequentially(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_powerup_order_{uuid4().hex[:8]}",
        password="secret123",
    )
    actor = _create_local_user(
        db_session,
        username=f"actor_powerup_order_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_powerup_order_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    double_powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    halve_powerup = _add_powerup(db_session, code="HALVE_POINTS")
    used_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=double_powerup.id,
        used_at=used_at,
    )
    _add_powerup_use(
        db_session,
        user_id=actor.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=halve_powerup.id,
        target_user_id=player.id,
        used_at=used_at + timedelta(seconds=1),
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
    _login(client, admin.username)

    response = client.post(
        f"/api/v1/management/scoring/seasons/{data['season'].year}/calculate",
        headers={"X-Group-Id": str(data["group"].public_id)},
    )

    assert response.status_code == 200
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.base_points == Decimal("15.00000000")
    assert score.total_points == Decimal("15.00000000")

    components = db_session.scalars(
        select(ScoreComponent)
        .where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type.in_(
                [ScoreComponentType.POWERUP, ScoreComponentType.PENALTY]
            ),
        )
        .order_by(ScoreComponent.id.asc())
    ).all()
    assert [component.component_type for component in components] == [
        ScoreComponentType.POWERUP,
        ScoreComponentType.PENALTY,
    ]
    assert components[0].points == Decimal("15.00000000")
    assert components[1].points == Decimal("15.00000000")


def test_calculate_scoring_skips_disabled_powerup_by_restriction(client, db_session) -> None:
    admin = _create_admin_user(
        db_session,
        username=f"admin_restricted_{uuid4().hex[:8]}",
        password="secret123",
    )
    player = _create_local_user(
        db_session,
        username=f"player_restricted_{uuid4().hex[:8]}",
        password="secret123",
    )
    data = _create_season_fixture(db_session)
    powerup = _add_powerup(db_session, code="DOUBLE_POINTS")
    _add_powerup_use(
        db_session,
        user_id=player.id,
        group_id=data["group"].id,
        bet_context_id=data["bet_context"].id,
        powerup_id=powerup.id,
    )
    db_session.add(
        PowerUpRestriction(
            powerup_id=powerup.id,
            bet_context_id=data["bet_context"].id,
            event_session_id=None,
            testing_event_session_id=None,
            is_disabled=True,
            note="Disabled for this context",
        )
    )
    db_session.flush()
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
    score = db_session.execute(
        select(Score).where(
            Score.user_id == player.id,
            Score.bet_context_id == data["bet_context"].id,
        )
    ).scalar_one()
    assert score.total_points == Decimal("15.00000000")

    powerup_components = db_session.scalars(
        select(ScoreComponent).where(
            ScoreComponent.score_id == score.id,
            ScoreComponent.component_type == ScoreComponentType.POWERUP,
        )
    ).all()
    assert powerup_components == []
