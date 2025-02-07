from flask import render_template, Blueprint, jsonify
from flask_jwt_extended import jwt_required

from backend.app.models import BetScore, Season
from backend.app.routes.api_bd import bet_status
from backend.app.utils.bets import get_bets_for_race, format_bet_name

from collections import defaultdict
from datetime import datetime

def get_user_bets(bet_status_response):
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
    # Obtener datos del evento y las apuestas usando las funciones que ya tienes
    race_name=race_name.replace("-", " ")
    bets_response = get_bets_for_race(race_name, race_year)
    if "error" in bets_response:
        return jsonify(bets_response), 404

    # Consulta el estado de las apuestas del usuario
    bet_status_response = bet_status(race_name, race_year)
    if isinstance(bet_status_response, tuple):  # Si devuelve un código de error
        bet_status_response = bet_status_response[0]  # Solo el contenido

    user_bets = get_user_bets(bet_status_response)

    # Pasar los datos al template
    return render_template(
        'race_detail.html',
        race_event=bets_response["race_event"],
        bets=bets_response["bets"],
        user_bets=user_bets,
        current_time=datetime.utcnow()
    )