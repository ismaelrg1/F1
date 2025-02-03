from datetime import timedelta

from flask import Blueprint, request, jsonify, make_response, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies

from backend.app.models import RaceEvent, User
from backend.app.models.bet import Bet
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
def bet_status(race_name):
    username = get_jwt_identity()  # Obtiene el username desde el JWT

    # Obtener el user_id basado en el username
    user = User.query.filter_by(username=username['username']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user.id  # Ahora tenemos el user_id

    # Query all bets for the user in the given race
    user_bets = Bet.query.filter_by(user_id=user_id, race=race_name).all()

    # Fetch race event details to determine session times and max edit times
    race_event = RaceEvent.query.filter_by(event_name=race_name).first()
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
            "max_edit_time": None  # No bets, so no max_edit_time to calculate
        }, 404

    # Get session meanings for the event format
    session_meanings = SESSION_MEANINGS.get(race_event.event_format, [])

    # Map session names to times
    session_times = [
        race_event.time_session1,
        race_event.time_session2,
        race_event.time_session3,
        race_event.time_session4,
        race_event.time_session5,
    ]

    # Create a dictionary of session name to time
    session_time_map = {
        session_name: session_time
        for session_name, session_time in zip(session_meanings, session_times)
        if session_name != 'N/A' and session_time  # Exclude 'N/A' and None values
    }

    bets = []
    for bet in user_bets:
        # Determine the session type from the bet type
        session_name = None
        if bet.type in ['qualy', 'qualifying']:
            session_name = 'Qualifying'
        elif bet.type == 'race':
            session_name = 'Race'
        elif bet.type == 'sprint':
            session_name = 'Sprint'

        # Calculate max edit time for the session
        max_edit_time = None
        if session_name and session_name in session_time_map:
            max_edit_time = session_time_map[session_name] - timedelta(hours=1)

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


@api.route('/api/set-bet', methods=['POST'])
@jwt_required(locations=["cookies"])
def set_bet():
    user_id = get_jwt_identity()  # Extract the user ID from the JWT

    data = request.get_json()
    season_id = data.get('season_id')
    race = data.get('race')
    parameter_bet_id = data.get('parameter_bet_id')
    bet_user = data.get('bet_user')
    bet_type = data.get('type')  # 'race', 'qualy', etc.

    if not all([season_id, race, parameter_bet_id, bet_user, bet_type]):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert into the unified Bet table
    new_bet = Bet(
        user_id=user_id,
        season_id=season_id,
        race=race,
        parameter_bet_id=parameter_bet_id,
        bet_user=bet_user,
        type=bet_type
    )

    db.session.add(new_bet)
    db.session.commit()

    return jsonify({"message": "Bet placed successfully!"}), 201


@api.route('/api/bets/<int:race_event_id>', methods=['GET'])
@jwt_required(locations=["cookies"])
def get_bets(race_event_id):
    response = get_bets_for_race(race_event_id)
    if "error" in response:
        return jsonify(response), 404

    return jsonify(response), 200