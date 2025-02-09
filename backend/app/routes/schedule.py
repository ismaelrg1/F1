from datetime import datetime

from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.utils.apiF1 import get_schedule

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/calendario')
@jwt_required(locations=["cookies"])
def calendario():
    # Solicitar las carreras
    races = get_schedule(datetime.now().year)

    return render_template('schedule.html', races=races)

