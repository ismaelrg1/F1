from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialResultInput:
    bet_score_code: str
    value: str
