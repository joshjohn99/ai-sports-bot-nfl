"""
NFL Debate Agent Implementation.

This module provides a debate agent for NFL statistics and player comparisons.
It uses the NFL API to fetch real-time data and generate structured debates
about players, teams, and their performance.

Example:
    ```python
    async with DebateAgent(api_key="your_api_key") as agent:
        debate = await agent.generate_debate(DebateContext(
            query="Compare Kyler Murray and Josh Allen",
            player_names=["Kyler Murray", "Josh Allen"],
            metrics=["completions", "passingYards"]
        ))
    ```
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, TypedDict, Literal

from pydantic import BaseModel, Field

from sports_bot.data.fetcher import NFLDataFetcher
from sports_bot.data.response_formatter import ResponseFormatter, Player, Team

logger = logging.getLogger(__name__)

class PlayerMetrics(TypedDict, total=False):
    """Type definition for player metrics comparison."""
    player1: Optional[float]
    player2: Optional[float]
    difference: Optional[float]

class PlayerComparison(TypedDict, total=False):
    """Type definition for player comparison data."""
    sameTeam: bool
    samePosition: bool
    experienceDiff: int
    metrics: Dict[str, PlayerMetrics]

class DebateContext(BaseModel):
    """
    Context for debate generation.
    
    This class defines the parameters for generating a debate about NFL players
    and teams. It supports comparing multiple players, analyzing specific metrics,
    and focusing on particular teams.
    
    Attributes:
        query: The main question or topic for the debate
        player_names: List of player names to compare
        team_names: List of team names to analyze
        metrics: List of specific statistics to compare
        time_period: Time period for historical analysis (e.g., "2023 season")
    """
    query: str = Field(..., description="The main question or topic for the debate")
    player_names: Optional[List[str]] = Field(None, description="List of player names to compare")
    team_names: Optional[List[str]] = Field(None, description="List of team names to analyze")
    metrics: Optional[List[str]] = Field(None, description="List of specific statistics to compare")
    time_period: Optional[str] = Field(None, description="Time period for historical analysis")

class DebateAgent:
    """
    Enhanced debate agent for NFL statistics and comparisons.
    
    This class provides methods for fetching NFL data, comparing players,
    and generating structured debates about player and team performance.
    It handles data fetching, caching, and error recovery automatically.
    
    Attributes:
        fetcher: NFL data fetching client
        formatter: Response formatting utility
    """
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the debate agent.
        
        Args:
            api_key: RapidAPI key for NFL data access. If not provided,
                    will attempt to use RAPIDAPI_KEY environment variable.
        
        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.fetcher = NFLDataFetcher(api_key=api_key)
        self.formatter = ResponseFormatter()
        
    async def __aenter__(self) -> 'DebateAgent':
        """
        Context manager entry.
        
        Returns:
            Self reference for use in async with statements.
        """
        return self
        
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """
        Context manager exit.
        
        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        pass

    async def _find_player_by_name(self, player_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Find a player by name in all team rosters.
        
        This method searches through all NFL team rosters to find a player
        by their full name. It's case-insensitive and returns both the player
        information and their team ID if found.
        
        Args:
            player_name: Player's full name (case-insensitive)
            
        Returns:
            Tuple of (player info, team ID) if found, (None, None) otherwise
            
        Note:
            This is an internal method used by other public methods.
            It performs a comprehensive search which may be slow for
            large numbers of players.
        """
        logger.debug(f"Searching for player: {player_name}")
        async with self.fetcher as fetcher:
            # Get all teams first
            teams = await fetcher.get_teams()
            for team_data in teams:
                team_id = team_data["team"]["id"]
                logger.debug(f"Checking team {team_id}")
                # Get team roster
                roster = await fetcher.get_team_roster(team_id)
                if not roster or "athletes" not in roster:
                    logger.debug(f"No roster found for team {team_id}")
                    continue
                    
                # Search roster for player
                for player in roster["athletes"]:
                    full_name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                    if full_name.lower() == player_name.lower():
                        logger.debug(f"Found player {player_name} in team {team_id}")
                        # Get player ID and detailed info
                        player_id = self.fetcher.extract_player_id(player)
                        if player_id:
                            player_info = await fetcher.get_player_info(player_id)
                            return player_info, team_id
                            
        logger.debug(f"Player {player_name} not found in any team")
        return None, None
        
    async def stats_lookup(self, player_name: str, stat_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Look up statistics for a player.
        
        This method retrieves comprehensive statistics for a player,
        including their team context and specific stats if requested.
        
        Args:
            player_name: Player's full name
            stat_type: Optional specific statistic to look up (e.g., "passingYards")
            
        Returns:
            Dictionary containing:
            - name: Player's name
            - position: Player's position
            - team: Team information if available
            - stats: Player statistics
            - error: Error message if player not found
            
        Example:
            ```python
            stats = await agent.stats_lookup("Kyler Murray", "passingYards")
            if "error" not in stats:
                print(f"Passing yards: {stats['stats'].get('passingYards')}")
            ```
        """
        logger.debug(f"Looking up stats for {player_name}")
        player_info, team_id = await self._find_player_by_name(player_name)
        if not player_info:
            logger.warning(f"Player {player_name} not found")
            return {"error": f"Player {player_name} not found"}
            
        # Format player data
        player = Player.from_api(player_info)
        formatted = player.to_agent_format()
        
        # Add team context
        if team_id:
            async with self.fetcher as fetcher:
                team_info = await fetcher.get_team_info(team_id)
                if team_info:
                    team = Team.from_api(team_info)
                    formatted["team"] = team.to_agent_format()
                    
        return formatted
            
    async def player_compare(
        self,
        player1_name: str,
        player2_name: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare two players across various metrics.
        
        This method provides a detailed comparison of two players,
        including their stats, team context, and specific metrics
        if provided.
        
        Args:
            player1_name: First player's full name
            player2_name: Second player's full name
            metrics: Optional list of specific metrics to compare
                    (e.g., ["completions", "passingYards"])
            
        Returns:
            Dictionary containing:
            - player1: First player's information
            - player2: Second player's information
            - comparison: Comparison metrics including:
                - sameTeam: Whether players are on same team
                - samePosition: Whether players play same position
                - experienceDiff: Difference in years of experience
                - metrics: Specific metric comparisons if requested
            - error: Error message if either player not found
            
        Example:
            ```python
            comparison = await agent.player_compare(
                "Kyler Murray",
                "Josh Allen",
                metrics=["completions", "passingYards"]
            )
            ```
        """
        logger.debug(f"Comparing players: {player1_name} vs {player2_name}")
        # Get player info
        p1_info, p1_team_id = await self._find_player_by_name(player1_name)
        p2_info, p2_team_id = await self._find_player_by_name(player2_name)
        
        if not p1_info or not p2_info:
            logger.warning(f"One or both players not found: {player1_name}, {player2_name}")
            return {"error": f"One or both players not found: {player1_name}, {player2_name}"}
            
        # Format player data
        p1 = Player.from_api(p1_info)
        p2 = Player.from_api(p2_info)
        
        # Add team context
        async with self.fetcher as fetcher:
            if p1_team_id:
                p1_team_info = await fetcher.get_team_info(p1_team_id)
                if p1_team_info:
                    p1_team = Team.from_api(p1_team_info)
                    p1.team = p1_team.display_name
                    
            if p2_team_id:
                p2_team_info = await fetcher.get_team_info(p2_team_id)
                if p2_team_info:
                    p2_team = Team.from_api(p2_team_info)
                    p2.team = p2_team.display_name
                    
        # Build comparison
        comparison: Dict[str, Any] = {
            "player1": p1.to_agent_format(),
            "player2": p2.to_agent_format(),
            "comparison": {
                "sameTeam": p1.team == p2.team,
                "samePosition": p1.position == p2.position,
                "experienceDiff": (p1.experience or 0) - (p2.experience or 0)
            }
        }
        
        # Add specific metrics if provided
        if metrics:
            comparison["metrics"] = {}
            for metric in metrics:
                p1_value = p1.stats.get_stat(metric) if p1.stats else None
                p2_value = p2.stats.get_stat(metric) if p2.stats else None
                comparison["metrics"][metric] = {
                    "player1": p1_value,
                    "player2": p2_value,
                    "difference": (p1_value or 0) - (p2_value or 0) if p1_value is not None and p2_value is not None else None
                }
                
        return comparison
            
    async def context_search(self, query: str) -> Dict[str, Any]:
        """
        Search for relevant context about teams or players.
        
        This method searches through teams and players to find
        matches for the given query. It returns both team and
        player information that matches the search.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            Dictionary containing:
            - teams: List of matching team information
            - players: List of matching player information
            
        Example:
            ```python
            results = await agent.context_search("Cardinals")
            for team in results["teams"]:
                print(f"Found team: {team['fullName']}")
            ```
        """
        logger.debug(f"Searching for context: {query}")
        results = {
            "teams": [],
            "players": []
        }
        
        async with self.fetcher as fetcher:
            # Search teams
            teams = await fetcher.get_teams()
            for team_data in teams:
                team = Team.from_api(team_data)
                if query.lower() in team.display_name.lower():
                    team_info = await fetcher.get_team_info(team.id)
                    if team_info:
                        detailed_team = Team.from_api(team_info)
                        results["teams"].append(detailed_team.to_agent_format())
                        
                    # Add roster preview
                    roster = await fetcher.get_team_roster(team.id)
                    if roster and "athletes" in roster:
                        results["teams"][-1]["roster_preview"] = [
                            {
                                "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                                "position": p.get("position", "Unknown")
                            }
                            for p in roster["athletes"][:5]  # Just first 5 players
                        ]
                        
            # Search players by iterating through team rosters
            for team_data in teams:
                team_id = team_data["team"]["id"]
                roster = await fetcher.get_team_roster(team_id)
                if not roster or "athletes" not in roster:
                    continue
                    
                for player in roster["athletes"]:
                    full_name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                    if query.lower() in full_name.lower():
                        player_id = self.fetcher.extract_player_id(player)
                        if player_id:
                            player_info = await fetcher.get_player_info(player_id)
                            if player_info:
                                formatted = Player.from_api(player_info).to_agent_format()
                                results["players"].append(formatted)
                                
        return results
            
    async def generate_debate(self, context: Union[Dict[str, Any], DebateContext]) -> Dict[str, Any]:
        """
        Generate debate content based on context.
        
        This method generates a comprehensive debate about players
        and teams based on the provided context. It can compare
        multiple players, analyze team performance, and focus on
        specific metrics.
        
        Args:
            context: Debate context with query and relevant entities.
                    Can be either a DebateContext object or a dictionary
                    with the same fields.
            
        Returns:
            Dictionary containing:
            - query: Original debate query
            - players: List of player information
            - teams: List of team information
            - comparisons: List of player comparisons
            - insights: List of generated insights
            
        Example:
            ```python
            debate = await agent.generate_debate(DebateContext(
                query="Compare the Cardinals' quarterbacks",
                player_names=["Kyler Murray", "Jacoby Brissett"],
                team_names=["Arizona Cardinals"],
                metrics=["completions", "passingYards"]
            ))
            ```
        """
        if isinstance(context, dict):
            context = DebateContext(**context)
            
        logger.debug(f"Generating debate for context: {context}")
        debate_data = {
            "query": context.query,
            "players": [],
            "teams": [],
            "comparisons": [],
            "insights": []
        }
        
        # Get player information
        if context.player_names:
            logger.debug(f"Processing {len(context.player_names)} players")
            for player_name in context.player_names:
                player_stats = await self.stats_lookup(player_name)
                if "error" not in player_stats:
                    debate_data["players"].append(player_stats)
                    
            # Generate player comparisons if multiple players
            if len(context.player_names) > 1:
                logger.debug("Generating player comparisons")
                for i in range(len(context.player_names)):
                    for j in range(i + 1, len(context.player_names)):
                        logger.debug(f"Comparing {context.player_names[i]} vs {context.player_names[j]}")
                        comparison = await self.player_compare(
                            context.player_names[i],
                            context.player_names[j],
                            context.metrics
                        )
                        if "error" not in comparison:
                            debate_data["comparisons"].append(comparison)
                            
        # Get team information
        if context.team_names:
            logger.debug(f"Processing {len(context.team_names)} teams")
            async with self.fetcher as fetcher:
                teams = await fetcher.get_teams()
                for team_name in context.team_names:
                    for team_data in teams:
                        team = Team.from_api(team_data)
                        if team_name.lower() in team.display_name.lower():
                            team_info = await fetcher.get_team_info(team.id)
                            if team_info:
                                formatted = Team.from_api(team_info).to_agent_format()
                                debate_data["teams"].append(formatted)
                                
                                # Add roster preview
                                roster = await fetcher.get_team_roster(team.id)
                                if roster and "athletes" in roster:
                                    formatted["roster_preview"] = [
                                        {
                                            "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                                            "position": p.get("position", "Unknown")
                                        }
                                        for p in roster["athletes"][:5]  # Just first 5 players
                                    ]
                                
        logger.debug(f"Generated debate data: {debate_data}")
        return debate_data