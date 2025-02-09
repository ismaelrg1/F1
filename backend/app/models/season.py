from config.db_config import db  # Importa db de config
class Season(db.Model):
    """
        Modelo para guardar todas las temporadas realizadas

        id -> identificador de la season
        year -> año de comienzo de la season

    """
    __tablename__ = 'season'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)