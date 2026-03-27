from datetime import datetime
import os

from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

from backend.app.models import Season, User, ScoreRace, RaceEvent, ScoreSeason
from config.db_config import db

ranking_bp = Blueprint('ranking', __name__)

@ranking_bp.route('/ranking')
@ranking_bp.route('/ranking-<int:season_year>')
@jwt_required(locations=["cookies"])
def ranking(season_year=None):
    # Obtener todas las temporadas disponibles en la BD
    seasons = (
        Season.query
        .with_entities(Season.year)
        .order_by(Season.year.desc())
        .all()
    )
    seasons = [season.year for season in seasons]

    year = season_year if season_year else datetime.now().year

    # Obtener la temporada correspondiente
    season = Season.query.filter_by(year=year).first()
    if not season:
        return render_template(
            'ranking.html',
            datos_puntos={},
            ranking=[],
            carreras=[],
            seasons=seasons,
            season_points={}    # 👈 añadimos para no romper el template
        )

    # Obtener todas las carreras de la temporada, ordenadas por ronda
    carreras = (
        RaceEvent.query
        .with_entities(RaceEvent.event_name, RaceEvent.event_date)
        .filter_by(year=year)
        .order_by(RaceEvent.round_number)
        .all()
    )

    # Obtener solo las carreras que ya han ocurrido
    now = datetime.utcnow()
    seen = set()
    carreras_hasta_ahora = []

    for event_name, event_date in carreras:
        if event_date and event_date < now and event_name not in seen:
            seen.add(event_name)
            carreras_hasta_ahora.append(event_name)


    if not carreras_hasta_ahora:
        # Si no hay carreras pasadas, no hay puntuaciones
        return render_template(
            'ranking.html',
            datos_puntos={},
            ranking=[],
            carreras=[],
            seasons=seasons,
            season_points={}    # 👈 igual aquí
        )

    # ==========================================
    # 1) PUNTOS POR CARRERAS (ScoreRace)
    # ==========================================
    scores = (
        db.session.query(
            User.username,            # nombre de usuario
            ScoreRace.race,           # nombre de la carrera
            db.func.coalesce(
                db.func.sum(ScoreRace.score), 0
            ).label("puntos")
        )
        .join(ScoreRace, ScoreRace.user_id == User.id)
        .filter(
            ScoreRace.season_id == season.id,
            ScoreRace.race.in_(carreras_hasta_ahora)
        )
        .group_by(User.username, ScoreRace.race)
        .all()
    )

    # Estructurar datos para asegurar que cada usuario tenga una lista
    # de puntuaciones por carrera
    datos_puntos = {}
    for username, race, puntos in scores:
        if username not in datos_puntos:
            # Inicializar todas las carreras con 0
            datos_puntos[username] = {
                carrera: 0 for carrera in carreras_hasta_ahora
            }
        datos_puntos[username][race] = puntos

    # Convertir a lista de listas con puntuaciones acumuladas por carrera
    datos_puntos_formateado = {}
    for user, puntos in datos_puntos.items():
        acumulado = 0
        datos_puntos_formateado[user] = []
        for carrera in carreras_hasta_ahora:
            actual = puntos.get(carrera, 0)
            print(
                "\nCarrera -> ", carrera,
                " , Puntuacion -> ", actual,
                " , Puntos acumulados-> ", acumulado
            )
            acumulado += actual
            datos_puntos_formateado[user].append(acumulado)

    # ==========================================
    # 2) PUNTOS DE PORRA DE TEMPORADA (ScoreSeason)
    # ==========================================
    # score_season tiene una fila por (season_id, user_id, bet_key)
    # sumamos por usuario
    season_scores = (
        db.session.query(
            User.username,
            db.func.coalesce(
                db.func.sum(ScoreSeason.score), 0
            ).label("puntos_season")
        )
        .join(ScoreSeason, ScoreSeason.user_id == User.id)
        .filter(ScoreSeason.season_id == season.id)
        .group_by(User.username)
        .all()
    )

    # Diccionario: { "usuario": puntos_de_porra_temporada }
    season_points = {
        username: puntos_season
        for username, puntos_season in season_scores
        if puntos_season is not None
    }

    # Si hay usuarios que solo tienen porra de temporada, pero ninguna carrera,
    # opcionalmente podríamos meterlos en datos_puntos_formateado con todo 0:
    for username in season_points.keys():
        if username not in datos_puntos_formateado:
            # Usuario sin carreras, pero con porra de temporada
            datos_puntos_formateado[username] = [0] * len(carreras_hasta_ahora)

    # ==========================================
    # 3) RANKING FINAL = carreras + temporada
    # ==========================================
    ranking = []
    for user, lista_puntos in datos_puntos_formateado.items():
        puntos_carreras = lista_puntos[-1] if lista_puntos else 0
        puntos_temp = season_points.get(user, 0)
        total = puntos_carreras + puntos_temp

        ranking.append({
            "nombre": user,
            "puntos_carreras": puntos_carreras,
            "puntos_temporada": puntos_temp,
            "puntos_totales": total
        })

    ranking = sorted(
        ranking,
        key=lambda x: x["puntos_totales"],
        reverse=True
    )

    # ==========================================
    # 4) ¿La temporada está terminada?
    #    -> usamos la existencia de resultados/season_<year>.json
    #    -> y sacamos el ganador (posición 1 del ranking)
    # ==========================================
    season_results_path = os.path.join("resultados", f"season_{year}.json")
    season_finished = os.path.exists(season_results_path)

    winner_name = ranking[0]["nombre"] if ranking and season_finished else None

    return render_template(
        'ranking.html',
        datos_puntos=datos_puntos_formateado,  # solo carreras (para el gráfico)
        ranking=ranking,                       # incluye temporada
        carreras=carreras_hasta_ahora,
        seasons=seasons,
        season_points=season_points,            # por si quieres mostrarlo en la tabla
        season_finished=season_finished,
        winner_name=winner_name,
        year=year
    )
