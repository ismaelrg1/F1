"""add more audit triggers

Revision ID: c2f9a6d4b8e1
Revises: 9e08fef16cb2
Create Date: 2026-03-29 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c2f9a6d4b8e1"
down_revision = "9e08fef16cb2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- competition
        DROP TRIGGER IF EXISTS trg_audit_competition_seasons ON competition.seasons;
        CREATE TRIGGER trg_audit_competition_seasons
        AFTER INSERT OR UPDATE OR DELETE ON competition.seasons
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_race_events ON competition.race_events;
        CREATE TRIGGER trg_audit_competition_race_events
        AFTER INSERT OR UPDATE OR DELETE ON competition.race_events
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_event_sessions ON competition.event_sessions;
        CREATE TRIGGER trg_audit_competition_event_sessions
        AFTER INSERT OR UPDATE OR DELETE ON competition.event_sessions
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_testing_events ON competition.testing_events;
        CREATE TRIGGER trg_audit_competition_testing_events
        AFTER INSERT OR UPDATE OR DELETE ON competition.testing_events
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_circuits ON competition.circuits;
        CREATE TRIGGER trg_audit_competition_circuits
        AFTER INSERT OR UPDATE OR DELETE ON competition.circuits
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_countries ON competition.countries;
        CREATE TRIGGER trg_audit_competition_countries
        AFTER INSERT OR UPDATE OR DELETE ON competition.countries
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_drivers ON competition.drivers;
        CREATE TRIGGER trg_audit_competition_drivers
        AFTER INSERT OR UPDATE OR DELETE ON competition.drivers
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_teams ON competition.teams;
        CREATE TRIGGER trg_audit_competition_teams
        AFTER INSERT OR UPDATE OR DELETE ON competition.teams
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_engines ON competition.engines;
        CREATE TRIGGER trg_audit_competition_engines
        AFTER INSERT OR UPDATE OR DELETE ON competition.engines
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_driver_entries ON competition.driver_entries;
        CREATE TRIGGER trg_audit_competition_driver_entries
        AFTER INSERT OR UPDATE OR DELETE ON competition.driver_entries
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_season_drivers ON competition.season_drivers;
        CREATE TRIGGER trg_audit_competition_season_drivers
        AFTER INSERT OR UPDATE OR DELETE ON competition.season_drivers
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_season_teams ON competition.season_teams;
        CREATE TRIGGER trg_audit_competition_season_teams
        AFTER INSERT OR UPDATE OR DELETE ON competition.season_teams
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_competition_season_engines ON competition.season_engines;
        CREATE TRIGGER trg_audit_competition_season_engines
        AFTER INSERT OR UPDATE OR DELETE ON competition.season_engines
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        -- betting configuration
        DROP TRIGGER IF EXISTS trg_audit_betting_bet_scores ON betting.bet_scores;
        CREATE TRIGGER trg_audit_betting_bet_scores
        AFTER INSERT OR UPDATE OR DELETE ON betting.bet_scores
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_betting_bet_templates ON betting.bet_templates;
        CREATE TRIGGER trg_audit_betting_bet_templates
        AFTER INSERT OR UPDATE OR DELETE ON betting.bet_templates
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_betting_bet_template_items ON betting.bet_template_items;
        CREATE TRIGGER trg_audit_betting_bet_template_items
        AFTER INSERT OR UPDATE OR DELETE ON betting.bet_template_items
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        -- scoring configuration
        DROP TRIGGER IF EXISTS trg_audit_scoring_scoring_rules ON scoring.scoring_rules;
        CREATE TRIGGER trg_audit_scoring_scoring_rules
        AFTER INSERT OR UPDATE OR DELETE ON scoring.scoring_rules
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        -- powerups configuration
        DROP TRIGGER IF EXISTS trg_audit_powerups_powerups ON powerups.powerups;
        CREATE TRIGGER trg_audit_powerups_powerups
        AFTER INSERT OR UPDATE OR DELETE ON powerups.powerups
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();

        DROP TRIGGER IF EXISTS trg_audit_powerups_powerup_restrictions ON powerups.powerup_restrictions;
        CREATE TRIGGER trg_audit_powerups_powerup_restrictions
        AFTER INSERT OR UPDATE OR DELETE ON powerups.powerup_restrictions
        FOR EACH ROW EXECUTE FUNCTION audit.log_change();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_audit_powerups_powerup_restrictions ON powerups.powerup_restrictions;
        DROP TRIGGER IF EXISTS trg_audit_powerups_powerups ON powerups.powerups;

        DROP TRIGGER IF EXISTS trg_audit_scoring_scoring_rules ON scoring.scoring_rules;

        DROP TRIGGER IF EXISTS trg_audit_betting_bet_template_items ON betting.bet_template_items;
        DROP TRIGGER IF EXISTS trg_audit_betting_bet_templates ON betting.bet_templates;
        DROP TRIGGER IF EXISTS trg_audit_betting_bet_scores ON betting.bet_scores;

        DROP TRIGGER IF EXISTS trg_audit_competition_season_engines ON competition.season_engines;
        DROP TRIGGER IF EXISTS trg_audit_competition_season_teams ON competition.season_teams;
        DROP TRIGGER IF EXISTS trg_audit_competition_season_drivers ON competition.season_drivers;
        DROP TRIGGER IF EXISTS trg_audit_competition_driver_entries ON competition.driver_entries;
        DROP TRIGGER IF EXISTS trg_audit_competition_engines ON competition.engines;
        DROP TRIGGER IF EXISTS trg_audit_competition_teams ON competition.teams;
        DROP TRIGGER IF EXISTS trg_audit_competition_drivers ON competition.drivers;
        DROP TRIGGER IF EXISTS trg_audit_competition_countries ON competition.countries;
        DROP TRIGGER IF EXISTS trg_audit_competition_circuits ON competition.circuits;
        DROP TRIGGER IF EXISTS trg_audit_competition_testing_events ON competition.testing_events;
        DROP TRIGGER IF EXISTS trg_audit_competition_event_sessions ON competition.event_sessions;
        DROP TRIGGER IF EXISTS trg_audit_competition_race_events ON competition.race_events;
        DROP TRIGGER IF EXISTS trg_audit_competition_seasons ON competition.seasons;
        """
    )
