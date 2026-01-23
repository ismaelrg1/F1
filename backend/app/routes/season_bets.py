from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_jwt_extended import jwt_required
from config.db_config import db

from backend.app.models import Season
from backend.app.models.season_bets import SeasonBet, SeasonBetPick
from backend.app.utils.season_lock import is_season_locked
from backend.app.routes.api_bd import get_user_id  # ← usamos tu helper

season_bets_bp = Blueprint('season_bets', __name__)

def parse_bool_value(value):
    return str(value).strip().lower() in ("true", "1", "yes", "y", "si", "sí")

@season_bets_bp.route('/season-bets-<int:year>', methods=['GET', 'POST'])
@jwt_required(locations=["cookies"])
def season_bets(year):
    season = Season.query.filter_by(year=year).first_or_404()

    user_id = get_user_id()
    if not user_id:
        abort(401)  # sesión inválida o usuario no encontrado

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

    if request.method == 'POST':
        if locked:
            flash("Las apuestas de temporada están bloqueadas por inicio de pre-season.", "warning")
            return redirect(url_for('season_bets.season_bets', year=year))

        pending = []
        missing = []

        for bet in bets:
            field = f'bet_{bet.id}'
            try:
                if bet.input_type == 'enum':
                    val = request.form.get(field)
                    if not val:
                        missing.append(bet.label)
                    else:
                        pending.append((bet.id, val))

                elif bet.input_type == 'bool':
                    raw = request.form.get(field)
                    if raw is None:
                        missing.append(bet.label)
                    else:
                        pending.append((bet.id, parse_bool_value(raw)))

                elif bet.input_type == 'int':
                    raw = request.form.get(field)
                    if raw is None or raw.strip() == '':
                        missing.append(bet.label)
                    else:
                        pending.append((bet.id, int(raw)))

                elif bet.input_type == 'position':
                    raw = request.form.get(field)
                    if not raw:
                        missing.append(bet.label)
                    else:
                        p = int(raw)
                        if 1 <= p <= 20:
                            pending.append((bet.id, p))
                        else:
                            missing.append(bet.label)

                elif bet.input_type == 'multienum':
                    raw = request.form.get(field, '')
                    vals = [x.strip() for x in raw.split(',') if x.strip()]
                    if not vals:
                        missing.append(bet.label)
                    else:
                        pending.append((bet.id, vals))

            except Exception as e:
                flash(f"Valor inválido en '{bet.label}': {e}", "danger")

        if missing:
            flash("Faltan opciones en: " + ", ".join(missing), "warning")
            return redirect(url_for('season_bets.season_bets', year=year))

        for bet_id, value in pending:
            upsert_pick(bet_id, user_id, value)

        db.session.commit()
        flash("Apuestas de temporada guardadas.", "success")
        return redirect(url_for('season_bets.season_bets', year=year))

    # GET
    picks = {bid: (p.value if p else None) for bid, p in existing.items()}
    return render_template('season_bets.html', year=year, bets=bets, picks=picks, locked=locked)

def upsert_pick(season_bet_id: int, user_id: int, value):
    pick = SeasonBetPick.query.filter_by(season_bet_id=season_bet_id, user_id=user_id).first()
    if pick:
        pick.value = value
    else:
        db.session.add(SeasonBetPick(season_bet_id=season_bet_id, user_id=user_id, value=value))
