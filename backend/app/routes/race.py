from flask import render_template, Blueprint, jsonify
from flask_jwt_extended import jwt_required

from backend.app.models import BetScore, Season, RaceEvent
from backend.app.routes.api_bd import get_user_bets_for_race
from backend.app.utils.bets import get_bets_for_race, format_bet_name

from collections import defaultdict
from datetime import datetime

def organize_bets_by_type(bet_status_response):
    """
        Organiza las apuestas del usuario en un diccionario, categorizadas por tipo de apuesta.

    :param bet_status_response: Respuesta JSON de `get_user_bets_for_race()`
    :return: Diccionario con apuestas organizadas por tipo
    """
    user_bets = defaultdict(list)

    for bet in bet_status_response.get("bets", []):
        # Obtener el nombre del parámetro a partir de parameter_bet_id
        bet_score = BetScore.query.get(bet["parameter_bet_id"])
        bet_name = bet_score.bet if bet_score else "Unknown"

        # Obtener el año a partir de season_id
        season = Season.query.get(bet["season_id"])
        year = season.year if season else "Unknown"

        user_bets[bet["type"]].append({
            "id": bet["id"],
            "parameter_bet": format_bet_name(bet_name),
            "bet_user": bet["bet_user"],
            "season": year,
            "max_edit_time": bet["max_edit_time"]
        })

    return dict(user_bets)


race_bp = Blueprint('race', __name__)
@race_bp.route('/race/<string:race_name>-<int:race_year>', endpoint='race_detail')
@jwt_required(locations=["cookies"])
def race_detail(race_name, race_year):
    """
        API para obtener todas las apuestas de una carrera y las respuestas del usuario(si existe)
    :param race_name: nombre de la carrera
    :param race_year: año de la carrea
    :return: 'race_detail.html',
        race_event=bets_response["race_event"], -> nombre de la carrera
        bets=bets_response["bets"], -> apuestas de la carrera
        user_bets=user_bets, -> resultado del usuario en las apuestas de la carrera
        current_time=datetime.utcnow() -> hora actual
    """

    # Obtener datos del evento y las apuestas usando las funciones que ya tienes
    if race_name == 'Pre-Season-Testing':
        race_name = "Pre-Season Testing"
    else:
        race_name=race_name.replace("-", " ")

    bets_response = get_bets_for_race(race_name, race_year)

    if "error" in bets_response:
        return jsonify(bets_response), 404

    # Consulta el estado de las apuestas del usuario
    bet_status_response = get_user_bets_for_race(race_name, race_year)
    if isinstance(bet_status_response, tuple):  # Si devuelve un código de error
        bet_status_response = bet_status_response[0]  # Solo el contenido

    # Organizar apuestas por tipo
    user_bets = organize_bets_by_type(bet_status_response)

    # Obtener la fecha de esta carrera
    current_event = RaceEvent.query.filter_by(event_name=race_name, year=race_year).first()

    # Obtener todas las carreras de ese año ordenadas
    race_list = RaceEvent.query.filter_by(year=race_year).order_by(RaceEvent.event_date).all()
    current_index = race_list.index(current_event) if current_event in race_list else -1

    prev_race = race_list[current_index - 1] if current_index > 0 else None
    next_race = race_list[current_index + 1] if current_index < len(race_list) - 1 else None

    # Pasar los datos al template
    return render_template(
        'race_detail.html',
        race_event=bets_response["race_event"],
        bets=bets_response["bets"],
        user_bets=user_bets,
        current_time=datetime.utcnow(),
        prev_race=prev_race,
        next_race=next_race
    )
