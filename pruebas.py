# from datetime import datetime
# import pandas as pd
#
# import fastf1
#
# # Carga los datos de la temporada
# temporada = fastf1.get_event_schedule(datetime.now().year)  # Reemplaza 2024 con el año que te interese
#
# df = pd.DataFrame(temporada)
#
# df_transformed = df.rename(columns={
#     'RoundNumber': 'round',
#     'Country': 'country',
#     'EventName': 'race_name',
#     'EventDate': 'date'
# })
#
# # Función para crear la URL de la bandera
# def obtener_flag_url(pais):
#     pais_normalizado = pais.lower().replace(' ', '_')
#     return f"flag_{pais_normalizado}.png"
#
# # Función para crear la URL del circuito
# def obtener_circuit_image_url(pais):
#     pais_normalizado = pais.lower().replace(' ', '_')
#     return f"circuit_{pais_normalizado}.png"
#
# # Aplicar las funciones para añadir las nuevas columnas
# #df_transformed['flag_url'] = df_transformed['country'].apply(obtener_flag_url)
# df_transformed['circuit_image_url'] = df_transformed['country'].apply(obtener_circuit_image_url)
#
# # Seleccionar y reordenar las columnas para el formato deseado
# #df_transformed = df_transformed[['round', 'date', 'country', 'race_name', 'flag_url', 'circuit_image_url']]
#
# # Convertir a JSON
# json_result = df_transformed.to_json(orient='records', lines=False)
#
# # Imprimir el resultado
# print(json_result)
#
# import requests
# from concurrent.futures import ThreadPoolExecutor
#
# session = requests.Session()
#
#
# def get_circuit_image_url(circuit_name):
#     url = f"https://en.wikipedia.org/w/api.php?action=query&titles={circuit_name}&prop=pageimages&format=json&pithumbsize=500"
#
#     try:
#         response = session.get(url, timeout=10)
#         response.raise_for_status()
#
#         data = response.json()
#         pages = data.get('query', {}).get('pages', {})
#         page = next(iter(pages.values()))
#         return page.get('thumbnail', {}).get('source', None)
#
#     except requests.exceptions.RequestException as e:
#         print(f"Error al obtener la imagen para {circuit_name}: {e}")
#         return None
#
#
# def fetch_images_concurrently(circuit_names):
#     # Usa ThreadPoolExecutor para realizar solicitudes concurrentes
#     with ThreadPoolExecutor(max_workers=5) as executor:
#         results = list(executor.map(get_circuit_image_url, circuit_names))
#     return results
#
# # Ejemplo de uso
# circuit_name = 'Circuit_de_Monaco'
# print(get_circuit_image_url(circuit_name))
#
# # Ejemplo de uso
# country_name = df_transformed["race_name"][3]
# print(get_circuit_image_url(country_name))

from config.db_config import db  # Asegúrate de importar la instancia de SQLAlchemy
from backend.application import create_app  # Importa tu aplicación Flask
import json
from backend.app.models.parameters_bets import BetTemplate

# Crear la aplicación Flask
app = create_app()

# Lista de pilotos
tires = [
    "Soft", "Medium", "Hard"
]

# Convertir la lista a JSON
options_json = json.dumps({"tires": tires})

# Ejecutar dentro del contexto de la aplicación
with app.app_context():
    # Buscar el registro que quieres actualizar
    bet_template = BetTemplate.query.filter_by(season_id=2, bet_score_id=19).first()

    if bet_template:
        bet_template.options = options_json  # Actualizar la columna
        db.session.commit()
        print("Columna 'options' actualizada correctamente.")
    else:
        print("No se encontró el registro.")