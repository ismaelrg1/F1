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
    """Convierte nombres como 'PolePosition' en 'Pole Position', pero mantiene siglas como 'SC' sin separar."""
    formatted = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', bet_name)  # Agrega espacio solo si la mayúscula va seguida de una minúscula
    return formatted.strip()  # Capitaliza cada palabra


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
        "Qualifying": {"bets": [], "max_edit_time": None},
        "Race": {"bets": [], "max_edit_time": None},
        "Sprint": {"bets": [], "max_edit_time": None},
        "Sprint Qualifying": {"bets": [], "max_edit_time": None},
        "Test": {"bets": [], "max_edit_time": None},
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

            bets_by_type[bet_type]["bets"].append({
                "bet": format_bet_name(bet.bet),  # Formateamos el nombre antes de enviarlo
                "options": options,
                "is_custom": False
            })

    exceptions = BetException.query.filter_by(race_event_id=race_event.id).all()
    print(f'exceptions: {exceptions}')
    for exception in exceptions:
        print(f'exception: {exception}')
        bet_type = get_bet_type(exception.event)

        if bet_type and bet_type in allowed_bets:
            options = exception.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    options = {}

            formatted_bet_name = format_bet_name(exception.bet)  # Formatear el nombre

            existing_bet = next(
                (bet for bet in bets_by_type[bet_type]["bets"]
                 if bet["bet"] == formatted_bet_name and bet["options"] == options),
                None
            )

            if existing_bet:
                # Si la apuesta ya existe con las mismas opciones, eliminarla
                bets_by_type[bet_type]["bets"].remove(existing_bet)
            else:
                if exception.is_custom:
                    bets_by_type[bet_type]["bets"].append({
                        "bet": formatted_bet_name,  # También formateamos excepciones
                        "options": options,
                        "is_custom": True
                    })
                else:
                    for bet in bets_by_type[bet_type]["bets"]:
                        if bet["bet"] == formatted_bet_name:
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

    # Asignar tiempos máximos de edición
    session_time_map = {
        SESSION_MEANINGS[race_event.event_format][0]: race_event.time_session1,
        SESSION_MEANINGS[race_event.event_format][1]: race_event.time_session2,
        SESSION_MEANINGS[race_event.event_format][2]: race_event.time_session3,
        SESSION_MEANINGS[race_event.event_format][3]: race_event.time_session4,
        SESSION_MEANINGS[race_event.event_format][4]: race_event.time_session5,
    }

    for bet_type, bet_data in bets_by_type.items():
        session_name = bet_type  # El tipo de apuesta coincide con el nombre de sesión en SESSION_MEANINGS
        session_time = session_time_map.get(session_name)

        if session_time:
            bet_data["max_edit_time"] = session_time  # Resta una hora al tiempo límite
        else:
            bet_data["max_edit_time"] = None  # Si no hay un tiempo definido, se deja como None

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