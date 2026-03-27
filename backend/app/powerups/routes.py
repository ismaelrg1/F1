from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backend.app.models import Season, User, RaceEvent
from backend.app.powerups.service import (
    get_inventory,
    get_usage_for_race,
    get_eligible_targets,
    use_powerup,
)

powerups_bp = Blueprint("powerups", __name__)


def get_current_user():
    identity = get_jwt_identity()
    if not identity:
        return None
    claims = get_jwt()
    if isinstance(identity, dict) and identity.get("username"):
        return User.query.filter_by(username=identity["username"]).first()
    if isinstance(identity, str) and identity.isdigit():
        return User.query.filter_by(id=int(identity)).first()
    username = claims.get("username") if isinstance(claims, dict) else None
    if username:
        return User.query.filter_by(username=username).first()
    return None


@powerups_bp.route("/api/powerups/status/<string:race_name>-<int:season_year>", methods=["GET"])
@jwt_required(locations=["cookies"])
def powerups_status(race_name, season_year):
    season = Season.query.filter_by(year=season_year).first()
    if not season:
        return jsonify({"error": "Season not found"}), 404

    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    race_event = RaceEvent.query.filter_by(event_name=race_name, year=season_year).first()
    if not race_event or race_event.event_format == "testing":
        return jsonify({"error": "Power-ups no disponibles para este evento"}), 400

    usage = get_usage_for_race(user.id, season.id, race_name)
    inventory = get_inventory(user.id, season.id)
    targets = get_eligible_targets(season.id, user.id)

    allowed_powerups = ["x2", "/2"]
    if race_name == "Monaco Grand Prix":
        allowed_powerups = ["/2"]

    return jsonify({
        "inventory": inventory,
        "used": usage is not None,
        "used_powerup": usage.powerup_type if usage else None,
        "targets": targets,
        "allowed_powerups": allowed_powerups,
    })


@powerups_bp.route("/api/powerups/use", methods=["POST"])
@jwt_required(locations=["cookies"])
def powerups_use():
    data = request.get_json() or {}
    race = data.get("race")
    season_year = data.get("season_year")
    powerup_type = data.get("powerup_type")
    target_user_id = data.get("target_user_id")

    if not all([race, season_year, powerup_type]):
        return jsonify({"error": "Missing required fields"}), 400

    season = Season.query.filter_by(year=season_year).first()
    if not season:
        return jsonify({"error": "Season not found"}), 404

    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404

    race_event = RaceEvent.query.filter_by(event_name=race, year=season_year).first()
    if not race_event or race_event.event_format == "testing":
        return jsonify({"error": "Power-ups no disponibles para este evento"}), 400

    ok, message = use_powerup(user.id, season.id, race, powerup_type, target_user_id)
    status = 200 if ok else 400
    return jsonify({"message": message}), status
