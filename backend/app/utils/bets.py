from backend.app.models import BetScore, RaceEvent, BetException, Season
from backend.app.models.parameters_bets import BetTemplate
import json

SESSION_MEANINGS = {
    'conventional': ['Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race'],
    'sprint': ['Practice 1', 'Qualifying', 'Practice 2', 'Sprint', 'Race'],
    'sprint_shootout': ['Practice 1', 'Qualifying', 'Sprint Shootout', 'Sprint', 'Race'],
    'sprint_qualifying': ['Practice 1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race'],
    'testing': ['Session 1', 'Session 2', 'Session 3', 'N/A', 'N/A']
}
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

    # Función auxiliar para mapear tipos de apuestas
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

    # Mapear las apuestas genéricas de la temporada a los tipos correspondientes
    for template in bet_templates:
        bet = template.bet_score  # Relación con BetScore

        # Si no hay una relación bien configurada, usar consulta manual
        if not bet:
            bet = BetScore.query.get(template.bet_score_id)

        bet_type = get_bet_type(bet.event)
        print(f"bet_type {bet_type}")
        if bet_type:
            options = template.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)  # Convertir JSON string a dict si es necesario
                except json.JSONDecodeError:
                    options = {}

            bets_by_type[bet_type].append({
                "bet": bet.bet,
                "options": options,
                "is_custom": False
            })

    # Obtener excepciones específicas para el evento
    exceptions = BetException.query.filter_by(race_event_id=race_event.id).all()
    for exception in exceptions:
        bet_type = get_bet_type(exception.bet)

        if bet_type:
            options = exception.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    options = {}

            if exception.is_custom:
                # Si es una apuesta personalizada, agregarla como nueva
                bets_by_type[bet_type].append({
                    "bet": exception.bet,
                    "options": options,
                    "is_custom": True
                })
            else:
                # Si es una modificación de una apuesta existente, buscar y sobreescribir
                for bet in bets_by_type[bet_type]:
                    if bet["bet"] == exception.bet:
                        bet["score"] = exception.score
                        bet["options"] = options
                        break

    # Mapear sesiones a nombres según el formato del evento
    session_mapping = {
        "time_session1": SESSION_MEANINGS[race_event.event_format][0],
        "time_session2": SESSION_MEANINGS[race_event.event_format][1],
        "time_session3": SESSION_MEANINGS[race_event.event_format][2],
        "time_session4": SESSION_MEANINGS[race_event.event_format][3],
        "time_session5": SESSION_MEANINGS[race_event.event_format][4],
    }

    print(
        f"Race Event:\nID: {race_event.id}\nName: {race_event.event_name}\nFormat: {race_event.event_format}\nSessions: {session_mapping}\nBets: {bets_by_type}")

    return {
        "race_event": {
            "id": race_event.id,
            "event_name": race_event.event_name,
            "event_format": race_event.event_format,
            "sessions": session_mapping
        },
        "bets": bets_by_type
    }