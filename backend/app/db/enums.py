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


class BetScoreRelationType(str, enum.Enum):
    DISTINCT = "DISTINCT"
    IMPLIES_VALUE = "IMPLIES_VALUE"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    MATCHES_POSITION = "MATCHES_POSITION"
    MUTUALLY_EXCLUSIVE = "MUTUALLY_EXCLUSIVE"


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


class SourceProvider(str, enum.Enum):
    MANUAL = "MANUAL"
    FASTF1 = "FASTF1"


class BetResultsVisibilityMode(str, enum.Enum):
    SUBMIT_REQUIRED = "SUBMIT_REQUIRED"
    ALWAYS_VISIBLE = "ALWAYS_VISIBLE"
    AFTER_LOCK = "AFTER_LOCK"
    AFTER_RESULTS_PUBLISHED = "AFTER_RESULTS_PUBLISHED"

    # SUBMIT_REQUIRED:
    #     si está abierto, solo ves otros si has enviado ese scope.
    #     si está cerrado, ves todos.
    # El usuario solo puede ver apuestas de otros si ya hizo submit de ese mismo scope, o si ya cerró, o si los resultados fueron publicados.

    # ALWAYS_VISIBLE:
    #     ves apuestas enviadas aunque no hayas enviado.
    # El usuario puede ver apuestas enviadas de otros aunque él no haya enviado.

    # AFTER_LOCK:
    #     solo ves cuando cierre.
    # El usuario solo puede ver apuestas de otros cuando el evento/sesión/season ya está cerrado.

    # AFTER_RESULTS_PUBLISHED:
    #     solo ves cuando admin publique resultados oficiales.
    # El usuario solo puede ver cuando el admin ha publicado resultados oficiales.

class RankingEventType(str, enum.Enum):
    TESTING_EVENT = "TESTING_EVENT"
    RACE_EVENT = "RACE_EVENT"
    SEASON = "SEASON"
