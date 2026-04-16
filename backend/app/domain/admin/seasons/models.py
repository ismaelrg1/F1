from dataclasses import dataclass


@dataclass(frozen=True)
class AdminSeason:
    id: int
    year: int
    is_active: bool