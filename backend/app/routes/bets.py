from datetime import datetime
import os, sys, json

from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required

from backend.app.models import Season, Bet, BetScore
from backend.app.utils.apiF1 import get_schedule

bets_bp = Blueprint('bets', __name__)

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

    # print("\nApuestas finales ->",bets_data)
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
        user_points_data=user_points_data
    )
