from flask import Blueprint, request, jsonify, make_response, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies
from config.db_config import db  # Asegúrate de importar db de config
from backend.app.models.user import User  # Asegúrate de que el path sea correcto
from backend.app.models import RaceEvent, Season, ScoreRace, ScoreSeason
import os

import sys
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return render_template('login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
        Registro del usuario en la base de datos
    :return:
    """
    username = request.json.get('username')
    password = request.json.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "User already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
        Login del usuario
    :return:
    """
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity={'username': user.username})

        # Crea una respuesta de Flask
        response = make_response(jsonify({"msg": "Login successful"}))

        # Establece la cookie de acceso usando el metodo proporcionado por Flask-JWT-Extended
        set_access_cookies(response, access_token)

        return response

    return jsonify({"msg": "Invalid credentials"}), 401
# @auth_bp.route('/protected', methods=['GET'])
# @jwt_required()
# def protected():
#     current_user = get_jwt_identity()
#     return jsonify(logged_in_as=current_user), 200

@auth_bp.route('/home', methods=['GET'])
@jwt_required(locations=["cookies"])
def protected():
    today = datetime.today().date()

    # Próxima carrera (si la hay)
    next_race = (
        RaceEvent.query
        .filter(RaceEvent.event_date >= today)
        .order_by(RaceEvent.event_date.asc())
        .first()
    )

    # Año actual
    year = datetime.today().year

    # Por defecto no hay campeón mostrado
    season_finished = False
    winner_name = None

    # Solo buscamos campeón si ya no hay más carreras
    if not next_race:
        # 1) Comprobar que existe el fichero de resultados de temporada
        resultados_path = os.path.join("resultados", f"season_{year}.json")
        if os.path.exists(resultados_path):
            season_finished = True

            # 2) Buscar temporada en BD
            season = Season.query.filter_by(year=year).first()
            if season:
                # Puntos por carreras
                race_scores = (
                    db.session.query(
                        User.username,
                        db.func.coalesce(db.func.sum(ScoreRace.score), 0).label("puntos_carreras")
                    )
                    .join(ScoreRace, ScoreRace.user_id == User.id)
                    .filter(ScoreRace.season_id == season.id)
                    .group_by(User.username)
                    .all()
                )
                race_points = {u: p for u, p in race_scores}

                # Puntos por porra de temporada
                season_scores = (
                    db.session.query(
                        User.username,
                        db.func.coalesce(db.func.sum(ScoreSeason.score), 0).label("puntos_temporada")
                    )
                    .join(ScoreSeason, ScoreSeason.user_id == User.id)
                    .filter(ScoreSeason.season_id == season.id)
                    .group_by(User.username)
                    .all()
                )
                season_points = {u: p for u, p in season_scores}

                # Suma total
                totals = {}
                for u, p in race_points.items():
                    totals[u] = totals.get(u, 0) + p
                for u, p in season_points.items():
                    totals[u] = totals.get(u, 0) + p

                if totals:
                    winner_name = max(totals.items(), key=lambda x: x[1])[0]

    return render_template(
        'home.html',
        next_race=next_race,
        season_finished=season_finished,
        winner_name=winner_name,
        year=year,
    )
