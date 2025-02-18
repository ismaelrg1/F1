from datetime import datetime

from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

from backend.app.models import Season
from backend.app.utils.apiF1 import get_schedule

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/calendario')
@schedule_bp.route('/calendario-<int:season_year>')
@jwt_required(locations=["cookies"])
def calendario(season_year=None):
    # Solicitar las carreras
    year = season_year if season_year else datetime.now().year

    # Obtener todas las temporadas disponibles en la BD
    seasons = Season.query.with_entities(Season.year).order_by(Season.year.desc()).all()
    seasons = [season.year for season in seasons]  # Extraer solo los años de las temporadas

    races = get_schedule(year)

    return render_template('schedule.html', races=races, year=year, seasons=seasons)

