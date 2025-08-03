"""
Enhanced API Client with LangChain Tools Integration
"""

import os
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
import logging
from ..utils.logging import get_logger
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain.callbacks.manager import CallbackManagerForToolRun
from .endpoints import ENDPOINTS, API_CONFIG
from ..config.api_config import api_config
from ..cache.shared_cache import sports_cache as shared_cache

logger = get_logger(__name__)

def get_endpoint_url(endpoint_type: str, **kwargs) -> str:
    """
    Construct endpoint URL based on type and parameters.
    This is a placeholder implementation - you should replace with your actual URL construction logic.
    """
    base_url = API_CONFIG.get('base_url', 'https://nfl-api-data.p.rapidapi.com/')
    
    # This is a simplified implementation
    # You should replace this with your actual endpoint construction logic
    endpoint_map = {
        'PlayerStats': f"{base_url}player-stats",
        'PlayerSearch': f"{base_url}player-search", 
        'LeagueLeaders': f"{base_url}league-leaders",
        'PlayerDetails': f"{base_url}player-details",
        'TeamDetails': f"{base_url}team-details"
    }
    
    url = endpoint_map.get(endpoint_type, f"{base_url}{endpoint_type.lower()}")
    
    # Add query parameters if provided
    if kwargs:
        params = "&".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])
        if params:
            url += f"?{params}"
    
    return url

class PlayerStatsInput(BaseModel):
    """Input schema for player stats tool"""
    player_id: str = Field(description="The player ID to fetch stats for")
    season: Optional[str] = Field(description="The season year (e.g., '2024')", default=None)

class PlayerStatsTool(BaseTool):
    """LangChain tool for fetching player statistics"""
    name: str = "get_player_stats"
    description: str = "Fetch comprehensive player statistics for a given player ID and season"
    args_schema: Type[BaseModel] = PlayerStatsInput
    
    def _run(
        self,
        player_id: str,
        season: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Execute the player stats retrieval"""
        try:
            # Use cache if available - using the appropriate method from SharedSportsCache
            sport = "NFL"  # Default sport - you might want to pass this as parameter
            cached_result = shared_cache.get_stats(sport, player_id, season or 'current', [])
            if cached_result:
                return cached_result
            
            # Fetch from API
            endpoint = get_endpoint_url('PlayerStats', player_id=player_id, season=season)
            headers = {'Ocp-Apim-Subscription-Key': api_config.api_key}
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache the result using SharedSportsCache method
            shared_cache.set_stats(sport, player_id, season or 'current', [], result)
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to fetch player stats: {str(e)}"}
    
    async def _arun(
        self,
        player_id: str,
        season: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Async version of the tool"""
        # For now, just call the sync version
        return self._run(player_id, season, run_manager)

class PlayerSearchInput(BaseModel):
    """Input schema for player search tool"""
    player_name: str = Field(description="The player name to search for")
    sport: Optional[str] = Field(description="The sport to search in (NFL, NBA, etc.)", default="NFL")

class PlayerSearchTool(BaseTool):
    """LangChain tool for searching players by name"""
    name: str = "search_players"
    description: str = "Search for players by name across different sports"
    args_schema: Type[BaseModel] = PlayerSearchInput
    
    def _run(
        self,
        player_name: str,
        sport: Optional[str] = "NFL",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the player search"""
        try:
            # Use cache if available - for player search, we'll use player cache
            cached_result = shared_cache.get_player(sport, player_name)
            if cached_result:
                return [cached_result]  # Return as list since this tool returns a list
            
            # Fetch from API - this would need to be implemented based on your search endpoint
            # For now, return a placeholder structure
            endpoint = get_endpoint_url('PlayerSearch', name=player_name, sport=sport)
            headers = {'Ocp-Apim-Subscription-Key': api_config.api_key}
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache the result using SharedSportsCache method
            # Assuming result is a list of players, we cache the first one
            if result and isinstance(result, list) and len(result) > 0:
                shared_cache.set_player(sport, player_name, result[0])
            
            return result
            
        except Exception as e:
            return [{"error": f"Failed to search players: {str(e)}"}]
    
    async def _arun(
        self,
        player_name: str,
        sport: Optional[str] = "NFL",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Any]]:
        """Async version of the tool"""
        return self._run(player_name, sport, run_manager)

class LeagueLeadersInput(BaseModel):
    """Input schema for league leaders tool"""
    stat_category: str = Field(description="The statistical category to get leaders for")
    season: Optional[str] = Field(description="The season year", default=None)
    limit: Optional[int] = Field(description="Number of leaders to return", default=10)

class LeagueLeadersTool(BaseTool):
    """LangChain tool for fetching league leaders"""
    name: str = "get_league_leaders"
    description: str = "Fetch league leaders for a specific statistical category"
    args_schema: Type[BaseModel] = LeagueLeadersInput
    
    def _run(
        self,
        stat_category: str,
        season: Optional[str] = None,
        limit: Optional[int] = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the league leaders retrieval"""
        try:
            # For league leaders, we'll use a simple cache approach since SharedSportsCache doesn't have a specific method
            # In a production system, you might want to extend SharedSportsCache with a leaders cache method
            sport = "NFL"  # Default sport
            # For now, we'll skip caching for leaders since it's not directly supported by SharedSportsCache
            
            # This would fetch from your actual leaderboard endpoint
            # Implementation depends on your API structure
            endpoint = get_endpoint_url('LeagueLeaders', stat=stat_category, season=season, limit=limit)
            headers = {'Ocp-Apim-Subscription-Key': api_config.api_key}
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Note: Caching skipped for league leaders as SharedSportsCache doesn't have a specific method
            # In production, you might want to extend SharedSportsCache to support leader caching
            
            return result
            
        except Exception as e:
            return [{"error": f"Failed to fetch league leaders: {str(e)}"}]
    
    async def _arun(
        self,
        stat_category: str,
        season: Optional[str] = None,
        limit: Optional[int] = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> List[Dict[str, Any]]:
        """Async version of the tool"""
        return self._run(stat_category, season, limit, run_manager)

# Create tool instances
player_stats_tool = PlayerStatsTool()
player_search_tool = PlayerSearchTool()
league_leaders_tool = LeagueLeadersTool()

# Tool registry for easy access
SPORTS_TOOLS = [
    player_stats_tool,
    player_search_tool,
    league_leaders_tool
]

class LangChainSportsAPIClient:
    """Enhanced API client with LangChain tools integration"""
    
    def __init__(self):
        self.tools = SPORTS_TOOLS
        self.tool_map = {tool.name: tool for tool in self.tools}
    
    def get_available_tools(self) -> List[BaseTool]:
        """Get list of available LangChain tools"""
        return self.tools
    
    def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name"""
        return self.tool_map.get(tool_name)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with given parameters"""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        return await tool._arun(**kwargs)
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return {tool.name: tool.description for tool in self.tools}

# Create enhanced client instance
enhanced_api_client = LangChainSportsAPIClient()

class NFLApiClient:
    """Client for interacting with the NFL API."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'nfl-api-data.p.rapidapi.com'
        }
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request with retries and error handling."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def get_player_stats(self, player_id: str, season: str) -> Dict[str, Any]:
        """Get player statistics for a specific season."""
        return self.make_request(
            'nfl-ath-statistics',
            {'id': player_id, 'year': season}
        )
    
    def get_team_roster(self, team_id: str) -> Dict[str, Any]:
        """Get team roster information."""
        return self.make_request(
            'nfl-player-listing/v1/data',
            {'id': team_id}
        )
    
    def get_all_teams(self) -> Dict[str, Any]:
        """Get information for all teams."""
        return self.make_request('nfl-team-listing/v1/data')
    
    def get_player_details(self, player_id: str) -> Dict[str, Any]:
        """Get detailed player information."""
        return self.make_request(
            'nfl-player-info/v1/data',
            {'id': player_id}
        )
    
    def get_team_details(self, team_id: str) -> Dict[str, Any]:
        """Get detailed team information."""
        return self.make_request(
            'nfl-team-info/v1/data',
            {'id': team_id}
        ) 