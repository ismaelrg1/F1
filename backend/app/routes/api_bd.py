from datetime import timedelta, datetime

from flask import Blueprint, request, jsonify, make_response, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies

from backend.app.models import RaceEvent, User, BetScore, Bet, Season
from backend.app.utils.bets import get_bets_for_race
from config.db_config import db

api = Blueprint('api', __name__)

SESSION_MEANINGS = {
    'conventional': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race'],
    'sprint': ['Practice 1', 'Qualifying', 'Practice 2', 'Sprint', 'Race'],
    'sprint_shootout': ['Practice 1', 'Qualifying', 'Sprint Shootout', 'Sprint', 'Race'],
    'sprint_qualifying': ['Practice 1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race'],
    'testing': ['Session 1', 'Session 2', 'Session 3', 'N/A', 'N/A']
}

@api.route('/api/bet-status', methods=['GET'])
@jwt_required(locations=["cookies"])
def bet_status(race_name, year):
    username = get_jwt_identity()  # Obtiene el username desde el JWT

    # Obtener el user_id basado en el username
    user = User.query.filter_by(username=username['username']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user.id  # Ahora tenemos el user_id

    # Query all bets for the user in the given race
    user_bets = Bet.query.filter_by(user_id=user_id, race=race_name).all()

    # Fetch race event details to determine session times and max edit times
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

    # Get session meanings for the event format
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
            "id": bet.id,
            "type": bet.type,
            "parameter_bet_id": bet.parameter_bet_id,
            "bet_user": bet.bet_user,
            "season_id": bet.season_id,
            "max_edit_time": max_edit_time.isoformat() if max_edit_time else None
        })

    return {
        "race": race_name,
        "bets": bets
    }, 200

def get_season_id_from_race_event(race_event_id):
    race_event = RaceEvent.query.get(race_event_id)  # Obtiene el evento de carrera
    if not race_event:
        return None  # Si no existe, retorna None o lanza un error

    season = Season.query.filter_by(year=race_event.year).first()  # Busca la temporada correspondiente
    return season.id if season else None  # Devuelve el ID de la temporada si existe


def get_user_id():
    user_identity = get_jwt_identity()  # Puede ser email, username, etc.

    print(f'user-> {user_identity['username']}')

    user = User.query.filter_by(username=user_identity['username']).first()  # Buscar en la base de datos

    if user:
        return user.id  # Devuelve el ID del usuario
    return None


@api.route('/api/set-bet', methods=['POST'])
@jwt_required(locations=["cookies"])
def set_bet():
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
        print(max_edit_time)

        if datetime.utcnow() > max_edit_time:
            return jsonify({"error": "Bet modification time has expired"}), 403

        # 🛑 Imprimimos lo que llega en `data` para depuración
        print("📩 Datos recibidos en el backend:", data)

        season_id = get_season_id_from_race_event(race_event.id)

        for bet_name, bet_value in data.items():
            if bet_name in ["season_id", "race", "type", "id"]:
                continue

            bet_score = BetScore.query.filter_by(bet=bet_name.replace(' ','')).first()
            print(f'Bet: {bet_name.replace(' ','')}')
            if not bet_score:
                return jsonify({"error": f"Invalid bet name: {bet_name.replace(' ','')}"}), 400

            print(f'bet_score :{bet_score}')
            print(f'user_id :{user_id}')
            print(f'season_id :{season_id}')
            print(f'race :{race}')
            print(f'parameter_bet_id :{bet_score.id}')
            print(f'bet_value :{bet_value}')
            print(f'type :{bet_type}')
            existing_bet = Bet.query.filter_by(
                user_id=user_id,
                season_id=season_id,
                race=race,
                parameter_bet_id=bet_score.id,
                type=bet_type
            ).first()

            if existing_bet:
                existing_bet.bet_user = bet_value
            else:
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


@api.route('/api/bets/<int:race_event_id>', methods=['GET'])
@jwt_required(locations=["cookies"])
def get_bets(race_event_id):
    response = get_bets_for_race(race_event_id)
    if "error" in response:
        return jsonify(response), 404

    return jsonify(response), 200