from __future__ import annotations

import re
from typing import Any

import pandas as pd

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
            for index in self._get_session_indexes(event):
                raw_session_name = event.get(f"Session{index}")
                raw_session_date_utc = event.get(f"Session{index}DateUtc")

                session_name_missing = self._is_missing(raw_session_name)
                scheduled_start_utc = self._to_datetime(raw_session_date_utc)

                if session_name_missing and scheduled_start_utc is None:
                    continue

                session_name = None if session_name_missing else str(raw_session_name).strip()

                sessions.append(
                    {
                        "order": index,
                        "fastf1_name": session_name,
                        "session_type": self._map_session_type(session_name) if session_name else None,
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
    

    def list_testing_event_previews(self, year: int) -> list[dict[str, Any]]:
        schedule = fastf1.get_event_schedule(year)
        items: list[dict[str, Any]] = []

        for _, event in schedule.iterrows():
            event_format = str(event["EventFormat"])

            if event_format != "testing":
                continue

            country_name = str(event["Country"]).strip()
            country = self._find_country_by_name(country_name)

            sessions: list[dict[str, Any]] = []
            for index in self._get_session_indexes(event):
                raw_session_name = event.get(f"Session{index}")
                raw_session_date_utc = event.get(f"Session{index}DateUtc")

                session_name_missing = self._is_missing(raw_session_name)
                scheduled_start_utc = self._to_datetime(raw_session_date_utc)

                if session_name_missing and scheduled_start_utc is None:
                    continue

                session_name = None if session_name_missing else str(raw_session_name).strip()

                sessions.append(
                    {
                        "order": index,
                        "fastf1_name": session_name,
                        "scheduled_start_utc": scheduled_start_utc,
                    }
                )

            items.append(
                {
                    "season_year": year,
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
        if value is None or pd.isna(value):
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
    
    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True

        if pd.isna(value):
            return True

        normalized = str(value).strip().lower()
        return normalized in {"", "none", "nan", "nat"}
    
    @staticmethod
    def _get_session_indexes(event) -> list[int]:
        indexes = []
        for key in event.keys():
            if not key.startswith("Session"):
                continue

            suffix = key.replace("Session", "")
            if suffix.isdigit():
                indexes.append(int(suffix))

        return sorted(indexes)