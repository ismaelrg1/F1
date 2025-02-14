from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

ranking_bp = Blueprint('ranking', __name__)


@ranking_bp.route('/ranking')
@jwt_required(locations=["cookies"])
def ranking():
    datos_puntos = {
        "usuario1": [10, 25, 40, 50],
        "usuario2": [5, 15, 30, 45],
        "usuario3": [0, 10, 20, 35],
        "usuario4": [0, 0, 30, 90],
        "usuario5": [0, 10, 30, 80],
    }

    ranking = sorted(
        [{"nombre": user, "puntos_totales": puntos[-1]} for user, puntos in datos_puntos.items()],
        key=lambda x: x["puntos_totales"],
        reverse=True
    )

    carreras = ["Carrera 1", "Carrera 2", "Carrera 3", "Carrera 4", "Carrera 5", "Carrera 6","Carrera 7", "Carrera 8","Carrera 9", "Carrera 10","Carrera 11", "Carrera 12", "Carrera 13", "Carrera 14", "Carrera 15", "Carrera 16", "Carrera 17", "Carrera 18", "Carrera 19", "Carrera 20", "Carrera 21", "Carrera 22", "Carrera 23", "Carrera 24"]

    return render_template('ranking.html', datos_puntos=datos_puntos, ranking=ranking, carreras=carreras)
