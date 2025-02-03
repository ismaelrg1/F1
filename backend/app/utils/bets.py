from backend.app.models import BetScore, RaceEvent, BetException, Season
from backend.app.models.parameters_bets import BetTemplate
import json
import re

SESSION_MEANINGS = {
    'conventional': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race'],
    'sprint': ['Practice 1', 'Qualifying', 'Practice 2', 'Sprint', 'Race'],
    'sprint_shootout': ['Practice 1', 'Qualifying', 'Sprint Shootout', 'Sprint', 'Race'],
    'sprint_qualifying': ['Practice 1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race'],
    'testing': ['Session 1', 'Session 2', 'Session 3', 'N/A', 'N/A']
}

# Define qué tipos de apuestas se permiten por cada formato
ALLOWED_BET_TYPES = {
    'conventional': ['Qualifying', 'Race'],
    'sprint': ['Qualifying', 'Race', 'Sprint'],
    'sprint_shootout': ['Qualifying', 'Race', 'Sprint'],
    'sprint_qualifying': ['Qualifying', 'Race', 'Sprint', 'Sprint Qualifying'],
    'testing': ['Test']
}

def format_bet_name(bet_name):
    """Convierte nombres como 'PolePosition' en 'Pole Position'."""
    formatted = re.sub(r'(?<!^)(?=[A-Z])', ' ', bet_name)  # Agrega espacios antes de mayúsculas
    return formatted.strip().title()  # Capitaliza cada palabra


def get_bets_for_race(event_name, year):
    # Obtener detalles del evento
    race_event = RaceEvent.query.filter_by(event_name=event_name.strip(), year=year).first()
    if not race_event:
        return {"error": "Race event not found"}, 404

    # Obtener la temporada correspondiente al año
    season = Season.query.filter_by(year=year).first()
    if not season:
        return {"error": "Season not found"}, 404

    # Obtener las apuestas definidas en la plantilla para esta temporada
    bet_templates = BetTemplate.query.filter_by(season_id=season.id).all()

    # Crear un diccionario inicial con las apuestas genéricas organizadas por tipo
    bets_by_type = {
        "Qualifying": [],
        "Race": [],
        "Sprint": [],
        "Sprint Qualifying": [],
        "Test": [],
    }

    allowed_bets = ALLOWED_BET_TYPES.get(race_event.event_format, [])

    def get_bet_type(event):
        event = event.lower()
        if "qualy-sprint" in event:
            return "Sprint Qualifying"
        elif "race" in event:
            return "Race"
        elif "sprint" in event:
            return "Sprint"
        elif "qualy" in event:
            return "Qualifying"
        elif "test" in event:
            return "Test"
        return None

    for template in bet_templates:
        bet = template.bet_score

        if not bet:
            bet = BetScore.query.get(template.bet_score_id)

        bet_type = get_bet_type(bet.event)
        if bet_type and bet_type in allowed_bets:
            options = template.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    options = {}

            bets_by_type[bet_type].append({
                "bet": format_bet_name(bet.bet),  # Formateamos el nombre antes de enviarlo
                "options": options,
                "is_custom": False
            })

    exceptions = BetException.query.filter_by(race_event_id=race_event.id).all()
    for exception in exceptions:
        bet_type = get_bet_type(exception.bet)

        if bet_type and bet_type in allowed_bets:
            options = exception.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    options = {}

            if exception.is_custom:
                bets_by_type[bet_type].append({
                    "bet": format_bet_name(exception.bet),  # También formateamos excepciones
                    "options": options,
                    "is_custom": True
                })
            else:
                for bet in bets_by_type[bet_type]:
                    if bet["bet"] == format_bet_name(exception.bet):
                        bet["score"] = exception.score
                        bet["options"] = options
                        break

    session_mapping = {
        "time_session1": SESSION_MEANINGS[race_event.event_format][0],
        "time_session2": SESSION_MEANINGS[race_event.event_format][1],
        "time_session3": SESSION_MEANINGS[race_event.event_format][2],
        "time_session4": SESSION_MEANINGS[race_event.event_format][3],
        "time_session5": SESSION_MEANINGS[race_event.event_format][4],
    }

    filtered_bets = {key: value for key, value in bets_by_type.items() if key in allowed_bets}

    return {
        "race_event": {
            "id": race_event.id,
            "event_name": race_event.event_name,
            "event_format": race_event.event_format,
            "sessions": session_mapping
        },
        "bets": filtered_bets
    }