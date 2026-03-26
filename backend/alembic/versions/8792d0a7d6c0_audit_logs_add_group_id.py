"""audit logs add group_id

Revision ID: 8792d0a7d6c0
Revises: d74eee313f38
Create Date: 2026-03-03 18:55:02.247971
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8792d0a7d6c0'
down_revision = 'd74eee313f38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) columna group_id
    op.add_column(
        "audit_logs",
        sa.Column("group_id", sa.Integer(), nullable=True),
        schema="audit",
    )

    # 2) FK -> social.groups(id)
    op.create_foreign_key(
        "fk_audit_logs_group_id",
        source_table="audit_logs",
        referent_table="groups",
        local_cols=["group_id"],
        remote_cols=["id"],
        source_schema="audit",
        referent_schema="social",
        ondelete="SET NULL",
    )

    # 3) índice
    op.create_index(
        "ix_audit_logs_group_id",
        "audit_logs",
        ["group_id"],
        unique=False,
        schema="audit",
    )

    # 4) actualizar función audit.log_change() para insertar group_id
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit.log_change()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
          v_actor_user_id int;
          v_actor_role text;
          v_actor_ip text;
          v_actor_user_agent text;

          v_context_schema text;
          v_context_table text;
          v_context_id text;

          v_group_id int;

          v_entity_id text;
          v_old jsonb;
          v_new jsonb;
        BEGIN
          v_actor_user_id := NULLIF(current_setting('app.actor_user_id', true), '')::int;
          v_actor_role := NULLIF(current_setting('app.actor_role', true), '');
          v_actor_ip := NULLIF(current_setting('app.actor_ip', true), '');
          v_actor_user_agent := NULLIF(current_setting('app.actor_user_agent', true), '');

          v_context_schema := NULLIF(current_setting('app.context_schema', true), '');
          v_context_table  := NULLIF(current_setting('app.context_table', true), '');
          v_context_id     := NULLIF(current_setting('app.context_id', true), '');

          -- group_id: preferimos SET LOCAL app.group_id
          v_group_id := NULLIF(current_setting('app.group_id', true), '')::int;

          IF (TG_OP = 'INSERT') THEN
            v_old := NULL;
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((to_jsonb(NEW)->>'id'), '');

            -- fallback: si la tabla tiene group_id
            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((to_jsonb(NEW)->>'group_id'), '')::int;
            END IF;

          ELSIF (TG_OP = 'UPDATE') THEN
            v_old := to_jsonb(OLD);
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((to_jsonb(NEW)->>'id'), (to_jsonb(OLD)->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((to_jsonb(NEW)->>'group_id'), '')::int;
            END IF;
            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((to_jsonb(OLD)->>'group_id'), '')::int;
            END IF;

          ELSE
            v_old := to_jsonb(OLD);
            v_new := NULL;
            v_entity_id := COALESCE((to_jsonb(OLD)->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((to_jsonb(OLD)->>'group_id'), '')::int;
            END IF;
          END IF;

          INSERT INTO audit.audit_logs (
            created_at,
            actor_user_id, actor_role, actor_ip, actor_user_agent,
            group_id,
            action_type,
            entity_schema, entity_table, entity_id,
            context_schema, context_table, context_id,
            old_data, new_data, metadata
          )
          VALUES (
            now(),
            v_actor_user_id, v_actor_role, v_actor_ip, v_actor_user_agent,
            v_group_id,
            TG_OP,
            TG_TABLE_SCHEMA, TG_TABLE_NAME, v_entity_id,
            v_context_schema, v_context_table, v_context_id,
            v_old, v_new,
            jsonb_build_object('txid', txid_current(), 'at', now())
          );

          IF TG_OP = 'DELETE' THEN
            RETURN OLD;
          ELSE
            RETURN NEW;
          END IF;
        END;
        $$;
        """
    )


def downgrade() -> None:
    # 1) volver a la función sin group_id
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit.log_change()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
          v_actor_user_id int;
          v_actor_role text;
          v_actor_ip text;
          v_actor_user_agent text;

          v_context_schema text;
          v_context_table text;
          v_context_id text;

          v_entity_id text;
          v_old jsonb;
          v_new jsonb;
        BEGIN
          v_actor_user_id := NULLIF(current_setting('app.actor_user_id', true), '')::int;
          v_actor_role := NULLIF(current_setting('app.actor_role', true), '');
          v_actor_ip := NULLIF(current_setting('app.actor_ip', true), '');
          v_actor_user_agent := NULLIF(current_setting('app.actor_user_agent', true), '');

          v_context_schema := NULLIF(current_setting('app.context_schema', true), '');
          v_context_table  := NULLIF(current_setting('app.context_table', true), '');
          v_context_id     := NULLIF(current_setting('app.context_id', true), '');

          IF (TG_OP = 'INSERT') THEN
            v_old := NULL;
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((to_jsonb(NEW)->>'id'), '');
          ELSIF (TG_OP = 'UPDATE') THEN
            v_old := to_jsonb(OLD);
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((to_jsonb(NEW)->>'id'), (to_jsonb(OLD)->>'id'), '');
          ELSE
            v_old := to_jsonb(OLD);
            v_new := NULL;
            v_entity_id := COALESCE((to_jsonb(OLD)->>'id'), '');
          END IF;

          INSERT INTO audit.audit_logs (
            actor_user_id, actor_role, actor_ip, actor_user_agent,
            action_type,
            entity_schema, entity_table, entity_id,
            context_schema, context_table, context_id,
            old_data, new_data, metadata
          )
          VALUES (
            v_actor_user_id, v_actor_role, v_actor_ip, v_actor_user_agent,
            TG_OP,
            TG_TABLE_SCHEMA, TG_TABLE_NAME, v_entity_id,
            v_context_schema, v_context_table, v_context_id,
            v_old, v_new,
            jsonb_build_object('txid', txid_current(), 'at', now())
          );

          IF TG_OP = 'DELETE' THEN
            RETURN OLD;
          ELSE
            RETURN NEW;
          END IF;
        END;
        $$;
        """
    )

    # 2) borrar índice, FK, columna
    op.drop_index("ix_audit_logs_group_id", table_name="audit_logs", schema="audit")
    op.drop_constraint("fk_audit_logs_group_id", "audit_logs", schema="audit", type_="foreignkey")
    op.drop_column("audit_logs", "group_id", schema="audit")