from flask import render_template, Blueprint
from flask_jwt_extended import jwt_required

race_bp = Blueprint('race', __name__)
@race_bp.route('/race/<int:race_id>', endpoint='race_detail')
@jwt_required(locations=["cookies"])
def race_detail(race_id):
    # lógica para obtener detalles de la carrera por race_id
    return render_template('test.html')