from config.db_config import db  # Importa db de config
from sqlalchemy import CheckConstraint


class BetScore(db.Model):
    __tablename__ = 'bet_score'

    id = db.Column(db.Integer, primary_key=True)
    bet = db.Column(db.String(100), unique=True, nullable=False)
    score = db.Column(db.Float, nullable=False, default=0)
    event = db.Column(db.String(50), nullable=False, server_default="race")

    # Agregar una restricción para que score siempre sea >= 0
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_non_negative'),
    )


class BetException(db.Model):
    __tablename__ = 'bet_exception'

    id = db.Column(db.Integer, primary_key=True)
    race_event_id = db.Column(db.Integer, db.ForeignKey('race_events.id'), nullable=False)
    bet = db.Column(db.String(100), nullable=False)  # Nombre de la apuesta
    score = db.Column(db.Integer, nullable=False, default=0)  # Puntuación personalizada
    options = db.Column(db.JSON, nullable=True)  # Opciones específicas (pilotos o valores)

    race_event = db.relationship('RaceEvent', backref='exceptions', lazy=True)

class BetTemplate(db.Model):
    __tablename__ = 'bet_template'

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    bet_score_id = db.Column(db.Integer, db.ForeignKey('bet_score.id'), nullable=False)
    options = db.Column(db.JSON, nullable=True)

    # Relación con BetScore
    bet_score = db.relationship('BetScore', backref='bet_templates', lazy=True)