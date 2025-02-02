from flask import render_template, Blueprint, jsonify
from flask_jwt_extended import jwt_required

from backend.app.routes.api_bd import bet_status
from backend.app.utils.bets import get_bets_for_race

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
    bet_status_response = bet_status(race_name)
    print(f"bet_status_response -> {bet_status_response}")
    if isinstance(bet_status_response, tuple):  # Si devuelve un código de error
        bet_status_response = bet_status_response[0]  # Solo el contenido

    # Pasar los datos al template
    return render_template(
        'race_detail.html',
        race_event=bets_response["race_event"],
        bets=bets_response["bets"],
        user_bets={bet["type"]: bet for bet in bet_status_response.get("bets", [])}
    )