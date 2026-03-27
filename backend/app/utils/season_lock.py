from datetime import datetime
from backend.app.models import RaceEvent

def get_season_lock_dt(year: int):
    """
    Devuelve la datetime UTC del primer evento 'testing' de la temporada.
    Si no existe, no bloquea (None).
    """

    if year == 2026:
        return datetime(2026, 3, 1, 13, 0, 0)

    ev = (RaceEvent.query
          .filter_by(year=year, event_format='testing')
          .order_by(RaceEvent.event_date.asc())
          .first())
    return ev.time_session1 if ev and ev.time_session1 else None

def is_season_locked(year: int, now_utc=None):
    now_utc = now_utc or datetime.utcnow()
    lock_dt = get_season_lock_dt(year)
    return bool(lock_dt and now_utc >= lock_dt)
