from config.db_config import db  # Importa db de config


class Bet(db.Model):
    __tablename__ = 'bet'

    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    race = db.Column(db.String(100), nullable=False)
    parameter_bet_id = db.Column(db.Integer, db.ForeignKey('bet_score.id'), nullable=False)
    bet_user = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)

    # Relaciones opcionales para unirse con otras tablas si es necesario
    user = db.relationship('User', backref='bet_qualy', lazy=True)
    season = db.relationship('Season', backref='bet_qualy', lazy=True)
    parametre = db.relationship('BetScore', backref='bet_qualy', lazy=True)