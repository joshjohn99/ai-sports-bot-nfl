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

    def _get_player_id(self, sport: str, player_name: str, query_context=None):
        """Get player ID using the API with context-aware disambiguation."""
        try:
            # Import the get_player_id function from api_config
            from sports_bot.config.api_config import get_player_id
            
            self.console.print(f"[cyan]🔍 Searching for player: {player_name}[/cyan]")
            
            # Extract stat context for disambiguation
            stat_context = []
            if query_context:
                if hasattr(query_context, 'metrics_needed') and query_context.metrics_needed:
                    stat_context.extend(query_context.metrics_needed)
                if hasattr(query_context, 'stat_type') and query_context.stat_type:
                    stat_context.append(query_context.stat_type)
                if hasattr(query_context, 'stats_filters') and query_context.stats_filters:
                    stat_context.extend(query_context.stats_filters)
            
            if stat_context:
                self.console.print(f"[dim]📊 Using stat context for disambiguation: {stat_context}[/dim]")
            
            # Use the API function to get player ID with context
            player_id = get_player_id(player_name, stat_context if stat_context else None)
            
            if player_id:
                self.console.print(f"[green]✅ Found player ID: {player_id}[/green]")
                # Create basic player info structure
                player_info = {
                    'id': player_id,
                    'fullName': player_name,
                    'position': {'abbreviation': 'Unknown'}  # We'll get this from stats later
                }
                return player_id, player_info, None
            else:
                self.console.print(f"[yellow]❌ Player '{player_name}' not found in API[/yellow]")
                return None, None, None
                
        except Exception as e:
            self.console.print(f"[red]❌ Error searching for player {player_name}: {e}[/red]")
            return None, None, None

    # Placeholder for _get_player_id_with_context
    def _get_player_id_with_context(self, sport: str, player_name: str, query_context=None):
        # This would call the refined _get_player_id
        return self._get_player_id(sport, player_name, query_context)

    def extract_stats_using_schema(self, data, requested_metrics, sport='NFL'):
        """Extract stats from API response data using schema mapping."""
        extracted = {}
        
        if not data or not requested_metrics:
            return extracted
        
        # Handle different API response structures
        stats_data = data
        if isinstance(data, dict):
            # Check for common API response structures
            if 'statistics' in data:
                stats_data = data['statistics']
            elif 'data' in data:
                stats_data = data['data']
            elif 'stats' in data:
                stats_data = data['stats']
        
        # Map common metric names to API field names
        field_mapping = {
            'passing_yards': ['passingYards', 'passing_yards', 'passYds'],
            'passing_touchdowns': ['passingTouchdowns', 'passing_tds', 'passTDs'],
            'rushing_yards': ['rushingYards', 'rushing_yards', 'rushYds'],
            'rushing_touchdowns': ['rushingTouchdowns', 'rushing_tds', 'rushTDs'],
            'receiving_yards': ['receivingYards', 'receiving_yards', 'recYds'],
            'receiving_touchdowns': ['receivingTouchdowns', 'receiving_tds', 'recTDs'],
            'receptions': ['receptions', 'catches', 'rec'],
            'sacks': ['sacks', 'sck'],
            'tackles': ['tackles', 'tkl'],
            'interceptions': ['interceptions', 'int'],
            'games_played': ['gamesPlayed', 'games_played', 'GP'],
            'games_started': ['gamesStarted', 'games_started', 'GS']
        }
        
        for metric in requested_metrics:
            value = None
            display_value = None
            
            # Try to find the metric in the data
            possible_fields = field_mapping.get(metric, [metric])
            
            for field in possible_fields:
                if isinstance(stats_data, dict):
                    if field in stats_data:
                        raw_value = stats_data[field]
                        if isinstance(raw_value, dict):
                            value = raw_value.get('value', raw_value.get('displayValue'))
                            display_value = raw_value.get('displayValue', str(value))
                        else:
                            value = raw_value
                            display_value = str(raw_value)
                        break
                elif isinstance(stats_data, list):
                    # Handle list of stat objects
                    for stat_obj in stats_data:
                        if isinstance(stat_obj, dict) and field in stat_obj:
                            raw_value = stat_obj[field]
                            if isinstance(raw_value, dict):
                                value = raw_value.get('value', raw_value.get('displayValue'))
                                display_value = raw_value.get('displayValue', str(value))
                            else:
                                value = raw_value
                                display_value = str(raw_value)
                            break
                    if value is not None:
                        break
            
            # Store the extracted value
            if value is not None:
                extracted[metric] = {
                    'value': value,
                    'displayValue': display_value or str(value)
                }
            else:
                # Return 0 for missing stats
                extracted[metric] = {
                    'value': 0,
                    'displayValue': '0'
                }
        
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
            # If not in database, try a more flexible search (partial name match)
            players = self.db_session.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).all()
            
            if players:
                # Use disambiguation logic if multiple players found
                if len(players) > 1:
                    self.console.print(f"[yellow]🔍 Found {len(players)} players matching '{player_name}', using disambiguation...[/yellow]")
                    
                    # Convert to API format for disambiguation
                    candidates = []
                    for p in players:
                        candidates.append({
                            'id': p.external_id,
                            'name': p.name,
                            'fullName': p.name,
                            'position': {'abbreviation': p.position},
                            'team': {'abbreviation': 'Unknown'}  # Could be enhanced with team lookup
                        })
                    
                    # Use disambiguation logic
                    stat_context = []
                    if query_context:
                        if hasattr(query_context, 'metrics_needed') and query_context.metrics_needed:
                            stat_context.extend(query_context.metrics_needed)
                        if hasattr(query_context, 'stat_type') and query_context.stat_type:
                            stat_context.append(query_context.stat_type)
                    
                    if stat_context:
                        from ...config.player_disambiguation import disambiguator
                        best_player = disambiguator.disambiguate_players(
                            candidates=candidates,
                            sport=sport,
                            stat_context=stat_context
                        )
                        if best_player:
                            # Find the corresponding database player
                            player = next((p for p in players if p.external_id == best_player['id']), players[0])
                        else:
                            player = players[0]  # Fallback to first match
                    else:
                        # No context, prefer QB if available
                        qb_players = [p for p in players if p.position and p.position.upper() == 'QB']
                        player = qb_players[0] if qb_players else players[0]
                        
                    self.console.print(f"[green]✅ Selected: {player.name} ({player.position})[/green]")
                else:
                    player = players[0]
            else:
                return {"error": f"Player '{player_name}' not found in database. Please ensure player data is loaded."}

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
            'passing yards': 'passing_yards',  # Add user-friendly name
            'career passing yards': 'passing_yards',  # Add career version
            'rushingYards': 'rushing_yards',
            'rushing yards': 'rushing_yards',
            'rushingTouchdowns': 'rushing_touchdowns',
            'rushing touchdowns': 'rushing_touchdowns',
            'receivingYards': 'receiving_yards',
            'receiving yards': 'receiving_yards',
            'receptions': 'receptions',
            'receivingTouchdowns': 'receiving_touchdowns',
            'receiving touchdowns': 'receiving_touchdowns',
            'sacks': 'sacks',
            'tackles': 'tackles',
            'interceptions': 'interceptions',
            'forcedFumbles': 'forced_fumbles',
            'forced fumbles': 'forced_fumbles',
            'fieldGoalsMade': 'field_goals_made',
            'field goals made': 'field_goals_made',
            'fieldGoalsAttempted': 'field_goals_attempted',
            'field goals attempted': 'field_goals_attempted',
            'extraPointsMade': 'extra_points_made',
            'extra points made': 'extra_points_made'
        }
        return mapping.get(stat_name, stat_name.lower().replace(' ', '_'))

    def _get_positions_for_stat(self, stat_name: str, sport: str) -> List[str]:
        """Get relevant positions for a stat."""
        stat_positions = {
            'passingTouchdowns': ['QB'],
            'passingYards': ['QB'],
            'passing yards': ['QB'],
            'career passing yards': ['QB'],
            'rushingYards': ['RB', 'QB', 'FB'],
            'rushing yards': ['RB', 'QB', 'FB'],
            'rushingTouchdowns': ['RB', 'QB', 'FB'],
            'rushing touchdowns': ['RB', 'QB', 'FB'],
            'receivingYards': ['WR', 'TE', 'RB'],
            'receiving yards': ['WR', 'TE', 'RB'],
            'receptions': ['WR', 'TE', 'RB'],
            'receivingTouchdowns': ['WR', 'TE', 'RB'],
            'receiving touchdowns': ['WR', 'TE', 'RB'],
            'sacks': ['DE', 'DT', 'LB', 'OLB', 'ILB', 'MLB', 'EDGE', 'DL'],
            'tackles': ['LB', 'DE', 'DT', 'S', 'CB', 'MLB', 'OLB', 'ILB', 'DL', 'DB'],
            'fieldGoals': ['K'],
            'field goals made': ['K'],
            'interceptions': ['CB', 'S', 'LB', 'DB']
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

    def fetch_stats_batch(self, query_context) -> Dict[str, Any]:
        """Fetch stats for multiple players for comparison."""
        sport = query_context.sport
        season = self.get_season_format(sport, query_context.season_years)
        player_names = query_context.player_names
        
        results = {}
        errors = {}
        
        for player_name in player_names:
            self.console.print(f"[cyan]🔍 Fetching stats for: {player_name}[/cyan]")
            
            # Create a temporary query context for this player
            temp_context = query_context.model_copy()
            temp_context.player_names = [player_name]
            
            # Fetch stats for this player
            player_stats = self.fetch_stats(temp_context)
            
            if isinstance(player_stats, dict) and "error" in player_stats:
                errors[player_name] = player_stats["error"]
                self.console.print(f"[yellow]❌ Error for {player_name}: {player_stats['error']}[/yellow]")
            else:
                results[player_name] = player_stats
                self.console.print(f"[green]✅ Successfully fetched stats for {player_name}[/green]")
        
        return {
            "player_stats": results,
            "errors": errors,
            "total_players": len(player_names),
            "successful_fetches": len(results),
            "failed_fetches": len(errors)
        }

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