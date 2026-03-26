import enum


class BetContextKind(str, enum.Enum):
    GP = "GP"
    PRETESTING = "PRETESTING"
    SEASON = "SEASON"


class RoleName(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"


class SessionType(str, enum.Enum):
    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"
    QUALY = "QUALY"
    SPRINT_QUALY = "SPRINT_QUALY"
    SPRINT = "SPRINT"
    RACE = "RACE"


class RaceEventStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"
    COMPLETED = "COMPLETED"


class SeasonDriverStatus(str, enum.Enum):
    PRIMARY = "PRIMARY"
    RESERVE = "RESERVE"
    INACTIVE = "INACTIVE"


class TestingEventStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    POSTPONED = "POSTPONED"
    COMPLETED = "COMPLETED"


class BetTemplateScope(str, enum.Enum):
    EVENT = "EVENT"
    SESSION = "SESSION"


class BetValueType(str, enum.Enum):
    DRIVER = "DRIVER"
    TEAM = "TEAM"
    ENGINE = "ENGINE"
    CIRCUIT = "CIRCUIT"
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    POSITION = "POSITION"


class ScoreComponentType(str, enum.Enum):
    BASE = "BASE"
    EXTRA = "EXTRA"
    POWERUP = "POWERUP"
    PENALTY = "PENALTY"


class ScoringRuleScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    BET_SCORE = "BET_SCORE"
    CONTEXT = "CONTEXT"
    SESSION = "SESSION"


class PowerUpTargetType(str, enum.Enum):
    USER = "USER"
    TEAM = "TEAM"
    GROUP = "GROUP"
    GROUP_EXCEPT_ACTOR = "GROUP_EXCEPT_ACTOR"
    ALL = "ALL"


class PowerUpTargetMode(str, enum.Enum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    RULE = "RULE"
