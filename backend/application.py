# from flask import Flask
#
# app = Flask(__name__)
#
#
# @app.route('/')
# def hello_world():  # put application's code here
#     return 'Hello World!'
#
#
# if __name__ == '__main__':
#     app.run()
#


from flask import Flask
from flask_jwt_extended import JWTManager
from config.config import Config
from config.db_config import db
from app.routes.auth import auth_bp
from app.routes.usuarios import usuarios_bp


def create_app():
    app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
    app.config.from_object(Config)

    # Inicializa la base de datos
    db.init_app(app)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()  # No es necesario pasar `app` aquí, ya que estamos en el contexto de `app`

    # Inicializa JWT
    jwt = JWTManager(app)

    # Registra Blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(usuarios_bp)

    return app