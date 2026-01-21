from flask.cli import AppGroup
import re

from backend.app.models import Scores
from backend.application import create_app  # Importa tu función para crear la aplicación Flask
from config.db_config import db  # Importa la instancia de SQLAlchemy
from backend.app.models.user import User
from backend.app.models.parameters_bets import BetScore
from backend.app.models.bet import Bet
from backend.app.models.season import Season

# Crea la aplicación
app = create_app()

# Configura un grupo de comandos personalizados
cli = AppGroup('manage')

@cli.command('add_user')
def add_user():
    """Añadir un usuario a la base de datos y asociar una entrada en la tabla Scores."""
    username = input("Nombre de usuario: ")
    password = input("Contraseña: ")
    year = input("Año de la temporada: ")  # Pedir el año de la temporada

    try:
        # Verificar si el año de la temporada existe en la tabla Season
        season = Season.query.filter_by(year=year).first()
        if not season:
            print(f"Error: No se encontró una temporada con el año '{year}'.")
            return  # Salir si la temporada no existe

        # Crear el nuevo usuario
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()  # Confirmar el usuario antes de crear la entrada en 'Scores'

        # Añadir una entrada en 'Scores' para el nuevo usuario
        new_score = Scores(user_id=new_user.id, season_id=season.id, total_score=0)
        db.session.add(new_score)
        db.session.commit()

        print(f"Usuario '{username}' y su puntuación para la temporada '{year}' añadidos con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al añadir usuario o puntuación: {e}")


@cli.command('add_parametro_apuesta')
def add_parametro_apuesta():
    """Añadir un nuevo parámetro de apuesta."""
    nombre = input("Nombre del parámetro de apuesta: ")
    puntuacion = int(input("Puntuación: "))
    event = input("Tipo de apuesta(race, qualy, sprint o qualy-sprint: ")

    try:
        nuevo_parametro = BetScore(bet=nombre, score=puntuacion, event=event)
        db.session.add(nuevo_parametro)
        db.session.commit()
        print(f"Parámetro de apuesta '{nombre}' añadido con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al añadir parámetro de apuesta: {e}")


@cli.command('add_temporada')
def add_temporada():
    """Añadir una nueva temporada."""

    # Solicitar el año de la temporada al usuario
    while True:
        temporada = input("Año de la temporada (formato YYYY): ")

        # Verificar si el formato es YYYY usando una expresión regular
        if re.match(r'^\d{4}$', temporada):
            # Comprueba si el año está en un rango razonable (1900 a 2100 por ejemplo)
            if 1900 <= int(temporada) <= 2100:
                break  # Si el año es válido, sale del bucle
            else:
                print("Por favor, introduce un año entre 1900 y 2100.")
        else:
            print("Formato inválido. Asegúrate de que el año tenga cuatro dígitos (YYYY).")

    try:
        # Crea la nueva temporada
        nueva_temporada = Season(year=temporada)
        db.session.add(nueva_temporada)
        db.session.commit()
        print(f"Temporada '{temporada}' añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al añadir temporada: {e}")


@cli.command('add_apuesta')
def add_apuesta_race():
    """Añadir una nueva apuesta de carrera."""
    usuario_id = int(input("ID del usuario: "))
    temporada_id = int(input("ID de la temporada: "))
    carrera = input("Nombre de la carrera: ")
    parametro_id = int(input("ID del parámetro de apuesta: "))
    valor = input("Valor de la apuesta: ")
    event = input("Tipo de apuesta(race, qualy, sprint o qualy-sprint: ")

    try:
        nueva_apuesta = Bet(
            user_id=usuario_id,
            season_id=temporada_id,
            race=carrera,
            parameter_bet_id=parametro_id,
            bet_user=valor,
            type=event,
        )
        db.session.add(nueva_apuesta)
        db.session.commit()
        print(f"Apuesta para la carrera '{carrera}' añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al añadir apuesta de carrera: {e}")

# Registra el grupo de comandos en la aplicación
app.cli.add_command(cli)  # 'cli' es el nombre de tu grupo de comandos

if __name__ == "__main__":
    app.run()