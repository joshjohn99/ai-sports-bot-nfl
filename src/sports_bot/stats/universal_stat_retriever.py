"""
Universal Sport Statistics Retriever.
Works with any sport using sport-specific configurations and databases.
Includes cache-first, then database, then API fallback strategy.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
from sqlalchemy import func, desc

from rich.console import Console

from ..config.sport_config import sport_config_manager, SportConfig
from ..database.sport_models import sport_db_manager
from ..cache.shared_cache import get_cache_instance
from ..config.api_config import api_config
from ..utils.enhanced_player_search import get_enhanced_search

class UniversalStatRetriever:
    """Universal stat retriever that works with any sport."""
    
    def __init__(self):
        self.console = Console(highlight=False)
        self.cache = get_cache_instance()
        self.api_config = api_config
        
        # Priority order for data fetching
        self.data_sources = ["cache", "database", "api"]
        
        self.console.print("[green]🌟 Universal Sport Stat Retriever initialized![/green]")
        self.console.print(f"[dim]Supported sports: {', '.join(sport_config_manager.get_supported_sports())}[/dim]")
    
    def fetch_stats(self, query_context) -> Dict[str, Any]:
        """Fetch stats for any sport with cache-first strategy."""
        sport = query_context.sport.upper()
        
        # Validate sport
        if sport not in sport_config_manager.get_supported_sports():
            return {"error": f"Sport '{sport}' not supported. Available: {', '.join(sport_config_manager.get_supported_sports())}"}
        
        config = sport_config_manager.get_config(sport)
        if not config:
            return {"error": f"Configuration not found for sport '{sport}'"}
        
        # Handle different query strategies
        if hasattr(query_context, 'strategy') and query_context.strategy == "leaderboard_query":
            return self.fetch_league_leaders(query_context)
        
        # Get player info
        player_name = query_context.player_names[0] if query_context.player_names else None
        if not player_name:
            return {"error": "No player specified"}
        
        # Try data sources in priority order
        for source in self.data_sources:
            try:
                if source == "cache":
                    result = self._fetch_from_cache(sport, player_name, query_context, config)
                elif source == "database":
                    result = self._fetch_from_database(sport, player_name, query_context, config)
                elif source == "api":
                    result = self._fetch_from_api(sport, player_name, query_context, config)
                
                if result and "error" not in result:
                    self.console.print(f"[green]✅ Data fetched from {source.upper()}[/green]")
                    
                    # Cache the result if it came from database or API
                    if source in ["database", "api"]:
                        self._cache_result(sport, player_name, query_context, result, config)
                    
                    return result
                    
            except Exception as e:
                self.console.print(f"[yellow]⚠️ {source.upper()} fetch failed: {str(e)}[/yellow]")
                continue
        
        return {"error": f"Could not fetch stats for {player_name} from any source"}
    
    def fetch_league_leaders(self, query_context) -> Dict[str, Any]:
        """Fetch league leaders for any sport."""
        sport = query_context.sport.upper()
        config = sport_config_manager.get_config(sport)
        
        if not config:
            return {"error": f"Configuration not found for sport '{sport}'"}
        
        # Get the metric to rank by
        metric = query_context.metrics_needed[0] if query_context.metrics_needed else None
        if not metric:
            return {"error": "No metric specified for leaderboard"}
        
        # For league leaders, we'll skip cache for now since it's more complex
        # and go straight to database
        
        # Try database
        try:
            result = self._fetch_leaders_from_database(sport, metric, query_context, config)
            if result and "error" not in result:
                self.console.print("[green]✅ League leaders fetched from DATABASE[/green]")
                return result
        except Exception as e:
            self.console.print(f"[yellow]⚠️ Database leaders fetch failed: {str(e)}[/yellow]")
        
        # Try API as fallback
        try:
            result = self._fetch_leaders_from_api(sport, metric, query_context, config)
            if result and "error" not in result:
                self.console.print("[green]✅ League leaders fetched from API[/green]")
                return result
        except Exception as e:
            self.console.print(f"[yellow]⚠️ API leaders fetch failed: {str(e)}[/yellow]")
        
        return {"error": f"Could not fetch league leaders for {metric} from any source"}
    
    def fetch_stats_batch(self, query_context) -> Dict[str, Any]:
        """Fetch stats for multiple players for comparison."""
        sport = query_context.sport.upper()
        player_names = query_context.player_names
        
        results = {}
        errors = {}
        
        for player_name in player_names:
            self.console.print(f"[cyan]🔍 Fetching {sport} stats for: {player_name}[/cyan]")
            
            # Create a temporary query context for this player
            temp_context = query_context.model_copy()
            temp_context.player_names = [player_name]
            
            # Fetch stats for this player
            player_stats = self.fetch_stats(temp_context)
            
            if isinstance(player_stats, dict) and "error" in player_stats:
                errors[player_name] = player_stats["error"]
                self.console.print(f"[yellow]❌ Error for {player_name}: {player_stats['error']}[/yellow]")
            elif isinstance(player_stats, dict) and "note" in player_stats:
                # Player found but no stats - include in results with note
                results[player_name] = player_stats
                self.console.print(f"[yellow]⚠️ {player_name}: {player_stats.get('note', 'No stats available')}[/yellow]")
            else:
                results[player_name] = player_stats
                self.console.print(f"[green]✅ Successfully fetched {sport} stats for {player_name}[/green]")
        
        return {
            "player_stats": results,
            "errors": errors,
            "total_players": len(player_names),
            "successful_fetches": len(results),
            "failed_fetches": len(errors)
        }
    
    def _fetch_from_cache(self, sport: str, player_name: str, query_context, config: SportConfig) -> Optional[Dict[str, Any]]:
        """Fetch stats from cache."""
        # First try to get player info from cache
        player_info = self.cache.get_player(sport, player_name)
        if not player_info:
            return None
        
        # Get season and metrics
        season = self._get_season_format(sport, query_context.season_years, config)
        metrics = query_context.metrics_needed or []
        
        # Try to get stats from cache
        result = self.cache.get_stats(sport, player_info.get('id', ''), season, metrics)
        if result:
            # Add cache metadata
            result["data_source"] = "cache"
            result["cache_hit"] = True
            
        return result
    
    def _fetch_from_database(self, sport: str, player_name: str, query_context, config: SportConfig) -> Optional[Dict[str, Any]]:
        """Fetch stats from sport-specific database with dynamic fallback strategies."""
        session = sport_db_manager.get_session(sport)
        models = sport_db_manager.get_models(sport)
        
        if not session or not models:
            return None
        
        try:
            # Find player with intelligent matching
            player = self._find_best_matching_player(session, models, player_name, query_context, config)
            
            if not player:
                return {"error": f"Player '{player_name}' not found in {sport} database"}
            
            # Try multiple seasons dynamically if current season has no stats
            seasons_to_try = self._get_seasons_to_try(sport, query_context.season_years, config)
            
            for season in seasons_to_try:
                # Get stats from database for this season
                stats = session.query(models['PlayerStats']).filter_by(
                    player_id=player.id,
                    season=season
                ).first()
                
                if stats:
                    self.console.print(f"[green]📊 Found {sport} stats for {player.name} in {season} season[/green]")
                    return self._format_stats_response(player, stats, season, sport, "database", config)
            
            # If no stats found in any season, try career stats
            career_stats = session.query(models.get('CareerStats')).filter_by(
                player_id=player.id
            ).first() if 'CareerStats' in models else None
            
            if career_stats:
                self.console.print(f"[yellow]📈 Using career stats for {player.name} (no season stats available)[/yellow]")
                return self._format_career_stats_response(player, career_stats, sport, "database", config)
            
            # If still no stats, provide a helpful response with player info
            return self._format_no_stats_response(player, sport, seasons_to_try, config)
                
        finally:
            session.close()
    
    def _fetch_from_api(self, sport: str, player_name: str, query_context, config: SportConfig) -> Optional[Dict[str, Any]]:
        """Fetch stats from API as fallback."""
        if sport not in self.api_config:
            return {"error": f"API configuration not found for {sport}"}
        
        # This would integrate with your existing API fetching logic
        # For now, return a placeholder
        return {"error": "API fetching not yet implemented for universal retriever"}
    
    def _fetch_leaders_from_database(self, sport: str, metric: str, query_context, config: SportConfig) -> Dict[str, Any]:
        """Fetch league leaders from database."""
        session = sport_db_manager.get_session(sport)
        models = sport_db_manager.get_models(sport)
        
        if not session or not models:
            return {"error": "Database not available"}
        
        try:
            # Get stat mapping
            stat_mapping = config.stat_mappings.get(metric)
            if not stat_mapping:
                # Try to find by user terms
                stat_mapping = self._find_stat_by_user_terms(metric, config)
            
            if not stat_mapping:
                return {"error": f"Stat '{metric}' not supported for {sport}"}
            
            db_column = stat_mapping.db_column
            
            # Get season
            season = self._get_season_format(sport, query_context.season_years, config)
            
            # Build query
            query = session.query(
                models['Player'],
                models['PlayerStats']
            ).join(
                models['PlayerStats']
            ).filter(
                models['PlayerStats'].season == season
            )
            
            # Filter by positions if specified
            if stat_mapping.positions:
                query = query.filter(models['Player'].position.in_(stat_mapping.positions))
            
            # Get the database column to order by
            stat_column = getattr(models['PlayerStats'], db_column, None)
            if not stat_column:
                return {"error": f"Database column '{db_column}' not found"}
            
            # Order by stat and limit results
            limit = getattr(query_context, 'limit', 10)
            results = query.order_by(desc(stat_column)).limit(limit).all()
            
            # Format results
            leaders = []
            for rank, (player, stats) in enumerate(results, 1):
                stat_value = getattr(stats, db_column, 0)
                leaders.append({
                    "rank": rank,
                    "player_id": player.external_id,
                    "player_name": player.name,
                    "position": player.position,
                    "team_id": player.current_team_id,
                    "value": stat_value,
                    "display_value": f"{stat_value:,}" if isinstance(stat_value, int) else f"{stat_value:.1f}"
                })
            
            # Calculate league average
            avg_query = session.query(func.avg(stat_column)).filter(
                models['PlayerStats'].season == season
            )
            
            if stat_mapping.positions:
                avg_query = avg_query.join(models['Player']).filter(
                    models['Player'].position.in_(stat_mapping.positions)
                )
            
            league_avg = avg_query.scalar() or 0
            
            return {
                "sport": sport,
                "season": season,
                "metric": metric,
                "display_name": stat_mapping.display_name,
                "category": stat_mapping.category,
                "leaders": leaders,
                "league_average": league_avg,
                "total_players": len(leaders),
                "filters_applied": {
                    "positions": stat_mapping.positions,
                    "season": season
                }
            }
            
        finally:
            session.close()
    
    def _fetch_leaders_from_api(self, sport: str, metric: str, query_context, config: SportConfig) -> Dict[str, Any]:
        """Fetch league leaders from API."""
        # Placeholder for API integration
        return {"error": "API leaders fetching not yet implemented"}
    
    def _find_best_matching_player(self, session, models, player_name: str, query_context, config: SportConfig) -> Optional[Any]:
        """Find the best matching player using enhanced SQL logic and intelligent disambiguation."""
        
        # Import and use enhanced player search
        enhanced_search = get_enhanced_search(session, models, config)
        
        # Use advanced SQL strategies to find players
        players_with_confidence = enhanced_search.find_players_with_advanced_sql(player_name, query_context)
        
        if not players_with_confidence:
            # If no matches found, get debug info to understand why
            debug_info = enhanced_search.get_sql_debug_info(player_name)
            self.console.print(f"[yellow]🔍 No players found for '{player_name}'. Debug info:[/yellow]")
            self.console.print(f"[dim]  - Total players in DB: {debug_info.get('total_players_in_db', 'Unknown')}[/dim]")
            self.console.print(f"[dim]  - Variations tried: {debug_info.get('generated_variations', [])}[/dim]")
            
            # Show results per strategy
            for strategy, result in debug_info.get('results_per_strategy', {}).items():
                if isinstance(result, dict) and 'count' in result:
                    self.console.print(f"[dim]  - {strategy}: {result['count']} matches[/dim]")
            
            return None
        
        if len(players_with_confidence) == 1:
            player, confidence = players_with_confidence[0]
            self.console.print(f"[green]✅ Found unique match: {player.name} ({getattr(player, 'position', 'Unknown')}) - Confidence: {confidence:.2f}[/green]")
            return player
        
        # Multiple matches - use intelligent disambiguation
        best_player, final_confidence, alternatives = self._enhanced_disambiguate_players(
            players_with_confidence, query_context, config
        )
        
        if best_player:
            self.console.print(f"[green]✅ Disambiguated '{player_name}' → {best_player.name} ({getattr(best_player, 'position', 'Unknown')}) - Confidence: {final_confidence:.2f}[/green]")
            
            if alternatives and final_confidence < 0.8:
                alt_names = [f"{alt.name} ({getattr(alt, 'position', 'Unknown')})" for alt in alternatives[:2]]
                self.console.print(f"[dim]   Other options: {', '.join(alt_names)}[/dim]")
        
        return best_player
    
    def _enhanced_disambiguate_players(self, players_with_confidence: List[Tuple[Any, float]], 
                                     query_context, config: SportConfig) -> Tuple[Optional[Any], float, List[Any]]:
        """
        Enhanced disambiguation using context clues, position matching, and statistical analysis.
        Returns: (best_player, confidence, alternatives)
        """
        if not players_with_confidence:
            return None, 0.0, []
        
        if len(players_with_confidence) == 1:
            player, confidence = players_with_confidence[0]
            return player, confidence, []
        
        # Score each player based on multiple factors
        scored_players = []
        
        for player, base_confidence in players_with_confidence:
            total_score = base_confidence * 100  # Convert to 0-100 scale
            
            # 1. Position-based scoring using query context
            if query_context and query_context.metrics_needed:
                position_bonus = self._get_position_bonus_for_query(player, query_context, config)
                total_score += position_bonus
            
            # 2. Activity and recency bonus
            activity_bonus = self._get_player_activity_bonus(player)
            total_score += activity_bonus
            
            # 3. Statistical prominence bonus
            stats_bonus = self._get_player_stats_bonus(player)
            total_score += stats_bonus
            
            scored_players.append((player, total_score, base_confidence))
        
        # Sort by total score
        scored_players.sort(key=lambda x: x[1], reverse=True)
        
        best_player, best_score, best_confidence = scored_players[0]
        
        # Determine final confidence based on score separation
        if len(scored_players) > 1:
            second_best_score = scored_players[1][1]
            score_gap = best_score - second_best_score
            
            # Adjust confidence based on how clear the winner is
            if score_gap > 50:
                final_confidence = min(0.95, best_confidence + 0.2)
            elif score_gap > 20:
                final_confidence = min(0.85, best_confidence + 0.1)
            else:
                final_confidence = max(0.5, best_confidence - 0.1)
        else:
            final_confidence = best_confidence
        
        # Get alternatives (other players)
        alternatives = [p for p, s, c in scored_players[1:4]]  # Top 3 alternatives
        
        return best_player, final_confidence, alternatives
    
    def _get_position_bonus_for_query(self, player: Any, query_context, config: SportConfig) -> float:
        """Get bonus points based on position relevance to query metrics."""
        if not query_context.metrics_needed:
            return 0
        
        position_bonus = 0
        player_position = getattr(player, 'position', '')
        
        for metric in query_context.metrics_needed:
            stat_mapping = config.stat_mappings.get(metric)
            if stat_mapping and stat_mapping.positions:
                if player_position in stat_mapping.positions:
                    position_bonus += 40  # High bonus for position match
                    break
        
        # General position priority (QB > skill positions > others)
        position_priority = {
            'QB': 30, 'RB': 25, 'WR': 25, 'TE': 20,
            'OL': 15, 'DL': 18, 'LB': 20, 'CB': 22, 'S': 20,
            'K': 10, 'P': 8, 'LS': 5
        }
        position_bonus += position_priority.get(player_position, 5)
        
        return position_bonus
    
    def _get_player_activity_bonus(self, player: Any) -> float:
        """Get bonus points based on player activity (games played)."""
        try:
            # Get current season stats
            current_season = "2024"  # Could be made dynamic
            session = sport_db_manager.get_session('NFL')  # Assuming NFL for now
            models = sport_db_manager.get_models('NFL')
            
            if session and models:
                stats = session.query(models['PlayerStats']).filter_by(
                    player_id=player.id,
                    season=current_season
                ).first()
                
                if stats:
                    games_played = getattr(stats, 'games_played', 0) or 0
                    return min(games_played * 2, 25)  # Up to 25 points for activity
                
                session.close()
            
            return 0
        except:
            return 0
    
    def _get_player_stats_bonus(self, player: Any) -> float:
        """Get bonus points based on statistical prominence."""
        try:
            # Get recent stats
            current_season = "2024"
            session = sport_db_manager.get_session('NFL')  # Assuming NFL for now
            models = sport_db_manager.get_models('NFL')
            
            if session and models:
                stats = session.query(models['PlayerStats']).filter_by(
                    player_id=player.id,
                    season=current_season
                ).first()
                
                if stats:
                    # Calculate total statistical impact
                    total_impact = (
                        (getattr(stats, 'passing_yards', 0) or 0) * 0.01 +
                        (getattr(stats, 'rushing_yards', 0) or 0) * 0.01 +
                        (getattr(stats, 'receiving_yards', 0) or 0) * 0.01 +
                        (getattr(stats, 'passing_touchdowns', 0) or 0) * 2 +
                        (getattr(stats, 'rushing_touchdowns', 0) or 0) * 2 +
                        (getattr(stats, 'receiving_touchdowns', 0) or 0) * 2 +
                        (getattr(stats, 'sacks', 0) or 0) * 3 +
                        (getattr(stats, 'interceptions', 0) or 0) * 4
                    )
                    
                    return min(total_impact / 10, 20)  # Up to 20 points for stats
                
                session.close()
            
            return 0
        except:
            return 0
    
    def _find_stat_by_user_terms(self, metric: str, config: SportConfig) -> Optional[Any]:
        """Find stat mapping by user terms."""
        metric_lower = metric.lower()
        
        for stat_name, stat_mapping in config.stat_mappings.items():
            if stat_mapping.user_terms:
                for term in stat_mapping.user_terms:
                    if term.lower() == metric_lower:
                        return stat_mapping
        
        return None
    
    def _get_season_format(self, sport: str, season_years: List[int], config: SportConfig) -> str:
        """Get properly formatted season string for the sport."""
        if season_years and len(season_years) > 0:
            year = season_years[0]
            if config.season_format == "YYYY":
                return str(year)
            elif config.season_format == "YYYY-YY":
                return f"{year}-{str(year + 1)[-2:]}"
            else:
                return str(year)
        
        # Return current season
        current_year = datetime.now().year
        if datetime.now().month < 8:  # Adjust for sports seasons
            current_year -= 1
        
        if config.season_format == "YYYY":
            return str(current_year)
        elif config.season_format == "YYYY-YY":
            return f"{current_year}-{str(current_year + 1)[-2:]}"
        else:
            return str(current_year)
    
    def _format_stats_response(self, player: Any, stats: Any, season: str, sport: str, source: str, config: SportConfig) -> Dict[str, Any]:
        """Format database stats into API response format."""
        simple_stats = {}
        
        # Convert database stats to simple format using sport configuration
        for stat_name, stat_mapping in config.stat_mappings.items():
            db_column = stat_mapping.db_column
            value = getattr(stats, db_column, 0) or 0
            simple_stats[stat_name] = value
        
        # Add common stats
        simple_stats.update({
            "games_played": getattr(stats, 'games_played', 0) or 0,
            "games_started": getattr(stats, 'games_started', 0) or 0,
        })
        
        return {
            "player_id": player.external_id,
            "player_fullName": player.name,
            "position": player.position,
            "sport": sport,
            "season": season,
            "data_source": source,
            "simple_stats": simple_stats
        }
    
    def _cache_result(self, sport: str, player_name: str, query_context, result: Dict[str, Any], config: SportConfig):
        """Cache the result for future use."""
        season = self._get_season_format(sport, query_context.season_years, config)
        metrics = query_context.metrics_needed or []
        
        # Cache player info if not already cached
        player_info = {
            'id': result.get('player_id', ''),
            'name': result.get('player_fullName', player_name),
            'position': result.get('position', ''),
            'sport': sport
        }
        self.cache.set_player(sport, player_name, player_info)
        
        # Cache stats
        cached_result = result.copy()
        cached_result.pop("data_source", None)
        cached_result.pop("cache_hit", None)
        
        self.cache.set_stats(sport, player_info['id'], season, metrics, cached_result)
        self.console.print(f"[dim]💾 Cached result for {player_name} ({sport}, {season})[/dim]")
    
    def _get_seasons_to_try(self, sport: str, requested_seasons: List[int], config: SportConfig) -> List[str]:
        """Get list of seasons to try in order of preference."""
        seasons = []
        
        # If specific seasons requested, try those first
        if requested_seasons:
            for year in requested_seasons:
                if config.season_format == "YYYY":
                    seasons.append(str(year))
                elif config.season_format == "YYYY-YY":
                    seasons.append(f"{year}-{str(year + 1)[-2:]}")
        
        # Add current season if not already included
        current_season = self._get_season_format(sport, [], config)
        if current_season not in seasons:
            seasons.append(current_season)
        
        # Add recent seasons as fallback
        current_year = datetime.now().year
        if datetime.now().month < 8:  # Adjust for sports seasons
            current_year -= 1
            
        for year_offset in [1, 2, 3]:  # Try previous 3 seasons
            fallback_year = current_year - year_offset
            if config.season_format == "YYYY":
                fallback_season = str(fallback_year)
            elif config.season_format == "YYYY-YY":
                fallback_season = f"{fallback_year}-{str(fallback_year + 1)[-2:]}"
            else:
                fallback_season = str(fallback_year)
                
            if fallback_season not in seasons:
                seasons.append(fallback_season)
        
        return seasons
    
    def _format_career_stats_response(self, player: Any, career_stats: Any, sport: str, source: str, config: SportConfig) -> Dict[str, Any]:
        """Format career stats when season stats aren't available."""
        simple_stats = {}
        
        # Convert career stats to simple format
        for stat_name, stat_mapping in config.stat_mappings.items():
            db_column = stat_mapping.db_column
            # Try to get career version of the stat
            career_column = f"career_{db_column}"
            value = getattr(career_stats, career_column, None) or getattr(career_stats, db_column, 0) or 0
            simple_stats[stat_name] = value
        
        return {
            "player_id": player.external_id,
            "player_fullName": player.name,
            "position": player.position,
            "sport": sport,
            "season": "career",
            "data_source": source,
            "simple_stats": simple_stats,
            "note": "Career stats used (no recent season stats available)"
        }
    
    def _format_no_stats_response(self, player: Any, sport: str, seasons_tried: List[str], config: SportConfig) -> Dict[str, Any]:
        """Format response when no stats are available but player exists."""
        return {
            "player_id": player.external_id,
            "player_fullName": player.name,
            "position": player.position,
            "sport": sport,
            "data_source": "database",
            "simple_stats": {},
            "note": f"Player found but no stats available for seasons: {', '.join(seasons_tried)}",
            "suggestion": "This player may be a rookie or have limited playing time. Try checking recent games or different seasons."
        }

# Global instance
universal_stat_retriever = UniversalStatRetriever() 