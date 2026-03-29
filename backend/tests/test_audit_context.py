from sqlalchemy import text

from app.db.audit.context import set_audit_actor


def test_set_audit_actor_sets_postgres_local_settings(db_session) -> None:
    set_audit_actor(
        db_session,
        user_id=123,
        role="ADMIN",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    row = db_session.execute(
        text(
            """
            SELECT
                current_setting('app.actor_user_id', true) AS actor_user_id,
                current_setting('app.actor_role', true) AS actor_role,
                current_setting('app.actor_ip', true) AS actor_ip,
                current_setting('app.actor_user_agent', true) AS actor_user_agent
            """
        )
    ).mappings().one()

    assert row["actor_user_id"] == "123"
    assert row["actor_role"] == "ADMIN"
    assert row["actor_ip"] == "127.0.0.1"
    assert row["actor_user_agent"] == "pytest"
