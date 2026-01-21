from config.db_config import db  # Importa db de config


class Bet(db.Model):
    """
        Model de la apuesta realizada por el usuario:

        id -> identificador de la apuesta
        user_id -> identificador del usuario
        season_id -> identificador del season de la apuesta
        race -> nombre de la carrera
        parameter_bet_id -> identificador de la apuesta
        bet_user -> resultado de la apuesta del usuario
        type -> tipo de la apuesta (qulay, race, sprint, qualy-sprint)
    """
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