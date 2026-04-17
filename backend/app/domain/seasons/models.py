from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonSummary:
    id: int
    year: int
    is_active: bool
