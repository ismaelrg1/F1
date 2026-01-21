from config.db_config import db  # Importa db de config
from sqlalchemy import CheckConstraint


class Scores(db.Model):
    """
        Modelo de las puntuaciones totales de los usuarios de la temporada

        id -> identificador de la puntuaciones
        user_id -> identificador del usuario
        season_id -> identificador del season
        total_score -> puntuacion total de la temporada
    """

    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    total_score = db.Column(db.Float, nullable=False, default=0)

    # Relaciones
    user = db.relationship('User', backref='scores', lazy=True)
    season = db.relationship('Season', backref='scores', lazy=True)

    # Agregar una restricción para que score siempre sea >= 0
    __table_args__ = (
        CheckConstraint('total_score >= 0', name='check_score_non_negative'),
    )