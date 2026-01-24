from datetime import datetime
import os, sys, json

from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.models import Season, Bet, BetScore, SeasonBet, SeasonBetPick, RaceEvent
from backend.app.utils.apiF1 import get_schedule
from backend.app.routes.api_bd import get_user_id

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


@bets_bp.route('/apuestas/<race_name>-<int:season_year>')
@jwt_required(locations=["cookies"])
def apuestas_carrera(race_name, season_year):
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
                can_view_others
                and (event_key in user_bet_types or (race_event and race_event.event_format == "testing") or is_closed)
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

    # Para cada tipo de evento
    for event_type, event_bets in bets_data.items():
        for user, user_bets in event_bets.items():
            points = 0
            if resultados:
                for bet_name, user_answer in user_bets.items():
                    resultado_real = resultados.get(event_type.replace('_', ' ').title(), {}).get(bet_name)
                    if resultado_real:
                        if str(user_answer).strip().lower() == str(resultado_real).strip().lower():
                            bet = Bet.query.join(Bet.parametre).filter(
                                Bet.user.has(username=user),
                                Bet.season_id==season.id,
                                Bet.race==race_name,
                                Bet.type==event_type.replace('_', ' ').title(),
                                Bet.parametre.has(bet=bet_name)
                            ).first()
                            if bet and bet.parameter_bet_id in bet_scores:
                                points += bet_scores[bet.parameter_bet_id]
                user_points_data[event_type][user] = points


    return render_template(
        'bets.html',
        race_name=race_name,
        season_year=season_year,
        bets_data=bets_data,
        resultados=resultados,
        user_points_data=user_points_data,
        can_view_others=can_view_others
    )
