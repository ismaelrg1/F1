from sqlalchemy import text
from sqlalchemy.orm import Session


def set_audit_actor(
    db: Session,
    *,
    user_id: int | None,
    role: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.execute(text("SELECT set_config('app.actor_user_id', :v, true)"), {"v": str(user_id) if user_id else ""})
    db.execute(text("SELECT set_config('app.actor_role', :v, true)"), {"v": role or ""})
    db.execute(text("SELECT set_config('app.actor_ip', :v, true)"), {"v": ip or ""})
    db.execute(text("SELECT set_config('app.actor_user_agent', :v, true)"), {"v": user_agent or ""})


def set_audit_group(db: Session, *, group_id: int | None) -> None:
    db.execute(text("SELECT set_config('app.group_id', :v, true)"), {"v": str(group_id) if group_id else ""})
