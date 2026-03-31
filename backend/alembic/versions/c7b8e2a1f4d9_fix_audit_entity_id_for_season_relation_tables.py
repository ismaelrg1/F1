"""fix audit entity id for season relation tables

Revision ID: c7b8e2a1f4d9
Revises: f22db9fd5552
Create Date: 2026-03-31 20:10:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c7b8e2a1f4d9"
down_revision = "f22db9fd5552"
branch_labels = None
depends_on = None


def upgrade() -> None:
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

          v_group_id := NULLIF(current_setting('app.group_id', true), '')::int;

          IF (TG_OP = 'INSERT') THEN
            v_old := NULL;
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((v_new->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_new->>'group_id'), '')::int;
            END IF;

          ELSIF (TG_OP = 'UPDATE') THEN
            v_old := to_jsonb(OLD);
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((v_new->>'id'), (v_old->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_new->>'group_id'), '')::int;
            END IF;
            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_old->>'group_id'), '')::int;
            END IF;

          ELSE
            v_old := to_jsonb(OLD);
            v_new := NULL;
            v_entity_id := COALESCE((v_old->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_old->>'group_id'), '')::int;
            END IF;
          END IF;

          IF v_entity_id = '' THEN
            IF TG_TABLE_SCHEMA = 'competition' AND TG_TABLE_NAME = 'season_drivers' THEN
              v_entity_id := concat(
                'season_id=', COALESCE(v_new->>'season_id', v_old->>'season_id', ''),
                ';driver_id=', COALESCE(v_new->>'driver_id', v_old->>'driver_id', '')
              );
            ELSIF TG_TABLE_SCHEMA = 'competition' AND TG_TABLE_NAME = 'season_teams' THEN
              v_entity_id := concat(
                'season_id=', COALESCE(v_new->>'season_id', v_old->>'season_id', ''),
                ';team_id=', COALESCE(v_new->>'team_id', v_old->>'team_id', '')
              );
            ELSIF TG_TABLE_SCHEMA = 'competition' AND TG_TABLE_NAME = 'season_engines' THEN
              v_entity_id := concat(
                'season_id=', COALESCE(v_new->>'season_id', v_old->>'season_id', ''),
                ';engine_id=', COALESCE(v_new->>'engine_id', v_old->>'engine_id', '')
              );
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

          v_group_id := NULLIF(current_setting('app.group_id', true), '')::int;

          IF (TG_OP = 'INSERT') THEN
            v_old := NULL;
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((v_new->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_new->>'group_id'), '')::int;
            END IF;

          ELSIF (TG_OP = 'UPDATE') THEN
            v_old := to_jsonb(OLD);
            v_new := to_jsonb(NEW);
            v_entity_id := COALESCE((v_new->>'id'), (v_old->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_new->>'group_id'), '')::int;
            END IF;
            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_old->>'group_id'), '')::int;
            END IF;

          ELSE
            v_old := to_jsonb(OLD);
            v_new := NULL;
            v_entity_id := COALESCE((v_old->>'id'), '');

            IF v_group_id IS NULL THEN
              v_group_id := NULLIF((v_old->>'group_id'), '')::int;
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
