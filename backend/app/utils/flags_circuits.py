import requests
import os

session = requests.Session()

from backend.app.utils.logging_utils import setup_logger
logger = setup_logger(__name__)
def get_flag_url(country_name):
    try:
        # response = requests.get(f'https://restcountries.com/v3.1/name/{country_name}')
        # response.raise_for_status()
        # data = response.json()
        # flag_url = data[0]['flags']['png']
        # return flag_url
        file_name = country_name.replace(" ", "_") + ".png"
        # print(f"flag path -> /static/images/flag/{file_name}")
        return f"/static/images/flags/{file_name}"
    except Exception as e:
        print(f'Error fetching flag URL: {e}')
        return None

def get_circuit_url(circuit_name):
    # Construye el nombre de archivo basado en el nombre del circuito
    # Asegúrate de que los nombres de los archivos de imagen coincidan con los nombres de los circuitos.
    file_name = circuit_name.replace(" ", "_") + ".png"  # Reemplaza espacios por guiones bajos

    # Construye la ruta completa a la imagen en la carpeta 'static/images/circuits/'
    file_path = os.path.join('frontend','static', 'images', 'circuits', file_name)

    # Verifica si el archivo existe
    if os.path.exists(file_path):
        # print(f"circuito path -> /static/images/circuits/{file_name}")
        # logger.debug(f"url circuit-> {url_for('static', filename=f'images/circuits/{file_name}')}")
        return f"/static/images/circuits/{file_name}"
    else:
        print(f"No se encontró la imagen para el circuito: {circuit_name}")
        return "/static/images/circuits/default_circuit.png"