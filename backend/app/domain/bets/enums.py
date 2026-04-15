from enum import StrEnum


class BetContextKind(StrEnum):
    GP = "GP"
    PRETESTING = "PRETESTING"
    SEASON = "SEASON"


class BetTemplateScope(StrEnum):
    EVENT = "EVENT"
    SESSION = "SESSION"


class BetValueType(StrEnum):
    DRIVER = "DRIVER"
    TEAM = "TEAM"
    ENGINE = "ENGINE"
    CIRCUIT = "CIRCUIT"
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    POSITION = "POSITION"