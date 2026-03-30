from __future__ import annotations

import re
from typing import Any

import fastf1
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.competition import Country
from app.domain.admin.fastf1.ports import AdminFastF1Repository


class FastF1AdminRepository(AdminFastF1Repository):
    def __init__(self, session: Session):
        self._session = session
    
    def list_race_event_previews(self, year: int) -> list[dict[str, Any]]:
        schedule = fastf1.get_event_schedule(year)
        items: list[dict[str, Any]] = []

        for _, event in schedule.iterrows():
            event_format = str(event["EventFormat"])

            if event_format == "testing":
                continue

            country_name = str(event["Country"]).strip()
            country = self._find_country_by_name(country_name)

            sessions: list[dict[str, Any]] = []
            for index in range(1, 6):
                session_name = event.get(f"Session{index}")
                if not session_name:
                    continue

                session_date_utc = event.get(f"Session{index}DateUtc")
                scheduled_start_utc = self._to_datetime(session_date_utc)

                sessions.append(
                    {
                        "order": index,
                        "fastf1_name": str(session_name),
                        "session_type": self._map_session_type(str(session_name)),
                        "scheduled_start_utc": scheduled_start_utc,
                    }
                )

            items.append(
                {
                    "season_year": year,
                    "round_number": int(event["RoundNumber"]),
                    "country_name": country_name,
                    "country_iso2_suggestion": country.iso2 if country else None,
                    "event_name": str(event["EventName"]),
                    "official_event_name": str(event["OfficialEventName"]),
                    "location": str(event["Location"]),
                    "event_format": event_format,
                    "circuit_code_suggestion": self._slugify(str(event["Location"])),
                    "scheduled_event_end_utc": self._to_datetime(event.get("EventDate")),
                    "sessions": sessions,
                }
            )

        return items

    def _find_country_by_name(self, country_name: str) -> Country | None:
        stmt = select(Country).where(func.lower(Country.name) == country_name.lower())
        return self._session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def _to_datetime(value):
        if value is None:
            return None

        try:
            return value.to_pydatetime()
        except AttributeError:
            return value

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = value.strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        return normalized.strip("-")

    @staticmethod
    def _map_session_type(name: str) -> str | None:
        mapping = {
            "Practice 1": "FP1",
            "Practice 2": "FP2",
            "Practice 3": "FP3",
            "Qualifying": "QUALY",
            "Sprint": "SPRINT",
            "Sprint Qualifying": "SPRINT_QUALY",
            "Sprint Shootout": "SPRINT_QUALY",
            "Race": "RACE",
        }
        return mapping.get(name)