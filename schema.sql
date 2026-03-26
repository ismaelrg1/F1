--
-- PostgreSQL database dump
--

\restrict 0HQuk3F7O2p2FSV81mxBfX5bjKgmR2wQNHYah12smE1JfIE3eYo9lsuJiPTd0dh

-- Dumped from database version 16.13
-- Dumped by pg_dump version 16.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA auth;


ALTER SCHEMA auth OWNER TO postgres;

--
-- Name: betting; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA betting;


ALTER SCHEMA betting OWNER TO postgres;

--
-- Name: competition; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA competition;


ALTER SCHEMA competition OWNER TO postgres;

--
-- Name: powerups; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA powerups;


ALTER SCHEMA powerups OWNER TO postgres;

--
-- Name: scoring; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA scoring;


ALTER SCHEMA scoring OWNER TO postgres;

--
-- Name: social; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA social;


ALTER SCHEMA social OWNER TO postgres;

--
-- Name: btree_gist; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION btree_gist; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';


--
-- Name: citext; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;


--
-- Name: EXTENSION citext; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION citext IS 'data type for case-insensitive character strings';


--
-- Name: role_name_enum; Type: TYPE; Schema: auth; Owner: postgres
--

CREATE TYPE auth.role_name_enum AS ENUM (
    'USER',
    'ADMIN',
    'EDITOR'
);


ALTER TYPE auth.role_name_enum OWNER TO postgres;

--
-- Name: bet_context_kind_enum; Type: TYPE; Schema: betting; Owner: postgres
--

CREATE TYPE betting.bet_context_kind_enum AS ENUM (
    'GP',
    'PRETESTING',
    'SEASON'
);


ALTER TYPE betting.bet_context_kind_enum OWNER TO postgres;

--
-- Name: bet_template_scope_enum; Type: TYPE; Schema: betting; Owner: postgres
--

CREATE TYPE betting.bet_template_scope_enum AS ENUM (
    'EVENT',
    'SESSION'
);


ALTER TYPE betting.bet_template_scope_enum OWNER TO postgres;

--
-- Name: bet_value_type_enum; Type: TYPE; Schema: betting; Owner: postgres
--

CREATE TYPE betting.bet_value_type_enum AS ENUM (
    'DRIVER',
    'TEAM',
    'ENGINE',
    'CIRCUIT',
    'STRING',
    'INTEGER',
    'FLOAT',
    'BOOLEAN',
    'POSITION'
);


ALTER TYPE betting.bet_value_type_enum OWNER TO postgres;

--
-- Name: event_session_type_enum; Type: TYPE; Schema: competition; Owner: postgres
--

CREATE TYPE competition.event_session_type_enum AS ENUM (
    'FP1',
    'FP2',
    'FP3',
    'QUALY',
    'SPRINT_QUALY',
    'SPRINT',
    'RACE'
);


ALTER TYPE competition.event_session_type_enum OWNER TO postgres;

--
-- Name: race_event_status_enum; Type: TYPE; Schema: competition; Owner: postgres
--

CREATE TYPE competition.race_event_status_enum AS ENUM (
    'SCHEDULED',
    'CANCELLED',
    'POSTPONED',
    'COMPLETED'
);


ALTER TYPE competition.race_event_status_enum OWNER TO postgres;

--
-- Name: season_driver_status_enum; Type: TYPE; Schema: competition; Owner: postgres
--

CREATE TYPE competition.season_driver_status_enum AS ENUM (
    'PRIMARY',
    'RESERVE',
    'INACTIVE'
);


ALTER TYPE competition.season_driver_status_enum OWNER TO postgres;

--
-- Name: testing_event_status_enum; Type: TYPE; Schema: competition; Owner: postgres
--

CREATE TYPE competition.testing_event_status_enum AS ENUM (
    'SCHEDULED',
    'CANCELLED',
    'POSTPONED',
    'COMPLETED'
);


ALTER TYPE competition.testing_event_status_enum OWNER TO postgres;

--
-- Name: powerup_target_mode_enum; Type: TYPE; Schema: powerups; Owner: postgres
--

CREATE TYPE powerups.powerup_target_mode_enum AS ENUM (
    'SINGLE',
    'MULTI',
    'RULE'
);


ALTER TYPE powerups.powerup_target_mode_enum OWNER TO postgres;

--
-- Name: powerup_target_type_enum; Type: TYPE; Schema: powerups; Owner: postgres
--

CREATE TYPE powerups.powerup_target_type_enum AS ENUM (
    'USER',
    'TEAM',
    'GROUP',
    'GROUP_EXCEPT_ACTOR',
    'ALL'
);


ALTER TYPE powerups.powerup_target_type_enum OWNER TO postgres;

--
-- Name: official_result_source_enum; Type: TYPE; Schema: scoring; Owner: postgres
--

CREATE TYPE scoring.official_result_source_enum AS ENUM (
    'MANUAL',
    'FASTF1',
    'OTHER'
);


ALTER TYPE scoring.official_result_source_enum OWNER TO postgres;

--
-- Name: score_component_type_enum; Type: TYPE; Schema: scoring; Owner: postgres
--

CREATE TYPE scoring.score_component_type_enum AS ENUM (
    'BASE',
    'EXTRA',
    'POWERUP',
    'PENALTY'
);


ALTER TYPE scoring.score_component_type_enum OWNER TO postgres;

--
-- Name: group_role_enum; Type: TYPE; Schema: social; Owner: postgres
--

CREATE TYPE social.group_role_enum AS ENUM (
    'OWNER',
    'MEMBER',
    'MODERATOR'
);


ALTER TYPE social.group_role_enum OWNER TO postgres;

--
-- Name: team_role_enum; Type: TYPE; Schema: social; Owner: postgres
--

CREATE TYPE social.team_role_enum AS ENUM (
    'CAPTAIN',
    'MEMBER'
);


ALTER TYPE social.team_role_enum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: permissions; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.permissions (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    description character varying(255) NOT NULL
);


ALTER TABLE auth.permissions OWNER TO postgres;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: auth; Owner: postgres
--

CREATE SEQUENCE auth.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE auth.permissions_id_seq OWNER TO postgres;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: postgres
--

ALTER SEQUENCE auth.permissions_id_seq OWNED BY auth.permissions.id;


--
-- Name: role_permissions; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.role_permissions (
    permission_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE auth.role_permissions OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.roles (
    id integer NOT NULL,
    name auth.role_name_enum NOT NULL,
    description character varying(255) NOT NULL
);


ALTER TABLE auth.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: auth; Owner: postgres
--

CREATE SEQUENCE auth.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE auth.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: postgres
--

ALTER SEQUENCE auth.roles_id_seq OWNED BY auth.roles.id;


--
-- Name: user_roles; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE auth.user_roles OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: auth; Owner: postgres
--

CREATE TABLE auth.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email public.citext NOT NULL,
    password_hash character varying(255),
    auth_provider character varying(20) DEFAULT 'LOCAL'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE auth.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: auth; Owner: postgres
--

CREATE SEQUENCE auth.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE auth.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: postgres
--

ALTER SEQUENCE auth.users_id_seq OWNED BY auth.users.id;


--
-- Name: bet_contexts; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_contexts (
    id integer NOT NULL,
    kind betting.bet_context_kind_enum NOT NULL,
    season_id integer NOT NULL,
    race_event_id integer,
    testing_event_id integer,
    label character varying(200) NOT NULL,
    results_published boolean DEFAULT false NOT NULL,
    results_published_at timestamp with time zone,
    group_id integer NOT NULL,
    CONSTRAINT ck_bet_contexts_kind_matches_ids CHECK ((((kind = 'GP'::betting.bet_context_kind_enum) AND (race_event_id IS NOT NULL) AND (testing_event_id IS NULL)) OR ((kind = 'PRETESTING'::betting.bet_context_kind_enum) AND (testing_event_id IS NOT NULL) AND (race_event_id IS NULL)) OR ((kind = 'SEASON'::betting.bet_context_kind_enum) AND (race_event_id IS NULL) AND (testing_event_id IS NULL)))),
    CONSTRAINT ck_bet_contexts_not_both_event_ids CHECK ((NOT ((race_event_id IS NOT NULL) AND (testing_event_id IS NOT NULL)))),
    CONSTRAINT ck_bet_contexts_published_requires_timestamp CHECK (((results_published = false) OR (results_published_at IS NOT NULL))),
    CONSTRAINT ck_bet_contexts_unpublished_has_no_timestamp CHECK (((results_published = true) OR (results_published_at IS NULL)))
);


ALTER TABLE betting.bet_contexts OWNER TO postgres;

--
-- Name: bet_contexts_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_contexts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_contexts_id_seq OWNER TO postgres;

--
-- Name: bet_contexts_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_contexts_id_seq OWNED BY betting.bet_contexts.id;


--
-- Name: bet_exceptions; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_exceptions (
    id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    bet_score_id integer NOT NULL,
    override_points double precision,
    is_disabled boolean,
    override_constraints_json jsonb,
    note character varying(500),
    CONSTRAINT ck_bet_exceptions_has_effect CHECK (((override_points IS NOT NULL) OR (is_disabled IS NOT NULL) OR (override_constraints_json IS NOT NULL))),
    CONSTRAINT ck_bet_exceptions_override_points_nonneg CHECK (((override_points IS NULL) OR (override_points >= (0)::double precision)))
);


ALTER TABLE betting.bet_exceptions OWNER TO postgres;

--
-- Name: bet_exceptions_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_exceptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_exceptions_id_seq OWNER TO postgres;

--
-- Name: bet_exceptions_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_exceptions_id_seq OWNED BY betting.bet_exceptions.id;


--
-- Name: bet_picks; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_picks (
    id integer NOT NULL,
    bet_id integer NOT NULL,
    bet_score_id integer NOT NULL,
    value character varying(255) NOT NULL,
    is_invalid boolean DEFAULT false NOT NULL,
    invalid_reason character varying(300),
    invalidated_at timestamp with time zone,
    invalidated_by_user_id integer
);


ALTER TABLE betting.bet_picks OWNER TO postgres;

--
-- Name: bet_picks_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_picks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_picks_id_seq OWNER TO postgres;

--
-- Name: bet_picks_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_picks_id_seq OWNED BY betting.bet_picks.id;


--
-- Name: bet_scores; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_scores (
    id integer NOT NULL,
    code character varying(80) NOT NULL,
    label character varying(200) NOT NULL,
    base_points double precision NOT NULL,
    value_type betting.bet_value_type_enum NOT NULL,
    constraints_json jsonb,
    CONSTRAINT ck_bet_scores_base_points_nonneg CHECK ((base_points >= (0)::double precision)),
    CONSTRAINT ck_bet_scores_code_format CHECK (((code)::text ~ '^[A-Z0-9_]+$'::text))
);


ALTER TABLE betting.bet_scores OWNER TO postgres;

--
-- Name: bet_scores_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_scores_id_seq OWNER TO postgres;

--
-- Name: bet_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_scores_id_seq OWNED BY betting.bet_scores.id;


--
-- Name: bet_template_items; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_template_items (
    id integer NOT NULL,
    template_id integer NOT NULL,
    bet_score_id integer NOT NULL,
    required boolean DEFAULT true NOT NULL,
    display_order integer NOT NULL
);


ALTER TABLE betting.bet_template_items OWNER TO postgres;

--
-- Name: bet_template_items_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_template_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_template_items_id_seq OWNER TO postgres;

--
-- Name: bet_template_items_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_template_items_id_seq OWNED BY betting.bet_template_items.id;


--
-- Name: bet_templates; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bet_templates (
    id integer NOT NULL,
    season_id integer NOT NULL,
    name character varying(255) NOT NULL,
    context_kind betting.bet_context_kind_enum NOT NULL,
    scope betting.bet_template_scope_enum DEFAULT 'EVENT'::betting.bet_template_scope_enum NOT NULL,
    session_type competition.event_session_type_enum,
    CONSTRAINT ck_bet_templates_scope_sessiontype CHECK ((((scope = 'EVENT'::betting.bet_template_scope_enum) AND (session_type IS NULL)) OR ((scope = 'SESSION'::betting.bet_template_scope_enum) AND (context_kind = 'GP'::betting.bet_context_kind_enum) AND (session_type IS NOT NULL))))
);


ALTER TABLE betting.bet_templates OWNER TO postgres;

--
-- Name: bet_templates_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bet_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bet_templates_id_seq OWNER TO postgres;

--
-- Name: bet_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bet_templates_id_seq OWNED BY betting.bet_templates.id;


--
-- Name: bets; Type: TABLE; Schema: betting; Owner: postgres
--

CREATE TABLE betting.bets (
    id integer NOT NULL,
    user_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    submitted_at timestamp with time zone,
    last_modified_at timestamp with time zone DEFAULT now() NOT NULL,
    locked_at timestamp with time zone,
    CONSTRAINT ck_bets_locked_after_submit CHECK (((locked_at IS NULL) OR (submitted_at IS NULL) OR (locked_at >= submitted_at)))
);


ALTER TABLE betting.bets OWNER TO postgres;

--
-- Name: bets_id_seq; Type: SEQUENCE; Schema: betting; Owner: postgres
--

CREATE SEQUENCE betting.bets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE betting.bets_id_seq OWNER TO postgres;

--
-- Name: bets_id_seq; Type: SEQUENCE OWNED BY; Schema: betting; Owner: postgres
--

ALTER SEQUENCE betting.bets_id_seq OWNED BY betting.bets.id;


--
-- Name: circuits; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.circuits (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    country_id integer NOT NULL,
    map_asset_url character varying(200),
    image_asset_url character varying(200)
);


ALTER TABLE competition.circuits OWNER TO postgres;

--
-- Name: circuits_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.circuits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.circuits_id_seq OWNER TO postgres;

--
-- Name: circuits_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.circuits_id_seq OWNED BY competition.circuits.id;


--
-- Name: countries; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.countries (
    id integer NOT NULL,
    iso2 character varying(2) NOT NULL,
    name character varying(50) NOT NULL,
    flag_asset_url character varying(200)
);


ALTER TABLE competition.countries OWNER TO postgres;

--
-- Name: countries_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.countries_id_seq OWNER TO postgres;

--
-- Name: countries_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.countries_id_seq OWNED BY competition.countries.id;


--
-- Name: driver_entries; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.driver_entries (
    id integer NOT NULL,
    season_id integer NOT NULL,
    driver_id integer NOT NULL,
    team_id integer NOT NULL,
    engine_id integer NOT NULL,
    seat_index smallint NOT NULL,
    active_from timestamp with time zone,
    active_to timestamp with time zone,
    note character varying(255),
    race_event_id integer,
    event_session_id integer,
    CONSTRAINT ck_driver_entries_active_window_order CHECK (((active_from IS NULL) OR (active_to IS NULL) OR (active_from < active_to))),
    CONSTRAINT ck_driver_entries_not_both_event_and_session CHECK ((NOT ((race_event_id IS NOT NULL) AND (event_session_id IS NOT NULL)))),
    CONSTRAINT ck_driver_entries_seat_index_1_2 CHECK ((seat_index = ANY (ARRAY[1, 2])))
);


ALTER TABLE competition.driver_entries OWNER TO postgres;

--
-- Name: driver_entries_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.driver_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.driver_entries_id_seq OWNER TO postgres;

--
-- Name: driver_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.driver_entries_id_seq OWNED BY competition.driver_entries.id;


--
-- Name: drivers; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.drivers (
    id integer NOT NULL,
    code character varying(3) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE competition.drivers OWNER TO postgres;

--
-- Name: drivers_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.drivers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.drivers_id_seq OWNER TO postgres;

--
-- Name: drivers_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.drivers_id_seq OWNED BY competition.drivers.id;


--
-- Name: engines; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.engines (
    id integer NOT NULL,
    code character varying(10) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE competition.engines OWNER TO postgres;

--
-- Name: engines_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.engines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.engines_id_seq OWNER TO postgres;

--
-- Name: engines_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.engines_id_seq OWNED BY competition.engines.id;


--
-- Name: event_sessions; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.event_sessions (
    id integer NOT NULL,
    race_event_id integer NOT NULL,
    session_type competition.event_session_type_enum NOT NULL,
    start_datetime timestamp with time zone NOT NULL,
    lock_cutoff timestamp with time zone NOT NULL,
    results_published boolean DEFAULT false NOT NULL,
    results_published_at timestamp with time zone
);


ALTER TABLE competition.event_sessions OWNER TO postgres;

--
-- Name: event_sessions_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.event_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.event_sessions_id_seq OWNER TO postgres;

--
-- Name: event_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.event_sessions_id_seq OWNED BY competition.event_sessions.id;


--
-- Name: race_events; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.race_events (
    id integer NOT NULL,
    season_id integer NOT NULL,
    name character varying(50) NOT NULL,
    circuit_id integer NOT NULL,
    event_start timestamp with time zone,
    event_end timestamp with time zone,
    status competition.race_event_status_enum DEFAULT 'SCHEDULED'::competition.race_event_status_enum NOT NULL,
    status_reason character varying(200)
);


ALTER TABLE competition.race_events OWNER TO postgres;

--
-- Name: race_events_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.race_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.race_events_id_seq OWNER TO postgres;

--
-- Name: race_events_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.race_events_id_seq OWNED BY competition.race_events.id;


--
-- Name: season_drivers; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.season_drivers (
    season_id integer NOT NULL,
    driver_id integer NOT NULL,
    status competition.season_driver_status_enum DEFAULT 'PRIMARY'::competition.season_driver_status_enum NOT NULL
);


ALTER TABLE competition.season_drivers OWNER TO postgres;

--
-- Name: season_engines; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.season_engines (
    season_id integer NOT NULL,
    engine_id integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE competition.season_engines OWNER TO postgres;

--
-- Name: season_teams; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.season_teams (
    season_id integer NOT NULL,
    team_id integer NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE competition.season_teams OWNER TO postgres;

--
-- Name: seasons; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.seasons (
    id integer NOT NULL,
    year integer NOT NULL,
    is_active boolean DEFAULT false NOT NULL
);


ALTER TABLE competition.seasons OWNER TO postgres;

--
-- Name: seasons_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.seasons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.seasons_id_seq OWNER TO postgres;

--
-- Name: seasons_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.seasons_id_seq OWNED BY competition.seasons.id;


--
-- Name: teams; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.teams (
    id integer NOT NULL,
    code character varying(3) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE competition.teams OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.teams_id_seq OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.teams_id_seq OWNED BY competition.teams.id;


--
-- Name: testing_events; Type: TABLE; Schema: competition; Owner: postgres
--

CREATE TABLE competition.testing_events (
    id integer NOT NULL,
    season_id integer NOT NULL,
    name character varying(50) NOT NULL,
    circuit_id integer NOT NULL,
    event_start timestamp with time zone,
    event_end timestamp with time zone,
    status competition.testing_event_status_enum DEFAULT 'SCHEDULED'::competition.testing_event_status_enum NOT NULL,
    status_reason character varying(200)
);


ALTER TABLE competition.testing_events OWNER TO postgres;

--
-- Name: testing_events_id_seq; Type: SEQUENCE; Schema: competition; Owner: postgres
--

CREATE SEQUENCE competition.testing_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE competition.testing_events_id_seq OWNER TO postgres;

--
-- Name: testing_events_id_seq; Type: SEQUENCE OWNED BY; Schema: competition; Owner: postgres
--

ALTER SEQUENCE competition.testing_events_id_seq OWNED BY competition.testing_events.id;


--
-- Name: powerup_assignments; Type: TABLE; Schema: powerups; Owner: postgres
--

CREATE TABLE powerups.powerup_assignments (
    id integer NOT NULL,
    group_id integer NOT NULL,
    user_id integer NOT NULL,
    season_id integer NOT NULL,
    bet_context_id integer,
    powerup_id integer NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_powerup_assignments_quantity_nonneg CHECK ((quantity >= 0)),
    CONSTRAINT ck_powerup_assignments_scope_xor CHECK ((((season_id IS NOT NULL) AND (bet_context_id IS NULL)) OR ((season_id IS NULL) AND (bet_context_id IS NOT NULL))))
);


ALTER TABLE powerups.powerup_assignments OWNER TO postgres;

--
-- Name: powerup_assignments_id_seq; Type: SEQUENCE; Schema: powerups; Owner: postgres
--

CREATE SEQUENCE powerups.powerup_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE powerups.powerup_assignments_id_seq OWNER TO postgres;

--
-- Name: powerup_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: powerups; Owner: postgres
--

ALTER SEQUENCE powerups.powerup_assignments_id_seq OWNED BY powerups.powerup_assignments.id;


--
-- Name: powerup_restrictions; Type: TABLE; Schema: powerups; Owner: postgres
--

CREATE TABLE powerups.powerup_restrictions (
    id integer NOT NULL,
    powerup_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    is_disabled boolean DEFAULT false NOT NULL,
    note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_powerup_restrictions_note_len CHECK (((note IS NULL) OR (length(note) <= 5000)))
);


ALTER TABLE powerups.powerup_restrictions OWNER TO postgres;

--
-- Name: powerup_restrictions_id_seq; Type: SEQUENCE; Schema: powerups; Owner: postgres
--

CREATE SEQUENCE powerups.powerup_restrictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE powerups.powerup_restrictions_id_seq OWNER TO postgres;

--
-- Name: powerup_restrictions_id_seq; Type: SEQUENCE OWNED BY; Schema: powerups; Owner: postgres
--

ALTER SEQUENCE powerups.powerup_restrictions_id_seq OWNED BY powerups.powerup_restrictions.id;


--
-- Name: powerup_use_targets; Type: TABLE; Schema: powerups; Owner: postgres
--

CREATE TABLE powerups.powerup_use_targets (
    id integer NOT NULL,
    powerup_use_id integer NOT NULL,
    target_type powerups.powerup_target_type_enum NOT NULL,
    target_user_id integer,
    target_team_id integer,
    target_group_id integer,
    rule_json jsonb,
    CONSTRAINT ck_put_target_type_matches_ids CHECK ((((target_type = 'USER'::powerups.powerup_target_type_enum) AND (target_user_id IS NOT NULL) AND (target_team_id IS NULL) AND (target_group_id IS NULL)) OR ((target_type = 'TEAM'::powerups.powerup_target_type_enum) AND (target_team_id IS NOT NULL) AND (target_user_id IS NULL) AND (target_group_id IS NULL)) OR ((target_type = 'GROUP'::powerups.powerup_target_type_enum) AND (target_group_id IS NOT NULL) AND (target_user_id IS NULL) AND (target_team_id IS NULL)) OR ((target_type = 'GROUP_EXCEPT_ACTOR'::powerups.powerup_target_type_enum) AND (target_group_id IS NOT NULL) AND (target_user_id IS NULL) AND (target_team_id IS NULL)) OR ((target_type = 'ALL'::powerups.powerup_target_type_enum) AND (target_user_id IS NULL) AND (target_team_id IS NULL) AND (target_group_id IS NULL))))
);


ALTER TABLE powerups.powerup_use_targets OWNER TO postgres;

--
-- Name: powerup_use_targets_id_seq; Type: SEQUENCE; Schema: powerups; Owner: postgres
--

CREATE SEQUENCE powerups.powerup_use_targets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE powerups.powerup_use_targets_id_seq OWNER TO postgres;

--
-- Name: powerup_use_targets_id_seq; Type: SEQUENCE OWNED BY; Schema: powerups; Owner: postgres
--

ALTER SEQUENCE powerups.powerup_use_targets_id_seq OWNED BY powerups.powerup_use_targets.id;


--
-- Name: powerup_uses; Type: TABLE; Schema: powerups; Owner: postgres
--

CREATE TABLE powerups.powerup_uses (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    powerup_id integer NOT NULL,
    used_at timestamp with time zone DEFAULT now() NOT NULL,
    rule_json jsonb
);


ALTER TABLE powerups.powerup_uses OWNER TO postgres;

--
-- Name: powerup_uses_id_seq; Type: SEQUENCE; Schema: powerups; Owner: postgres
--

CREATE SEQUENCE powerups.powerup_uses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE powerups.powerup_uses_id_seq OWNER TO postgres;

--
-- Name: powerup_uses_id_seq; Type: SEQUENCE OWNED BY; Schema: powerups; Owner: postgres
--

ALTER SEQUENCE powerups.powerup_uses_id_seq OWNED BY powerups.powerup_uses.id;


--
-- Name: powerups; Type: TABLE; Schema: powerups; Owner: postgres
--

CREATE TABLE powerups.powerups (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    is_enabled boolean DEFAULT true NOT NULL,
    target_mode powerups.powerup_target_mode_enum DEFAULT 'SINGLE'::powerups.powerup_target_mode_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_powerups_code_minlen CHECK ((length((code)::text) >= 2)),
    CONSTRAINT ck_powerups_name_minlen CHECK ((length((name)::text) >= 2))
);


ALTER TABLE powerups.powerups OWNER TO postgres;

--
-- Name: powerups_id_seq; Type: SEQUENCE; Schema: powerups; Owner: postgres
--

CREATE SEQUENCE powerups.powerups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE powerups.powerups_id_seq OWNER TO postgres;

--
-- Name: powerups_id_seq; Type: SEQUENCE OWNED BY; Schema: powerups; Owner: postgres
--

ALTER SEQUENCE powerups.powerups_id_seq OWNED BY powerups.powerups.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: official_results; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.official_results (
    id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    bet_score_id integer NOT NULL,
    value character varying(255) NOT NULL,
    source scoring.official_result_source_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_official_results_value_not_empty CHECK (((value)::text <> ''::text))
);


ALTER TABLE scoring.official_results OWNER TO postgres;

--
-- Name: official_results_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.official_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.official_results_id_seq OWNER TO postgres;

--
-- Name: official_results_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.official_results_id_seq OWNED BY scoring.official_results.id;


--
-- Name: result_publications; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.result_publications (
    id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer,
    published_by_user_id integer,
    published_at timestamp with time zone DEFAULT now() NOT NULL,
    note text,
    CONSTRAINT ck_result_publications_note_len CHECK (((note IS NULL) OR (length(note) <= 5000)))
);


ALTER TABLE scoring.result_publications OWNER TO postgres;

--
-- Name: result_publications_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.result_publications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.result_publications_id_seq OWNER TO postgres;

--
-- Name: result_publications_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.result_publications_id_seq OWNED BY scoring.result_publications.id;


--
-- Name: score_components; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.score_components (
    id integer NOT NULL,
    score_id integer NOT NULL,
    component_type scoring.score_component_type_enum NOT NULL,
    code character varying(80) NOT NULL,
    points numeric(14,8) DEFAULT 0 NOT NULL,
    details_json jsonb,
    CONSTRAINT ck_score_components_points_notnull CHECK ((points IS NOT NULL))
);


ALTER TABLE scoring.score_components OWNER TO postgres;

--
-- Name: score_components_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.score_components_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.score_components_id_seq OWNER TO postgres;

--
-- Name: score_components_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.score_components_id_seq OWNED BY scoring.score_components.id;


--
-- Name: score_season_aggregates; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.score_season_aggregates (
    id integer NOT NULL,
    user_id integer NOT NULL,
    season_id integer NOT NULL,
    total_points numeric(14,8) DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE scoring.score_season_aggregates OWNER TO postgres;

--
-- Name: score_season_aggregates_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.score_season_aggregates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.score_season_aggregates_id_seq OWNER TO postgres;

--
-- Name: score_season_aggregates_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.score_season_aggregates_id_seq OWNED BY scoring.score_season_aggregates.id;


--
-- Name: score_session_components; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.score_session_components (
    id integer NOT NULL,
    score_session_id integer NOT NULL,
    component_type scoring.score_component_type_enum NOT NULL,
    code character varying(80) NOT NULL,
    points numeric(14,8) DEFAULT 0 NOT NULL,
    datails_json jsonb,
    CONSTRAINT ck_score_sess_components_points_notnull CHECK ((points IS NOT NULL))
);


ALTER TABLE scoring.score_session_components OWNER TO postgres;

--
-- Name: score_session_components_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.score_session_components_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.score_session_components_id_seq OWNER TO postgres;

--
-- Name: score_session_components_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.score_session_components_id_seq OWNED BY scoring.score_session_components.id;


--
-- Name: score_sessions; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.score_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    event_session_id integer NOT NULL,
    base_points numeric(12,4) DEFAULT 0 NOT NULL,
    total_points numeric(14,8) DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_score_sessions_base_points_nonneg CHECK ((base_points >= (0)::numeric)),
    CONSTRAINT ck_score_sessions_total_points_nonneg CHECK ((total_points >= (0)::numeric))
);


ALTER TABLE scoring.score_sessions OWNER TO postgres;

--
-- Name: score_sessions_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.score_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.score_sessions_id_seq OWNER TO postgres;

--
-- Name: score_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.score_sessions_id_seq OWNED BY scoring.score_sessions.id;


--
-- Name: scores; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.scores (
    id integer NOT NULL,
    user_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    base_points numeric(14,8) DEFAULT 0 NOT NULL,
    total_points numeric(14,8) DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_scores_base_points_nonneg CHECK ((base_points >= (0)::numeric)),
    CONSTRAINT ck_scores_total_points_nonneg CHECK ((total_points >= (0)::numeric))
);


ALTER TABLE scoring.scores OWNER TO postgres;

--
-- Name: scores_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.scores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.scores_id_seq OWNER TO postgres;

--
-- Name: scores_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.scores_id_seq OWNED BY scoring.scores.id;


--
-- Name: team_event_aggregates; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.team_event_aggregates (
    id integer NOT NULL,
    group_id integer NOT NULL,
    team_id integer NOT NULL,
    bet_context_id integer NOT NULL,
    total_points numeric(14,8) DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE scoring.team_event_aggregates OWNER TO postgres;

--
-- Name: team_event_aggregates_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.team_event_aggregates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.team_event_aggregates_id_seq OWNER TO postgres;

--
-- Name: team_event_aggregates_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.team_event_aggregates_id_seq OWNED BY scoring.team_event_aggregates.id;


--
-- Name: team_season_aggregates; Type: TABLE; Schema: scoring; Owner: postgres
--

CREATE TABLE scoring.team_season_aggregates (
    id integer NOT NULL,
    group_id integer NOT NULL,
    team_id integer NOT NULL,
    season_id integer NOT NULL,
    total_points numeric(14,8) DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE scoring.team_season_aggregates OWNER TO postgres;

--
-- Name: team_season_aggregates_id_seq; Type: SEQUENCE; Schema: scoring; Owner: postgres
--

CREATE SEQUENCE scoring.team_season_aggregates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE scoring.team_season_aggregates_id_seq OWNER TO postgres;

--
-- Name: team_season_aggregates_id_seq; Type: SEQUENCE OWNED BY; Schema: scoring; Owner: postgres
--

ALTER SEQUENCE scoring.team_season_aggregates_id_seq OWNED BY scoring.team_season_aggregates.id;


--
-- Name: group_memberships; Type: TABLE; Schema: social; Owner: postgres
--

CREATE TABLE social.group_memberships (
    id integer NOT NULL,
    group_id integer NOT NULL,
    user_id integer NOT NULL,
    role social.group_role_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE social.group_memberships OWNER TO postgres;

--
-- Name: group_memberships_id_seq; Type: SEQUENCE; Schema: social; Owner: postgres
--

CREATE SEQUENCE social.group_memberships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE social.group_memberships_id_seq OWNER TO postgres;

--
-- Name: group_memberships_id_seq; Type: SEQUENCE OWNED BY; Schema: social; Owner: postgres
--

ALTER SEQUENCE social.group_memberships_id_seq OWNED BY social.group_memberships.id;


--
-- Name: groups; Type: TABLE; Schema: social; Owner: postgres
--

CREATE TABLE social.groups (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    join_code text,
    is_private boolean DEFAULT true NOT NULL,
    teams_enabled boolean DEFAULT false NOT NULL,
    max_team_size integer,
    CONSTRAINT ck_groups_join_code_len CHECK (((join_code IS NULL) OR ((length(join_code) >= 4) AND (length(join_code) <= 20)))),
    CONSTRAINT ck_groups_name_minlen CHECK ((length((name)::text) >= 2))
);


ALTER TABLE social.groups OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: social; Owner: postgres
--

CREATE SEQUENCE social.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE social.groups_id_seq OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: social; Owner: postgres
--

ALTER SEQUENCE social.groups_id_seq OWNED BY social.groups.id;


--
-- Name: team_memberships; Type: TABLE; Schema: social; Owner: postgres
--

CREATE TABLE social.team_memberships (
    id integer NOT NULL,
    team_id integer NOT NULL,
    user_id integer NOT NULL,
    role social.team_role_enum NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE social.team_memberships OWNER TO postgres;

--
-- Name: team_memberships_id_seq; Type: SEQUENCE; Schema: social; Owner: postgres
--

CREATE SEQUENCE social.team_memberships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE social.team_memberships_id_seq OWNER TO postgres;

--
-- Name: team_memberships_id_seq; Type: SEQUENCE OWNED BY; Schema: social; Owner: postgres
--

ALTER SEQUENCE social.team_memberships_id_seq OWNED BY social.team_memberships.id;


--
-- Name: teams; Type: TABLE; Schema: social; Owner: postgres
--

CREATE TABLE social.teams (
    id integer NOT NULL,
    group_id integer NOT NULL,
    name character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_teams_name_minlen CHECK ((length((name)::text) >= 2))
);


ALTER TABLE social.teams OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: social; Owner: postgres
--

CREATE SEQUENCE social.teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE social.teams_id_seq OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: social; Owner: postgres
--

ALTER SEQUENCE social.teams_id_seq OWNED BY social.teams.id;


--
-- Name: permissions id; Type: DEFAULT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.permissions ALTER COLUMN id SET DEFAULT nextval('auth.permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.roles ALTER COLUMN id SET DEFAULT nextval('auth.roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users ALTER COLUMN id SET DEFAULT nextval('auth.users_id_seq'::regclass);


--
-- Name: bet_contexts id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts ALTER COLUMN id SET DEFAULT nextval('betting.bet_contexts_id_seq'::regclass);


--
-- Name: bet_exceptions id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_exceptions ALTER COLUMN id SET DEFAULT nextval('betting.bet_exceptions_id_seq'::regclass);


--
-- Name: bet_picks id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks ALTER COLUMN id SET DEFAULT nextval('betting.bet_picks_id_seq'::regclass);


--
-- Name: bet_scores id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_scores ALTER COLUMN id SET DEFAULT nextval('betting.bet_scores_id_seq'::regclass);


--
-- Name: bet_template_items id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items ALTER COLUMN id SET DEFAULT nextval('betting.bet_template_items_id_seq'::regclass);


--
-- Name: bet_templates id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_templates ALTER COLUMN id SET DEFAULT nextval('betting.bet_templates_id_seq'::regclass);


--
-- Name: bets id; Type: DEFAULT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bets ALTER COLUMN id SET DEFAULT nextval('betting.bets_id_seq'::regclass);


--
-- Name: circuits id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.circuits ALTER COLUMN id SET DEFAULT nextval('competition.circuits_id_seq'::regclass);


--
-- Name: countries id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.countries ALTER COLUMN id SET DEFAULT nextval('competition.countries_id_seq'::regclass);


--
-- Name: driver_entries id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries ALTER COLUMN id SET DEFAULT nextval('competition.driver_entries_id_seq'::regclass);


--
-- Name: drivers id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.drivers ALTER COLUMN id SET DEFAULT nextval('competition.drivers_id_seq'::regclass);


--
-- Name: engines id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.engines ALTER COLUMN id SET DEFAULT nextval('competition.engines_id_seq'::regclass);


--
-- Name: event_sessions id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.event_sessions ALTER COLUMN id SET DEFAULT nextval('competition.event_sessions_id_seq'::regclass);


--
-- Name: race_events id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.race_events ALTER COLUMN id SET DEFAULT nextval('competition.race_events_id_seq'::regclass);


--
-- Name: seasons id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.seasons ALTER COLUMN id SET DEFAULT nextval('competition.seasons_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.teams ALTER COLUMN id SET DEFAULT nextval('competition.teams_id_seq'::regclass);


--
-- Name: testing_events id; Type: DEFAULT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.testing_events ALTER COLUMN id SET DEFAULT nextval('competition.testing_events_id_seq'::regclass);


--
-- Name: powerup_assignments id; Type: DEFAULT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments ALTER COLUMN id SET DEFAULT nextval('powerups.powerup_assignments_id_seq'::regclass);


--
-- Name: powerup_restrictions id; Type: DEFAULT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_restrictions ALTER COLUMN id SET DEFAULT nextval('powerups.powerup_restrictions_id_seq'::regclass);


--
-- Name: powerup_use_targets id; Type: DEFAULT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets ALTER COLUMN id SET DEFAULT nextval('powerups.powerup_use_targets_id_seq'::regclass);


--
-- Name: powerup_uses id; Type: DEFAULT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses ALTER COLUMN id SET DEFAULT nextval('powerups.powerup_uses_id_seq'::regclass);


--
-- Name: powerups id; Type: DEFAULT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerups ALTER COLUMN id SET DEFAULT nextval('powerups.powerups_id_seq'::regclass);


--
-- Name: official_results id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.official_results ALTER COLUMN id SET DEFAULT nextval('scoring.official_results_id_seq'::regclass);


--
-- Name: result_publications id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.result_publications ALTER COLUMN id SET DEFAULT nextval('scoring.result_publications_id_seq'::regclass);


--
-- Name: score_components id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_components ALTER COLUMN id SET DEFAULT nextval('scoring.score_components_id_seq'::regclass);


--
-- Name: score_season_aggregates id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_season_aggregates ALTER COLUMN id SET DEFAULT nextval('scoring.score_season_aggregates_id_seq'::regclass);


--
-- Name: score_session_components id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_session_components ALTER COLUMN id SET DEFAULT nextval('scoring.score_session_components_id_seq'::regclass);


--
-- Name: score_sessions id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions ALTER COLUMN id SET DEFAULT nextval('scoring.score_sessions_id_seq'::regclass);


--
-- Name: scores id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.scores ALTER COLUMN id SET DEFAULT nextval('scoring.scores_id_seq'::regclass);


--
-- Name: team_event_aggregates id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_event_aggregates ALTER COLUMN id SET DEFAULT nextval('scoring.team_event_aggregates_id_seq'::regclass);


--
-- Name: team_season_aggregates id; Type: DEFAULT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_season_aggregates ALTER COLUMN id SET DEFAULT nextval('scoring.team_season_aggregates_id_seq'::regclass);


--
-- Name: group_memberships id; Type: DEFAULT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.group_memberships ALTER COLUMN id SET DEFAULT nextval('social.group_memberships_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.groups ALTER COLUMN id SET DEFAULT nextval('social.groups_id_seq'::regclass);


--
-- Name: team_memberships id; Type: DEFAULT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.team_memberships ALTER COLUMN id SET DEFAULT nextval('social.team_memberships_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.teams ALTER COLUMN id SET DEFAULT nextval('social.teams_id_seq'::regclass);


--
-- Name: permissions permissions_code_key; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.permissions
    ADD CONSTRAINT permissions_code_key UNIQUE (code);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (permission_id, role_id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: users uq_users_username; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT uq_users_username UNIQUE (username);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: bet_contexts bet_contexts_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts
    ADD CONSTRAINT bet_contexts_pkey PRIMARY KEY (id);


--
-- Name: bet_exceptions bet_exceptions_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_exceptions
    ADD CONSTRAINT bet_exceptions_pkey PRIMARY KEY (id);


--
-- Name: bet_picks bet_picks_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks
    ADD CONSTRAINT bet_picks_pkey PRIMARY KEY (id);


--
-- Name: bet_scores bet_scores_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_scores
    ADD CONSTRAINT bet_scores_pkey PRIMARY KEY (id);


--
-- Name: bet_template_items bet_template_items_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items
    ADD CONSTRAINT bet_template_items_pkey PRIMARY KEY (id);


--
-- Name: bet_templates bet_templates_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_templates
    ADD CONSTRAINT bet_templates_pkey PRIMARY KEY (id);


--
-- Name: bets bets_pkey; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bets
    ADD CONSTRAINT bets_pkey PRIMARY KEY (id);


--
-- Name: bet_picks uq_bet_picks_bet_score; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks
    ADD CONSTRAINT uq_bet_picks_bet_score UNIQUE (bet_id, bet_score_id);


--
-- Name: bet_template_items uq_template_bet_score; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items
    ADD CONSTRAINT uq_template_bet_score UNIQUE (template_id, bet_score_id);


--
-- Name: bet_template_items uq_template_display_order; Type: CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items
    ADD CONSTRAINT uq_template_display_order UNIQUE (template_id, display_order);


--
-- Name: circuits circuits_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.circuits
    ADD CONSTRAINT circuits_pkey PRIMARY KEY (id);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (id);


--
-- Name: driver_entries driver_entries_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_pkey PRIMARY KEY (id);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (id);


--
-- Name: engines engines_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.engines
    ADD CONSTRAINT engines_pkey PRIMARY KEY (id);


--
-- Name: event_sessions event_sessions_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.event_sessions
    ADD CONSTRAINT event_sessions_pkey PRIMARY KEY (id);


--
-- Name: driver_entries excl_driver_entries_season_team_seat_time_overlap; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT excl_driver_entries_season_team_seat_time_overlap EXCLUDE USING gist (season_id WITH =, team_id WITH =, seat_index WITH =, tstzrange(active_from, active_to, '[)'::text) WITH &&) WHERE (((race_event_id IS NULL) AND (event_session_id IS NULL)));


--
-- Name: race_events race_events_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.race_events
    ADD CONSTRAINT race_events_pkey PRIMARY KEY (id);


--
-- Name: season_drivers season_drivers_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_drivers
    ADD CONSTRAINT season_drivers_pkey PRIMARY KEY (season_id, driver_id);


--
-- Name: season_engines season_engines_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_engines
    ADD CONSTRAINT season_engines_pkey PRIMARY KEY (season_id, engine_id);


--
-- Name: season_teams season_teams_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_teams
    ADD CONSTRAINT season_teams_pkey PRIMARY KEY (season_id, team_id);


--
-- Name: seasons seasons_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.seasons
    ADD CONSTRAINT seasons_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: testing_events testing_events_pkey; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.testing_events
    ADD CONSTRAINT testing_events_pkey PRIMARY KEY (id);


--
-- Name: event_sessions uq_event_sessions_race_event_session_type; Type: CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.event_sessions
    ADD CONSTRAINT uq_event_sessions_race_event_session_type UNIQUE (race_event_id, session_type);


--
-- Name: powerup_assignments powerup_assignments_pkey; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_pkey PRIMARY KEY (id);


--
-- Name: powerup_restrictions powerup_restrictions_pkey; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_restrictions
    ADD CONSTRAINT powerup_restrictions_pkey PRIMARY KEY (id);


--
-- Name: powerup_use_targets powerup_use_targets_pkey; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets
    ADD CONSTRAINT powerup_use_targets_pkey PRIMARY KEY (id);


--
-- Name: powerup_uses powerup_uses_pkey; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_pkey PRIMARY KEY (id);


--
-- Name: powerups powerups_pkey; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerups
    ADD CONSTRAINT powerups_pkey PRIMARY KEY (id);


--
-- Name: powerups uq_powerups_code; Type: CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerups
    ADD CONSTRAINT uq_powerups_code UNIQUE (code);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: official_results official_results_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.official_results
    ADD CONSTRAINT official_results_pkey PRIMARY KEY (id);


--
-- Name: result_publications result_publications_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.result_publications
    ADD CONSTRAINT result_publications_pkey PRIMARY KEY (id);


--
-- Name: score_components score_components_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_components
    ADD CONSTRAINT score_components_pkey PRIMARY KEY (id);


--
-- Name: score_season_aggregates score_season_aggregates_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_season_aggregates
    ADD CONSTRAINT score_season_aggregates_pkey PRIMARY KEY (id);


--
-- Name: score_session_components score_session_components_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_session_components
    ADD CONSTRAINT score_session_components_pkey PRIMARY KEY (id);


--
-- Name: score_sessions score_sessions_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions
    ADD CONSTRAINT score_sessions_pkey PRIMARY KEY (id);


--
-- Name: scores scores_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.scores
    ADD CONSTRAINT scores_pkey PRIMARY KEY (id);


--
-- Name: team_event_aggregates team_event_aggregates_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_event_aggregates
    ADD CONSTRAINT team_event_aggregates_pkey PRIMARY KEY (id);


--
-- Name: team_season_aggregates team_season_aggregates_pkey; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_season_aggregates
    ADD CONSTRAINT team_season_aggregates_pkey PRIMARY KEY (id);


--
-- Name: score_components uq_score_components_score_type_code; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_components
    ADD CONSTRAINT uq_score_components_score_type_code UNIQUE (score_id, component_type, code);


--
-- Name: score_session_components uq_score_sess_components_sess_type_code; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_session_components
    ADD CONSTRAINT uq_score_sess_components_sess_type_code UNIQUE (score_session_id, component_type, code);


--
-- Name: score_sessions uq_score_sessions_user_ctx_session; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions
    ADD CONSTRAINT uq_score_sessions_user_ctx_session UNIQUE (user_id, bet_context_id, event_session_id);


--
-- Name: scores uq_scores_user_context; Type: CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.scores
    ADD CONSTRAINT uq_scores_user_context UNIQUE (user_id, bet_context_id);


--
-- Name: group_memberships group_memberships_pkey; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.group_memberships
    ADD CONSTRAINT group_memberships_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: team_memberships team_memberships_pkey; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.team_memberships
    ADD CONSTRAINT team_memberships_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: group_memberships uq_group_memberships_group_user; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.group_memberships
    ADD CONSTRAINT uq_group_memberships_group_user UNIQUE (group_id, user_id);


--
-- Name: groups uq_groups_name; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.groups
    ADD CONSTRAINT uq_groups_name UNIQUE (name);


--
-- Name: team_memberships uq_team_memberships_team_user; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.team_memberships
    ADD CONSTRAINT uq_team_memberships_team_user UNIQUE (team_id, user_id);


--
-- Name: teams uq_teams_group_name; Type: CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.teams
    ADD CONSTRAINT uq_teams_group_name UNIQUE (group_id, name);


--
-- Name: ix_role_permissions_permission_id; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_role_permissions_permission_id ON auth.role_permissions USING btree (permission_id);


--
-- Name: ix_role_permissions_role_id; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_role_permissions_role_id ON auth.role_permissions USING btree (role_id);


--
-- Name: ix_user_roles_role_id; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_user_roles_role_id ON auth.user_roles USING btree (role_id);


--
-- Name: ix_user_roles_user_id; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_user_roles_user_id ON auth.user_roles USING btree (user_id);


--
-- Name: ix_users_auth_provider; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_users_auth_provider ON auth.users USING btree (auth_provider);


--
-- Name: ix_users_created_at; Type: INDEX; Schema: auth; Owner: postgres
--

CREATE INDEX ix_users_created_at ON auth.users USING btree (created_at);


--
-- Name: ix_bet_contexts_group_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_contexts_group_id ON betting.bet_contexts USING btree (group_id);


--
-- Name: ix_bet_contexts_group_season_kind; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_contexts_group_season_kind ON betting.bet_contexts USING btree (group_id, season_id, kind);


--
-- Name: ix_bet_contexts_kind; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_contexts_kind ON betting.bet_contexts USING btree (kind);


--
-- Name: ix_bet_contexts_season_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_contexts_season_id ON betting.bet_contexts USING btree (season_id);


--
-- Name: ix_bet_exceptions_context_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_exceptions_context_id ON betting.bet_exceptions USING btree (bet_context_id);


--
-- Name: ix_bet_exceptions_score_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_exceptions_score_id ON betting.bet_exceptions USING btree (bet_score_id);


--
-- Name: ix_bet_exceptions_session_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_exceptions_session_id ON betting.bet_exceptions USING btree (event_session_id);


--
-- Name: ix_bet_picks_bet_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_picks_bet_id ON betting.bet_picks USING btree (bet_id);


--
-- Name: ix_bet_picks_invalid; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_picks_invalid ON betting.bet_picks USING btree (bet_id) WHERE (is_invalid = true);


--
-- Name: ix_bet_picks_invalidated_by; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_picks_invalidated_by ON betting.bet_picks USING btree (invalidated_by_user_id);


--
-- Name: ix_bet_picks_score_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_picks_score_id ON betting.bet_picks USING btree (bet_score_id);


--
-- Name: ix_bet_scores_value_type; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_scores_value_type ON betting.bet_scores USING btree (value_type);


--
-- Name: ix_bet_templates_season_kind; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bet_templates_season_kind ON betting.bet_templates USING btree (season_id, context_kind);


--
-- Name: ix_bets_context_ranking; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bets_context_ranking ON betting.bets USING btree (bet_context_id, last_modified_at, id) WHERE (submitted_at IS NOT NULL);


--
-- Name: ix_bets_ctx_session_ranking; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bets_ctx_session_ranking ON betting.bets USING btree (bet_context_id, event_session_id, last_modified_at, id) WHERE (submitted_at IS NOT NULL);


--
-- Name: ix_bets_user_context; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_bets_user_context ON betting.bets USING btree (user_id, bet_context_id);


--
-- Name: ix_template_items_bet_score_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_template_items_bet_score_id ON betting.bet_template_items USING btree (bet_score_id);


--
-- Name: ix_template_items_template_id; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE INDEX ix_template_items_template_id ON betting.bet_template_items USING btree (template_id);


--
-- Name: uq_bet_contexts_group_race_event; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_contexts_group_race_event ON betting.bet_contexts USING btree (group_id, race_event_id) WHERE (race_event_id IS NOT NULL);


--
-- Name: uq_bet_contexts_group_season; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_contexts_group_season ON betting.bet_contexts USING btree (group_id, season_id) WHERE (kind = 'SEASON'::betting.bet_context_kind_enum);


--
-- Name: uq_bet_contexts_group_testing_event; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_contexts_group_testing_event ON betting.bet_contexts USING btree (group_id, testing_event_id) WHERE (testing_event_id IS NOT NULL);


--
-- Name: uq_bet_exceptions_context_score_nosession; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_exceptions_context_score_nosession ON betting.bet_exceptions USING btree (bet_context_id, bet_score_id) WHERE (event_session_id IS NULL);


--
-- Name: uq_bet_exceptions_context_session_score; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_exceptions_context_session_score ON betting.bet_exceptions USING btree (bet_context_id, event_session_id, bet_score_id) WHERE (event_session_id IS NOT NULL);


--
-- Name: uq_bet_scores_code; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_scores_code ON betting.bet_scores USING btree (code);


--
-- Name: uq_bet_templates_gp_event; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_templates_gp_event ON betting.bet_templates USING btree (season_id, context_kind, scope) WHERE ((context_kind = 'GP'::betting.bet_context_kind_enum) AND (scope = 'EVENT'::betting.bet_template_scope_enum));


--
-- Name: uq_bet_templates_gp_session; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_templates_gp_session ON betting.bet_templates USING btree (season_id, context_kind, scope, session_type) WHERE ((context_kind = 'GP'::betting.bet_context_kind_enum) AND (scope = 'SESSION'::betting.bet_template_scope_enum));


--
-- Name: uq_bet_templates_non_gp; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bet_templates_non_gp ON betting.bet_templates USING btree (season_id, context_kind) WHERE (context_kind <> 'GP'::betting.bet_context_kind_enum);


--
-- Name: uq_bets_user_ctx_session_notnull; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bets_user_ctx_session_notnull ON betting.bets USING btree (user_id, bet_context_id, event_session_id) WHERE (event_session_id IS NOT NULL);


--
-- Name: uq_bets_user_ctx_session_null; Type: INDEX; Schema: betting; Owner: postgres
--

CREATE UNIQUE INDEX uq_bets_user_ctx_session_null ON betting.bets USING btree (user_id, bet_context_id) WHERE (event_session_id IS NULL);


--
-- Name: ix_competition_drivers_code; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX ix_competition_drivers_code ON competition.drivers USING btree (code);


--
-- Name: ix_competition_engines_code; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX ix_competition_engines_code ON competition.engines USING btree (code);


--
-- Name: ix_competition_race_events_season_id; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE INDEX ix_competition_race_events_season_id ON competition.race_events USING btree (season_id);


--
-- Name: ix_competition_seasons_year; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX ix_competition_seasons_year ON competition.seasons USING btree (year);


--
-- Name: ix_competition_teams_code; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX ix_competition_teams_code ON competition.teams USING btree (code);


--
-- Name: ix_competition_testing_events_season_id; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE INDEX ix_competition_testing_events_season_id ON competition.testing_events USING btree (season_id);


--
-- Name: ix_driver_entries_season_level_window; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE INDEX ix_driver_entries_season_level_window ON competition.driver_entries USING btree (season_id, team_id, seat_index, active_from, active_to);


--
-- Name: ix_driver_entries_season_team_seat; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE INDEX ix_driver_entries_season_team_seat ON competition.driver_entries USING btree (season_id, team_id, seat_index);


--
-- Name: ix_event_sessions_race_event_id; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE INDEX ix_event_sessions_race_event_id ON competition.event_sessions USING btree (race_event_id);


--
-- Name: uq_driver_entries_gp_season_event_team_seat; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX uq_driver_entries_gp_season_event_team_seat ON competition.driver_entries USING btree (season_id, race_event_id, team_id, seat_index) WHERE ((race_event_id IS NOT NULL) AND (event_session_id IS NULL));


--
-- Name: uq_driver_entries_session_season_session_team_seat; Type: INDEX; Schema: competition; Owner: postgres
--

CREATE UNIQUE INDEX uq_driver_entries_session_season_session_team_seat ON competition.driver_entries USING btree (season_id, event_session_id, team_id, seat_index) WHERE (event_session_id IS NOT NULL);


--
-- Name: ix_powerup_assignments_bet_context_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_bet_context_id ON powerups.powerup_assignments USING btree (bet_context_id);


--
-- Name: ix_powerup_assignments_group_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_group_id ON powerups.powerup_assignments USING btree (group_id);


--
-- Name: ix_powerup_assignments_group_user; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_group_user ON powerups.powerup_assignments USING btree (group_id, user_id);


--
-- Name: ix_powerup_assignments_powerup_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_powerup_id ON powerups.powerup_assignments USING btree (powerup_id);


--
-- Name: ix_powerup_assignments_season_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_season_id ON powerups.powerup_assignments USING btree (season_id);


--
-- Name: ix_powerup_assignments_user_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_assignments_user_id ON powerups.powerup_assignments USING btree (user_id);


--
-- Name: ix_powerup_restrictions_ctx_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_restrictions_ctx_id ON powerups.powerup_restrictions USING btree (bet_context_id);


--
-- Name: ix_powerup_restrictions_is_disabled; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_restrictions_is_disabled ON powerups.powerup_restrictions USING btree (is_disabled);


--
-- Name: ix_powerup_restrictions_powerup_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_restrictions_powerup_id ON powerups.powerup_restrictions USING btree (powerup_id);


--
-- Name: ix_powerup_restrictions_session_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_restrictions_session_id ON powerups.powerup_restrictions USING btree (event_session_id);


--
-- Name: ix_powerup_uses_bet_context_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_uses_bet_context_id ON powerups.powerup_uses USING btree (bet_context_id);


--
-- Name: ix_powerup_uses_event_session_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_uses_event_session_id ON powerups.powerup_uses USING btree (event_session_id);


--
-- Name: ix_powerup_uses_group_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_uses_group_id ON powerups.powerup_uses USING btree (group_id);


--
-- Name: ix_powerup_uses_powerup_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_uses_powerup_id ON powerups.powerup_uses USING btree (powerup_id);


--
-- Name: ix_powerup_uses_user_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerup_uses_user_id ON powerups.powerup_uses USING btree (user_id);


--
-- Name: ix_powerups_is_enabled; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_powerups_is_enabled ON powerups.powerups USING btree (is_enabled);


--
-- Name: ix_put_powerup_use_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_put_powerup_use_id ON powerups.powerup_use_targets USING btree (powerup_use_id);


--
-- Name: ix_put_target_group_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_put_target_group_id ON powerups.powerup_use_targets USING btree (target_group_id);


--
-- Name: ix_put_target_team_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_put_target_team_id ON powerups.powerup_use_targets USING btree (target_team_id);


--
-- Name: ix_put_target_type; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_put_target_type ON powerups.powerup_use_targets USING btree (target_type);


--
-- Name: ix_put_target_user_id; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE INDEX ix_put_target_user_id ON powerups.powerup_use_targets USING btree (target_user_id);


--
-- Name: uq_powerup_assignments_event; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE UNIQUE INDEX uq_powerup_assignments_event ON powerups.powerup_assignments USING btree (group_id, user_id, bet_context_id, powerup_id) WHERE (bet_context_id IS NOT NULL);


--
-- Name: uq_powerup_assignments_season; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE UNIQUE INDEX uq_powerup_assignments_season ON powerups.powerup_assignments USING btree (group_id, user_id, season_id, powerup_id) WHERE (bet_context_id IS NULL);


--
-- Name: uq_powerup_restrictions_ctx_nosession; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE UNIQUE INDEX uq_powerup_restrictions_ctx_nosession ON powerups.powerup_restrictions USING btree (powerup_id, bet_context_id) WHERE (event_session_id IS NULL);


--
-- Name: uq_powerup_restrictions_ctx_session; Type: INDEX; Schema: powerups; Owner: postgres
--

CREATE UNIQUE INDEX uq_powerup_restrictions_ctx_session ON powerups.powerup_restrictions USING btree (powerup_id, bet_context_id, event_session_id) WHERE (event_session_id IS NOT NULL);


--
-- Name: ix_official_results_ctx; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_official_results_ctx ON scoring.official_results USING btree (bet_context_id);


--
-- Name: ix_official_results_score; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_official_results_score ON scoring.official_results USING btree (bet_score_id);


--
-- Name: ix_official_results_session; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_official_results_session ON scoring.official_results USING btree (event_session_id);


--
-- Name: ix_result_publications_ctx; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_result_publications_ctx ON scoring.result_publications USING btree (bet_context_id);


--
-- Name: ix_result_publications_published_at; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_result_publications_published_at ON scoring.result_publications USING btree (published_at);


--
-- Name: ix_result_publications_published_by; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_result_publications_published_by ON scoring.result_publications USING btree (published_by_user_id);


--
-- Name: ix_result_publications_session; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_result_publications_session ON scoring.result_publications USING btree (event_session_id);


--
-- Name: ix_score_components_score_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_components_score_id ON scoring.score_components USING btree (score_id);


--
-- Name: ix_score_components_score_type; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_components_score_type ON scoring.score_components USING btree (score_id, component_type);


--
-- Name: ix_score_components_type; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_components_type ON scoring.score_components USING btree (component_type);


--
-- Name: ix_score_season_agg_group_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_season_agg_group_id ON scoring.score_season_aggregates USING btree (group_id);


--
-- Name: ix_score_season_agg_group_season_rank; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_season_agg_group_season_rank ON scoring.score_season_aggregates USING btree (group_id, season_id, total_points, computed_at);


--
-- Name: ix_score_season_agg_group_user; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_season_agg_group_user ON scoring.score_season_aggregates USING btree (group_id, user_id);


--
-- Name: ix_score_season_agg_season_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_season_agg_season_id ON scoring.score_season_aggregates USING btree (season_id);


--
-- Name: ix_score_season_agg_user_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_season_agg_user_id ON scoring.score_season_aggregates USING btree (user_id);


--
-- Name: ix_score_sess_components_sess_type; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_sess_components_sess_type ON scoring.score_session_components USING btree (score_session_id, component_type);


--
-- Name: ix_score_sess_components_session_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_sess_components_session_id ON scoring.score_session_components USING btree (score_session_id);


--
-- Name: ix_score_sess_components_type; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_sess_components_type ON scoring.score_session_components USING btree (component_type);


--
-- Name: ix_score_sessions_ctx_session_total; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_sessions_ctx_session_total ON scoring.score_sessions USING btree (bet_context_id, event_session_id, total_points);


--
-- Name: ix_score_sessions_user_ctx; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_score_sessions_user_ctx ON scoring.score_sessions USING btree (user_id, bet_context_id);


--
-- Name: ix_scores_bet_context_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_scores_bet_context_id ON scoring.scores USING btree (bet_context_id);


--
-- Name: ix_scores_context_ranking; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_scores_context_ranking ON scoring.scores USING btree (bet_context_id, total_points, computed_at);


--
-- Name: ix_scores_user_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_scores_user_id ON scoring.scores USING btree (user_id);


--
-- Name: ix_team_event_agg_ctx_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_event_agg_ctx_id ON scoring.team_event_aggregates USING btree (bet_context_id);


--
-- Name: ix_team_event_agg_group_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_event_agg_group_id ON scoring.team_event_aggregates USING btree (group_id);


--
-- Name: ix_team_event_agg_group_team; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_event_agg_group_team ON scoring.team_event_aggregates USING btree (group_id, team_id);


--
-- Name: ix_team_event_agg_rank; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_event_agg_rank ON scoring.team_event_aggregates USING btree (group_id, bet_context_id, total_points, computed_at);


--
-- Name: ix_team_event_agg_team_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_event_agg_team_id ON scoring.team_event_aggregates USING btree (team_id);


--
-- Name: ix_team_season_agg_group_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_season_agg_group_id ON scoring.team_season_aggregates USING btree (group_id);


--
-- Name: ix_team_season_agg_rank; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_season_agg_rank ON scoring.team_season_aggregates USING btree (group_id, season_id, total_points, computed_at);


--
-- Name: ix_team_season_agg_season_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_season_agg_season_id ON scoring.team_season_aggregates USING btree (season_id);


--
-- Name: ix_team_season_agg_team_id; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE INDEX ix_team_season_agg_team_id ON scoring.team_season_aggregates USING btree (team_id);


--
-- Name: uq_official_results_ctx_score_nosession; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_official_results_ctx_score_nosession ON scoring.official_results USING btree (bet_context_id, bet_score_id) WHERE (event_session_id IS NULL);


--
-- Name: uq_official_results_ctx_session_score; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_official_results_ctx_session_score ON scoring.official_results USING btree (bet_context_id, event_session_id, bet_score_id) WHERE (event_session_id IS NOT NULL);


--
-- Name: uq_result_publications_ctx_nosession; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_result_publications_ctx_nosession ON scoring.result_publications USING btree (bet_context_id) WHERE (event_session_id IS NULL);


--
-- Name: uq_result_publications_ctx_session; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_result_publications_ctx_session ON scoring.result_publications USING btree (bet_context_id, event_session_id) WHERE (event_session_id IS NOT NULL);


--
-- Name: uq_score_season_agg_group_user_season; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_score_season_agg_group_user_season ON scoring.score_season_aggregates USING btree (group_id, user_id, season_id);


--
-- Name: uq_team_event_agg_group_team_ctx; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_team_event_agg_group_team_ctx ON scoring.team_event_aggregates USING btree (group_id, team_id, bet_context_id);


--
-- Name: uq_team_season_agg_group_team_season; Type: INDEX; Schema: scoring; Owner: postgres
--

CREATE UNIQUE INDEX uq_team_season_agg_group_team_season ON scoring.team_season_aggregates USING btree (group_id, team_id, season_id);


--
-- Name: ix_group_memberships_group_id; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_group_memberships_group_id ON social.group_memberships USING btree (group_id);


--
-- Name: ix_group_memberships_group_role; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_group_memberships_group_role ON social.group_memberships USING btree (group_id, role);


--
-- Name: ix_group_memberships_user_id; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_group_memberships_user_id ON social.group_memberships USING btree (user_id);


--
-- Name: ix_groups_join_code; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_groups_join_code ON social.groups USING btree (join_code);


--
-- Name: ix_team_memberships_team_id; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_team_memberships_team_id ON social.team_memberships USING btree (team_id);


--
-- Name: ix_team_memberships_user_id; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_team_memberships_user_id ON social.team_memberships USING btree (user_id);


--
-- Name: ix_teams_group_id; Type: INDEX; Schema: social; Owner: postgres
--

CREATE INDEX ix_teams_group_id ON social.teams USING btree (group_id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES auth.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES auth.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES auth.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: postgres
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: bet_contexts bet_contexts_group_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts
    ADD CONSTRAINT bet_contexts_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: bet_contexts bet_contexts_race_event_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts
    ADD CONSTRAINT bet_contexts_race_event_id_fkey FOREIGN KEY (race_event_id) REFERENCES competition.race_events(id) ON DELETE RESTRICT;


--
-- Name: bet_contexts bet_contexts_season_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts
    ADD CONSTRAINT bet_contexts_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: bet_contexts bet_contexts_testing_event_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_contexts
    ADD CONSTRAINT bet_contexts_testing_event_id_fkey FOREIGN KEY (testing_event_id) REFERENCES competition.testing_events(id) ON DELETE RESTRICT;


--
-- Name: bet_exceptions bet_exceptions_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_exceptions
    ADD CONSTRAINT bet_exceptions_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE RESTRICT;


--
-- Name: bet_exceptions bet_exceptions_bet_score_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_exceptions
    ADD CONSTRAINT bet_exceptions_bet_score_id_fkey FOREIGN KEY (bet_score_id) REFERENCES betting.bet_scores(id) ON DELETE RESTRICT;


--
-- Name: bet_exceptions bet_exceptions_event_session_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_exceptions
    ADD CONSTRAINT bet_exceptions_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: bet_picks bet_picks_bet_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks
    ADD CONSTRAINT bet_picks_bet_id_fkey FOREIGN KEY (bet_id) REFERENCES betting.bets(id) ON DELETE CASCADE;


--
-- Name: bet_picks bet_picks_bet_score_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks
    ADD CONSTRAINT bet_picks_bet_score_id_fkey FOREIGN KEY (bet_score_id) REFERENCES betting.bet_scores(id) ON DELETE CASCADE;


--
-- Name: bet_picks bet_picks_invalidated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_picks
    ADD CONSTRAINT bet_picks_invalidated_by_user_id_fkey FOREIGN KEY (invalidated_by_user_id) REFERENCES auth.users(id) ON DELETE SET NULL;


--
-- Name: bet_template_items bet_template_items_bet_score_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items
    ADD CONSTRAINT bet_template_items_bet_score_id_fkey FOREIGN KEY (bet_score_id) REFERENCES betting.bet_scores(id) ON DELETE RESTRICT;


--
-- Name: bet_template_items bet_template_items_template_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_template_items
    ADD CONSTRAINT bet_template_items_template_id_fkey FOREIGN KEY (template_id) REFERENCES betting.bet_templates(id) ON DELETE CASCADE;


--
-- Name: bet_templates bet_templates_season_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bet_templates
    ADD CONSTRAINT bet_templates_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: bets bets_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bets
    ADD CONSTRAINT bets_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE RESTRICT;


--
-- Name: bets bets_event_session_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bets
    ADD CONSTRAINT bets_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: bets bets_user_id_fkey; Type: FK CONSTRAINT; Schema: betting; Owner: postgres
--

ALTER TABLE ONLY betting.bets
    ADD CONSTRAINT bets_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: circuits circuits_country_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.circuits
    ADD CONSTRAINT circuits_country_id_fkey FOREIGN KEY (country_id) REFERENCES competition.countries(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_driver_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES competition.drivers(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_engine_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_engine_id_fkey FOREIGN KEY (engine_id) REFERENCES competition.engines(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_event_session_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_race_event_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_race_event_id_fkey FOREIGN KEY (race_event_id) REFERENCES competition.race_events(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: driver_entries driver_entries_team_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.driver_entries
    ADD CONSTRAINT driver_entries_team_id_fkey FOREIGN KEY (team_id) REFERENCES competition.teams(id) ON DELETE RESTRICT;


--
-- Name: event_sessions event_sessions_race_event_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.event_sessions
    ADD CONSTRAINT event_sessions_race_event_id_fkey FOREIGN KEY (race_event_id) REFERENCES competition.race_events(id) ON DELETE CASCADE;


--
-- Name: race_events race_events_circuit_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.race_events
    ADD CONSTRAINT race_events_circuit_id_fkey FOREIGN KEY (circuit_id) REFERENCES competition.circuits(id) ON DELETE RESTRICT;


--
-- Name: race_events race_events_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.race_events
    ADD CONSTRAINT race_events_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: season_drivers season_drivers_driver_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_drivers
    ADD CONSTRAINT season_drivers_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES competition.drivers(id) ON DELETE RESTRICT;


--
-- Name: season_drivers season_drivers_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_drivers
    ADD CONSTRAINT season_drivers_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: season_engines season_engines_engine_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_engines
    ADD CONSTRAINT season_engines_engine_id_fkey FOREIGN KEY (engine_id) REFERENCES competition.engines(id) ON DELETE RESTRICT;


--
-- Name: season_engines season_engines_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_engines
    ADD CONSTRAINT season_engines_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: season_teams season_teams_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_teams
    ADD CONSTRAINT season_teams_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: season_teams season_teams_team_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.season_teams
    ADD CONSTRAINT season_teams_team_id_fkey FOREIGN KEY (team_id) REFERENCES competition.teams(id) ON DELETE RESTRICT;


--
-- Name: testing_events testing_events_circuit_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.testing_events
    ADD CONSTRAINT testing_events_circuit_id_fkey FOREIGN KEY (circuit_id) REFERENCES competition.circuits(id) ON DELETE RESTRICT;


--
-- Name: testing_events testing_events_season_id_fkey; Type: FK CONSTRAINT; Schema: competition; Owner: postgres
--

ALTER TABLE ONLY competition.testing_events
    ADD CONSTRAINT testing_events_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: powerup_assignments powerup_assignments_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: powerup_assignments powerup_assignments_group_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: powerup_assignments powerup_assignments_powerup_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_powerup_id_fkey FOREIGN KEY (powerup_id) REFERENCES powerups.powerups(id) ON DELETE RESTRICT;


--
-- Name: powerup_assignments powerup_assignments_season_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE CASCADE;


--
-- Name: powerup_assignments powerup_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_assignments
    ADD CONSTRAINT powerup_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: powerup_restrictions powerup_restrictions_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_restrictions
    ADD CONSTRAINT powerup_restrictions_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: powerup_restrictions powerup_restrictions_event_session_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_restrictions
    ADD CONSTRAINT powerup_restrictions_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE CASCADE;


--
-- Name: powerup_restrictions powerup_restrictions_powerup_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_restrictions
    ADD CONSTRAINT powerup_restrictions_powerup_id_fkey FOREIGN KEY (powerup_id) REFERENCES powerups.powerups(id) ON DELETE CASCADE;


--
-- Name: powerup_use_targets powerup_use_targets_powerup_use_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets
    ADD CONSTRAINT powerup_use_targets_powerup_use_id_fkey FOREIGN KEY (powerup_use_id) REFERENCES powerups.powerup_uses(id) ON DELETE CASCADE;


--
-- Name: powerup_use_targets powerup_use_targets_target_group_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets
    ADD CONSTRAINT powerup_use_targets_target_group_id_fkey FOREIGN KEY (target_group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: powerup_use_targets powerup_use_targets_target_team_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets
    ADD CONSTRAINT powerup_use_targets_target_team_id_fkey FOREIGN KEY (target_team_id) REFERENCES social.teams(id) ON DELETE CASCADE;


--
-- Name: powerup_use_targets powerup_use_targets_target_user_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_use_targets
    ADD CONSTRAINT powerup_use_targets_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: powerup_uses powerup_uses_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: powerup_uses powerup_uses_event_session_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE CASCADE;


--
-- Name: powerup_uses powerup_uses_group_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: powerup_uses powerup_uses_powerup_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_powerup_id_fkey FOREIGN KEY (powerup_id) REFERENCES powerups.powerups(id) ON DELETE RESTRICT;


--
-- Name: powerup_uses powerup_uses_user_id_fkey; Type: FK CONSTRAINT; Schema: powerups; Owner: postgres
--

ALTER TABLE ONLY powerups.powerup_uses
    ADD CONSTRAINT powerup_uses_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: official_results official_results_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.official_results
    ADD CONSTRAINT official_results_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: official_results official_results_bet_score_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.official_results
    ADD CONSTRAINT official_results_bet_score_id_fkey FOREIGN KEY (bet_score_id) REFERENCES betting.bet_scores(id) ON DELETE RESTRICT;


--
-- Name: official_results official_results_event_session_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.official_results
    ADD CONSTRAINT official_results_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: result_publications result_publications_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.result_publications
    ADD CONSTRAINT result_publications_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: result_publications result_publications_event_session_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.result_publications
    ADD CONSTRAINT result_publications_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: result_publications result_publications_published_by_user_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.result_publications
    ADD CONSTRAINT result_publications_published_by_user_id_fkey FOREIGN KEY (published_by_user_id) REFERENCES auth.users(id) ON DELETE SET NULL;


--
-- Name: score_components score_components_score_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_components
    ADD CONSTRAINT score_components_score_id_fkey FOREIGN KEY (score_id) REFERENCES scoring.scores(id) ON DELETE CASCADE;


--
-- Name: score_season_aggregates score_season_aggregates_group_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_season_aggregates
    ADD CONSTRAINT score_season_aggregates_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: score_season_aggregates score_season_aggregates_season_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_season_aggregates
    ADD CONSTRAINT score_season_aggregates_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: score_season_aggregates score_season_aggregates_user_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_season_aggregates
    ADD CONSTRAINT score_season_aggregates_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: score_session_components score_session_components_score_session_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_session_components
    ADD CONSTRAINT score_session_components_score_session_id_fkey FOREIGN KEY (score_session_id) REFERENCES scoring.score_sessions(id) ON DELETE CASCADE;


--
-- Name: score_sessions score_sessions_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions
    ADD CONSTRAINT score_sessions_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE RESTRICT;


--
-- Name: score_sessions score_sessions_event_session_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions
    ADD CONSTRAINT score_sessions_event_session_id_fkey FOREIGN KEY (event_session_id) REFERENCES competition.event_sessions(id) ON DELETE RESTRICT;


--
-- Name: score_sessions score_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.score_sessions
    ADD CONSTRAINT score_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: scores scores_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.scores
    ADD CONSTRAINT scores_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE RESTRICT;


--
-- Name: scores scores_user_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.scores
    ADD CONSTRAINT scores_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: team_event_aggregates team_event_aggregates_bet_context_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_event_aggregates
    ADD CONSTRAINT team_event_aggregates_bet_context_id_fkey FOREIGN KEY (bet_context_id) REFERENCES betting.bet_contexts(id) ON DELETE CASCADE;


--
-- Name: team_event_aggregates team_event_aggregates_group_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_event_aggregates
    ADD CONSTRAINT team_event_aggregates_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: team_event_aggregates team_event_aggregates_team_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_event_aggregates
    ADD CONSTRAINT team_event_aggregates_team_id_fkey FOREIGN KEY (team_id) REFERENCES social.teams(id) ON DELETE CASCADE;


--
-- Name: team_season_aggregates team_season_aggregates_group_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_season_aggregates
    ADD CONSTRAINT team_season_aggregates_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: team_season_aggregates team_season_aggregates_season_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_season_aggregates
    ADD CONSTRAINT team_season_aggregates_season_id_fkey FOREIGN KEY (season_id) REFERENCES competition.seasons(id) ON DELETE RESTRICT;


--
-- Name: team_season_aggregates team_season_aggregates_team_id_fkey; Type: FK CONSTRAINT; Schema: scoring; Owner: postgres
--

ALTER TABLE ONLY scoring.team_season_aggregates
    ADD CONSTRAINT team_season_aggregates_team_id_fkey FOREIGN KEY (team_id) REFERENCES social.teams(id) ON DELETE CASCADE;


--
-- Name: group_memberships group_memberships_group_id_fkey; Type: FK CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.group_memberships
    ADD CONSTRAINT group_memberships_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- Name: group_memberships group_memberships_user_id_fkey; Type: FK CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.group_memberships
    ADD CONSTRAINT group_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: team_memberships team_memberships_team_id_fkey; Type: FK CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.team_memberships
    ADD CONSTRAINT team_memberships_team_id_fkey FOREIGN KEY (team_id) REFERENCES social.teams(id) ON DELETE CASCADE;


--
-- Name: team_memberships team_memberships_user_id_fkey; Type: FK CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.team_memberships
    ADD CONSTRAINT team_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: teams teams_group_id_fkey; Type: FK CONSTRAINT; Schema: social; Owner: postgres
--

ALTER TABLE ONLY social.teams
    ADD CONSTRAINT teams_group_id_fkey FOREIGN KEY (group_id) REFERENCES social.groups(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 0HQuk3F7O2p2FSV81mxBfX5bjKgmR2wQNHYah12smE1JfIE3eYo9lsuJiPTd0dh

