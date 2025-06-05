"""
NFL API endpoint configurations.
"""

from typing import Dict

# API Endpoints
ENDPOINTS: Dict[str, str] = {
    'player_stats': 'nfl-ath-statistics',
    'player_details': 'nfl-player-info/v1/data',
    'team_details': 'nfl-team-info/v1/data',
    'team_roster': 'nfl-player-listing/v1/data',
    'all_teams': 'nfl-team-listing/v1/data',
    'league_info': 'nfl-leagueinfo',
    'team_stats': 'nfl-team-statistics',
    'player_gamelog': 'nfl-ath-gamelog'
}

# API Configuration
API_CONFIG = {
    'base_url': 'https://nfl-api-data.p.rapidapi.com/',
    'host': 'nfl-api-data.p.rapidapi.com',
    'timeout': 30,  # seconds
    'max_retries': 3,
    'retry_delay': 1  # seconds
} 