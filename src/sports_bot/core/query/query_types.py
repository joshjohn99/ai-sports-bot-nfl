"""
Query Type Classification and Handling Strategies
Defines different types of sports queries and how they should be processed.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy import func
from ...db.models import Player, Team, PlayerStats

class QueryType(Enum):
    """Classification of different sports query types."""
    SINGLE_PLAYER_STAT = "single_player_stat"           # "Micah Parsons sacks"
    PLAYER_COMPARISON = "player_comparison"             # "Micah Parsons vs T.J. Watt sacks"
    MULTI_PLAYER_COMPARISON = "multi_player_comparison" # "Compare Micah Parsons, T.J. Watt, and Myles Garrett"
    LEAGUE_LEADERS = "league_leaders"                   # "Who leads the league in sacks?"
    TEAM_STATS = "team_stats"                          # "Cowboys total sacks this season"
    PLAYER_RANKING = "player_ranking"                   # "Where does Micah Parsons rank in sacks?"
    MULTI_STAT_PLAYER = "multi_stat_player"           # "Micah Parsons sacks, tackles, and interceptions"
    TEAM_COMPARISON = "team_comparison"                 # "Cowboys vs Giants defensive stats"
    MULTI_TEAM_COMPARISON = "multi_team_comparison"     # "Cowboys vs Giants vs Eagles defensive stats"
    SEASON_COMPARISON = "season_comparison"             # "Micah Parsons 2023 vs 2024 stats"
    MULTI_SEASON_COMPARISON = "multi_season_comparison" # "Micah Parsons 2022 vs 2023 vs 2024 stats"
    THRESHOLD_QUERY = "threshold_query"                 # "Players with more than 10 sacks"
    AGGREGATE_STAT = "aggregate_stat"                   # "Average sacks per game in the NFL"
    CONTEXTUAL_QUERY = "contextual_query"              # "Best pass rusher in the NFC East"
    TREND_ANALYSIS = "trend_analysis"                   # "Micah Parsons sack progression by game"
    GAME_SPECIFIC_STATS = "game_specific_stats"         # "Burrow vs Ravens Week 5"
    CONTEXTUAL_PERFORMANCE = "contextual_performance"   # "Burrow home vs away games"
    GAME_PERFORMANCE_COMPARISON = "game_performance_comparison" # "Burrow's best games this season"

@dataclass
class QueryPlan:
    """Execution plan for a sports query."""
    query_type: QueryType
    primary_players: List[str] = field(default_factory=list)
    secondary_players: List[str] = field(default_factory=list)  # For comparisons
    teams: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)  # season, position, etc.
    aggregation_type: Optional[str] = None  # sum, avg, max, min, rank
    comparison_operators: List[str] = field(default_factory=list)  # vs, more than, less than
    response_format: str = "simple"  # simple, detailed, comparison_table, ranking
    data_sources_needed: List[str] = field(default_factory=list)
    processing_steps: List[str] = field(default_factory=list)

class QueryClassifier:
    """
    Classifies sports queries into types and creates execution plans.
    
    Architecture Decision: Hybrid AI + Keywords Approach
    1. Trust AI-generated hints from NLU agent first (most flexible)
    2. Use keyword matching as fallback (reliable for simple cases)
    3. This gives us the best of both worlds: AI flexibility + deterministic reliability
    """
    
    COMPARISON_KEYWORDS = ['vs', 'versus', 'compare', 'compared to', 'against', 'better than', 'more than', 'less than', 'between', 'who has more', 'who had more', 'who has most', 'who had most']
    RANKING_KEYWORDS = ['rank', 'ranking', 'position', 'where does', 'top', 'best', 'worst', 'leaders']
    AGGREGATE_KEYWORDS = ['total', 'average', 'mean', 'sum', 'combined', 'league', 'all teams']
    THRESHOLD_KEYWORDS = ['more than', 'less than', 'at least', 'over', 'under', 'above', 'below']
    GAME_SPECIFIC_KEYWORDS = ['week', 'in week', 'game against', 'performance against', 'in the game', 'that game', 'game stats']
    CONTEXTUAL_KEYWORDS = ['home', 'away', 'road', 'at home', 'on the road', 'home games', 'away games', 'division games', 'conference games', 'home vs away']
    GAME_COMPARISON_KEYWORDS = ['best game', 'worst game', 'top games', 'best performance', 'best games', 'worst games', 'game by game']
    
    @classmethod
    def classify_query(cls, query_context) -> QueryPlan:
        """Classify a query and create an execution plan."""
        question = query_context.question.lower()
        
        # Initialize plan
        plan = QueryPlan(
            query_type=QueryType.SINGLE_PLAYER_STAT,  # default
            primary_players=query_context.player_names.copy(),
            teams=query_context.team_names.copy(),
            metrics=query_context.metrics_needed.copy(),
            filters={
                'sport': query_context.sport,
                'season_years': query_context.season_years,
                'season': query_context.season
            }
        )
        
        # --- HIGHEST PRIORITY: Check for programmatically overridden leaderboard strategy ---
        if hasattr(query_context, 'strategy') and query_context.strategy == "leaderboard_query":
            plan.query_type = QueryType.LEAGUE_LEADERS
            plan.response_format = "ranking"
            # Skip other classification if this is met, directly set steps and sources below
            plan.processing_steps = cls._get_processing_steps(plan.query_type)
            plan.data_sources_needed = cls._get_data_sources(plan.query_type)
            return plan # Return early as strategy is definitive
        # --- END LEADERBOARD STRATEGY CHECK ---

        # Check for game-specific queries FIRST (high priority after explicit strategy)
        if ('week' in question and ('against' in question or 'vs' in question)) or any(keyword in question for keyword in cls.GAME_SPECIFIC_KEYWORDS):
            plan.query_type = QueryType.GAME_SPECIFIC_STATS
            plan.response_format = "detailed"
            # Extract game context (week, opponent, etc.)
            plan.filters.update(cls._extract_game_context(question, query_context))
        
        elif any(keyword in question for keyword in cls.CONTEXTUAL_KEYWORDS):
            plan.query_type = QueryType.CONTEXTUAL_PERFORMANCE
            plan.response_format = "comparison_table"
            # Extract contextual filters (home/away, division, etc.)
            plan.filters.update(cls._extract_contextual_filters(question))
        
        elif any(keyword in question for keyword in cls.GAME_COMPARISON_KEYWORDS):
            plan.query_type = QueryType.GAME_PERFORMANCE_COMPARISON
            plan.response_format = "ranking"
            # Extract performance criteria
            plan.filters.update(cls._extract_performance_criteria(question))
        
        # Classify based on AI-generated query context hints and comparison keywords
        elif (
            # Trust the NLU agent's AI analysis first
            query_context.comparison_target in ["player_comparison", "team_comparison", "season_comparison"] or
            query_context.output_expectation == "comparison" or
            # Fallback to keyword matching for simple cases
            any(keyword in question for keyword in cls.COMPARISON_KEYWORDS)
        ):
            if len(query_context.player_names) >= 3:
                plan.query_type = QueryType.MULTI_PLAYER_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.player_names) == 2:
                plan.query_type = QueryType.PLAYER_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.team_names) >= 3:
                plan.query_type = QueryType.MULTI_TEAM_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.team_names) == 2:
                plan.query_type = QueryType.TEAM_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.season_years) >= 3 and len(query_context.player_names) == 1:
                plan.query_type = QueryType.MULTI_SEASON_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.season_years) == 2 and len(query_context.player_names) == 1:
                plan.query_type = QueryType.SEASON_COMPARISON
                plan.response_format = "comparison_table"
        
        elif any(keyword in question for keyword in cls.RANKING_KEYWORDS):
            if 'league' in question or 'nfl' in question:
                plan.query_type = QueryType.LEAGUE_LEADERS
                plan.response_format = "ranking"
            else:
                plan.query_type = QueryType.PLAYER_RANKING
                plan.response_format = "ranking"
        
        elif any(keyword in question for keyword in cls.AGGREGATE_KEYWORDS):
            plan.query_type = QueryType.AGGREGATE_STAT
            plan.response_format = "detailed"
        
        elif any(keyword in question for keyword in cls.THRESHOLD_KEYWORDS):
            plan.query_type = QueryType.THRESHOLD_QUERY
            plan.response_format = "ranking"
        
        elif len(query_context.metrics_needed) > 1 and len(query_context.player_names) == 1:
            plan.query_type = QueryType.MULTI_STAT_PLAYER
            plan.response_format = "detailed"
        
        elif len(query_context.team_names) > 0 and len(query_context.player_names) == 0:
            plan.query_type = QueryType.TEAM_STATS
        
        # Set processing steps based on query type
        plan.processing_steps = cls._get_processing_steps(plan.query_type)
        plan.data_sources_needed = cls._get_data_sources(plan.query_type)
        
        return plan
    
    @classmethod
    def _extract_game_context(cls, question: str, query_context) -> Dict[str, Any]:
        """Extract game-specific context like week number, opponent, etc."""
        context = {}
        
        # Extract week number
        import re
        week_match = re.search(r'week\s+(\d+)', question.lower())
        if week_match:
            context['week'] = int(week_match.group(1))
        
        # Extract opponent team - check both query_context teams and common team patterns
        question_lower = question.lower()
        
        # First check teams from query_context
        for team in query_context.team_names:
            if team.lower() in question_lower:
                context['opponent'] = team
                break
        
        # Also check for common team name patterns in the question
        team_patterns = [
            'ravens', 'patriots', 'chiefs', 'steelers', 'bengals', 'cowboys', 'giants', 
            'eagles', 'commanders', 'browns', 'titans', 'colts', 'jaguars', 'texans',
            'broncos', 'chargers', 'raiders', 'dolphins', 'bills', 'jets', 'panthers'
        ]
        
        for pattern in team_patterns:
            if pattern in question_lower:
                context['opponent'] = pattern.title()
                break
        
        return context
    
    @classmethod
    def _extract_contextual_filters(cls, question: str) -> Dict[str, Any]:
        """Extract contextual filters like home/away, division games, etc."""
        filters = {}
        
        if any(keyword in question.lower() for keyword in ['home', 'at home']):
            filters['venue'] = 'home'
        elif any(keyword in question.lower() for keyword in ['away', 'road', 'on the road']):
            filters['venue'] = 'away'
        
        if 'division' in question.lower():
            filters['opponent_type'] = 'division'
        elif 'conference' in question.lower():
            filters['opponent_type'] = 'conference'
        
        return filters
    
    @classmethod
    def _extract_performance_criteria(cls, question: str) -> Dict[str, Any]:
        """Extract performance criteria for game comparisons."""
        criteria = {}
        
        if any(keyword in question.lower() for keyword in ['best', 'highest', 'most']):
            criteria['sort_order'] = 'desc'
        elif any(keyword in question.lower() for keyword in ['worst', 'lowest', 'least']):
            criteria['sort_order'] = 'asc'
        
        # Extract specific metric for sorting
        if 'yards' in question.lower():
            criteria['sort_metric'] = 'passing_yards'
        elif 'touchdown' in question.lower():
            criteria['sort_metric'] = 'passing_touchdowns'
        elif 'rating' in question.lower():
            criteria['sort_metric'] = 'passer_rating'
        
        return criteria
    
    @classmethod
    def _get_processing_steps(cls, query_type: QueryType) -> List[str]:
        """Get the processing steps needed for each query type."""
        steps_map = {
            QueryType.SINGLE_PLAYER_STAT: [
                "resolve_player_id",
                "fetch_player_stats", 
                "extract_requested_metrics",
                "format_simple_response"
            ],
            QueryType.PLAYER_COMPARISON: [
                "resolve_all_player_ids",
                "fetch_all_player_stats",
                "extract_metrics_for_all_players", 
                "compare_metrics",
                "format_comparison_response"
            ],
            QueryType.MULTI_PLAYER_COMPARISON: [
                "resolve_all_player_ids",
                "batch_fetch_player_stats",
                "extract_metrics_for_all_players",
                "perform_n_way_comparison",
                "rank_by_metrics",
                "format_multi_comparison_response"
            ],
            QueryType.TEAM_COMPARISON: [
                "resolve_all_team_ids",
                "fetch_all_team_stats",
                "extract_metrics_for_all_teams",
                "compare_team_metrics",
                "format_team_comparison_response"
            ],
            QueryType.MULTI_TEAM_COMPARISON: [
                "resolve_all_team_ids",
                "batch_fetch_team_stats",
                "extract_metrics_for_all_teams",
                "perform_n_way_team_comparison",
                "rank_teams_by_metrics",
                "format_multi_team_comparison_response"
            ],
            QueryType.SEASON_COMPARISON: [
                "resolve_player_id",
                "fetch_multi_season_stats",
                "extract_metrics_across_seasons",
                "compare_season_metrics",
                "format_season_comparison_response"
            ],
            QueryType.MULTI_SEASON_COMPARISON: [
                "resolve_player_id",
                "batch_fetch_multi_season_stats",
                "extract_metrics_across_all_seasons",
                "perform_n_way_season_comparison",
                "identify_trends",
                "format_multi_season_comparison_response"
            ],
            QueryType.LEAGUE_LEADERS: [
                "fetch_league_stats",
                "rank_by_metric",
                "format_ranking_response"
            ],
            QueryType.PLAYER_RANKING: [
                "resolve_player_id",
                "fetch_player_stats",
                "fetch_league_stats", 
                "calculate_player_rank",
                "format_ranking_response"
            ],
            QueryType.GAME_SPECIFIC_STATS: [
                "resolve_player_id",
                "fetch_player_gamelog",
                "filter_by_game_context",
                "extract_game_stats",
                "format_game_response"
            ],
            QueryType.CONTEXTUAL_PERFORMANCE: [
                "resolve_player_id",
                "fetch_player_gamelog",
                "filter_by_context",
                "aggregate_contextual_stats",
                "format_contextual_comparison"
            ],
            QueryType.GAME_PERFORMANCE_COMPARISON: [
                "resolve_player_id",
                "fetch_player_gamelog",
                "rank_games_by_performance",
                "identify_best_worst_games",
                "format_game_ranking_response"
            ]
        }
        return steps_map.get(query_type, ["unknown_query_type"])
    
    @classmethod 
    def _get_data_sources(cls, query_type: QueryType) -> List[str]:
        """Get the data sources needed for each query type."""
        sources_map = {
            QueryType.SINGLE_PLAYER_STAT: ["PlayerStats"],
            QueryType.PLAYER_COMPARISON: ["PlayerStats", "MultiplePlayerStats"],
            QueryType.MULTI_PLAYER_COMPARISON: ["PlayerStats", "BatchPlayerStats"],
            QueryType.TEAM_COMPARISON: ["TeamStats", "MultipleTeamStats"],
            QueryType.MULTI_TEAM_COMPARISON: ["TeamStats", "BatchTeamStats"],
            QueryType.SEASON_COMPARISON: ["PlayerStats", "MultiSeasonStats"],
            QueryType.MULTI_SEASON_COMPARISON: ["PlayerStats", "BatchSeasonStats"],
            QueryType.LEAGUE_LEADERS: ["LeagueStats", "AllPlayersStats"],
            QueryType.TEAM_STATS: ["TeamStats", "PlayersByTeam"],
            QueryType.PLAYER_RANKING: ["PlayerStats", "LeagueStats"],
            QueryType.GAME_SPECIFIC_STATS: ["PlayerGamelog"],
            QueryType.CONTEXTUAL_PERFORMANCE: ["PlayerGamelog"],
            QueryType.GAME_PERFORMANCE_COMPARISON: ["PlayerGamelog"]
        }
        return sources_map.get(query_type, ["PlayerStats"])

class QueryExecutor:
    """Executes query plans and manages the data flow."""
    
    def __init__(self, stat_retriever_agent):
        self.stat_agent = stat_retriever_agent
        self.execution_cache = {}  # Cache results to avoid redundant API calls
    
    async def execute_plan(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute a query plan and return structured results."""
        
        if plan.query_type == QueryType.SINGLE_PLAYER_STAT:
            return await self._execute_single_player_stat(plan, query_context)
        elif plan.query_type == QueryType.PLAYER_COMPARISON:
            return await self._execute_player_comparison(plan, query_context)
        elif plan.query_type == QueryType.MULTI_PLAYER_COMPARISON:
            return await self._execute_multi_player_comparison(plan, query_context)
        elif plan.query_type == QueryType.TEAM_COMPARISON:
            return await self._execute_team_comparison(plan, query_context)
        elif plan.query_type == QueryType.MULTI_TEAM_COMPARISON:
            return await self._execute_multi_team_comparison(plan, query_context)
        elif plan.query_type == QueryType.SEASON_COMPARISON:
            return await self._execute_season_comparison(plan, query_context)
        elif plan.query_type == QueryType.MULTI_SEASON_COMPARISON:
            return await self._execute_multi_season_comparison(plan, query_context)
        elif plan.query_type == QueryType.LEAGUE_LEADERS:
            return await self._execute_league_leaders(plan, query_context)
        elif plan.query_type == QueryType.GAME_SPECIFIC_STATS:
            return await self._execute_game_specific_stats(plan, query_context)
        elif plan.query_type == QueryType.CONTEXTUAL_PERFORMANCE:
            return await self._execute_contextual_performance(plan, query_context)
        elif plan.query_type == QueryType.GAME_PERFORMANCE_COMPARISON:
            return await self._execute_game_performance_comparison(plan, query_context)
        else:
            return {"error": f"Query type {plan.query_type} not yet implemented"}
    
    async def _execute_single_player_stat(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute single player stat query."""
        if not plan.primary_players:
            return {"error": "No player specified for single player query"}
        
        # Use existing logic
        player_stats = self.stat_agent.fetch_stats(query_context)
        
        # Check if user wants season totals and calculate them
        query_lower = query_context.question.lower()
        if "for season" in query_lower and isinstance(player_stats, dict) and "simple_stats" in player_stats:
            # Calculate season totals
            simple_stats = player_stats["simple_stats"]
            games_played = simple_stats.get("games_played", 0)
            
            if games_played > 0:
                # Create enhanced response with season totals
                player_name = player_stats.get("player_fullName", plan.primary_players[0])
                season = player_stats.get("season", "2024-25")
                
                response_parts = [f"🏀 **{player_name}** Season Totals:"]
                
                # Points calculation
                if "points" in query_lower:
                    points_ppg = simple_stats.get("points", 0)
                    if points_ppg:
                        season_total = points_ppg * games_played
                        response_parts.append(f"• **Season Total Points**: {season_total:,.0f} points")
                        response_parts.append(f"• **Points Per Game**: {points_ppg} PPG")
                        response_parts.append(f"• **Games Played**: {games_played} games")
                        response_parts.append(f"• **Season**: {season}")
                        response_parts.append("")
                        response_parts.append(f"📊 **Calculation**: {points_ppg} PPG × {games_played} games = {season_total:,.0f} total points")
                        
                        response_parts.append("")
                        response_parts.append("✅ **Season totals calculated from per-game averages**")
                        response_parts.append("🚀 *Powered by Enhanced Query Engine*")
                        
                        # Return the calculated response directly
                        return {
                            "query_type": plan.query_type.value,
                            "player": plan.primary_players[0],
                            "stats": player_stats,
                            "response_format": plan.response_format,
                            "calculated_response": "\n".join(response_parts)
                        }
        
        return {
            "query_type": plan.query_type.value,
            "player": plan.primary_players[0],
            "stats": player_stats,
            "response_format": plan.response_format,
            "original_query": query_context.question
        }
    
    async def _execute_player_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute player comparison query with optimized performance."""
        print(f"[DEBUG] _execute_player_comparison called with {len(plan.primary_players)} players: {plan.primary_players}")
        
        if len(plan.primary_players) < 2:
            # Check if we should look in query_context.player_names instead
            if len(query_context.player_names) >= 2:
                plan.primary_players = query_context.player_names
                print(f"[DEBUG] Using player_names from query_context: {plan.primary_players}")
            else:
                return {"error": f"Need at least 2 players for comparison. Found: {plan.primary_players}"}
        
        # Create a single query context with all players and metrics
        batch_query_context = query_context.model_copy()
        batch_query_context.player_names = plan.primary_players
        
        # Batch fetch stats for all players at once
        try:
            batch_stats = self.stat_agent.fetch_stats_batch(batch_query_context)
            
            if isinstance(batch_stats, dict) and "error" in batch_stats:
                return {"error": batch_stats["error"]}
            
            all_player_stats = batch_stats.get("player_stats", {})
            errors = batch_stats.get("errors", {})
            
            # If we couldn't get stats for any players, return error
            if not all_player_stats:
                return {
                    "error": "Could not retrieve stats for any players",
                    "individual_errors": errors,
                    "players_attempted": plan.primary_players
                }
            
            # Compare the stats
            comparison_results = self._compare_player_stats(all_player_stats, plan.metrics)
            
            return {
                "query_type": plan.query_type.value,
                "players": plan.primary_players,
                "individual_stats": all_player_stats,
                "comparison": comparison_results,
                "errors": errors if errors else None,
                "response_format": plan.response_format
            }
            
        except Exception as e:
            print(f"[DEBUG] Exception in batch stats fetch: {str(e)}")
            return {"error": f"Failed to fetch player stats: {str(e)}"}
    
    def _compare_player_stats(self, all_stats: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Compare stats between players."""
        comparison = {
            "winner_by_metric": {},
            "stat_differences": {},
            "summary": ""
        }
        
        for metric in metrics:
            player_values = {}
            for player, stats in all_stats.items():
                if isinstance(stats, dict) and 'simple_stats' in stats:
                    # Try both formats: with spaces and with underscores
                    value = stats['simple_stats'].get(metric, None)
                    if value is None:
                        # Try underscore version
                        underscore_metric = metric.replace(' ', '_')
                        value = stats['simple_stats'].get(underscore_metric, 0)
                    
                    if isinstance(value, (int, float)):
                        player_values[player] = value
            
            if player_values:
                winner = max(player_values, key=player_values.get)
                comparison["winner_by_metric"][metric] = {
                    "winner": winner,
                    "value": player_values[winner],
                    "all_values": player_values
                }
        
        return comparison
    
    async def _execute_multi_player_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute multi-player comparison query (3+ players)."""
        print(f"[DEBUG] _execute_multi_player_comparison called with {len(plan.primary_players)} players: {plan.primary_players}")
        
        players = plan.primary_players if plan.primary_players else query_context.player_names
        
        if len(players) < 3:
            return {"error": f"Need at least 3 players for multi-player comparison. Found: {players}"}
        
        all_player_stats = {}
        errors = {}
        
        # Batch fetch stats for all players
        for player_name in players:
            print(f"[DEBUG] Fetching stats for player: {player_name}")
            player_query_context = query_context.model_copy()
            player_query_context.player_names = [player_name]
            
            try:
                player_stats = self.stat_agent.fetch_stats(player_query_context)
                
                if isinstance(player_stats, dict) and "error" in player_stats:
                    errors[player_name] = player_stats["error"]
                    print(f"[DEBUG] Error fetching stats for {player_name}: {player_stats['error']}")
                else:
                    all_player_stats[player_name] = player_stats
                    print(f"[DEBUG] Successfully fetched stats for {player_name}")
                    
            except Exception as e:
                errors[player_name] = str(e)
                print(f"[DEBUG] Exception fetching stats for {player_name}: Type: {type(e).__name__}, Message: {str(e)}")
        
        if not all_player_stats:
            return {
                "error": "Could not retrieve stats for any players",
                "individual_errors": errors,
                "players_attempted": players
            }
        
        # Perform n-way comparison and ranking
        comparison_results = self._perform_n_way_player_comparison(all_player_stats, plan.metrics)
        
        return {
            "query_type": plan.query_type.value,
            "players": players,
            "individual_stats": all_player_stats,
            "comparison": comparison_results,
            "errors": errors if errors else None,
            "response_format": plan.response_format
        }
    
    async def _execute_team_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute team comparison query using database aggregation."""
        print(f"[DEBUG] _execute_team_comparison called with teams: {plan.teams}")
        
        teams = plan.teams if plan.teams else query_context.team_names
        
        if len(teams) < 2:
            return {"error": f"Need at least 2 teams for comparison. Found: {teams}"}
        
        # Get team stats from database by aggregating player stats
        team_stats = {}
        errors = {}
        
        for team_name in teams:
            try:
                # Find team in database
                team = self.stat_agent.db_session.query(Team).filter(
                    Team.name.ilike(f"%{team_name}%")
                ).first()
                
                if not team:
                    errors[team_name] = "Team not found in database"
                    continue
                
                # Get current season
                season = self.stat_agent.get_season_format(query_context.sport, query_context.season_years)
                
                # Aggregate player stats for this team
                team_totals = self.stat_agent.db_session.query(
                    func.sum(PlayerStats.passing_yards).label('total_passing_yards'),
                    func.sum(PlayerStats.rushing_yards).label('total_rushing_yards'),
                    func.sum(PlayerStats.receiving_yards).label('total_receiving_yards'),
                    func.sum(PlayerStats.passing_touchdowns).label('total_passing_tds'),
                    func.sum(PlayerStats.rushing_touchdowns).label('total_rushing_tds'),
                    func.sum(PlayerStats.receiving_touchdowns).label('total_receiving_tds'),
                    func.sum(PlayerStats.sacks).label('total_sacks'),
                    func.sum(PlayerStats.tackles).label('total_tackles'),
                    func.sum(PlayerStats.interceptions).label('total_interceptions'),
                    func.count(PlayerStats.id).label('player_count')
                ).join(Player).filter(
                    Player.current_team_id == team.id,
                    PlayerStats.season == season
                ).first()
                
                team_stats[team_name] = {
                    'passing_yards': team_totals.total_passing_yards or 0,
                    'rushing_yards': team_totals.total_rushing_yards or 0,
                    'receiving_yards': team_totals.total_receiving_yards or 0,
                    'total_touchdowns': (team_totals.total_passing_tds or 0) + (team_totals.total_rushing_tds or 0) + (team_totals.total_receiving_tds or 0),
                    'sacks': team_totals.total_sacks or 0,
                    'tackles': team_totals.total_tackles or 0,
                    'interceptions': team_totals.total_interceptions or 0,
                    'player_count': team_totals.player_count or 0
                }
                
            except Exception as e:
                errors[team_name] = str(e)
                print(f"[DEBUG] Error fetching stats for team {team_name}: {e}")
        
        if not team_stats:
            return {
                "error": "Could not retrieve stats for any teams",
                "individual_errors": errors,
                "teams_attempted": teams
            }
        
        # Compare team stats
        comparison_results = self._compare_team_stats(team_stats, plan.metrics)
        
        return {
            "query_type": plan.query_type.value,
            "teams": list(team_stats.keys()),
            "team_stats": team_stats,
            "comparison": comparison_results,
            "errors": errors if errors else None,
            "response_format": plan.response_format
        }
    
    def _compare_team_stats(self, team_stats: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Compare stats between teams."""
        comparison = {
            "metrics": {},
            "overall_winner": None,
            "team_scores": {}
        }
        
        # Compare each metric
        for metric in ['passing_yards', 'rushing_yards', 'receiving_yards', 'total_touchdowns', 'sacks', 'tackles', 'interceptions']:
            team_values = {}
            for team, stats in team_stats.items():
                value = stats.get(metric, 0)
                if isinstance(value, (int, float)):
                    team_values[team] = value
            
            if team_values:
                comparison["metrics"][metric] = team_values
        
        # Calculate overall scores (sum of normalized rankings)
        team_scores = {team: 0 for team in team_stats.keys()}
        
        for metric, team_values in comparison["metrics"].items():
            # Sort teams by this metric (higher is better for most stats)
            sorted_teams = sorted(team_values.items(), key=lambda x: x[1], reverse=True)
            
            # Assign points based on ranking (1st place = len(teams) points, 2nd = len(teams)-1, etc.)
            for i, (team, value) in enumerate(sorted_teams):
                team_scores[team] += len(sorted_teams) - i
        
        comparison["team_scores"] = team_scores
        
        # Determine overall winner
        if team_scores:
            comparison["overall_winner"] = max(team_scores, key=team_scores.get)
        
        return comparison
    
    def _compare_multi_team_stats(self, team_stats: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Compare stats between multiple teams (3+) with rankings."""
        comparison = {
            "rankings_by_metric": {},
            "overall_rankings": [],
            "team_scores": {}
        }
        
        # Create rankings for each metric
        for metric in ['passing_yards', 'rushing_yards', 'receiving_yards', 'total_touchdowns', 'sacks', 'tackles', 'interceptions']:
            team_values = {}
            for team, stats in team_stats.items():
                value = stats.get(metric, 0)
                if isinstance(value, (int, float)):
                    team_values[team] = value
            
            if team_values:
                # Sort teams by this metric (higher is better)
                sorted_teams = sorted(team_values.items(), key=lambda x: x[1], reverse=True)
                
                comparison["rankings_by_metric"][metric] = [
                    {"rank": i+1, "team": team, "value": value} 
                    for i, (team, value) in enumerate(sorted_teams)
                ]
        
        # Calculate overall rankings across all metrics
        team_scores = {team: 0 for team in team_stats.keys()}
        
        for metric_rankings in comparison["rankings_by_metric"].values():
            for ranking in metric_rankings:
                team = ranking["team"]
                rank = ranking["rank"]
                # Lower rank number = higher score
                team_scores[team] += len(team_stats) - rank + 1
        
        comparison["team_scores"] = team_scores
        
        # Sort by overall score
        overall_rankings = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
        comparison["overall_rankings"] = [
            {"rank": i+1, "team": team, "score": score}
            for i, (team, score) in enumerate(overall_rankings)
        ]
        
        return comparison
    
    async def _execute_multi_team_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute multi-team comparison query (3+ teams) using database aggregation."""
        print(f"[DEBUG] _execute_multi_team_comparison called with teams: {plan.teams}")
        
        teams = plan.teams if plan.teams else query_context.team_names
        
        if len(teams) < 3:
            return {"error": f"Need at least 3 teams for multi-team comparison. Found: {teams}"}
        
        # Get team stats from database by aggregating player stats
        team_stats = {}
        errors = {}
        
        for team_name in teams:
            try:
                # Find team in database
                team = self.stat_agent.db_session.query(Team).filter(
                    Team.name.ilike(f"%{team_name}%")
                ).first()
                
                if not team:
                    errors[team_name] = "Team not found in database"
                    continue
                
                # Get current season
                season = self.stat_agent.get_season_format(query_context.sport, query_context.season_years)
                
                # Aggregate player stats for this team
                team_totals = self.stat_agent.db_session.query(
                    func.sum(PlayerStats.passing_yards).label('total_passing_yards'),
                    func.sum(PlayerStats.rushing_yards).label('total_rushing_yards'),
                    func.sum(PlayerStats.receiving_yards).label('total_receiving_yards'),
                    func.sum(PlayerStats.passing_touchdowns).label('total_passing_tds'),
                    func.sum(PlayerStats.rushing_touchdowns).label('total_rushing_tds'),
                    func.sum(PlayerStats.receiving_touchdowns).label('total_receiving_tds'),
                    func.sum(PlayerStats.sacks).label('total_sacks'),
                    func.sum(PlayerStats.tackles).label('total_tackles'),
                    func.sum(PlayerStats.interceptions).label('total_interceptions'),
                    func.count(PlayerStats.id).label('player_count')
                ).join(Player).filter(
                    Player.current_team_id == team.id,
                    PlayerStats.season == season
                ).first()
                
                team_stats[team_name] = {
                    'passing_yards': team_totals.total_passing_yards or 0,
                    'rushing_yards': team_totals.total_rushing_yards or 0,
                    'receiving_yards': team_totals.total_receiving_yards or 0,
                    'total_touchdowns': (team_totals.total_passing_tds or 0) + (team_totals.total_rushing_tds or 0) + (team_totals.total_receiving_tds or 0),
                    'sacks': team_totals.total_sacks or 0,
                    'tackles': team_totals.total_tackles or 0,
                    'interceptions': team_totals.total_interceptions or 0,
                    'player_count': team_totals.player_count or 0
                }
                
            except Exception as e:
                errors[team_name] = str(e)
                print(f"[DEBUG] Error fetching stats for team {team_name}: {e}")
        
        if not team_stats:
            return {
                "error": "Could not retrieve stats for any teams",
                "individual_errors": errors,
                "teams_attempted": teams
            }
        
        # Compare team stats and create rankings
        comparison_results = self._compare_multi_team_stats(team_stats, plan.metrics)
        
        return {
            "query_type": plan.query_type.value,
            "teams": list(team_stats.keys()),
            "team_stats": team_stats,
            "comparison": comparison_results,
            "errors": errors if errors else None,
            "response_format": plan.response_format
        }
    
    async def _execute_season_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute season comparison query for a single player across multiple seasons."""
        print(f"[DEBUG] _execute_season_comparison called with seasons: {query_context.season_years}")
        
        if not plan.primary_players and not query_context.player_names:
            return {"error": "No player specified for season comparison"}
        
        player_name = plan.primary_players[0] if plan.primary_players else query_context.player_names[0]
        seasons = query_context.season_years
        
        if len(seasons) < 2:
            return {"error": f"Need at least 2 seasons for comparison. Found: {seasons}"}
        
        season_stats = {}
        errors = {}
        
        # Fetch stats for each season
        for season in seasons:
            print(f"[DEBUG] Fetching stats for {player_name} in season {season}")
            try:
                season_query_context = query_context.model_copy()
                season_query_context.season = str(season)
                season_query_context.season_years = [season]
                
                # Use StatRetriever's season-aware functionality
                player_stats = self.stat_agent.fetch_stats_for_season(season_query_context, season)
                
                if isinstance(player_stats, dict) and "error" in player_stats:
                    errors[str(season)] = player_stats["error"]
                    print(f"[DEBUG] Error fetching stats for {player_name} in {season}: {player_stats['error']}")
                else:
                    season_stats[str(season)] = player_stats
                    print(f"[DEBUG] Successfully fetched stats for {player_name} in {season}")
                    
            except Exception as e:
                errors[str(season)] = str(e)
                print(f"[DEBUG] Exception fetching stats for {player_name} in {season}: Type: {type(e).__name__}, Message: {str(e)}")
        
        if not season_stats:
            return {
                "error": "Could not retrieve stats for any seasons",
                "individual_errors": errors,
                "seasons_attempted": seasons
            }
        
        # Compare the season stats
        comparison_results = self._compare_season_stats(season_stats, plan.metrics, player_name)
        
        return {
            "query_type": plan.query_type.value,
            "player": player_name,
            "seasons": seasons,
            "individual_stats": season_stats,
            "comparison": comparison_results,
            "errors": errors if errors else None,
            "response_format": plan.response_format
        }
    
    async def _execute_multi_season_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute multi-season comparison query for a single player across 3+ seasons."""
        print(f"[DEBUG] _execute_multi_season_comparison called with seasons: {query_context.season_years}")
        
        if not plan.primary_players and not query_context.player_names:
            return {"error": "No player specified for multi-season comparison"}
        
        player_name = plan.primary_players[0] if plan.primary_players else query_context.player_names[0]
        seasons = query_context.season_years
        
        if len(seasons) < 3:
            return {"error": f"Need at least 3 seasons for multi-season comparison. Found: {seasons}"}
        
        season_stats = {}
        errors = {}
        
        # Batch fetch stats for all seasons
        for season in seasons:
            print(f"[DEBUG] Fetching stats for {player_name} in season {season}")
            try:
                season_query_context = query_context.model_copy()
                season_query_context.season = str(season)
                season_query_context.season_years = [season]
                
                player_stats = self.stat_agent.fetch_stats_for_season(season_query_context, season)
                
                if isinstance(player_stats, dict) and "error" in player_stats:
                    errors[str(season)] = player_stats["error"]
                    print(f"[DEBUG] Error fetching stats for {player_name} in {season}: {player_stats['error']}")
                else:
                    season_stats[str(season)] = player_stats
                    print(f"[DEBUG] Successfully fetched stats for {player_name} in {season}")
                    
            except Exception as e:
                errors[str(season)] = str(e)
                print(f"[DEBUG] Exception fetching stats for {player_name} in {season}: Type: {type(e).__name__}, Message: {str(e)}")
        
        if not season_stats:
            return {
                "error": "Could not retrieve stats for any seasons",
                "individual_errors": errors,
                "seasons_attempted": seasons
            }
        
        # Perform n-way season comparison and trend analysis
        comparison_results = self._perform_n_way_season_comparison(season_stats, plan.metrics, player_name)
        
        return {
            "query_type": plan.query_type.value,
            "player": player_name,
            "seasons": seasons,
            "individual_stats": season_stats,
            "comparison": comparison_results,
            "errors": errors if errors else None,
            "response_format": plan.response_format
        }

    async def _execute_league_leaders(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute league leaders query by calling the stat_agent's fetch_league_leaders method."""
        # This was previously a placeholder.
        # Now it calls the actual implementation in StatRetrieverApiAgent.
        if not hasattr(self.stat_agent, 'fetch_league_leaders'):
            return {"error": "StatRetrieverApiAgent does not have fetch_league_leaders method."}
        
        # Ensure query_context.strategy is appropriate if it wasn't set by the classifier's override
        # (though the classifier change should handle this ideally)
        if query_context.strategy != "leaderboard_query":
            # This is a safeguard, ideally QueryClassifier sets plan.query_type correctly
            # based on our forced strategy, or the strategy itself is enough for fetch_league_leaders.
            # For now, we assume if plan.query_type is LEAGUE_LEADERS, query_context is fit for fetch_league_leaders.
            pass # Assuming query_context is suitable if plan.query_type is LEAGUE_LEADERS

        # Call the method in StatRetrieverApiAgent that handles programmatic leaderboard fetching
        # This method is synchronous, so we don't await it directly here unless it's refactored to be async.
        # For now, if fetch_league_leaders is synchronous, we call it directly.
        # If your application uses asyncio extensively and fetch_league_leaders becomes async, you'd await it.
        
        # Assuming fetch_league_leaders is synchronous based on its current implementation in stat_retriever.py
        # (It uses requests.get(), not an async HTTP client)
        try:
            # We are in an async def, so if stat_agent methods are not async, 
            # they should be run in an executor or StatRetrieverApiAgent needs async methods.
            # For now, let's assume direct call if it's designed to work in this async context
            # or that the event loop handles synchronous calls appropriately for your setup.
            
            # Given the structure, the actual call should be made from StatRetrieverAgent,
            # which is synchronous. The QueryExecutor is async.
            # To bridge this, ideally StatRetrieverAgent would also have async methods or 
            # use asyncio.to_thread for blocking calls.
            # For a direct fix, if stat_agent.fetch_league_leaders is blocking:
            # result = await asyncio.to_thread(self.stat_agent.fetch_league_leaders, query_context)
            # However, let's try a direct call first and see if the execution model handles it.
            # If fetch_league_leaders is synchronous, this call will block the event loop.

            # The StatRetrieverApiAgent.fetch_league_leaders method is synchronous.
            # QueryExecutor methods are async.
            # To call a synchronous method from an async one without blocking the event loop
            # for too long (especially if it makes network requests), use asyncio.to_thread.
            import asyncio # Ensure asyncio is imported
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.stat_agent.fetch_league_leaders, query_context)
            
            # Add query_type to the result for consistency if not already present
            if isinstance(result, dict) and 'query_type' not in result:
                 result['query_type'] = plan.query_type.value
            if isinstance(result, dict) and 'response_format' not in result:
                 result['response_format'] = plan.response_format
            return result
        except Exception as e:
            # Log the exception for debugging
            # console.print_exception(show_locals=True) # If console is available here
            return {"error": f"Error executing league_leaders query: {str(e)}"}

    def _perform_n_way_player_comparison(self, all_stats: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Perform n-way comparison between multiple players."""
        comparison = {
            "winner_by_metric": {},
            "rankings_by_metric": {},
            "stat_differences": {},
            "summary": "",
            "overall_rankings": {}
        }
        
        for metric in metrics:
            player_values = {}
            for player, stats in all_stats.items():
                if isinstance(stats, dict) and 'simple_stats' in stats:
                    value = stats['simple_stats'].get(metric, 0)
                    if isinstance(value, (int, float)):
                        player_values[player] = value
            
            if player_values:
                # Sort players by metric value (descending)
                ranked_players = sorted(player_values.items(), key=lambda x: x[1], reverse=True)
                
                comparison["winner_by_metric"][metric] = {
                    "winner": ranked_players[0][0],
                    "value": ranked_players[0][1],
                    "all_values": player_values
                }
                
                comparison["rankings_by_metric"][metric] = [
                    {"rank": i+1, "player": player, "value": value} 
                    for i, (player, value) in enumerate(ranked_players)
                ]
        
        # Calculate overall rankings across all metrics
        if comparison["winner_by_metric"]:
            overall_scores = {}
            for player in all_stats.keys():
                score = 0
                for metric_data in comparison["rankings_by_metric"].values():
                    for ranking in metric_data:
                        if ranking["player"] == player:
                            # Lower rank number = higher score
                            score += (len(all_stats) - ranking["rank"] + 1)
                overall_scores[player] = score
            
            # Sort by overall score
            overall_rankings = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
            comparison["overall_rankings"] = [
                {"rank": i+1, "player": player, "score": score}
                for i, (player, score) in enumerate(overall_rankings)
            ]
        
        return comparison
    
    def _compare_season_stats(self, season_stats: Dict[str, Any], metrics: List[str], player_name: str) -> Dict[str, Any]:
        """Compare stats between seasons for a single player."""
        comparison = {
            "best_season_by_metric": {},
            "season_differences": {},
            "trends": {},
            "summary": f"Season comparison for {player_name}"
        }
        
        for metric in metrics:
            season_values = {}
            for season, stats in season_stats.items():
                if isinstance(stats, dict) and 'simple_stats' in stats:
                    value = stats['simple_stats'].get(metric, 0)
                    if isinstance(value, (int, float)):
                        season_values[season] = value
            
            if season_values:
                best_season = max(season_values, key=season_values.get)
                worst_season = min(season_values, key=season_values.get)
                
                comparison["best_season_by_metric"][metric] = {
                    "best_season": best_season,
                    "best_value": season_values[best_season],
                    "worst_season": worst_season,
                    "worst_value": season_values[worst_season],
                    "all_values": season_values,
                    "improvement": season_values[best_season] - season_values[worst_season]
                }
                
                # Calculate trend (simple linear trend)
                seasons_ordered = sorted(season_values.keys())
                if len(seasons_ordered) >= 2:
                    first_season_value = season_values[seasons_ordered[0]]
                    last_season_value = season_values[seasons_ordered[-1]]
                    trend = "increasing" if last_season_value > first_season_value else "decreasing"
                    comparison["trends"][metric] = {
                        "direction": trend,
                        "change": last_season_value - first_season_value,
                        "percentage_change": ((last_season_value - first_season_value) / first_season_value * 100) if first_season_value > 0 else 0
                    }
        
        return comparison
    
    def _perform_n_way_season_comparison(self, season_stats: Dict[str, Any], metrics: List[str], player_name: str) -> Dict[str, Any]:
        """Perform n-way comparison between multiple seasons for a single player."""
        comparison = {
            "best_season_by_metric": {},
            "rankings_by_metric": {},
            "trends": {},
            "career_progression": {},
            "summary": f"Multi-season analysis for {player_name}",
            "overall_rankings": {}
        }
        
        for metric in metrics:
            season_values = {}
            for season, stats in season_stats.items():
                if isinstance(stats, dict) and 'simple_stats' in stats:
                    value = stats['simple_stats'].get(metric, 0)
                    if isinstance(value, (int, float)):
                        season_values[season] = value
            
            if season_values:
                # Sort seasons by metric value (descending)
                ranked_seasons = sorted(season_values.items(), key=lambda x: x[1], reverse=True)
                
                comparison["best_season_by_metric"][metric] = {
                    "best_season": ranked_seasons[0][0],
                    "best_value": ranked_seasons[0][1],
                    "worst_season": ranked_seasons[-1][0],
                    "worst_value": ranked_seasons[-1][1],
                    "all_values": season_values
                }
                
                comparison["rankings_by_metric"][metric] = [
                    {"rank": i+1, "season": season, "value": value} 
                    for i, (season, value) in enumerate(ranked_seasons)
                ]
                
                # Calculate career progression
                seasons_ordered = sorted(season_values.keys())
                progression = []
                for i, season in enumerate(seasons_ordered):
                    if i > 0:
                        prev_value = season_values[seasons_ordered[i-1]]
                        curr_value = season_values[season]
                        change = curr_value - prev_value
                        progression.append({
                            "from_season": seasons_ordered[i-1],
                            "to_season": season,
                            "change": change,
                            "trend": "improved" if change > 0 else "declined" if change < 0 else "stable"
                        })
                
                comparison["career_progression"][metric] = progression
        
        # Calculate overall season rankings across all metrics
        if comparison["best_season_by_metric"]:
            overall_scores = {}
            all_seasons = set()
            for season_data in season_stats.keys():
                all_seasons.add(season_data)
            
            for season in all_seasons:
                score = 0
                for metric_data in comparison["rankings_by_metric"].values():
                    for ranking in metric_data:
                        if ranking["season"] == season:
                            # Lower rank number = higher score
                            score += (len(all_seasons) - ranking["rank"] + 1)
                            break
                overall_scores[season] = score
            
            # Sort by overall score
            overall_rankings = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
            comparison["overall_rankings"] = [
                {"rank": i+1, "season": season, "score": score}
                for i, (season, score) in enumerate(overall_rankings)
            ]
        
        return comparison

    async def _execute_game_specific_stats(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute game-specific stats query (e.g., 'Burrow vs Ravens Week 5')."""
        print(f"[DEBUG] _execute_game_specific_stats called")
        
        if not plan.primary_players and not query_context.player_names:
            return {"error": "No player specified for game-specific query"}
        
        player_name = plan.primary_players[0] if plan.primary_players else query_context.player_names[0]
        
        try:
            # Fetch player gamelog data
            gamelog_data = await self._fetch_player_gamelog(player_name, query_context)
            
            if isinstance(gamelog_data, dict) and "error" in gamelog_data:
                return gamelog_data
            
            # Filter games based on context (week, opponent, etc.)
            filtered_games = self._filter_games_by_context(gamelog_data, plan.filters)
            
            if not filtered_games:
                return {"error": f"No games found matching the specified criteria"}
            
            return {
                "query_type": plan.query_type.value,
                "player": player_name,
                "filters_applied": plan.filters,
                "matching_games": filtered_games,
                "response_format": plan.response_format
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch game-specific stats: {str(e)}"}
    
    async def _execute_contextual_performance(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute contextual performance query (e.g., 'Burrow home vs away games')."""
        print(f"[DEBUG] _execute_contextual_performance called")
        
        if not plan.primary_players and not query_context.player_names:
            return {"error": "No player specified for contextual performance query"}
        
        player_name = plan.primary_players[0] if plan.primary_players else query_context.player_names[0]
        
        try:
            # Fetch player gamelog data
            gamelog_data = await self._fetch_player_gamelog(player_name, query_context)
            
            if isinstance(gamelog_data, dict) and "error" in gamelog_data:
                return gamelog_data
            
            # Aggregate stats by context (home/away, division games, etc.)
            contextual_stats = self._aggregate_contextual_stats(gamelog_data, plan.filters, plan.metrics)
            
            return {
                "query_type": plan.query_type.value,
                "player": player_name,
                "context_type": plan.filters,
                "contextual_breakdown": contextual_stats,
                "response_format": plan.response_format
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch contextual performance: {str(e)}"}
    
    async def _execute_game_performance_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute game performance comparison query (e.g., 'Burrow's best games this season')."""
        print(f"[DEBUG] _execute_game_performance_comparison called")
        
        if not plan.primary_players and not query_context.player_names:
            return {"error": "No player specified for game performance comparison"}
        
        player_name = plan.primary_players[0] if plan.primary_players else query_context.player_names[0]
        
        try:
            # Fetch player gamelog data
            gamelog_data = await self._fetch_player_gamelog(player_name, query_context)
            
            if isinstance(gamelog_data, dict) and "error" in gamelog_data:
                return gamelog_data
            
            # Rank games by performance
            ranked_games = self._rank_games_by_performance(gamelog_data, plan.filters, plan.metrics)
            
            return {
                "query_type": plan.query_type.value,
                "player": player_name,
                "performance_criteria": plan.filters,
                "ranked_games": ranked_games,
                "response_format": plan.response_format
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch game performance comparison: {str(e)}"}
    
    async def _fetch_player_gamelog(self, player_name: str, query_context) -> Dict[str, Any]:
        """Fetch player gamelog data using the new API endpoint."""
        try:
            # Get player ID first
            player_id = await self._resolve_player_id(player_name, query_context)
            
            if not player_id:
                return {"error": f"Could not find player ID for {player_name}"}
            
            # Use the gamelog function from api_config
            from sports_bot.config.api_config import get_player_gamelog
            gamelog_data = get_player_gamelog(player_id)
            
            return gamelog_data
            
        except Exception as e:
            return {"error": f"Failed to fetch gamelog for {player_name}: {str(e)}"}
    
    async def _resolve_player_id(self, player_name: str, query_context) -> Optional[str]:
        """Resolve player name to player ID."""
        try:
            # Use existing stat agent's player resolution logic
            if hasattr(self.stat_agent, '_get_player_id_with_context'):
                return await self.stat_agent._get_player_id_with_context(player_name, query_context)
            else:
                # Fallback to basic player ID resolution
                from sports_bot.config.api_config import get_player_id
                return get_player_id(player_name)
        except Exception as e:
            print(f"[DEBUG] Error resolving player ID for {player_name}: {e}")
            return None
    
    def _filter_games_by_context(self, gamelog_data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter gamelog data based on specified context (week, opponent, etc.)."""
        if not gamelog_data or 'events' not in gamelog_data:
            return []
        
        events = gamelog_data['events']
        matching_games = []
        
        for event_id, game_data in events.items():
            # Check week filter
            if 'week' in filters:
                if game_data.get('week') != filters['week']:
                    continue
            
            # Check opponent filter
            if 'opponent' in filters:
                opponent_name = game_data.get('opponent', {}).get('displayName', '')
                if filters['opponent'].lower() not in opponent_name.lower():
                    continue
            
            # If game matches all filters, add it
            matching_games.append({
                'event_id': event_id,
                'week': game_data.get('week'),
                'opponent': game_data.get('opponent', {}).get('displayName'),
                'score': game_data.get('score'),
                'result': game_data.get('gameResult'),
                'date': game_data.get('gameDate'),
                'game_data': game_data
            })
        
        return matching_games
    
    def _aggregate_contextual_stats(self, gamelog_data: Dict[str, Any], filters: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        """Aggregate stats by context (home/away, division games, etc.)."""
        if not gamelog_data or 'events' not in gamelog_data:
            return {}
        
        events = gamelog_data['events']
        categories = gamelog_data.get('seasonTypes', [{}])[0].get('categories', [{}])[0]
        event_stats = {event['eventId']: event['stats'] for event in categories.get('events', [])}
        
        contextual_breakdown = {}
        
        for event_id, game_data in events.items():
            # Determine context for this game
            context = self._determine_game_context(game_data, filters)
            
            if context not in contextual_breakdown:
                contextual_breakdown[context] = {
                    'games': [],
                    'total_stats': {},
                    'avg_stats': {}
                }
            
            # Add game to appropriate context
            contextual_breakdown[context]['games'].append({
                'week': game_data.get('week'),
                'opponent': game_data.get('opponent', {}).get('displayName'),
                'result': game_data.get('gameResult'),
                'stats': event_stats.get(event_id, [])
            })
        
        # Calculate aggregated stats for each context
        for context, data in contextual_breakdown.items():
            if data['games']:
                data['game_count'] = len(data['games'])
                # Calculate totals and averages (implementation depends on stat structure)
                # This would need to be enhanced based on the actual gamelog structure
        
        return contextual_breakdown
    
    def _rank_games_by_performance(self, gamelog_data: Dict[str, Any], filters: Dict[str, Any], metrics: List[str]) -> List[Dict[str, Any]]:
        """Rank games by performance based on specified criteria."""
        if not gamelog_data or 'events' not in gamelog_data:
            return []
        
        events = gamelog_data['events']
        categories = gamelog_data.get('seasonTypes', [{}])[0].get('categories', [{}])[0]
        event_stats = {event['eventId']: event['stats'] for event in categories.get('events', [])}
        stat_names = gamelog_data.get('names', [])
        
        ranked_games = []
        
        for event_id, game_data in events.items():
            game_stats = event_stats.get(event_id, [])
            
            # Extract the sorting metric value
            sort_metric = filters.get('sort_metric', 'passing_yards')
            sort_order = filters.get('sort_order', 'desc')
            
            # Map metric name to index in stats array
            metric_value = 0
            try:
                if sort_metric == 'passing_yards' and len(game_stats) >= 3:
                    metric_value = int(game_stats[2])  # Passing yards is typically index 2
                elif sort_metric == 'passing_touchdowns' and len(game_stats) >= 6:
                    metric_value = int(game_stats[5])  # Passing TDs is typically index 5
                elif sort_metric == 'passer_rating' and len(game_stats) >= 10:
                    metric_value = float(game_stats[9])  # Passer rating is typically index 9
            except (ValueError, IndexError):
                metric_value = 0
            
            ranked_games.append({
                'event_id': event_id,
                'week': game_data.get('week'),
                'opponent': game_data.get('opponent', {}).get('displayName'),
                'score': game_data.get('score'),
                'result': game_data.get('gameResult'),
                'metric_value': metric_value,
                'sort_metric': sort_metric,
                'stats': game_stats
            })
        
        # Sort games by performance
        reverse_order = sort_order == 'desc'
        ranked_games.sort(key=lambda x: x['metric_value'], reverse=reverse_order)
        
        # Add ranking
        for i, game in enumerate(ranked_games):
            game['rank'] = i + 1
        
        return ranked_games
    
    def _determine_game_context(self, game_data: Dict[str, Any], filters: Dict[str, Any]) -> str:
        """Determine the context category for a game (home/away, division, etc.)."""
        # Check venue context
        if 'venue' in filters:
            venue_type = filters['venue']
            at_vs = game_data.get('atVs', '@')
            
            if venue_type == 'home' and at_vs == 'vs':
                return 'home'
            elif venue_type == 'away' and at_vs == '@':
                return 'away'
        
        # Check opponent type context
        if 'opponent_type' in filters:
            # This would need division/conference mapping logic
            # For now, return a basic categorization
            return filters['opponent_type']
        
        # Default context
        return 'all_games'

# Usage example for scalable queries
QUERY_EXAMPLES = {
    # Single entity queries
    "simple": "Micah Parsons sacks",
    "multi_stat": "Micah Parsons sacks, tackles, and QB hits",
    
    # 2-way comparisons
    "comparison": "Micah Parsons vs T.J. Watt sacks and tackles",
    "team_comparison": "Cowboys vs Giants defensive stats",
    "season_comparison": "Micah Parsons 2023 vs 2024 stats",
    
    # N-way comparisons (3+)
    "multi_player": "Compare Micah Parsons, T.J. Watt, and Myles Garrett sacks",
    "multi_team": "Cowboys vs Giants vs Eagles vs Commanders defensive stats",
    "multi_season": "Micah Parsons 2022 vs 2023 vs 2024 stats",
    
    # Complex scalable queries
    "5_player_comparison": "Compare Aaron Donald, Micah Parsons, T.J. Watt, Myles Garrett, and Nick Bosa sacks and QB hits",
    "division_comparison": "Compare all NFC East teams total sacks",
    "career_progression": "Micah Parsons stats from 2021, 2022, 2023, and 2024",
    
    # Rankings and aggregates
    "league_leaders": "Who leads the NFL in sacks?",
    "ranking": "Where does Micah Parsons rank in NFL sacks?",
    "threshold": "NFL players with more than 10 sacks",
    "aggregate": "Average sacks per team in the NFC East"
} 