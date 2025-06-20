# stat_retriever_agent.py
from sports_bot.config.api_config import api_config
import requests
import json
from datetime import datetime
from urllib.parse import urljoin, urlencode
import os # Ensure os is imported
import time # For potential delays, though primarily used in loader
from typing import Optional, List, Dict, Any # Ensure List, Dict, Any are imported

# Rich imports
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Make ensure_dir accessible 
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

from sports_bot.cache.shared_cache import get_cache_instance
from sports_bot.db.models import db_manager, Player, Team, PlayerStats, CareerStats

# --- Local Data Store Configuration ---
# This should ideally be consistent with data_loader.py or from a shared config
# Assuming stat_retriever.py is in sports_bot_beta/src/sports_bot/core/
# So, ../../.. goes up to sports_bot_beta/
DATA_STORE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'daily_store')

# Define core positions CONSISTENTLY with data_loader.py
CORE_PLAYER_POSITIONS_FOR_STAT_RETRIEVER = {
    "NFL": ["QB", "RB", "WR", "TE", "FB",
            "DE", "DT", "LB", "CB", "S", "MLB", "OLB", "ILB", "EDGE", "DL", "DB",
            "K", "P"]
    # Add other sports as needed, ensure this matches data_loader.py
}

class StatRetrieverApiAgent:
    def __init__(self, api_config_obj):
        self.api_config = api_config_obj
        self.console = Console()
        self.cache = get_cache_instance()
        self.db_session = db_manager.get_session()
        self.position_priority = {
            'QB': 100, 'RB': 90, 'WR': 85, 'TE': 80, 'FB': 75, 'K': 70, 'P': 65,
            'LB': 60, 'MLB': 60, 'OLB': 60, 'ILB': 60, 'DE': 55, 'DT': 50,
            'CB': 45, 'S': 40, 'DB': 40, 'EDGE': 55, 'DL': 50, 'OL': 30,
            'T': 30, 'G': 25, 'C': 25, 'LS': 20
        }

    def get_current_season(self, sport: str) -> str:
        current_year = datetime.now().year
        if sport == 'NFL' and datetime.now().month < 9:
            return str(current_year - 1)
        return str(current_year)

    def find_best_matching_player(self, player_name: str) -> tuple:
        """
        Intelligently find the best matching player by name from the database.
        Handles cases where multiple players have the same name by scoring them.
        """
        matches = self.db_session.query(Player).filter(Player.name.ilike(f"%{player_name}%")).all()

        if not matches:
            return None, 0.0, []
        if len(matches) == 1:
            return matches[0], 1.0, []

        scored_players = []
        current_season = self.get_current_season("NFL")
        for player in matches:
            score = 0
            position_score = self.position_priority.get(player.position, 10)
            score += position_score * 10
            
            stats = self.db_session.query(PlayerStats).filter_by(player_id=player.id, season=current_season).first()
            if stats:
                score += (stats.games_played or 0) * 5
                total_stats = (
                    (stats.passing_yards or 0) + (stats.rushing_yards or 0) + (stats.receiving_yards or 0) +
                    ((stats.passing_touchdowns or 0) * 20) + ((stats.rushing_touchdowns or 0) * 20) +
                    ((stats.receiving_touchdowns or 0) * 20) + ((stats.sacks or 0) * 25) +
                    ((stats.interceptions or 0) * 30)
                )
                score += min(total_stats / 100, 50)
            
            if player.name.lower() == player_name.lower():
                score += 100
            elif player_name.lower() in player.name.lower():
                score += 50
            
            scored_players.append((player, score))

        scored_players.sort(key=lambda x: x[1], reverse=True)
        best_player, best_score = scored_players[0]
        alternatives = [p for p, s in scored_players[1:4]]

        if len(scored_players) > 1 and (best_score - scored_players[1][1]) > 100:
            return best_player, 0.8, alternatives
        else:
            return best_player, 0.5, alternatives
            
    def fetch_stats(self, query_context):
        sport = query_context.sport
        player_name = query_context.player_names[0]
        season = self.get_current_season(sport)

        player, confidence, alternatives = self.find_best_matching_player(player_name)

        if not player:
            return {"error": f"Player '{player_name}' not found."}

        if confidence < 0.7 and alternatives:
            all_matches = [player] + alternatives
            return {
                "error": "Multiple players found",
                "player_name": player_name,
                "matching_players": [
                    {
                        "player_id": p.id,
                        "player_info": {"fullName": p.name},
                        "team_name": p.current_team.name if p.current_team else "N/A",
                        "position": p.position
                    } for p in all_matches
                ],
                "follow_up_question": "Multiple players found, please specify."
            }
        
        stats = self.db_session.query(PlayerStats).filter_by(player_id=player.id, season=season).first()
        if not stats:
            # Fallback to API if no stats in DB
            api_stats = self._fetch_stats_from_api(player.external_id, season, sport)
            if "error" in api_stats:
                return api_stats
            return self._format_api_stats_response(player, api_stats)

        return self._format_stats_response(player, stats)

    def _fetch_stats_from_api(self, player_id, season, sport):
        url, headers = self.build_url(sport, 'PlayerStats', query_params={'id': player_id, 'year': season})
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"API fetch failed: {e}"}

    def _format_stats_response(self, player, stats):
        return {
            "player_fullName": player.name,
            "simple_stats": {c.name: getattr(stats, c.name) for c in stats.__table__.columns if c.name not in ['id', 'player_id', 'created_at', 'updated_at']}
        }
    
    def _format_api_stats_response(self, player, api_stats):
        simple_stats = {}
        stats_data = api_stats.get('statistics', {}).get('splits', {}).get('categories', [])
        for category in stats_data:
            for stat in category.get('stats', []):
                if stat.get('name') in ['passingYards', 'passingTouchdowns', 'rushingYards', 'rushingTouchdowns', 'sacks', 'tackles', 'interceptions']:
                    simple_stats[stat['name']] = stat.get('value')
        return {"player_fullName": player.name, "simple_stats": simple_stats}

    def build_url(self, sport: str, endpoint_key: str, path_params: dict = None, query_params: dict = None):
        sport_conf = self.api_config[sport]
        base_url = sport_conf['base_url']
        endpoint_template = sport_conf['endpoints'].get(endpoint_key, '')
        if not endpoint_template: raise ValueError(f"Endpoint key '{endpoint_key}' not found for '{sport}'")
        endpoint = endpoint_template
        if path_params: 
            for k, v in path_params.items(): endpoint = endpoint.replace(f"{{{k}}}", str(v))
        url = urljoin(base_url, endpoint.lstrip('/'))
        if query_params: url = f"{url}?{urlencode(query_params)}"
        return url, sport_conf['headers']
    
    def get_season_format(self, sport, season_years=None):
        if season_years and len(season_years) > 0:
            year = season_years[0]
            if sport == "NFL": return str(year)
            elif sport in ["NBA", "NHL"]: return f"{year}-{year + 1}-regular"
            else: return f"{year}-regular"
        return self.get_current_season(sport)

    def fetch_league_leaders(self, query_context):
        return {"error": "League leaders not fully implemented."}

    @classmethod
    def get_aggregatable_stats(cls):
        """Get list of stats that can be aggregated across seasons/games."""
        return [name for name, info in cls.STATS_MAPPING.items() 
                if info.get('aggregatable', False)]
    
    @classmethod
    def get_stats_by_category(cls, category):
        """Get all stats in a specific category."""
        return [name for name, info in cls.STATS_MAPPING.items() 
                if info.get('category') == category]
    
    @classmethod
    def get_all_user_terms(cls):
        """Get all possible user terms for debugging/reference."""
        all_terms = []
        for stat_name, info in cls.STATS_MAPPING.items():
            all_terms.extend(info.get('user_terms', []))
            all_terms.append(stat_name.lower())
            if info.get('display_name'):
                all_terms.append(info.get('display_name').lower())
            if info.get('abbreviation'):
                all_terms.append(info.get('abbreviation').lower())
        return sorted(set(all_terms))