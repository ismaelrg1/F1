from datetime import datetime
from config.db_config import db

# Tipos de entrada soportados:
#  - enum:      una opción de una lista (e.g., "Equipo campeón: McLaren")
#  - bool:      sí/no
#  - int:       número entero (e.g., "Pilotos en podio: 10")
#  - position:  posición P1..P20 (valida que sea 1..20)
#  - multienum: lista ordenada de opciones (se guarda lista; útil para “Duelos”)

class SeasonBet(db.Model):
    __tablename__ = "season_bet"
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("season.id"), nullable=False)
    bet_key = db.Column(db.String(64), nullable=False)   # clave estable (p.ej. 'champ_driver')
    label = db.Column(db.String(128), nullable=False)    # texto visible
    input_type = db.Column(db.String(16), nullable=False, default="enum")
    options = db.Column(db.JSON, nullable=True)          # lista de strings o None (para int/bool/position)
    points = db.Column(db.Integer, default=0)            # puntos por acierto (puedes ajustarlo en admin)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('season_id','bet_key', name='uq_season_bet_unique'),)

class SeasonBetPick(db.Model):
    __tablename__ = "season_bet_pick"
    id = db.Column(db.Integer, primary_key=True)
    season_bet_id = db.Column(db.Integer, db.ForeignKey("season_bet.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # value: string/int/bool/list según input_type. Lo guardamos siempre como JSON para flexibilidad.
    value = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('season_bet_id','user_id', name='uq_season_bet_pick_unique'),)
    
    # 🔹 Relaciones al estilo Bet.user / Bet.parametre
    user = db.relationship("User", backref=db.backref("season_bet_picks", lazy=True))
    season_bet = db.relationship("SeasonBet", backref=db.backref("picks", lazy=True))


# NOTA: la corrección y sumatorio para ranking se harán con ScoreSeason (cuando lo necesites).
class ScoreSeason(db.Model):
    __tablename__ = "score_season"
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("season.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    bet_key = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

