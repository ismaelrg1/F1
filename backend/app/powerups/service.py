from datetime import datetime
from typing import Optional

from sqlalchemy import func

from config.db_config import db
from backend.app.models import Bet, User, RaceEvent, Season
from backend.app.models.season_bets import SeasonBetPick, SeasonBet
from backend.app.powerups.models import PowerupInventory, PowerupUsage


DEFAULT_POWERUPS = {
    "x2": 2,
    "/2": 1,
}

X2_BLOCKED_RACES = {"Monaco Grand Prix"}

def ensure_inventory(user_id: int, season_id: int):
    for powerup_type, qty in DEFAULT_POWERUPS.items():
        row = PowerupInventory.query.filter_by(
            user_id=user_id, season_id=season_id, powerup_type=powerup_type
        ).first()
        if not row:
            db.session.add(
                PowerupInventory(
                    user_id=user_id,
                    season_id=season_id,
                    powerup_type=powerup_type,
                    remaining=qty,
                )
            )
    db.session.commit()


def get_inventory(user_id: int, season_id: int):
    ensure_inventory(user_id, season_id)
    rows = PowerupInventory.query.filter_by(user_id=user_id, season_id=season_id).all()
    return {r.powerup_type: r.remaining for r in rows}


def get_usage_for_race(user_id: int, season_id: int, race: str):
    return PowerupUsage.query.filter_by(
        user_id=user_id, season_id=season_id, race=race
    ).first()


def can_use_powerup(user_id: int, season_id: int, race: str) -> bool:
    # No permite elegir powerup si ya ha enviado alguna apuesta de este GP
    return not Bet.query.filter_by(user_id=user_id, season_id=season_id, race=race).first()


def get_eligible_targets(season_id: int, current_user_id: int):
    # Usuarios que han participado en test o porra de temporada (misma season)
    season = Season.query.get(season_id)
    testing_races = {
        r.event_name
        for r in RaceEvent.query.filter_by(event_format="testing", year=season.year).all()
    } if season else set()
    testers = {
        b.user_id
        for b in Bet.query.filter(
            Bet.season_id == season_id,
            Bet.race.in_(testing_races)
        ).all()
    }
    season_players = {
        p.user_id
        for p in SeasonBetPick.query.join(SeasonBet, SeasonBet.id == SeasonBetPick.season_bet_id)
        .filter(SeasonBet.season_id == season_id)
        .all()
    }
    eligible_user_ids = testers | season_players

    users = User.query.filter(User.id.in_(eligible_user_ids)).all()
    # Contar en cuántos GP distintos ha recibido /2 cada usuario
    received_counts = dict(
        db.session.query(
            PowerupUsage.target_user_id,
            func.count(func.distinct(PowerupUsage.race))
        )
        .filter(
            PowerupUsage.season_id == season_id,
            PowerupUsage.powerup_type == "/2",
            PowerupUsage.target_user_id.isnot(None),
        )
        .group_by(PowerupUsage.target_user_id)
        .all()
    )
    eligible = []
    for u in users:
        if u.id == current_user_id:
            continue
        if received_counts.get(u.id, 0) >= 2:
            continue
        eligible.append({"id": u.id, "username": u.username})
    return eligible


def use_powerup(user_id: int, season_id: int, race: str, powerup_type: str, target_user_id: Optional[int]):
    if get_usage_for_race(user_id, season_id, race):
        return False, "Power-up ya usado en este GP."

    if not can_use_powerup(user_id, season_id, race):
        return False, "Debes elegir el power-up antes de tu primera apuesta."

    inventory = get_inventory(user_id, season_id)
    if inventory.get(powerup_type, 0) <= 0:
        return False, "No tienes power-ups disponibles de este tipo."

    if powerup_type == "x2" and race in X2_BLOCKED_RACES:
        return False, "En este GP no se permite usar x2."

    if powerup_type == "/2":
        if not target_user_id:
            return False, "Debes seleccionar un usuario objetivo."
        if target_user_id == user_id:
            return False, "No puedes usar /2 sobre ti mismo."
        # El objetivo no puede haber recibido /2 en 2 GPs distintos
        received = (
            db.session.query(func.count(func.distinct(PowerupUsage.race)))
            .filter(
                PowerupUsage.season_id == season_id,
                PowerupUsage.powerup_type == "/2",
                PowerupUsage.target_user_id == target_user_id,
            )
            .scalar()
        )
        if received and received >= 2:
            return False, "Este usuario ya ha recibido /2 en 2 GPs."
    else:
        target_user_id = None

    # Registrar uso
    db.session.add(
        PowerupUsage(
            user_id=user_id,
            season_id=season_id,
            race=race,
            powerup_type=powerup_type,
            target_user_id=target_user_id,
            created_at=datetime.utcnow(),
        )
    )
    # Descontar inventario
    inv_row = PowerupInventory.query.filter_by(
        user_id=user_id, season_id=season_id, powerup_type=powerup_type
    ).first()
    inv_row.remaining -= 1
    db.session.commit()
    return True, "Power-up aplicado."
