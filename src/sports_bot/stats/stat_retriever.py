"""
Response Formatter Module
Handles formatting of query results into user-friendly responses.
"""

from typing import Dict, Any, List, Optional
import os
import json
import requests
from datetime import datetime
from sqlalchemy import func, desc
from rich.console import Console
from urllib.parse import urljoin, urlencode

from sports_bot.config.api_config import api_config
from sports_bot.cache.shared_cache import get_cache_instance
from sports_bot.database.models import db_manager, Player, Team, PlayerStats, CareerStats

# --- Local Data Store Configuration ---
# This should ideally be consistent with data_loader.py or from a shared config
# Assuming stat_retriever.py is in sports_bot_beta/src/sports_bot/core/
# So, ../../.. goes up to sports_bot_beta/
DATA_STORE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'daily_store')

def ensure_dir(file_path):
    """Ensure the directory for a file path exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

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
        
        # Position priority for disambiguation (higher number = higher priority)
        self.position_priority = {
            'QB': 100,  # Quarterbacks are most likely to be searched
            'RB': 90,   # Running backs
            'WR': 85,   # Wide receivers
            'TE': 80,   # Tight ends
            'FB': 75,   # Fullbacks
            'K': 70,    # Kickers
            'P': 65,    # Punters
            'LB': 60,   # Linebackers
            'MLB': 60,  # Middle linebackers
            'OLB': 60,  # Outside linebackers
            'ILB': 60,  # Inside linebackers
            'DE': 55,   # Defensive ends
            'DT': 50,   # Defensive tackles
            'CB': 45,   # Cornerbacks
            'S': 40,    # Safeties
            'DB': 40,   # Defensive backs
            'EDGE': 55, # Edge rushers
            'DL': 50,   # Defensive line
            'OL': 30,   # Offensive line
            'T': 30,    # Tackles
            'G': 25,    # Guards
            'C': 25,    # Centers
            'LS': 20    # Long snappers
        }

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

    def _get_player_id(self, sport: str, player_name: str):
        """Get player ID using database-first approach."""
        # Use intelligent player matching from database
        player, confidence, alternatives = self.find_best_matching_player(player_name)
        
        if player and confidence > 0.5:
            return player.external_id, player.name, player.current_team_id
        
        self.console.print(f"[yellow]Could not find player ID for {player_name}[/yellow]")
        return None, None, None

    def _get_player_id_with_context(self, sport: str, player_name: str, query_context=None):
        """Get player ID with query context for disambiguation."""
        # Use intelligent player matching with context
        player, confidence, alternatives = self.find_best_matching_player(player_name, query_context)
        
        if player and confidence > 0.5:
            return player.external_id, player.name, player.current_team_id
        
        # If low confidence, could use query_context to improve matching
        if query_context and hasattr(query_context, 'metrics_needed'):
            # Could use metrics to infer position and improve matching
            pass
        
        self.console.print(f"[yellow]Could not find player ID for {player_name} with context[/yellow]")
        return None, None, None

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

    def find_best_matching_player(self, player_name: str, query_context=None):
        """
        Intelligently find the best matching player by name.
        Handles cases where multiple players have the same name.
        
        Returns: (player, confidence_score, alternatives)
        """
        # First, try exact name match
        exact_matches = self.db_session.query(Player).filter(
            Player.name.ilike(player_name)
        ).all()
        
        if len(exact_matches) == 1:
            return exact_matches[0], 1.0, []
        
        # If no exact match, try partial match
        if not exact_matches:
            partial_matches = self.db_session.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).all()
        else:
            partial_matches = exact_matches
        
        if not partial_matches:
            return None, 0.0, []
        
        if len(partial_matches) == 1:
            return partial_matches[0], 0.9, []
        
        # Multiple matches found - need to disambiguate
        print(f"[DEBUG] Found {len(partial_matches)} players matching '{player_name}':")
        for player in partial_matches:
            print(f"  - {player.name} ({player.position}) - Team ID: {player.current_team_id}")
        
        # Score each player based on multiple factors
        scored_players = []
        current_season = self.get_current_season("NFL")
        
        for player in partial_matches:
            score = 0
            
            # 1. Position priority (most important factor)
            position_score = self.position_priority.get(player.position, 10)
            score += position_score * 10  # Weight position heavily
            
            # 2. Activity level (games played in current season)
            stats = self.db_session.query(PlayerStats).filter_by(
                player_id=player.id,
                season=current_season
            ).first()
            
            if stats:
                games_played = stats.games_played or 0
                score += games_played * 5  # More active players get higher score
                
                # 3. Statistical prominence (total yards, touchdowns, etc.)
                total_stats = (
                    (stats.passing_yards or 0) +
                    (stats.rushing_yards or 0) +
                    (stats.receiving_yards or 0) +
                    ((stats.passing_touchdowns or 0) * 20) +
                    ((stats.rushing_touchdowns or 0) * 20) +
                    ((stats.receiving_touchdowns or 0) * 20) +
                    ((stats.sacks or 0) * 25) +
                    ((stats.interceptions or 0) * 30)
                )
                score += min(total_stats / 100, 50)  # Cap statistical bonus at 50
            
            # 4. Name similarity bonus
            if player.name.lower() == player_name.lower():
                score += 100  # Exact name match bonus
            elif player_name.lower() in player.name.lower():
                score += 50   # Partial name match bonus
            
            scored_players.append((player, score))
            print(f"  - {player.name} ({player.position}): Score = {score}")
        
        # Sort by score (highest first)
        scored_players.sort(key=lambda x: x[1], reverse=True)
        best_player, best_score = scored_players[0]
        
        # If the best player has a significantly higher score, return it
        if len(scored_players) > 1:
            second_best_score = scored_players[1][1]
            score_difference = best_score - second_best_score
            
            # If the difference is significant (>100 points), we're confident
            if score_difference > 100:
                alternatives = [p for p, s in scored_players[1:4]]  # Top 3 alternatives
                return best_player, 0.8, alternatives
        
        # If scores are close, we need clarification
        alternatives = [p for p, s in scored_players[1:]]
        return best_player, 0.5, alternatives

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

        # Use intelligent player matching
        player, confidence, alternatives = self.find_best_matching_player(player_name, query_context)
        
        if not player:
            return {"error": f"Player '{player_name}' not found"}
        
        # If confidence is low, provide disambiguation info
        if confidence < 0.7 and alternatives:
            alternative_info = []
            for alt in alternatives[:3]:  # Show top 3 alternatives
                alternative_info.append({
                    "name": alt.name,
                    "position": alt.position,
                    "team_id": alt.current_team_id
                })
            
            return {
                "error": "Multiple players found",
                "player_name": player_name,
                "best_match": {
                    "name": player.name,
                    "position": player.position,
                    "team_id": player.current_team_id
                },
                "alternatives": alternative_info,
                "follow_up_question": f"Multiple players named '{player_name}' found. Did you mean {player.name} ({player.position})?"
            }

        # Continue with stats fetching for the matched player
        print(f"[DEBUG] Selected player: {player.name} ({player.position}) with confidence {confidence}")

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

    def fetch_league_leaders(self, query_context, metric: str = None, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch league leaders for a specific metric across all players in a sport.
        Designed to be sport-agnostic.
        """
        sport = query_context.sport
        if not sport or sport not in self.api_config:
            return {"error": f"Sport '{sport}' not configured or not provided."}

        # Get season
        season = self.get_season_format(sport, query_context.season_years)

        # Get the metric to rank by
        if not metric and query_context.metrics_needed:
            metric = query_context.metrics_needed[0]
        
        if not metric:
            return {"error": "No metric specified for leaderboard"}

        # Map common metric names to database columns
        metric_mapping = {
            # Football metrics
            "passing_yards": PlayerStats.passing_yards,
            "passing_touchdowns": PlayerStats.passing_touchdowns,
            "rushing_yards": PlayerStats.rushing_yards,
            "rushing_touchdowns": PlayerStats.rushing_touchdowns,
            "receiving_yards": PlayerStats.receiving_yards,
            "receiving_touchdowns": PlayerStats.receiving_touchdowns,
            "receptions": PlayerStats.receptions,
            "touchdowns": None,  # Special handling for combined stats
            "sacks": PlayerStats.sacks,
            "tackles": PlayerStats.tackles,
            "interceptions": PlayerStats.interceptions,
            "forced_fumbles": PlayerStats.forced_fumbles,
            "field_goals": PlayerStats.field_goals_made,
            "field_goals_made": PlayerStats.field_goals_made,
            "field_goals_attempted": PlayerStats.field_goals_attempted,
            "extra_points_made": PlayerStats.extra_points_made,
            # Quarterback-specific metrics
            "quarterback_rating": PlayerStats.passing_yards,  # Fallback to passing yards for now
            "passer_rating": PlayerStats.passing_yards,  # Alternative name
            "qb_rating": PlayerStats.passing_yards,  # Short name
            "yards_per_game": None,  # Special handling for calculated stats
            "passing_yards_per_game": None,  # Special handling
            # Basketball metrics (for future)
            "points": "points",
            "rebounds": "rebounds",
            "assists": "assists",
            # Baseball metrics (for future)
            "batting_average": "batting_avg",
            "home_runs": "home_runs",
            "runs_batted_in": "rbi",
            # Generic metrics
            "games_played": PlayerStats.games_played,
            "games_started": PlayerStats.games_started
        }

        # Get the database column to query
        db_column = metric_mapping.get(metric)
        
        # Check for special metrics that don't have direct db_column mapping
        if not db_column and metric not in ["touchdowns", "yards_per_game", "passing_yards_per_game"]:
            return {"error": f"Unsupported metric: {metric}"}

        try:
            # Start building the query
            query = self.db_session.query(
                Player,
                PlayerStats
            ).join(
                PlayerStats
            ).filter(
                PlayerStats.season == season
            )

            # Special handling for combined stats (like total touchdowns)
            if metric == "touchdowns":
                # Calculate total touchdowns as sum of all TD types
                total_td_expr = (
                    func.coalesce(PlayerStats.passing_touchdowns, 0) + 
                    func.coalesce(PlayerStats.rushing_touchdowns, 0) + 
                    func.coalesce(PlayerStats.receiving_touchdowns, 0)
                )
                query = self.db_session.query(
                    Player,
                    PlayerStats,
                    total_td_expr.label('total_touchdowns')
                ).join(PlayerStats).filter(
                    PlayerStats.season == season
                ).order_by(desc('total_touchdowns'))
            elif metric in ["yards_per_game", "passing_yards_per_game"]:
                # Calculate yards per game (passing_yards / games_played)
                query = query.from_self(
                    Player,
                    PlayerStats,
                    (PlayerStats.passing_yards / PlayerStats.games_played).label('yards_per_game')
                ).filter(PlayerStats.games_played > 0).order_by(desc('yards_per_game'))
            else:
                query = query.order_by(desc(db_column))

            # Get position filter if specified
            if query_context.position_filters:
                positions = query_context.position_filters
                if isinstance(positions, str):
                    positions = [positions]
                query = query.filter(Player.position.in_(positions))

            # Execute query with limit
            results = query.limit(limit).all()

            # Format results
            leaders = []
            for rank, result_tuple in enumerate(results, 1):
                if metric == "touchdowns":
                    # Handle both 2-tuple and 3-tuple cases
                    if len(result_tuple) == 3:
                        player, stats, total_tds = result_tuple
                        value = total_tds or 0
                    else:
                        player, stats = result_tuple
                        value = (
                            (stats.passing_touchdowns or 0) +
                            (stats.rushing_touchdowns or 0) +
                            (stats.receiving_touchdowns or 0)
                        )
                elif metric in ["yards_per_game", "passing_yards_per_game"]:
                    player, stats, calculated_value = result_tuple
                    value = round(calculated_value, 1) if calculated_value else 0
                else:
                    player, stats = result_tuple
                    # Handle quarterback_rating fallback to passing_yards
                    if metric in ["quarterback_rating", "passer_rating", "qb_rating"]:
                        value = getattr(stats, 'passing_yards', 0)
                    else:
                        value = getattr(stats, metric, 0)

                leaders.append({
                    "rank": rank,
                    "player_id": player.external_id,
                    "player_name": player.name,
                    "position": player.position,
                    "team_id": player.current_team_id,
                    "value": value
                })

            # Get league average for context
            if metric == "touchdowns":
                avg_query = self.db_session.query(
                    func.avg(PlayerStats.passing_touchdowns +
                            PlayerStats.rushing_touchdowns +
                            PlayerStats.receiving_touchdowns)
                ).filter(PlayerStats.season == season)
            elif metric in ["yards_per_game", "passing_yards_per_game"]:
                avg_query = self.db_session.query(
                    func.avg(PlayerStats.passing_yards / PlayerStats.games_played)
                ).filter(
                    PlayerStats.season == season,
                    PlayerStats.games_played > 0
                )
            elif metric in ["quarterback_rating", "passer_rating", "qb_rating"]:
                # Use passing_yards as fallback for quarterback rating
                avg_query = self.db_session.query(
                    func.avg(PlayerStats.passing_yards)
                ).filter(PlayerStats.season == season)
            else:
                avg_query = self.db_session.query(
                    func.avg(db_column)
                ).filter(PlayerStats.season == season)

            if query_context.position_filters:
                positions = query_context.position_filters
                if isinstance(positions, str):
                    positions = [positions]
                if metric in ["yards_per_game", "passing_yards_per_game"]:
                    avg_query = avg_query.join(Player).filter(
                        Player.position.in_(positions),
                        PlayerStats.games_played > 0
                    )
                else:
                    avg_query = avg_query.join(Player).filter(
                        Player.position.in_(positions)
                    )

            league_avg = avg_query.scalar() or 0

            return {
                "sport": sport,
                "season": season,
                "metric": metric,
                "leaders": leaders,
                "league_average": league_avg,
                "total_players": len(leaders),
                "filters_applied": {
                    "position": query_context.position_filters,
                    "team": query_context.team_filters,
                    "player": query_context.player_filters
                }
            }

        except Exception as e:
            self.console.print(f"[red]Error fetching league leaders: {str(e)}[/red]")
            return {"error": f"Failed to fetch league leaders: {str(e)}"}

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

    def fetch_team_stats(self, query_context):
        """Fetch team statistics from database or API."""
        sport = query_context.sport
        if not sport or sport not in self.api_config:
            return {"error": f"Sport '{sport}' not configured or not provided."}

        team_name = query_context.team_names[0] if query_context.team_names else None
        if not team_name:
            return {"error": "No team specified"}

        # Try to get team from database first
        team = self.db_session.query(Team).filter(Team.name.ilike(f"%{team_name}%")).first()
        
        if not team:
            return {"error": f"Team '{team_name}' not found"}

        # Get season
        season = self.get_season_format(sport, query_context.season_years)

        # Get all players from this team
        players = self.db_session.query(Player).filter_by(current_team_id=team.id).all()
        
        # Get team stats by aggregating player stats
        team_stats = {
            "total_passing_yards": 0,
            "total_rushing_yards": 0,
            "total_receiving_yards": 0,
            "total_touchdowns": 0,
            "total_sacks": 0,
            "total_interceptions": 0,
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "player_count": len(players)
        }

        for player in players:
            stats = self.db_session.query(PlayerStats).filter_by(
                player_id=player.id,
                season=season
            ).first()

            if stats:
                team_stats["total_passing_yards"] += stats.passing_yards or 0
                team_stats["total_rushing_yards"] += stats.rushing_yards or 0
                team_stats["total_receiving_yards"] += stats.receiving_yards or 0
                team_stats["total_touchdowns"] += (
                    (stats.passing_touchdowns or 0) +
                    (stats.rushing_touchdowns or 0) +
                    (stats.receiving_touchdowns or 0)
                )
                team_stats["total_sacks"] += stats.sacks or 0
                team_stats["total_interceptions"] += stats.interceptions or 0
                team_stats["games_played"] = max(team_stats["games_played"], stats.games_played or 0)

        return {
            "team_id": team.external_id,
            "team_name": team.name,
            "team_display_name": team.display_name,
            "season": season,
            "sport": sport,
            "data_source": "database",
            "stats": team_stats
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