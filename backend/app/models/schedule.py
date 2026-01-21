from config.db_config import db


class RaceEvent(db.Model):
    """
        Modelo de las carreras

        id -> identificador de la carrera
        year -> año de la carrera #TODO posible cambio a id de Season
        round_number -> numero de la carrera segun el orden de calendario
        country -> pais de la carrera
        event_name -> nombre de la carrera (... Grand Prix)
        event_date -> fecha de la carrera
        event_format -> formato de la carrera (convetional, sprint-qualifying, testing, ...)[segund fastf1]
        time_session1 -> dia y hora de la sesion 1 (libre 1)
        time_session2 -> dia y hora de la sesion 2 (libre 2 o qualy-sprint)
        time_session3 -> dia y hora de la sesion 3 (libre 3 o sprint)
        time_session4 -> dia y hora de la sesion 4 (qualy)
        time_session5 -> dia y hora de la sesion 5 (carrera)
        flag_url -> path fichero bandera del pais de la carrera
        circuit_url -> path fichero imagen del circuito de la carrera
    """
    __tablename__ = 'race_events'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_format = db.Column(db.String(100), nullable=False, default="conventional")
    time_session1 = db.Column(db.DateTime, nullable=True)
    time_session2 = db.Column(db.DateTime, nullable=True)
    time_session3 = db.Column(db.DateTime, nullable=True)
    time_session4 = db.Column(db.DateTime, nullable=True)
    time_session5 = db.Column(db.DateTime, nullable=True)
    flag_url = db.Column(db.String(200), nullable=True)
    circuit_image_url = db.Column(db.String(200), nullable=True)
