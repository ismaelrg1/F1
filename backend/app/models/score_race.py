from config.db_config import db  # Importa db de config
from sqlalchemy import CheckConstraint


class ScoreRace(db.Model):
    __tablename__ = 'score_race'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    race = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)

    # Relaciones
    user = db.relationship('User', backref='score_race', lazy=True)
    season = db.relationship('Season', backref='score_race', lazy=True)

    # Agregar una restricción para que score siempre sea >= 0
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_non_negative'),
    )