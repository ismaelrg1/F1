from config.db_config import db  # Importa db de config
from sqlalchemy import CheckConstraint


class ScoreRace(db.Model):
    """
        Modelo de la puntuacion total del usuario en cada carrera

        id -> identificador de la puntuacion del usuario
        user_id -> identificador del usuario
        season_id -> identificador de la temporada
        race -> nombre de la carrera #TODO cambiar a llave foranea del race_event
        score -> puntuacion obtenida en esa carrera
    """
    __tablename__ = 'score_race'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    race = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False, default=0)

    # Relaciones
    user = db.relationship('User', backref='score_race', lazy=True)
    season = db.relationship('Season', backref='score_race', lazy=True)

    # Agregar una restricción para que score siempre sea >= 0
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_non_negative'),
    )