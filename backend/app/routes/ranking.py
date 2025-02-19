from datetime import datetime

from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

from backend.app.models import Season, User, ScoreRace, RaceEvent
from config.db_config import db

ranking_bp = Blueprint('ranking', __name__)

@ranking_bp.route('/ranking')
@ranking_bp.route('/ranking-<int:season_year>')
@jwt_required(locations=["cookies"])
def ranking(season_year=None):
    # Obtener todas las temporadas disponibles en la BD
    seasons = Season.query.with_entities(Season.year).order_by(Season.year.desc()).all()
    seasons = [season.year for season in seasons]  # Extraer solo los años de las temporadas

    year = season_year if season_year else datetime.now().year

    # Obtener la temporada correspondiente
    season = Season.query.filter_by(year=year).first()
    if not season:
        return render_template('ranking.html', datos_puntos={}, ranking=[], carreras=[], seasons=seasons)

    # Obtener todas las carreras de la temporada, ordenadas por ronda
    carreras = (
        RaceEvent.query.with_entities(RaceEvent.event_name, RaceEvent.event_date)
        .filter_by(year=year)
        .order_by(RaceEvent.round_number)
        .all()
    )

    # Obtener solo las carreras que ya han ocurrido
    now = datetime.utcnow()
    carreras_hasta_ahora = [carrera[0] for carrera in carreras if carrera[1] and carrera[1] < now]

    if not carreras_hasta_ahora:
        # Si no hay carreras pasadas, no hay puntuaciones
        return render_template('ranking.html', datos_puntos={}, ranking=[], carreras=[], seasons=seasons)

    # Obtener las puntuaciones de los usuarios en las carreras que ya han ocurrido
    scores = (
        db.session.query(
            User.username,  # Obtener el nombre de usuario
            ScoreRace.race,  # Nombre de la carrera
            db.func.coalesce(db.func.sum(ScoreRace.score), 0).label("puntos")  # Sumar puntuaciones, 0 si no hay
        )
        .join(ScoreRace, ScoreRace.user_id == User.id)
        .filter(ScoreRace.season_id == season.id, ScoreRace.race.in_(carreras_hasta_ahora))
        .group_by(User.username, ScoreRace.race)
        .all()
    )

    # Estructurar datos para asegurar que cada usuario tenga una lista de puntuaciones por carrera
    datos_puntos = {}
    for username, race, puntos in scores:
        if username not in datos_puntos:
            # Inicializar todas las carreras con puntuación 0
            datos_puntos[username] = {carrera: 0 for carrera in carreras_hasta_ahora}
        datos_puntos[username][race] = puntos  # Asignar puntuaciones obtenidas

    # Convertir a lista de listas con puntuaciones acumuladas
    datos_puntos_formateado = {}
    for user, puntos in datos_puntos.items():
        acumulado = 0
        datos_puntos_formateado[user] = []
        for carrera in carreras_hasta_ahora:
            print("\nCarrera -> ", carrera, " , Puntuacion -> ", puntos.get(carrera, 0), " , Puntos acumulados-> ", acumulado)
            acumulado += puntos.get(carrera, 0)  # Sumar puntos actuales al acumulado
            datos_puntos_formateado[user].append(acumulado)  # Guardar puntuación acumulativa

    # Crear ranking basado en la puntuación total acumulada
    ranking = sorted(
        [{"nombre": user, "puntos_totales": puntos[-1]} for user, puntos in datos_puntos_formateado.items()],
        key=lambda x: x["puntos_totales"],
        reverse=True
    )

    return render_template(
        'ranking.html',
        datos_puntos=datos_puntos_formateado,
        ranking=ranking,
        carreras=carreras_hasta_ahora,
        seasons=seasons
    )