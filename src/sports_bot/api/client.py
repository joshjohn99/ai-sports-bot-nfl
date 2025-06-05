"""
API client for NFL data retrieval.
"""

import os
import requests
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import logging
from ..utils.logging import get_logger

logger = get_logger(__name__)

class NFLApiClient:
    """Client for interacting with the NFL API."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'nfl-api-data.p.rapidapi.com'
        }
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request with retries and error handling."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def get_player_stats(self, player_id: str, season: str) -> Dict[str, Any]:
        """Get player statistics for a specific season."""
        return self.make_request(
            'nfl-ath-statistics',
            {'id': player_id, 'year': season}
        )
    
    def get_team_roster(self, team_id: str) -> Dict[str, Any]:
        """Get team roster information."""
        return self.make_request(
            'nfl-player-listing/v1/data',
            {'id': team_id}
        )
    
    def get_all_teams(self) -> Dict[str, Any]:
        """Get information for all teams."""
        return self.make_request('nfl-team-listing/v1/data')
    
    def get_player_details(self, player_id: str) -> Dict[str, Any]:
        """Get detailed player information."""
        return self.make_request(
            'nfl-player-info/v1/data',
            {'id': player_id}
        )
    
    def get_team_details(self, team_id: str) -> Dict[str, Any]:
        """Get detailed team information."""
        return self.make_request(
            'nfl-team-info/v1/data',
            {'id': team_id}
        ) 