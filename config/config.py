from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuraciones de Flask-JWT-Extended para manejar JWT en cookies
    JWT_TOKEN_LOCATION = ['cookies']  # Especifica que el JWT se debe buscar en las cookies
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'  # Nombre predeterminado que espera Flask-JWT-Extended
    JWT_COOKIE_SECURE = False  # Cambia a True si estás usando HTTPS
    JWT_ACCESS_COOKIE_PATH = '/'  # Ruta donde la cookie JWT de acceso es válida
    JWT_REFRESH_COOKIE_PATH = '/token/refresh'  # Ruta específica para la cookie de refresh, si estás usando
    JWT_COOKIE_CSRF_PROTECT = False  # Cambia a True si deseas proteger contra CSRF
    JWT_COOKIE_SAMESITE = 'Lax'  # Opciones: 'Strict', 'Lax', o None para control de SameSite