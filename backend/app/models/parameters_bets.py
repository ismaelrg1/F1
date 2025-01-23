from config.db_config import db  # Importa db de config
from sqlalchemy import CheckConstraint


class BetScore(db.Model):
    __tablename__ = 'bet_score'

    id = db.Column(db.Integer, primary_key=True)
    bet = db.Column(db.String(100), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)

    # Agregar una restricción para que score siempre sea >= 0
    __table_args__ = (
        CheckConstraint('score >= 0', name='check_score_non_negative'),
    )