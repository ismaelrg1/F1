from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_jwt_extended import jwt_required
from config.db_config import db


from backend.app.models import Season
from backend.app.models.season_bets import SeasonBet, SeasonBetPick
from backend.app.utils.season_lock import is_season_locked, get_season_lock_dt
from backend.app.routes.api_bd import get_user_id  # ← usamos tu helper


season_bets_bp = Blueprint('season_bets', __name__)

def parse_bool_value(value):
    return str(value).strip().lower() in ("true", "1", "yes", "y", "si", "sí")

@season_bets_bp.route('/season-bets-<int:year>', methods=['GET'])
@jwt_required(locations=["cookies"])
def season_bets(year):
    season = Season.query.filter_by(year=year).first_or_404()

    user_id = get_user_id()
    if not user_id:
        abort(401)  # sesión inválida o usuario no encontrado

    lock_dt = get_season_lock_dt(year)
    locked = is_season_locked(year)

    bets = (
        SeasonBet.query
        .filter_by(season_id=season.id, is_active=True)
        .order_by(SeasonBet.id.asc())
        .all()
    )

    existing = {
        p.season_bet_id: p
        for p in SeasonBetPick.query.filter_by(user_id=user_id).all()
    }

    # GET
    picks = {bid: (p.value if p else None) for bid, p in existing.items()}
    return render_template('season_bets.html', year=year, bets=bets, picks=picks, locked=locked, lock_dt=lock_dt)


@season_bets_bp.route('/api/season-bets-<int:year>', methods=['POST'])
@jwt_required(locations=["cookies"])
def season_bets_api(year):
    season = Season.query.filter_by(year=year).first_or_404()

    user_id = get_user_id()
    if not user_id:
        abort(401)

    locked = is_season_locked(year)
    if locked:
        return jsonify({"msg": "Apuestas de temporada bloqueadas"}), 403

    bets = (SeasonBet.query
        .filter_by(season_id=season.id, is_active=True)
        .order_by(SeasonBet.id.asc())
        .all())

    payload = request.get_json() or {}
    data = payload.get("bets", {})

    pending = []
    missing = []

    for bet in bets:
        raw = data.get(str(bet.id))

        try:
            if bet.input_type == 'enum':
                if not raw:
                    missing.append(bet.label)
                else:
                    pending.append((bet.id, raw))

            elif bet.input_type == 'bool':
                if raw is None:
                    missing.append(bet.label)
                else:
                    pending.append((bet.id, parse_bool_value(raw)))

            elif bet.input_type == 'int':
                if raw is None or str(raw).strip() == '':
                    missing.append(bet.label)
                else:
                    value = int(raw)
                    if value < 0:
                        missing.append(bet.label)
                    else:
                        pending.append((bet.id, value))

            elif bet.input_type == 'position':
                if not raw:
                    missing.append(bet.label)
                else:
                    p = int(raw)
                    if 1 <= p <= 22:
                        pending.append((bet.id, p))
                    else:
                        missing.append(bet.label)

            elif bet.input_type == 'multienum':
                vals = [x.strip() for x in str(raw).split(',') if x.strip()]
                if not vals:
                    missing.append(bet.label)
                else:
                    pending.append((bet.id, vals))

        except Exception as e:
            return jsonify({"msg": f"Valor inválido en '{bet.label}': {e}"}), 400

    if missing:
        return jsonify({"msg": "Faltan opciones en: " + ", ".join(missing)}), 400

    for bet_id, value in pending:
        upsert_pick(bet_id, user_id, value)

    db.session.commit()
    return jsonify({"msg": "Apuestas de temporada guardadas."}), 200


def upsert_pick(season_bet_id: int, user_id: int, value):
    pick = SeasonBetPick.query.filter_by(season_bet_id=season_bet_id, user_id=user_id).first()
    if pick:
        pick.value = value
    else:
        db.session.add(SeasonBetPick(season_bet_id=season_bet_id, user_id=user_id, value=value))
