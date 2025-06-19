# stat_retriever_agent.py
from ..config.api_config import api_config
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
        os.makedirs(directory)

from .shared_cache import get_cache_instance
from .database import db_manager, Player, Team, PlayerStats, CareerStats

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
    def __init__(self, api_config_obj): # api_config_obj to avoid conflict with any imported api_config module
        self.api_config = api_config_obj
        self.console = Console(highlight=False)
        self.shared_cache = get_cache_instance()
        self.db_session = db_manager.get_session()
        self.console.print(f"[dim white]INITIALIZED[/dim white]: Using database and shared cache.")

    def _load_local_all_teams(self, sport_code: str) -> Optional[list]:
        file_path = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'all_teams.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f: data = json.load(f)
                self.console.print(f"  [green]LOCAL_HIT (AllTeams)[/green]: Loaded from {file_path}")
                return data
            except Exception as e: self.console.print(f"  [yellow]LOCAL_ERROR (AllTeams)[/yellow]: {file_path}: {e}")
        return None

    def _load_local_team_roster(self, sport_code: str, team_id: str) -> Optional[dict]:
        file_path = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'rosters', f"team_{team_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f: data = json.load(f)
                # self.console.print(f"    [green]LOCAL_HIT (TeamRoster)[/green]: Team {team_id} from {file_path}") # Too verbose for many teams
                return data
            except Exception as e: self.console.print(f"    [yellow]LOCAL_ERROR (TeamRoster)[/yellow]: {file_path}: {e}")
        return None

    def _load_local_player_stats(self, sport_code: str, player_id: str, season: str) -> Optional[dict]:
        season_year_for_path = season.split('-')[0]
        file_path = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'player_stats', str(season_year_for_path), f"player_{player_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f: data = json.load(f)
                return data # Success, no print needed here as it's per player
            except Exception as e: self.console.print(f"      [yellow]LOCAL_ERROR (PlayerStats)[/yellow]: {file_path}: {e}")
        return None

    def _save_player_stats_locally(self, sport_code: str, player_id: str, season: str, data: dict):
        try:
            season_year_for_path = season.split('-')[0]
            season_stats_dir = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'player_stats', str(season_year_for_path))
            file_path = os.path.join(season_stats_dir, f"player_{player_id}.json")
            ensure_dir(file_path)
            with open(file_path, 'w') as f: json.dump(data, f, indent=2)
            self.console.print(f"      [blue]LOCAL_SAVE (PlayerStats)[/blue]: Saved API data for {player_id} Season {season} to {file_path}")
        except Exception as e: self.console.print(f"      [yellow]LOCAL_SAVE_ERROR (PlayerStats)[/yellow]: {file_path}: {e}")

    def get_current_season(self, sport):
        current_year = datetime.now().year
        if datetime.now().month < 8: current_year -= 1
        if sport == "NFL": return str(current_year)
        elif sport == "NBA": return f"{current_year}-{current_year + 1}-regular"
        return f"{current_year}-regular"

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

    # Placeholder for _get_player_id - ensure it uses local data strategy from previous iterations
    def _get_player_id(self, sport: str, player_name: str):
        # This should be the version that prioritizes local data for AllTeams and TeamRosters
        # For this edit, we focus on fetch_league_leaders, assuming _get_player_id is correctly implemented elsewhere
        self.console.print(f"[dim]Stubbed _get_player_id called for {player_name}. Ensure full version is used.[/dim]")
        return None, None, None # Placeholder

    # Placeholder for _get_player_id_with_context
    def _get_player_id_with_context(self, sport: str, player_name: str, query_context=None):
        # This would call the refined _get_player_id
        return self._get_player_id(sport, player_name) # Simplified call for stub

    # Placeholder for extract_stats_using_schema
    def extract_stats_using_schema(self, data, requested_metrics, sport='NFL'):
        # This should be the full schema extraction logic
        # For this edit, we return a simplified mock if data is present
        extracted = {}
        if data and requested_metrics:
            for metric in requested_metrics:
                # Simplistic mock extraction - replace with your actual schema logic
                if isinstance(data, dict) and 'statistics' in data: # A guess at typical structure
                     extracted[metric] = {'value': 'ExtractedValue', 'displayValue': 'Extracted Value'}
                else:
                     extracted[metric] = {'value': 'MockValue', 'displayValue': 'Mock Value'}
        return extracted

    def get_season_format(self, sport, season_years=None):
        if season_years and len(season_years) > 0:
            year = season_years[0]
            if sport == "NFL": return str(year)
            elif sport in ["NBA", "NHL"]: return f"{year}-{year + 1}-regular"
            else: return f"{year}-regular"
        return self.get_current_season(sport)

    def fetch_stats(self, query_context):
        """Fetch stats with database as primary source."""
        sport = query_context.sport
        if not sport or sport not in self.api_config:
            return {"error": f"Sport '{sport}' not configured or not provided."}

        if hasattr(query_context, 'strategy') and query_context.strategy == "leaderboard_query":
            return self.fetch_league_leaders(query_context)

        # Get player info
        player_name = query_context.player_names[0] if query_context.player_names else None
        if not player_name:
            return {"error": "No player specified"}

        # Try to get player from database first
        player = self.db_session.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
        
        if not player:
            # If not in database, try API
            player_id, player_info, _ = self._get_player_id_with_context(sport, player_name, query_context)
            if not player_id:
                return {"error": f"Player '{player_name}' not found"}
            
            # Create new player in database
            player = Player(
                external_id=str(player_id),
                name=player_info.get('fullName'),
                position=player_info.get('position', {}).get('abbreviation')
            )
            self.db_session.add(player)
            self.db_session.commit()

        # Get season
        season = self.get_season_format(sport, query_context.season_years)

        # Try to get stats from database
        stats = self.db_session.query(PlayerStats).filter_by(
            player_id=player.id,
            season=season
        ).first()

        if stats:
            # Convert database stats to API response format
            return self._format_stats_response(player, stats, season, sport, "database")
        else:
            # If not in database, try API
            api_stats = self._fetch_stats_from_api(player.external_id, season, sport)
            if isinstance(api_stats, dict) and "error" not in api_stats:
                # Save to database
                stats = PlayerStats(
                    player_id=player.id,
                    season=season,
                    games_played=api_stats.get('gamesPlayed'),
                    games_started=api_stats.get('gamesStarted'),
                    passing_yards=api_stats.get('passingYards'),
                    passing_touchdowns=api_stats.get('passingTouchdowns'),
                    rushing_yards=api_stats.get('rushingYards'),
                    rushing_touchdowns=api_stats.get('rushingTouchdowns'),
                    receiving_yards=api_stats.get('receivingYards'),
                    receptions=api_stats.get('receptions'),
                    receiving_touchdowns=api_stats.get('receivingTouchdowns'),
                    sacks=api_stats.get('sacks'),
                    tackles=api_stats.get('tackles'),
                    interceptions=api_stats.get('interceptions'),
                    forced_fumbles=api_stats.get('forcedFumbles'),
                    field_goals_made=api_stats.get('fieldGoalsMade'),
                    field_goals_attempted=api_stats.get('fieldGoalsAttempted'),
                    extra_points_made=api_stats.get('extraPointsMade')
                )
                self.db_session.add(stats)
                self.db_session.commit()
                
                # Update career stats
                db_manager.update_career_stats(player.id)
                
                return self._format_stats_response(player, stats, season, sport, "api")
            
            return api_stats  # Return error from API

    def fetch_league_leaders(self, query_context):
        """Fetch league leaders using database."""
        sport = query_context.sport
        stat_to_rank_by = query_context.metrics_needed[0] if query_context.metrics_needed else None
        season = self.get_season_format(sport, query_context.season_years)
        
        if not stat_to_rank_by:
            return {"error": "No stat specified for leaderboard"}
            
        # Map stat name to database column
        stat_column = getattr(PlayerStats, self._map_stat_to_column(stat_to_rank_by), None)
        if not stat_column:
            return {"error": f"Stat '{stat_to_rank_by}' not supported"}
            
        # Get position filter
        positions = self._get_positions_for_stat(stat_to_rank_by, sport)
        
        # Query database for leaders
        query = self.db_session.query(
            Player,
            PlayerStats
        ).join(
            PlayerStats
        ).filter(
            PlayerStats.season == season
        )
        
        if positions:
            query = query.filter(Player.position.in_(positions))
            
        # Order by the stat and limit results
        query = query.order_by(stat_column.desc())
        limit = getattr(query_context, 'limit', 10)
        results = query.limit(limit).all()
        
        # Format results
        leaders = []
        for rank, (player, stats) in enumerate(results, 1):
            stat_value = getattr(stats, self._map_stat_to_column(stat_to_rank_by))
            leaders.append({
                'rank': rank,
                'playerName': player.name,
                'position': player.position,
                'statValue': str(stat_value)
            })
            
        return {
            "query": query_context.question,
            "sport": sport,
            "season": season,
            "ranked_stat": stat_to_rank_by,
            "leaders": leaders,
            "status": f"Successfully ranked {len(leaders)} players using database"
        }

    def _map_stat_to_column(self, stat_name: str) -> str:
        """Map API stat name to database column name."""
        mapping = {
            'passingTouchdowns': 'passing_touchdowns',
            'passingYards': 'passing_yards',
            'rushingYards': 'rushing_yards',
            'rushingTouchdowns': 'rushing_touchdowns',
            'receivingYards': 'receiving_yards',
            'receptions': 'receptions',
            'receivingTouchdowns': 'receiving_touchdowns',
            'sacks': 'sacks',
            'tackles': 'tackles',
            'interceptions': 'interceptions',
            'forcedFumbles': 'forced_fumbles',
            'fieldGoalsMade': 'field_goals_made',
            'fieldGoalsAttempted': 'field_goals_attempted',
            'extraPointsMade': 'extra_points_made'
        }
        return mapping.get(stat_name, stat_name.lower())

    def _get_positions_for_stat(self, stat_name: str, sport: str) -> List[str]:
        """Get relevant positions for a stat."""
        stat_positions = {
            'passingTouchdowns': ['QB'],
            'passingYards': ['QB'],
            'rushingYards': ['RB', 'QB', 'FB'],
            'rushingTouchdowns': ['RB', 'QB', 'FB'],
            'receivingYards': ['WR', 'TE', 'RB'],
            'receptions': ['WR', 'TE', 'RB'],
            'sacks': ['DE', 'DT', 'LB', 'OLB', 'ILB', 'MLB', 'EDGE', 'DL'],
            'tackles': ['LB', 'DE', 'DT', 'S', 'CB', 'MLB', 'OLB', 'ILB', 'DL', 'DB'],
            'fieldGoals': ['K']
        }
        return stat_positions.get(stat_name, CORE_PLAYER_POSITIONS_FOR_STAT_RETRIEVER.get(sport, []))

    def _format_stats_response(self, player: Player, stats: PlayerStats, season: str, sport: str, source: str) -> Dict[str, Any]:
        """Format database stats into API response format."""
        return {
            "player_id": player.external_id,
            "player_fullName": player.name,
            "season": season,
            "sport": sport,
            "data_source": source,
            "simple_stats": {
                "games_played": stats.games_played,
                "games_started": stats.games_started,
                "passing_yards": stats.passing_yards,
                "passing_touchdowns": stats.passing_touchdowns,
                "rushing_yards": stats.rushing_yards,
                "rushing_touchdowns": stats.rushing_touchdowns,
                "receiving_yards": stats.receiving_yards,
                "receptions": stats.receptions,
                "receiving_touchdowns": stats.receiving_touchdowns,
                "sacks": stats.sacks,
                "tackles": stats.tackles,
                "interceptions": stats.interceptions,
                "forced_fumbles": stats.forced_fumbles,
                "field_goals_made": stats.field_goals_made,
                "field_goals_attempted": stats.field_goals_attempted,
                "extra_points_made": stats.extra_points_made
            }
        }

    def _fetch_stats_from_api(self, player_id: str, season: str, sport: str) -> Dict[str, Any]:
        """Fetch stats from API as fallback."""
        endpoint_key = "PlayerStats"
        if endpoint_key not in self.api_config[sport]['endpoints']:
            return {"error": f"Endpoint '{endpoint_key}' not configured"}
            
        url, headers = self.build_url(
            sport,
            endpoint_key,
            query_params={'id': player_id, 'year': season}
        )
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"API fetch failed: {str(e)}"}

# Ensure other necessary methods (NFLStatsSchema, _validate_query_requirements, etc.) are present and correct.

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