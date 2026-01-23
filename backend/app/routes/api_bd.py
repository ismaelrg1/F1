from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.models import RaceEvent, User, BetScore, Bet, Season
from backend.app.utils.bets import get_bets_for_race
from config.db_config import db

api = Blueprint('api', __name__)

# Significado de los time_sessionX
SESSION_MEANINGS = {
    'conventional': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race'],
    'sprint': ['Practice 1', 'Qualifying', 'Practice 2', 'Sprint', 'Race'],
    'sprint_shootout': ['Practice 1', 'Qualifying', 'Sprint Shootout', 'Sprint', 'Race'],
    'sprint_qualifying': ['Practice 1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race'],
    'testing': ['Test', 'Test1', 'Test2', 'N/A', 'N/A']
}

@api.route('/api/bet-status', methods=['GET'])
@jwt_required(locations=["cookies"])
def get_user_bets_for_race(race_name, year):
    """
        Obtiene todas las apuestas realizadas por el usuario en una carrera y año específico.
    :param race_name: nombre de la carrera
    :param year: año de la carrera
    :return: {
        "race": race_name : nombre de la carrera,
        "bets":  apuestas realizadas por el usuario o lista vacia
    }
    """
    username = get_jwt_identity()  # Obtiene el username desde el JWT

    # Obtener el user_id basado en el username
    user = User.query.filter_by(username=username['username']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user.id  # Ahora tenemos el user_id

    # Limitar por temporada para no mezclar apuestas de años distintos
    season = Season.query.filter_by(year=year).first()
    if not season:
        return {
            "message": "Season not found.",
            "race": race_name,
            "bets": []
        }, 404

    # Query para obtener todas las apuestas del usuario en esa carrera y temporada
    user_bets = Bet.query.filter_by(user_id=user_id, race=race_name, season_id=season.id).all()

    # Obtenemos toda la informacion de la carrera
    race_event = RaceEvent.query.filter_by(event_name=race_name, year=year).first()
    if not race_event:
        return {
            "message": "Race event not found.",
            "race": race_name,
            "bets": []
        }, 404

    if not user_bets:
        return {
            "message": "No bets found for this race.",
            "race": race_name,
            "bets": [],
        }, 404

    # Obtenemos los nombres de los eventos(libre 1, qualy, carrera...) y su tiempo
    session_meanings = SESSION_MEANINGS.get(race_event.event_format, [])
    session_times = [
        race_event.time_session1, race_event.time_session2,
        race_event.time_session3, race_event.time_session4, race_event.time_session5
    ]
    session_time_map = {session_name: session_time for session_name, session_time in
                        zip(session_meanings, session_times) if session_name != 'N/A' and session_time}


    bets = []
    for bet in user_bets:
        # Calculate max edit time for the session
        max_edit_time = session_time_map[bet.type]
        # Append bet details, including max_edit_time
        bets.append({
            "id": str(bet.id),
            "type": bet.type,
            "parameter_bet_id": str(bet.parameter_bet_id),
            "bet_user": bet.bet_user,
            "season_id": str(bet.season_id),
            "max_edit_time": max_edit_time.isoformat() if max_edit_time else None
        })

    return {
        "race": race_name,
        "bets": bets
    }, 200


def get_season_id_from_race_event(race_event_id):
    """
      Funcion para obtener el id de la season segun el id de la carrera #TODO posible eliminacion si se modifica el modelo del race_event

    :param race_event_id: identificador de la carrera
    :return: identificador de la season
    """

    race_event = RaceEvent.query.get(race_event_id)  # Obtiene el evento de carrera
    if not race_event:
        return None

    season = Season.query.filter_by(year=race_event.year).first()  # Busca la temporada correspondiente
    return season.id if season else None  # Devuelve el ID de la temporada si existe


def get_user_id():
    """
        Funcion para obtener el id del usuario
    :return: id del usuario
    """
    user_identity = get_jwt_identity()

    # print(f'user-> {user_identity['username']}')

    user = User.query.filter_by(username=user_identity['username']).first()  # Buscar en la base de datos

    if user:
        return user.id  # Devuelve el ID del usuario
    return None


@api.route('/api/set-bet', methods=['POST'])
@jwt_required(locations=["cookies"])
def set_bet():
    """
        API para añadir las apuestas realizadas por el usuario #TODO posible modificacion para simplificar el codigo haciendo una funcion que se llame guardar apuestas y utilizar lambda con la lista que nos llega
        :parameter data : apuestas realizadas por el usuario
    :return: Mensaje de verificacion de las apuestas guardadas correctamente
    """

    try:
        user_id = get_user_id()

        if not user_id:
            return jsonify({"error": "No user found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400

        id = data.get('id')
        race = data.get('race')
        bet_type = data.get('type')

        if not all([id, race, bet_type]):
            return jsonify({"error": "Missing required fields"}), 400

        if not id:
            return jsonify({"error": "ID not found"}), 404

        race_event = RaceEvent.query.filter_by(id=id).first()
        if not race_event:
            return jsonify({"error": "Race event not found"}), 404

        session_meanings = SESSION_MEANINGS.get(race_event.event_format, [])
        session_times = [
            race_event.time_session1, race_event.time_session2,
            race_event.time_session3, race_event.time_session4, race_event.time_session5
        ]
        session_time_map = {session_name: session_time for session_name, session_time in
                            zip(session_meanings, session_times) if session_name != 'N/A' and session_time}


        if bet_type not in session_time_map:
            return jsonify({"error": "Invalid bet type"}), 400

        max_edit_time = session_time_map[bet_type]
        # print(max_edit_time)

       # Verificacion si es posible el añadir/modificar la apuesta
        if datetime.utcnow() > max_edit_time:
            return jsonify({"error": "Bet modification time has expired"}), 403

        # # 🛑 Imprimimos lo que llega en `data` para depuración
        # print("📩 Datos recibidos en el backend:", data)

        season_id = get_season_id_from_race_event(race_event.id)

        # Iteramos por todas las apuestas
        for bet_name, bet_value in data.items():
            if bet_name in ["season_id", "race", "type", "id"]:
                continue

            bet_score = BetScore.query.filter_by(bet=bet_name.replace(' ',''), event=bet_type.replace(' ','_').lower()).first()
            #print(f'Bet: {bet_name.replace(' ','')}')
            if not bet_score:
                return jsonify({"error": f"Invalid bet name: {bet_name.replace(' ','')}"}), 400

            # print(f'bet_score :{bet_score}')
            # print(f'user_id :{user_id}')
            # print(f'season_id :{season_id}')
            # print(f'race :{race}')
            # print(f'parameter_bet_id :{bet_score.id}')
            # print(f'bet_value :{bet_value}')
            # print(f'type :{bet_type}')

            # Buscamos si el usuario ya habia realizado esa apuesta
            existing_bet = Bet.query.filter_by(
                user_id=user_id,
                season_id=season_id,
                race=race,
                parameter_bet_id=bet_score.id,
                type=bet_type
            ).first()

            if existing_bet:  # Modificamos la apuesta del usuario
                existing_bet.bet_user = bet_value
            else: # Añadimos la nueva apuesta a la base de datos
                new_bet = Bet(
                    user_id=user_id,
                    season_id=season_id,
                    race=race,
                    parameter_bet_id=bet_score.id,
                    bet_user=bet_value,
                    type=bet_type
                )
                print(f'New bet {new_bet}')
                db.session.add(new_bet)

        db.session.commit()

        return jsonify({"message": "Bet(s) placed successfully!"}), 201

    except Exception as e:
        print("❌ Error en el backend:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

#TODO Modificar esto
@api.route('/api/bets/<int:race_event_id>', methods=['GET'])
@jwt_required(locations=["cookies"])
def get_bets(race_event_id, year):
    """
        Api para obtener las apuestas de una carrera(template + excepciones)

    :param race_event_id: identificador de la carrera
    :return: todas las apuestas de la carrera
    """

    response = get_bets_for_race(race_event_id, year)
    if "error" in response:
        return jsonify(response), 404

    return jsonify(response), 200
