import os
import re

from flask import Blueprint, render_template, current_app
from flask_jwt_extended import jwt_required

from backend.app.models import Season

normativa_bp = Blueprint("normativa", __name__)

FILE_RE = re.compile(r'^(?:normativa_)?(?P<year>\d{4})\.(?P<ext>pdf|png|jpg|jpeg|webp)$', re.IGNORECASE)


def build_normativa_index(static_folder):
    normativa_dir = os.path.join(static_folder, "normativa")
    files_by_year = {}
    if not os.path.isdir(normativa_dir):
        return files_by_year

    for filename in os.listdir(normativa_dir):
        match = FILE_RE.match(filename)
        if not match:
            continue
        year = int(match.group("year"))
        ext = match.group("ext").lower()
        files_by_year.setdefault(year, {})
        files_by_year[year][ext] = filename
    return files_by_year


@normativa_bp.route("/normativa")
@normativa_bp.route("/normativa-<int:year>")
@jwt_required(locations=["cookies"])
def normativa(year=None):
    seasons = [s.year for s in Season.query.order_by(Season.year.desc()).all()]

    files_by_year = build_normativa_index(current_app.static_folder or "")
    available_years = sorted(set(seasons) | set(files_by_year.keys()), reverse=True)

    selected_year = year or (available_years[0] if available_years else None)
    selected_file = None
    selected_type = None

    if selected_year is not None:
        year_files = files_by_year.get(selected_year, {})
        if "pdf" in year_files:
            selected_file = year_files["pdf"]
            selected_type = "pdf"
        else:
            for ext in ("png", "jpg", "jpeg", "webp"):
                if ext in year_files:
                    selected_file = year_files[ext]
                    selected_type = "image"
                    break

    return render_template(
        "normativa.html",
        years=available_years,
        selected_year=selected_year,
        selected_file=selected_file,
        selected_type=selected_type,
    )
