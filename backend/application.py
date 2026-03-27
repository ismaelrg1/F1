from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate  # Importa Flask-Migrate

from backend.app.utils.socket_manager import socketio
from config.config import Config
from config.db_config import db

from backend.app.utils.logging_utils import setup_logger
logger = setup_logger(__name__)


def create_app():
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config.from_object(Config)

    # Inicializa la base de datos
    db.init_app(app)
    import backend.app.models
    migrate = Migrate(app, db)

    # Crear tablas si no existen
    # with app.app_context():
    #     db.create_all()  # No es necesario pasar `app` aquí, ya que estamos en el contexto de `app`

    logger.debug(f"Table DB: {db.Model.metadata.tables.items()}")

    # Inicializa JWT
    jwt = JWTManager(app)

    # Inicializa socketio con la app
    socketio.init_app(app)

    migrate.init_app(app, db)

    # Registra Blueprints
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.api_bd import api
    from backend.app.routes.schedule import schedule_bp
    from backend.app.routes.race import race_bp
    from backend.app.routes.ranking import ranking_bp
    from backend.app.routes.bets import bets_bp
    from backend.app.routes.season_bets import season_bets_bp
    from backend.app.powerups.routes import powerups_bp
    from backend.app.routes.normativa import normativa_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(api)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(race_bp)
    app.register_blueprint(ranking_bp)
    app.register_blueprint(bets_bp)
    app.register_blueprint(season_bets_bp)
    app.register_blueprint(powerups_bp)
    app.register_blueprint(normativa_bp)

    return app
