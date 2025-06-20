import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve RapidAPI credentials from environment variables
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

if not RAPIDAPI_KEY:
    raise ValueError("Missing RapidAPI credentials. Please set RAPIDAPI_KEY in your .env file")

HEADERS = {
    'X-RapidAPI-Key': RAPIDAPI_KEY,
    'X-RapidAPI-Host': 'nfl-api-data.p.rapidapi.com'
}

def get_player_id(player_name):
    url = 'https://nfl-api-data.p.rapidapi.com/players'
    params = {'search': player_name}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    # Assuming the API returns a list of players
    for player in data:
        if player['name'].lower() == player_name.lower():
            return player['id']
    return None

def get_player_stats(player_id, season):
    url = f'https://nfl-api-data.p.rapidapi.com/player-stats/{player_id}'
    params = {'season': season}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_player_gamelog(player_id):
    """Get detailed game-by-game statistics for a player"""
    url = f'https://nfl-api-data.p.rapidapi.com/nfl-ath-gamelog'
    params = {'id': player_id}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# Example usage
# player_name = 'Jordan Love'
# season = '2024'  # Adjust the season as needed
# player_id = get_player_id(player_name)
# if player_id:
#     stats = get_player_stats(player_id, season)
#     touchdowns = stats.get('touchdowns')  # Adjust the key based on the API's response structure
#     print(f"{player_name} threw {touchdowns} touchdowns in {season}.")
# else:
#     print(f"Player ID for {player_name} not found.") 

api_config = {
    'NFL': {
        'base_url': 'https://nfl-api-data.p.rapidapi.com/',
        'endpoints': {
            # Verified from user's list:
            'PlayerDetails': 'nfl-player-info/v1/data',      # Expects ?id={player_id}
            'TeamDetails': 'nfl-team-info/v1/data',        # Expects ?id={team_id}
            'PlayersByTeam': 'nfl-player-listing/v1/data', # Expects ?id={team_id}
            'AllPlayersList': 'nfl-player-listing/v1/data', # Hoping this returns ALL players when no ?id is given
            'AllTeams': 'nfl-team-listing/v1/data',
            'LeagueInfo': 'nfl-leagueinfo',
            
            # From earlier user confirmation for stats:
            'PlayerStats': 'nfl-ath-statistics',           # Expects ?year=...&id=...
            
            # NEW: Team Statistics endpoint for season comparisons
            'TeamStats': 'nfl-team-statistics',            # Expects ?year=...&id=...
            
            # NEW: Player Gamelog endpoint for game-by-game performance
            'PlayerGamelog': 'nfl-ath-gamelog',            # Expects ?id={player_id}

            # 'GameSchedule' and 'Teams' were defaults, keeping them for now unless confirmed otherwise
            'GameSchedule': 'games',
            'Teams': 'teams' 
        },
        'headers': {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'nfl-api-data.p.rapidapi.com'
        }
    },
    'NBA': {
        'base_url': 'https://nba-api-free-data.p.rapidapi.com/',
        'endpoints': {
            # Player endpoints - corrected based on user feedback
            'PlayerInfo': 'nba-player-info',                # Expects ?playerid={player_id}
            'PlayerStats': 'nba-player-stats',              # Expects ?playerid={player_id}
            'PlayerStatsSummary': 'nba-player-stats-summary', # Expects ?playerid={player_id}
            'PlayersByTeam': 'nba-player-list',             # Expects ?teamid={team_id} - CONFIRMED by user
            
            # Team endpoints
            'TeamInfo': 'nba-team-info',                    # Expects ?teamid={team_id}
            'TeamStats': 'nba-team-stats',                  # Expects ?teamid={team_id}
            'AllTeams': 'nba-teams',                        # All NBA teams (to be tested)
            'TeamsList': 'nba-team-list',                   # Alternative teams endpoint
            
            # League endpoints
            'LeagueInfo': 'nba-league-info',                # NBA league information
            'Standings': 'nba-standings',                   # NBA standings
            
            # Game endpoints  
            'GameSchedule': 'nba-games',                    # NBA game schedule
            'PlayerGamelog': 'nba-player-gamelog',          # Expects ?playerid={player_id}
        },
        'headers': {
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
        }
    }
}