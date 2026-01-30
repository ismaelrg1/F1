from datetime import datetime
import os, sys, json

from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.models import Season, Bet, BetScore, SeasonBet, SeasonBetPick, RaceEvent, User
from backend.app.models.parameters_bets import BetTemplate
from backend.app.powerups.models import PowerupUsage
from config.db_config import db
from backend.app.utils.apiF1 import get_schedule
from backend.app.routes.api_bd import get_user_id
from sqlalchemy import text

bets_bp = Blueprint('bets', __name__)

# Significado de las sesiones por formato (para cierres por tipo)
SESSION_MEANINGS = {
    'conventional': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race'],
    'sprint': ['Practice 1', 'Qualifying', 'Practice 2', 'Sprint', 'Race'],
    'sprint_shootout': ['Practice 1', 'Qualifying', 'Sprint Shootout', 'Sprint', 'Race'],
    'sprint_qualifying': ['Practice 1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race'],
    'testing': ['Test', 'Test1', 'Test2', 'N/A', 'N/A']
}


# Helpers para comparar valores (reusados de la lógica de temporada)
def norm_str(x):
    return (str(x) if x is not None else "").strip().lower()

def to_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("true", "1", "si", "sí", "yes", "y")


@bets_bp.route('/apuestas')
@bets_bp.route('/apuestas-<int:season_year>')
@jwt_required(locations=["cookies"])
def apuestas(season_year=None):
    # Solicitar las carreras
    year = season_year if season_year else datetime.now().year

    # Obtener todas las temporadas disponibles en la BD
    seasons = Season.query.with_entities(Season.year).order_by(Season.year.desc()).all()
    seasons = [season.year for season in seasons]  # Extraer solo los años de las temporadas

    races = get_schedule(year)

    return render_template('bets_calendar.html', races=races, year=year, seasons=seasons)


@bets_bp.route('/apuestas-temporada-<int:season_year>')
@jwt_required(locations=["cookies"])
def apuestas_temporada(season_year):
    """
    Muestra todas las apuestas de temporada de todos los usuarios
    + (si existe) los resultados oficiales desde resultados/season_<year>.json
    """

    # 1) Temporada
    season = Season.query.filter_by(year=season_year).first_or_404()

    # 2) Cargar todas las apuestas + picks de esa temporada
    #    Usamos relaciones ORM: pick.user, pick.season_bet
    picks = (
        SeasonBetPick.query
        .join(SeasonBet, SeasonBet.id == SeasonBetPick.season_bet_id)
        .filter(SeasonBet.season_id == season.id, SeasonBet.is_active == True)
        .all()
    )

    # Estructura:
    # {
    #   "generales": { "usuario": { bet_key: {label, value, points} } },
    #   "duelos":    { "usuario": { bet_key: {label, value, points} } }
    # }
    season_bets_data = {
        "generales": {},
        "duelos": {}
    }

    for pick in picks:
        bet = pick.season_bet
        username = pick.user.username

        group = "duelos" if bet.bet_key.startswith("duel_") else "generales"

        if username not in season_bets_data[group]:
            season_bets_data[group][username] = {}

        season_bets_data[group][username][bet.bet_key] = {
            "label": bet.label,
            "value": pick.value,
            "points": bet.points
        }

    # 3) Intentar cargar resultados oficiales de temporada
    resultados = {}
    resultados_path = os.path.join("resultados", f"season_{season_year}.json")
    print(f"⚡ season resultados path: {resultados_path}", file=sys.stderr)
    if os.path.exists(resultados_path):
        try:
            with open(resultados_path, "r", encoding="utf-8") as f:
                resultados = json.load(f)
        except Exception as e:
            print(f"❌ Error leyendo {resultados_path}: {e}", file=sys.stderr)
    else:
        print(f"⚠ No existe archivo de resultados de temporada: {resultados_path}", file=sys.stderr)

    # 4) Calcular puntos por usuario (solo si hay resultados)
    user_points_data = {
        "generales": {},
        "duelos": {},
    }

    if resultados:
        for group_name, users_bets in season_bets_data.items():
            for username, bets_dict in users_bets.items():
                puntos = 0
                for bet_key, info in bets_dict.items():
                    real = resultados.get(bet_key)
                    
                    if real is None:
                        continue

                    user_val = info["value"]
                    correcto = False
    
                    # 🔸 Caso especial: most_dnfs_* (varios posibles ganadores)
                    if bet_key.startswith("most_dnfs_") and isinstance(real, list):
                        if not real:
                            # Aún no hay resultado real -> no puntuamos
                            continue

                        # Normalizar pick del usuario a lista de strings
                        if isinstance(user_val, list):
                            picks_norm = [norm_str(p) for p in user_val]
                        else:
                            picks_norm = [norm_str(str(user_val))]

                        truths_norm = [norm_str(t) for t in real]

                        # Correcto si al menos uno de los picks está en la lista real
                        correcto = any(p in truths_norm for p in picks_norm)

                    else:
                        # 🔹 Resto de apuestas (comparación normal)
                        if isinstance(user_val, list) and isinstance(real, list):
                            correcto = [norm_str(x) for x in user_val] == [
                                norm_str(x) for x in real
                            ]
                        else:
                            correcto = norm_str(user_val) == norm_str(real)

                    if correcto:
                        puntos += info["points"]

                user_points_data[group_name][username] = puntos

    return render_template(
        "season_bets_results.html",
        season_year=season_year,
        season_bets_data=season_bets_data,
        resultados=resultados,
        user_points_data=user_points_data
    )


def _apuestas_carrera_impl(race_name, season_year, use_new_template):
    # Buscar la temporada en la base de datos
    season = Season.query.filter_by(year=season_year).first()
    if not season:
        return jsonify({"error": "Temporada no encontrada"}), 404

    if race_name == 'Pre-Season-Testing':
        race_name = "Pre-Season Testing"
    else:
        race_name = race_name.replace("-", " ")
    # Obtener todas las apuestas relacionadas con la carrera y la temporada
    bets = Bet.query.filter_by(race=race_name, season_id=season.id).all()
    race_event = RaceEvent.query.filter_by(event_name=race_name, year=season_year).first()
    user_id = get_user_id()
    current_username = None
    if user_id:
        user = next((b.user for b in bets if b.user_id == user_id), None)
        if user:
            current_username = user.username
        else:
            identity = get_jwt_identity()
            current_username = identity["username"] if identity else None

    user_bet_types = set()
    if user_id:
        user_bet_types = {
            b.type.lower().replace(" ", "_")
            for b in Bet.query.filter_by(user_id=user_id, season_id=season.id, race=race_name).all()
        }
    has_user_bets = bool(user_bet_types)

    # Estructurar los datos en el formato deseado
    bets_data = {
        "race": {},
        "qualifying": {},
        "sprint": {},
        "sprint_qualifying": {},
	    "test": {}
    }

    for bet in bets:
        username = bet.user.username  # Obtener el nombre del usuario
        bet_type = bet.type.lower().replace(" ", "_") # Convertir el tipo de apuesta a minúsculas
        bet_name = bet.parametre.bet  # Obtener el nombre de la apuesta
        bet_value = bet.bet_user  # Resultado de la apuesta del usuario

        # print("username: ", username)
        # Asegurar que el usuario tiene una entrada en el diccionario
        if username not in bets_data[bet_type]:
            bets_data[bet_type][username] = {}

        # Guardar la apuesta del usuario
        bets_data[bet_type][username][bet_name] = bet_value

    # Si el usuario no ha apostado, ocultar apuestas de otros usuarios
    # Permitir ver apuestas ajenas cuando:
    # - Es testing, o
    # - El usuario ya envio ese tipo, o
    # - El tipo ya esta cerrado (no se puede apostar mas)
    can_view_others = has_user_bets or (race_event and race_event.event_format == "testing")
    now_utc = datetime.utcnow()
    session_meanings = SESSION_MEANINGS.get(race_event.event_format, []) if race_event else []
    session_times = [
        race_event.time_session1,
        race_event.time_session2,
        race_event.time_session3,
        race_event.time_session4,
        race_event.time_session5,
    ] if race_event else []
    session_time_map = {
        session_name: session_time
        for session_name, session_time in zip(session_meanings, session_times)
        if session_name != 'N/A' and session_time
    }
    if current_username:
        for event_type in list(bets_data.keys()):
            event_key = event_type.replace(" ", "_")
            session_key = event_type.replace("_", " ").title()
            close_time = session_time_map.get(session_key)
            is_closed = bool(close_time and now_utc >= close_time)
            can_view_type = (
                (event_key in user_bet_types)
                or (race_event and race_event.event_format == "testing")
                or is_closed
            )
            if not can_view_type:
                if current_username in bets_data[event_type]:
                    bets_data[event_type] = {current_username: bets_data[event_type][current_username]}
                else:
                    bets_data[event_type] = {}
    # 🔥 Aquí cargamos resultados oficiales si existen
    resultados = {}
    print("⚡ Working directory:", os.getcwd(), file=sys.stderr)
    try:
        resultados_path = os.path.join('resultados', f'resultados_{season_year}_{race_name}.json')
        if os.path.exists(resultados_path):
            print("⚡ path : ", resultados_path, file=sys.stderr)
            with open(resultados_path, 'r') as f:
                resultados = json.load(f)
            print(" 🔥 resultados: ", resultados, file=sys.stderr)
        else:
            print("res ", resultados_path, file=sys.stderr)
    except Exception as e:
        print(f"Error al cargar resultados: {e}", file=sys.stderr)

    # 🔥 Calculamos los puntos de cada usuario
    user_points_data = {
        "race": {},
        "qualifying": {},
        "sprint": {},
        "sprint_qualifying": {},
        "test": {}
    }

    bet_scores = {b.id: b.score for b in BetScore.query.all()}
    template_scores = {
        (bet, event): score
        for bet, event, score in db.session.query(BetScore.bet, BetScore.event, BetScore.score)
        .join(BetTemplate, BetScore.id == BetTemplate.bet_score_id)
        .filter(BetTemplate.season_id == season.id)
        .all()
    }
    bet_id_by_user = {
        (bet.user.username, bet.type.lower().replace(" ", "_"), bet.parametre.bet): bet.parameter_bet_id
        for bet in bets
    }
    row_points = {
        "race": {},
        "qualifying": {},
        "sprint": {},
        "sprint_qualifying": {},
        "test": {}
    }

    # Para cada tipo de evento
    for event_type, event_bets in bets_data.items():
        for user, user_bets in event_bets.items():
            points = 0
            if resultados:
                for bet_name, user_answer in user_bets.items():
                    resultado_real = resultados.get(event_type.replace('_', ' ').title(), {}).get(bet_name)
                    if resultado_real:
                        if str(user_answer).strip().lower() == str(resultado_real).strip().lower():
                            param_id = bet_id_by_user.get((user, event_type, bet_name))
                            row_score = 0
                            if param_id in bet_scores:
                                row_score = template_scores.get((bet_name, event_type), bet_scores[param_id])
                            if season_year >= 2026 and str(resultado_real).strip().lower() == "dnf":
                                row_score = 2
                            points += row_score
                            if season_year >= 2026:
                                row_points[event_type].setdefault(bet_name, {})[user] = row_score
                        elif season_year >= 2026:
                            row_points[event_type].setdefault(bet_name, {})[user] = 0
                user_points_data[event_type][user] = points

    users_by_id = {u.id: u.username for u in User.query.all()}

    extra_points = {}
    powerups_summary = {}
    users_sorted = sorted({u for event in bets_data.values() for u in event.keys()})
    summary_points = {}
    if season_year >= 2026 and use_new_template:
        extra_points = {
            "race": {},
            "qualifying": {},
            "sprint": {},
            "sprint_qualifying": {}
        }
        for event_label, event_key, extra in [
            ("Race", "race", 1.0),
            ("Qualifying", "qualifying", 0.5),
            ("Sprint", "sprint", 0.5),
            ("Sprint Qualifying", "sprint_qualifying", 0.5),
        ]:
            row = db.session.execute(
                text("""
                    SELECT user_id
                    FROM bet_activity
                    WHERE season_id = :season_id AND race = :race AND bet_type = :bet_type
                    ORDER BY updated_at DESC
                    LIMIT 1
                """),
                {"season_id": season.id, "race": race_name, "bet_type": event_label}
            ).fetchone()
            if row:
                winner_id = row[0]
                winner_name = users_by_id.get(winner_id, f"Usuario {winner_id}")
                extra_points[event_key][winner_name] = extra

        usage_rows = PowerupUsage.query.filter_by(season_id=season.id, race=race_name).all()
        x2_users = {u.user_id for u in usage_rows if u.powerup_type == "x2"}
        half_counts = {}
        for usage in usage_rows:
            user_name = users_by_id.get(usage.user_id, f"Usuario {usage.user_id}")
            powerups_summary.setdefault(user_name, {"used": [], "received": []})
            if usage.powerup_type == "x2":
                powerups_summary[user_name]["used"].append("x2")
            elif usage.powerup_type == "/2" and usage.target_user_id:
                target_name = users_by_id.get(usage.target_user_id, f"Usuario {usage.target_user_id}")
                powerups_summary[user_name]["used"].append(f"/2 a {target_name}")
                powerups_summary.setdefault(target_name, {"used": [], "received": []})
                powerups_summary[target_name]["received"].append(f"/2 de {user_name}")
                half_counts[usage.target_user_id] = half_counts.get(usage.target_user_id, 0) + 1

        # Resumen por usuario: base, bonus, extra, total
        for user in users_sorted:
            base_points = sum(
                user_points_data.get(evt, {}).get(user, 0)
                for evt in ["race", "qualifying", "sprint", "sprint_qualifying", "test"]
            )
            user_id = next((uid for uid, uname in users_by_id.items() if uname == user), None)
            half_count = half_counts.get(user_id, 0) if user_id is not None else 0
            if user_id in x2_users:
                multiplier = 2 / (2 ** half_count)
            else:
                multiplier = 1 / (2 ** half_count)
            powerup_points = base_points * multiplier
            aciertos = 0
            for evt_points in row_points.values():
                for bet_points in evt_points.values():
                    if bet_points.get(user, 0) > 0:
                        aciertos += 1
            bonus_points = 1 if aciertos >= 7 else 0
            extra_total = sum(
                extra_points.get(evt, {}).get(user, 0)
                for evt in ["race", "qualifying", "sprint", "sprint_qualifying"]
            )
            summary_points[user] = {
                "base": base_points,
                "powerups": powerup_points,
                "bonus": bonus_points,
                "extra": extra_total,
                "total": powerup_points + bonus_points + extra_total
            }
    powerups_counts = dict(
        db.session.query(PowerupUsage.powerup_type, db.func.count())
        .filter_by(season_id=season.id, race=race_name)
        .group_by(PowerupUsage.powerup_type)
        .all()
    )
    powerups_total = sum(powerups_counts.values()) if powerups_counts else 0

    template_name = 'bets_2026.html' if use_new_template else 'bets.html'
    return render_template(
        template_name,
        race_name=race_name,
        season_year=season_year,
        bets_data=bets_data,
        resultados=resultados,
        user_points_data=user_points_data,
        row_points=row_points,
        extra_points=extra_points,
        powerups_summary=powerups_summary,
        users_sorted=users_sorted,
        summary_points=summary_points,
        powerups_total=powerups_total,
        can_view_others=can_view_others
    )


@bets_bp.route('/apuestas/<race_name>-2026')
@jwt_required(locations=["cookies"])
def apuestas_carrera_2026(race_name):
    return _apuestas_carrera_impl(race_name, 2026, use_new_template=True)


@bets_bp.route('/apuestas/<race_name>-<int:season_year>')
@jwt_required(locations=["cookies"])
def apuestas_carrera(race_name, season_year):
    return _apuestas_carrera_impl(race_name, season_year, use_new_template=False)
