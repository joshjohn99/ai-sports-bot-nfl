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
    LEAGUE_LEADERS = "league_leaders"                   # "Who leads the league in sacks?"
    TEAM_STATS = "team_stats"                          # "Cowboys total sacks this season"
    PLAYER_RANKING = "player_ranking"                   # "Where does Micah Parsons rank in sacks?"
    MULTI_STAT_PLAYER = "multi_stat_player"           # "Micah Parsons sacks, tackles, and interceptions"
    TEAM_COMPARISON = "team_comparison"                 # "Cowboys vs Giants defensive stats"
    SEASON_COMPARISON = "season_comparison"             # "Micah Parsons 2023 vs 2024 stats"
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
    """Classifies sports queries into types and creates execution plans."""
    
    COMPARISON_KEYWORDS = ['vs', 'versus', 'compare', 'compared to', 'against', 'better than', 'more than', 'less than']
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
        
        # Classify based on question patterns
        if any(keyword in question for keyword in cls.COMPARISON_KEYWORDS):
            if len(query_context.player_names) >= 2:
                plan.query_type = QueryType.PLAYER_COMPARISON
                plan.response_format = "comparison_table"
            elif len(query_context.team_names) >= 2:
                plan.query_type = QueryType.TEAM_COMPARISON
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
        if len(plan.primary_players) < 2:
            return {"error": "Need at least 2 players for comparison"}
        
        all_player_stats = {}
        for player_name in plan.primary_players:
            # Create a query context for each player
            player_query_context = query_context.model_copy()
            player_query_context.player_names = [player_name]
            
            player_stats = self.stat_agent.fetch_stats(player_query_context)
            all_player_stats[player_name] = player_stats
        
        # Compare the stats
        comparison_results = self._compare_player_stats(all_player_stats, plan.metrics)
        
        return {
            "query_type": plan.query_type.value,
            "players": plan.primary_players,
            "individual_stats": all_player_stats,
            "comparison": comparison_results,
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
    
    async def _execute_league_leaders(self, plan: QueryPlan, query_context) -> Dict[str, Any]:
        """Execute league leaders query - this would need additional API endpoints."""
        return {"error": "League leaders queries require additional API endpoints not yet implemented"}

# Usage example for complex queries
QUERY_EXAMPLES = {
    "simple": "Micah Parsons sacks",
    "comparison": "Micah Parsons vs T.J. Watt sacks and tackles", 
    "league_leaders": "Who leads the NFL in sacks?",
    "team_stats": "Dallas Cowboys total sacks this season",
    "ranking": "Where does Micah Parsons rank in NFL sacks?",
    "multi_stat": "Micah Parsons sacks, tackles, and QB hits",
    "threshold": "NFL players with more than 10 sacks",
    "aggregate": "Average sacks per team in the NFC East"
} 