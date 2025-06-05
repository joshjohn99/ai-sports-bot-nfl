import requests
from config import Config

HEADERS = {
    'X-RapidAPI-Key': Config.RAPIDAPI_KEY,
    'X-RapidAPI-Host': Config.RAPIDAPI_HOST
}

def get_player_id(player_name):
    url = f"{Config.BASE_URL}players"
    params = {'search': player_name}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    for player in data:
        if player['name'].lower() == player_name.lower():
            return player['id']
    return None

def get_player_stats(player_id, season):
    url = f"{Config.BASE_URL}player-stats/{player_id}"
    params = {'season': season}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()