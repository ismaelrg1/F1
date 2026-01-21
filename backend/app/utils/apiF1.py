from threading import Thread

import fastf1
import pandas as pd
from flask import current_app

from backend.app.utils.flags_circuits import get_flag_url, get_circuit_url
from backend.app.models.schedule import RaceEvent
from config.db_config import db

from backend.app.utils.logging_utils import setup_logger
logger = setup_logger(__name__)
def get_schedule(year=int) -> list:
    """
        Funcion para obtener todas las carreras de una season de la BD y en segundo plano comprobar si no ha habido
        modificaciones en fastF1

    :param year: año
    :return: Toda la informacion de las carreras de una season de la BD
    """

    # Verifica si los datos de la temporada ya están en la base de datos
    events_in_db = RaceEvent.query.filter_by(year=year).all()
    # print(f"Current DB: {events_in_db}")

    if events_in_db:
        # Si hay datos en la base de datos, devuélvelos inmediatamente
        races = [{
            'round': event.round_number,
            'year': event.year,
            'formatted_date': event.event_date.strftime('%d-%b'),
            'country': event.country,
            'race_name': event.event_name,
            'flag_url': event.flag_url,
            'time_session1': event.time_session1,
            'time_session2': event.time_session2,
            'time_session3': event.time_session3,
            'time_session4': event.time_session4,
            'time_session5': event.time_session5,
            'event_format': event.event_format,
            'circuit_image_url': event.circuit_image_url
        } for event in events_in_db]

        # En segundo plano, busca en FastF1 y actualiza si es necesario
        app = current_app._get_current_object()
        Thread(target=fetch_and_compare_schedule, args=(year, app)).start()


        return races
    else:
        # Si no hay datos, busca en FastF1 y almacena en la base de datos
        races = fetch_and_store_schedule(year)
        return races


def fetch_and_store_schedule(year):
    """
        Buscar datos de las carreras en fastF1 y guardar datos en la BD

    :param year: año
    :return: Toda la informacion de las carreras de una season de la BD
    """
    # Obtener la información de FastF1
    # print(f"Consultando la API de FastF1")
    df_transformed = fetch_api(year)

    # Guardar los datos válidos en la base de datos
    store_schedule(df_transformed)

    # Convertir el DataFrame a una lista de diccionarios para devolverlo
    # Aquí formateamos las fechas a strings antes de pasarlas a la vista
    df_transformed['formatted_date'] = df_transformed['event_date'].dt.strftime('%d-%b')

    # Reemplazar "-" por espacios en la columna 'race_name'
    df_transformed['race_name'] = df_transformed['race_name'].str.replace("-", " ")

    races = df_transformed[
        ['round', 'formatted_date', 'country', 'race_name', 'flag_url', 'circuit_image_url', 'time_session1', 'time_session2', 'time_session3', 'time_session4', 'time_session5', 'event_format']].to_dict(
        orient='records')

    return races

def store_schedule(races):
    """
        Guardar datos de las carreras en la BD
    :param races: datos de las carreras
    """

    # Guardar los datos válidos en la base de datos
    for row in races.itertuples():
        event = RaceEvent(
            round_number=row.round,
            year=row.year,
            country=row.country,
            event_name=row.race_name,
            event_date=row.event_date,
            time_session1=row.time_session1,
            time_session2=row.time_session2,
            time_session3=row.time_session3,
            time_session4=row.time_session4,
            time_session5=row.time_session5,
            event_format=row.event_format,
            flag_url=row.flag_url,
            circuit_image_url=row.circuit_image_url
        )
        db.session.add(event)
    db.session.commit()


def fetch_api(year):
    """
        Buscar datos de las carreras en fastF1

    :param year: año
    :return: datos de la carrea
    """
    temporada = fastf1.get_event_schedule(year)

    # Convertir el DataFrame y renombrar columnas
    df = pd.DataFrame(temporada)
    df_transformed = df.rename(columns={
        'RoundNumber': 'round',
        'Country': 'country',
        'EventName': 'race_name',
        'EventDate': 'event_date',
        'Session1DateUtc': 'time_session1',
        'Session2DateUtc': 'time_session2',
        'Session3DateUtc': 'time_session3',
        'Session4DateUtc': 'time_session4',
        'Session5DateUtc': 'time_session5',
        'EventFormat': 'event_format',
    })

    # print(f"Current API -> {df_transformed['time_session5']}")

    # Aplicar las funciones para obtener las URLs
    df_transformed['flag_url'] = df_transformed['country'].apply(get_flag_url)
    df_transformed['circuit_image_url'] = df_transformed['race_name'].apply(get_circuit_url)

    # Convertir la columna de fechas a tipo DateTime para la base de datos
    df_transformed['event_date'] = pd.to_datetime(df_transformed['event_date'], errors='coerce', format='%Y-%m-%d')

    for col in ['time_session1', 'time_session2', 'time_session3', 'time_session4', 'time_session5']:
        df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce', format='%Y-%m-%d %H:%M:%S')
        df_transformed[col] = df_transformed[col].fillna(df_transformed['event_date'])  # Rellenar NaN con la fecha base

    # Crear la columna 'year' con solo el año en formato YYYY
    df_transformed['year'] = df_transformed['event_date'].dt.year

    # Rellena las columnas time_session1 a time_session5 con el valor de la columna date cuando haya valores nulos
    for col in ['time_session1', 'time_session2', 'time_session3', 'time_session4', 'time_session5']:
        df_transformed[col] = df_transformed[col].fillna(df_transformed['event_date'])

    df_transformed = df_transformed[['round', 'country', 'race_name', 'event_date', 'time_session1',
                                     'time_session2', 'time_session3', 'time_session4', 'time_session5',
                                     'event_format', 'flag_url', 'circuit_image_url', 'year']]

    # print(f"Next Current API -> {df_transformed['time_session5']}")

    return df_transformed

def fetch_and_compare_schedule(year, app):
    """
        Funcion que busca los datos de fastF1 y los compara con la BD, si fastF1 != BD -> Actualiza BD, sino -> nada

    :param year: año
    :param app: contexto de la aplicacion
    """

    print(f'inicializando fecth_and_compare_schedule')
    with app.app_context():
        # Obtener los datos desde FastF1
        new_races = fetch_api(year)

        # Comparar con la base de datos
        stored_races = RaceEvent.query.filter_by(year=year).all()

        # Formatear los datos almacenados en la base de datos para comparar
        stored_races_list = [{
            'round': event.round_number,
            'year': event.year,
            'event_date': event.event_date,
            'country': event.country,
            'race_name': event.event_name,
            'event_format': event.event_format,
            'time_session1': event.time_session1,
            'time_session2': event.time_session2,
            'time_session3': event.time_session3,
            'time_session4': event.time_session4,
            'time_session5': event.time_session5,
            'flag_url': event.flag_url,
            'circuit_image_url': event.circuit_image_url
        } for event in stored_races]


        # Comparamos si los datos son diferentes
        new_races_sorted = new_races.sort_index(axis=1)
        stored_races_sorted = pd.DataFrame(stored_races_list).sort_index(axis=1)

        new_races_sorted = new_races_sorted.sort_index()
        stored_races_sorted = stored_races_sorted.sort_index()

        stored_races_sorted = stored_races_sorted.astype(new_races_sorted.dtypes)

        if not new_races_sorted.equals(stored_races_sorted):
            print(f"Actualizando la base de datos con nuevos datos de FastF1.")

            # 🔹 Eliminar los datos antiguos
            db.session.query(RaceEvent).filter(RaceEvent.year == year).delete(synchronize_session=False)
            db.session.commit()

            # 🔹 Expulsar objetos de la sesión para evitar conflictos
            db.session.expunge_all()

            try:
                # 🔹 Insertar los nuevos datos
                for index, race in new_races.iterrows():
                    event = RaceEvent(
                        round_number=int(race['round']),
                        year=int(race['year']),
                        country=race['country'],
                        event_name=race['race_name'],
                        event_date=race['event_date'],
                        flag_url=race['flag_url'],
                        circuit_image_url=race['circuit_image_url'],
                        event_format=race['event_format'],
                        time_session1=race['time_session1'],
                        time_session2=race['time_session2'],
                        time_session3=race['time_session3'],
                        time_session4=race['time_session4'],
                        time_session5=race['time_session5'],
                    )
                    db.session.add(event)

                # 🔹 Confirmar los cambios
                db.session.commit()
            except Exception as e:
                print(f"❌ Error al insertar nuevos datos: {e}")
                db.session.rollback()  # Revertir cambios en caso de error

        else:
            print('Bases de datos iguales, NO guardamos')