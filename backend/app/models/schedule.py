from config.db_config import db


class RaceEvent(db.Model):
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
