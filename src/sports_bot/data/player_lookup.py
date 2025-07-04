"""
Player lookup helper for NFL data.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from sports_bot.data.fetcher import NFLDataFetcher
from sports_bot.data.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class PlayerLookup:
    """Helper class for looking up player data through multiple API calls."""
    
    def __init__(self, fetcher: NFLDataFetcher, formatter: ResponseFormatter):
        """Initialize lookup helper.
        
        Args:
            fetcher: NFLDataFetcher instance
            formatter: ResponseFormatter instance
        """
        self.fetcher = fetcher
        self.formatter = formatter
        self._teams_cache = None
        self._players_by_team = {}
        
    async def _ensure_teams_loaded(self) -> List[Dict[str, Any]]:
        """Ensure teams data is loaded in cache."""
        if self._teams_cache is None:
            self._teams_cache = await self.fetcher.get_teams()
        return self._teams_cache
        
    async def _get_team_players(self, team_id: str) -> List[Dict[str, Any]]:
        """Get players for a team, using cache if available."""
        if team_id not in self._players_by_team:
            self._players_by_team[team_id] = await self.fetcher.get_players(team_id=team_id)
        return self._players_by_team[team_id]
        
    async def find_player_by_name(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Find player by name across all teams.
        
        Args:
            player_name: Player's full name
            
        Returns:
            Player data if found, None otherwise
        """
        # First try direct player search
        players = await self.fetcher.get_players()
        player = next(
            (p for p in players if p["fullName"].lower() == player_name.lower()),
            None
        )
        
        if player:
            return player
            
        # If not found, try searching team by team
        teams = await self._ensure_teams_loaded()
        for team_data in teams:
            team_id = team_data["team"]["id"]
            team_players = await self._get_team_players(team_id)
            
            player = next(
                (p for p in team_players if p["fullName"].lower() == player_name.lower()),
                None
            )
            if player:
                return player
                
        return None
        
    async def get_player_with_stats(
        self,
        player_id: str,
        season: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get player details and stats.
        
        Args:
            player_id: Player ID
            season: Optional season for stats
            
        Returns:
            Tuple of (player details, player stats)
        """
        details = await self.fetcher.get_player_details(player_id)
        stats = await self.fetcher.get_player_stats(player_id, season=season)
        return details, stats
        
    async def lookup_player_stats(
        self,
        player_name: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete player lookup flow including stats.
        
        Args:
            player_name: Player's full name
            season: Optional season for stats
            
        Returns:
            Formatted player data with stats
        """
        # Find player
        player = await self.find_player_by_name(player_name)
        if not player:
            return {"error": f"Player {player_name} not found"}
            
        # Get details and stats
        details, stats = await self.get_player_with_stats(player["id"], season)
        
        # Format response
        return self.formatter.format_player(details, stats)
        
    async def compare_players(
        self,
        player1_name: str,
        player2_name: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare two players including stats.
        
        Args:
            player1_name: First player's name
            player2_name: Second player's name
            season: Optional season for stats
            
        Returns:
            Formatted comparison data
        """
        # Find both players
        player1 = await self.find_player_by_name(player1_name)
        player2 = await self.find_player_by_name(player2_name)
        
        if not player1 or not player2:
            return {
                "error": f"One or both players not found: {player1_name}, {player2_name}"
            }
            
        # Get details and stats
        p1_details, p1_stats = await self.get_player_with_stats(player1["id"], season)
        p2_details, p2_stats = await self.get_player_with_stats(player2["id"], season)
        
        # Format and compare
        return self.formatter.format_player_comparison(
            p1_details,
            p2_details,
            p1_stats,
            p2_stats
        ) 