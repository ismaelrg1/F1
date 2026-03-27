from datetime import datetime

from config.db_config import db


class PowerupInventory(db.Model):
    __tablename__ = "powerup_inventory"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("season.id"), nullable=False)
    powerup_type = db.Column(db.String(16), nullable=False)
    remaining = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "season_id", "powerup_type", name="uq_powerup_inventory_unique"),
    )


class PowerupUsage(db.Model):
    __tablename__ = "powerup_usage"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey("season.id"), nullable=False)
    race = db.Column(db.String(100), nullable=False)
    powerup_type = db.Column(db.String(16), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "season_id", "race", name="uq_powerup_usage_unique"),
    )
