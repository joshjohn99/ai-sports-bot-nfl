"""
LangChain Tools for Sports Bot - Sport Agnostic API Integration

This module implements the recommendation from the architectural review to standardize
API integration using LangChain's tools framework while maintaining sport scalability.
"""

from typing import Dict, Any, List, Optional, Type, ClassVar
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from sports_bot.config.api_config import api_config
from sports_bot.cache.shared_cache import get_cache_instance
from sports_bot.core.stats.stat_retriever import StatRetrieverApiAgent
import requests
import asyncio


class SportContext(BaseModel):
    """Context information for sport-specific operations"""
    sport: str = Field(description="Sport code (NFL, NBA, MLB, etc.)")
    season: Optional[str] = Field(default=None, description="Season year")
    
    
class PlayerStatsInput(BaseModel):
    """Input schema for player statistics tool"""
    player_name: str = Field(description="Name of the player")
    sport_context: SportContext = Field(description="Sport and season context")
    metrics: List[str] = Field(default=[], description="Specific metrics to retrieve")


class TeamListingInput(BaseModel):
    """Input schema for team listing tool"""
    sport_context: SportContext = Field(description="Sport context")


class PlayerSearchInput(BaseModel):
    """Input schema for player search/disambiguation tool"""
    player_name: str = Field(description="Player name (possibly misspelled)")
    sport_context: SportContext = Field(description="Sport context")
    confidence_threshold: float = Field(default=0.85, description="Minimum confidence for auto-selection")


class FetchPlayerStatsTool(BaseTool):
    """
    LangChain Tool for fetching player statistics across sports.
    
    This implements the recommendation to encapsulate API calls within LangChain Tools,
    allowing LLMs to dynamically decide when and how to invoke external services.
    """
    name: str = "fetch_player_stats"
    description: str = """
    Fetch comprehensive statistics for a specific player in any sport.
    Use this when you need detailed performance data for a player.
    Input should include player name, sport, and optionally specific metrics.
    """
    args_schema: Type[BaseModel] = PlayerStatsInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        player_name: str,
        sport_context: SportContext,
        metrics: List[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Execute the player stats fetch operation"""
        
        # Create a minimal query context for the existing system
        from sports_bot.agents.sports_agents import QueryContext
        
        query_context = QueryContext(
            question=f"Get {player_name} stats",
            sport=sport_context.sport,
            player_names=[player_name],
            season=sport_context.season,
            metrics_needed=metrics or []
        )
        
        # Use existing stat retriever with caching
        try:
            stat_agent = StatRetrieverApiAgent(api_config)
            result = stat_agent.fetch_stats(query_context)
            
            # Standardize the response format
            return {
                "success": True,
                "player_name": player_name,
                "sport": sport_context.sport,
                "season": sport_context.season,
                "data": result,
                "source": "langchain_tool"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "player_name": player_name,
                "sport": sport_context.sport
            }


class FetchTeamListingTool(BaseTool):
    """
    LangChain Tool for fetching team listings across sports.
    
    Supports the League Leaders workflow by providing team data for roster fetching.
    """
    name: str = "fetch_team_listing"
    description: str = """
    Fetch the complete list of teams for a specific sport.
    Use this when you need to get all teams in a league for comprehensive analysis.
    """
    args_schema: Type[BaseModel] = TeamListingInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        sport_context: SportContext,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Execute the team listing fetch operation"""
        
        sport = sport_context.sport.upper()
        
        # Check cache first
        cache = get_cache_instance()
        cached_teams = cache.get_team_list(sport)
        if cached_teams:
            return {
                "success": True,
                "sport": sport,
                "teams": cached_teams,
                "source": "cache"
            }
        
        # Fetch from API
        try:
            sport_config = api_config.get(sport, {})
            if not sport_config:
                raise ValueError(f"Sport {sport} not configured")
            
            base_url = sport_config['base_url']
            endpoint = sport_config['endpoints']['AllTeams']
            headers = sport_config['headers']
            
            url = f"{base_url}{endpoint}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            teams_data = response.json()
            
            # Cache the result
            cache.set_team_list(sport, teams_data)
            
            return {
                "success": True,
                "sport": sport,
                "teams": teams_data,
                "source": "api"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sport": sport
            }


class FuzzyPlayerSearchTool(BaseTool):
    """
    LangChain Tool for fuzzy player name search and disambiguation.
    
    This implements the recommendation for enhanced player disambiguation using
    LLM reasoning combined with fuzzy matching logic.
    """
    name: str = "fuzzy_player_search"
    description: str = """
    Search for players with fuzzy name matching to handle typos and ambiguity.
    Returns potential matches with confidence scores for disambiguation.
    Use this when a player name might be misspelled or ambiguous.
    """
    args_schema: Type[BaseModel] = PlayerSearchInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        player_name: str,
        sport_context: SportContext,
        confidence_threshold: float = 0.85,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Execute fuzzy player search"""
        
        try:
            # Use existing fuzzy matching logic
            from sports_bot.agents.sports_agents import QueryContext
            
            query_context = QueryContext(
                question=f"Find player {player_name}",
                sport=sport_context.sport,
                player_names=[player_name]
            )
            
            # Get best matching players
            stat_agent = StatRetrieverApiAgent(api_config)
            matches = stat_agent.find_best_matching_player(player_name, query_context)
            
            if not matches:
                return {
                    "success": False,
                    "error": "No matching players found",
                    "player_name": player_name,
                    "sport": sport_context.sport
                }
            
            # If it's a disambiguation scenario (multiple matches)
            if isinstance(matches, dict) and matches.get('error') == 'Multiple players found':
                return {
                    "success": True,
                    "disambiguation_needed": True,
                    "matches": matches.get('matching_players', []),
                    "original_name": player_name,
                    "sport": sport_context.sport
                }
            
            # Single match found
            return {
                "success": True,
                "disambiguation_needed": False,
                "player": matches,
                "original_name": player_name,
                "sport": sport_context.sport
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "player_name": player_name,
                "sport": sport_context.sport
            }


class PositionNormalizationTool(BaseTool):
    """
    LangChain Tool for normalizing position names across sports.
    
    Supports position-based queries by standardizing position terminology.
    """
    name: str = "normalize_position"
    description: str = """
    Normalize position names to standardized format for a specific sport.
    Use this to convert user-provided position strings to internal identifiers.
    """
    
    # Position mappings for different sports
    POSITION_MAPPINGS: ClassVar[Dict[str, Dict[str, str]]] = {
        'NFL': {
            'quarterback': 'QB', 'qb': 'QB', 'signal caller': 'QB',
            'running back': 'RB', 'rb': 'RB', 'halfback': 'RB', 'fullback': 'FB',
            'wide receiver': 'WR', 'wr': 'WR', 'receiver': 'WR',
            'tight end': 'TE', 'te': 'TE',
            'offensive line': 'OL', 'lineman': 'OL', 'tackle': 'OT', 'guard': 'OG', 'center': 'C',
            'defensive end': 'DE', 'de': 'DE', 'edge rusher': 'DE',
            'defensive tackle': 'DT', 'dt': 'DT', 'nose tackle': 'NT',
            'linebacker': 'LB', 'lb': 'LB', 'middle linebacker': 'MLB', 'outside linebacker': 'OLB',
            'cornerback': 'CB', 'cb': 'CB', 'corner': 'CB',
            'safety': 'S', 'free safety': 'FS', 'strong safety': 'SS',
            'kicker': 'K', 'punter': 'P', 'long snapper': 'LS'
        },
        'NBA': {
            'point guard': 'PG', 'pg': 'PG', 'guard': 'G',
            'shooting guard': 'SG', 'sg': 'SG',
            'small forward': 'SF', 'sf': 'SF', 'forward': 'F',
            'power forward': 'PF', 'pf': 'PF',
            'center': 'C', 'c': 'C', 'big man': 'C'
        }
    }
    
    def _run(
        self,
        position_input: str,
        sport: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Normalize position name"""
        
        sport = sport.upper()
        position_lower = position_input.lower().strip()
        
        mappings = self.POSITION_MAPPINGS.get(sport, {})
        normalized = mappings.get(position_lower, position_input.upper())
        
        return {
            "success": True,
            "original": position_input,
            "normalized": normalized,
            "sport": sport,
            "mapping_found": position_lower in mappings
        }


# Tool registry for easy access
SPORTS_TOOLS = [
    FetchPlayerStatsTool(),
    FetchTeamListingTool(),
    FuzzyPlayerSearchTool(),
    PositionNormalizationTool(),
]


def get_tools_for_sport(sport: str) -> List[BaseTool]:
    """
    Get all available tools for a specific sport.
    
    This function allows for sport-specific tool filtering if needed in the future.
    Currently returns all tools as they are sport-agnostic.
    """
    return SPORTS_TOOLS


def get_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    """Get a specific tool by name"""
    for tool in SPORTS_TOOLS:
        if tool.name == tool_name:
            return tool
    return None 