"""
API configuration and utilities for sports data retrieval.
Handles player search, data fetching, and response formatting across all sports.
"""

import os
import requests
from dotenv import load_dotenv
import sqlite3
from typing import Dict, List, Optional, Any, Union
from .player_disambiguation import disambiguator
import logging

logger = logging.getLogger(__name__)

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

class UniversalApiConfig:
    """Universal API configuration for all sports."""
    
    def __init__(self):
        self.db_path = 'data/sports_stats.db'
        self.sport_endpoints = {
            'NFL': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
                'people_endpoint': 'athletes',
                'team_roster_endpoint': 'teams/{team_id}/roster'
            },
            'NBA': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba',
                'people_endpoint': 'athletes', 
                'team_roster_endpoint': 'teams/{team_id}/roster'
            },
            'MLB': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb',
                'people_endpoint': 'athletes',
                'team_roster_endpoint': 'teams/{team_id}/roster'
            },
            'NHL': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl',
                'people_endpoint': 'athletes',
                'team_roster_endpoint': 'teams/{team_id}/roster'
            }
        }
    
    def get_universal_player_id(self, 
                               sport: str,
                               player_name: str, 
                               stat_context: List[str] = None,
                               team_context: str = None,
                               season_context: str = None) -> Optional[str]:
        """
        Universal player search function that works across all sports.
        
        This function:
        1. Searches the local database for all players matching the name
        2. Searches across all teams in the specified sport
        3. Uses the universal disambiguation system to find the best match
        4. Returns the most likely player ID
        
        Args:
            sport: Sport code (NFL, NBA, MLB, NHL, etc.)
            player_name: Name to search for
            stat_context: List of stats being requested (helps with disambiguation)
            team_context: Team name/abbreviation if mentioned
            season_context: Season if specified
            
        Returns:
            Best matching player ID or None if not found
        """
        logger.info(f"🔍 Universal search for '{player_name}' in {sport}")
        
        # Step 1: Generate name variations
        name_variations = disambiguator.expand_name_variations(player_name)
        logger.info(f"   Name variations: {name_variations}")
        
        # Step 2: Search database for all matching players
        candidates = self._search_database_for_players(sport, name_variations)
        logger.info(f"   Found {len(candidates)} database candidates")
        
        # Step 3: If no database matches, try API search
        if not candidates:
            candidates = self._search_api_for_players(sport, name_variations)
            logger.info(f"   Found {len(candidates)} API candidates")
        
        # Step 4: Use disambiguation system to find best match
        if candidates:
            best_match = disambiguator.disambiguate_players(
                candidates=candidates,
                sport=sport,
                stat_context=stat_context,
                team_context=team_context,
                season_context=season_context
            )
            
            if best_match:
                player_id = str(best_match.get('id', best_match.get('external_id', '')))
                logger.info(f"   ✅ Best match: {best_match.get('name', 'Unknown')} (ID: {player_id})")
                return player_id
        
        logger.warning(f"   ❌ No match found for '{player_name}' in {sport}")
        return None
    
    def _search_database_for_players(self, sport: str, name_variations: List[str]) -> List[Dict[str, Any]]:
        """Search local database for player matches across all teams."""
        candidates = []
        
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}")
            return candidates
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build parameterized query for all name variations 
            # Note: This is safe SQL construction - placeholders are created dynamically
            # but all actual values are bound as parameters to prevent injection
            placeholders = ','.join(['?' for _ in name_variations])
            
            # Parameterized SQL query - all user input is bound as parameters
            query = """
                SELECT DISTINCT 
                    p.external_id as id,
                    p.name,
                    p.position,
                    p.current_team_id,
                    t.name as team_name,
                    t.abbreviation as team_abbr
                FROM players p
                LEFT JOIN teams t ON p.current_team_id = t.id
                WHERE (
                    p.name IN ({placeholders})
                    OR p.name LIKE ? 
                    OR p.name LIKE ?
                )
                ORDER BY p.name, p.position
            """.format(placeholders=placeholders)
            
            # All parameters are safely bound - no SQL injection risk
            params = name_variations + [f"%{name_variations[0]}%", f"{name_variations[0]}%"]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to candidate dictionaries
            for row in rows:
                candidate = {
                    'id': row[0],
                    'name': row[1],
                    'position': row[2] or '',
                    'team': row[5] or row[4] or '',  # Use abbreviation if available, otherwise full name
                    'active': True  # Assume active since there's no active column
                }
                candidates.append(candidate)
                logger.debug(f"     DB candidate: {candidate}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
        
        return candidates
    
    def _search_api_for_players(self, sport: str, name_variations: List[str]) -> List[Dict[str, Any]]:
        """Search API for player matches if database search fails."""
        candidates = []
        
        # Note: This would implement API searches for each sport
        # For now, we'll focus on database searches since that's where the data is
        logger.info(f"API search not yet implemented for {sport}")
        
        return candidates
    
    def _normalize_player_data(self, player_data: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """Normalize player data from different sources into standard format."""
        # Handle different API response formats
        normalized = {
            'id': str(player_data.get('id', player_data.get('external_id', ''))),
            'name': player_data.get('name', player_data.get('fullName', player_data.get('displayName', ''))),
            'position': '',
            'team': '',
            'active': player_data.get('active', True)
        }
        
        # Handle position data (can be string or object)
        position = player_data.get('position')
        if isinstance(position, dict):
            normalized['position'] = position.get('abbreviation', position.get('name', ''))
        else:
            normalized['position'] = str(position) if position else ''
        
        # Handle team data (can be string or object)
        team = player_data.get('team')
        if isinstance(team, dict):
            normalized['team'] = team.get('abbreviation', team.get('name', ''))
        else:
            normalized['team'] = str(team) if team else ''
        
        return normalized

# Global instance
api_config = UniversalApiConfig()

def get_player_id(player_name: str, 
                  stat_context: List[str] = None,
                  sport: str = 'NFL',
                  team_context: str = None,
                  season_context: str = None) -> Optional[str]:
    """
    Universal player ID lookup function.
    
    This function searches across all teams in the specified sport and uses
    advanced disambiguation logic to find the most likely correct player.
    
    Args:
        player_name: Name to search for
        stat_context: List of stats being requested (helps with disambiguation)
        sport: Sport code (NFL, NBA, MLB, NHL, etc.)
        team_context: Team name/abbreviation if mentioned  
        season_context: Season if specified
        
    Returns:
        Player ID string or None if not found
    """
    return api_config.get_universal_player_id(
        sport=sport,
        player_name=player_name,
        stat_context=stat_context,
        team_context=team_context,
        season_context=season_context
    )

def get_player_stats(player_id, season):
    """Get player statistics for a specific season (NFL-specific endpoint)"""
    url = f'https://nfl-api-data.p.rapidapi.com/player-stats/{player_id}'
    params = {'season': season}
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def get_player_gamelog(player_id):
    """Get detailed game-by-game statistics for a player (NFL-specific endpoint)"""
    url = f'https://nfl-api-data.p.rapidapi.com/nfl-ath-gamelog'
    params = {'id': player_id}
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# Legacy API configuration (maintained for backward compatibility)
legacy_api_config = {
    'NFL': {
        'base_url': 'https://nfl-api-data.p.rapidapi.com/',
        'endpoints': {
            'PlayerDetails': 'nfl-player-info/v1/data',
            'TeamDetails': 'nfl-team-info/v1/data',
            'PlayersByTeam': 'nfl-player-listing/v1/data',
            'AllPlayersList': 'nfl-player-listing/v1/data',
            'AllTeams': 'nfl-team-listing/v1/data',
            'LeagueInfo': 'nfl-leagueinfo',
            'PlayerStats': 'nfl-ath-statistics',
            'TeamStats': 'nfl-team-statistics',
            'PlayerGamelog': 'nfl-ath-gamelog',
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