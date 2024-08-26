import requests


def get_flag_url(country_name):
    try:
        response = requests.get(f'https://restcountries.com/v3.1/name/{country_name}')
        response.raise_for_status()
        data = response.json()
        flag_url = data[0]['flags']['png']
        return flag_url
    except Exception as e:
        print(f'Error fetching flag URL: {e}')
        return None

def get_circuit_url(circuit_name):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={circuit_name}&prop=pageimages&format=json&pithumbsize=500"
    response = requests.get(url)
    data = response.json()
    pages = data['query']['pages']
    page = next(iter(pages.values()))
    return page.get('thumbnail', {}).get('source', None)