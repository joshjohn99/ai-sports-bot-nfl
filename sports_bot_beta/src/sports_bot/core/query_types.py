"""
Query Type Classification and Handling Strategies
Defines different types of sports queries and how they should be processed.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

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
        
        # Classify based on AI-generated query context hints FIRST, then keywords as fallback
        is_comparison_query = (
            # Trust the NLU agent's AI analysis first
            query_context.comparison_target in ["player_comparison", "team_comparison", "season_comparison"] or
            query_context.output_expectation == "comparison" or
            # Fallback to keyword matching for simple cases
            any(keyword in question for keyword in cls.COMPARISON_KEYWORDS)
        )
        
        if is_comparison_query:
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
            QueryType.PLAYER_RANKING: ["PlayerStats", "LeagueStats"]
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
        else:
            return {"error": f"Query type {plan.query_type} not yet implemented"}
    
    async def _execute_single_player_stat(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute single player stat query."""
        if not plan.primary_players:
            return {"error": "No player specified for single player query"}
        
        # Use existing logic
        player_stats = self.stat_agent.fetch_stats(query_context)
        return {
            "query_type": plan.query_type.value,
            "player": plan.primary_players[0],
            "stats": player_stats,
            "response_format": plan.response_format
        }
    
    async def _execute_player_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute player comparison query."""
        print(f"[DEBUG] _execute_player_comparison called with {len(plan.primary_players)} players: {plan.primary_players}")
        
        if len(plan.primary_players) < 2:
            # Check if we should look in query_context.player_names instead
            if len(query_context.player_names) >= 2:
                plan.primary_players = query_context.player_names
                print(f"[DEBUG] Using player_names from query_context: {plan.primary_players}")
            else:
                return {"error": f"Need at least 2 players for comparison. Found: {plan.primary_players}"}
        
        all_player_stats = {}
        errors = {}
        
        for player_name in plan.primary_players:
            print(f"[DEBUG] Fetching stats for player: {player_name}")
            # Create a query context for each player
            player_query_context = query_context.model_copy()
            player_query_context.player_names = [player_name]
            
            try:
                player_stats = self.stat_agent.fetch_stats(player_query_context)
                
                # Check if there was an error in fetching stats
                if isinstance(player_stats, dict) and "error" in player_stats:
                    errors[player_name] = player_stats["error"]
                    print(f"[DEBUG] Error fetching stats for {player_name}: {player_stats['error']}")
                else:
                    all_player_stats[player_name] = player_stats
                    print(f"[DEBUG] Successfully fetched stats for {player_name}")
                    
            except Exception as e:
                errors[player_name] = str(e)
                print(f"[DEBUG] Exception fetching stats for {player_name}: {e}")
        
        # If we couldn't get stats for any players, return error
        if not all_player_stats:
            return {
                "error": "Could not retrieve stats for any players",
                "individual_errors": errors,
                "players_attempted": plan.primary_players
            }
        
        # If we got stats for some but not all players
        if errors:
            print(f"[DEBUG] Partial success - got stats for {list(all_player_stats.keys())}, failed for {list(errors.keys())}")
        
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
                    value = stats['simple_stats'].get(metric, 0)
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
                print(f"[DEBUG] Exception fetching stats for {player_name}: {e}")
        
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
        """Execute team comparison query."""
        return {"error": "Team comparisons require additional API endpoints not yet implemented"}
    
    async def _execute_multi_team_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute multi-team comparison query (3+ teams)."""
        return {"error": "Multi-team comparisons require additional API endpoints not yet implemented"}
    
    async def _execute_season_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute season comparison query for a single player across multiple seasons."""
        return {"error": "Season comparisons require additional API endpoints not yet implemented"}
    
    async def _execute_multi_season_comparison(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute multi-season comparison query for a single player across 3+ seasons."""
        return {"error": "Multi-season comparisons require additional API endpoints not yet implemented"}

    async def _execute_league_leaders(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute league leaders query - this would need additional API endpoints."""
        return {"error": "League leaders queries require additional API endpoints not yet implemented"}
    
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
                            break
                overall_scores[player] = score
            
            # Sort by overall score
            overall_rankings = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
            comparison["overall_rankings"] = [
                {"rank": i+1, "player": player, "score": score}
                for i, (player, score) in enumerate(overall_rankings)
            ]
        
        return comparison

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