from app.db.base import Base

# Auth
from app.db.auth.user import User  # noqa: F401
from app.db.auth.role import Role  # noqa: F401
from app.db.auth.permission import Permission  # noqa: F401
from app.db.auth.user_role import UserRole  # noqa: F401
from app.db.auth.role_permission import RolePermission  # noqa: F401
from app.db.auth.password_reset_token import PasswordResetToken  # noqa: F401


# Competition
from app.db.competition.season import Season  # noqa: F401
from app.db.competition.country import Country  # noqa: F401
from app.db.competition.circuit import Circuit  # noqa: F401
from app.db.competition.driver import Driver  # noqa: F401
from app.db.competition.team import TeamF1  # noqa: F401
from app.db.competition.engine import Engine  # noqa: F401
from app.db.competition.season_driver import SeasonDriver  # noqa: F401
from app.db.competition.season_team import SeasonTeam  # noqa: F401
from app.db.competition.season_engine import SeasonEngine  # noqa: F401
from app.db.competition.race_event import RaceEvent  # noqa: F401
from app.db.competition.testing_event import TestingEvent  # noqa: F401
from app.db.competition.testing_event_session import TestingEventSession  # noqa: F401
from app.db.competition.event_session import EventSession  # noqa: F401
from app.db.competition.driver_entry import DriverEntry  # noqa: F401

# Betting
from app.db.betting.bet import Bet  # noqa: F401
from app.db.betting.bet_context import BetContext  # noqa: F401
from app.db.betting.bet_exception import BetException  # noqa: F401
from app.db.betting.bet_pick import BetPick  # noqa: F401
from app.db.betting.bet_score import BetScore  # noqa: F401
from app.db.betting.bet_template import BetTemplate  # noqa: F401
from app.db.betting.bet_template_item import BetTemplateItem  # noqa: F401

# Scoring
from app.db.scoring.official_result import OfficialResult  # noqa: F401
from app.db.scoring.result_publication import ResultPublication  # noqa: F401
from app.db.scoring.score import Score  # noqa: F401
from app.db.scoring.score_component import ScoreComponent  # noqa: F401
from app.db.scoring.scoring_rule import ScoringRule  # noqa: F401
from app.db.scoring.score_session import ScoreSession  # noqa: F401
from app.db.scoring.score_session_component import ScoreSessionComponent  # noqa: F401
from app.db.scoring.score_season_aggregate import ScoreSeasonAggregate  # noqa: F401
from app.db.scoring.team_event_aggregate import TeamEventAggregate  # noqa: F401
from app.db.scoring.team_season_aggregate import TeamSeasonAggregate  # noqa: F401

# Social
from app.db.social.group import Group  # noqa: F401
from app.db.social.group_membership import GroupMembership  # noqa: F401
from app.db.social.team import Team as SocialTeam  # noqa: F401
from app.db.social.team_membership import TeamMembership  # noqa: F401

# Powerups
from app.db.powerups.power_up import PowerUp  # noqa: F401
from app.db.powerups.power_up_assignment import PowerUpAssignment  # noqa: F401
from app.db.powerups.power_up_restriction import PowerUpRestriction  # noqa: F401
from app.db.powerups.power_up_use import PowerUpUse  # noqa: F401
from app.db.powerups.power_up_use_target import PowerUpUseTarget  # noqa: F401

# Audit
from app.db.audit.audit_log import AuditLog  # noqa: F401
