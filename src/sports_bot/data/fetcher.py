"""
NFL Data Fetcher using RapidAPI.

This module provides a client for fetching NFL data from the RapidAPI NFL API.
It handles authentication, rate limiting, caching, and error recovery.

Example:
    ```python
    async with NFLDataFetcher(api_key="your_api_key") as fetcher:
        # Get all teams
        teams = await fetcher.get_teams()
        
        # Get specific team info
        team_info = await fetcher.get_team_info("22")  # Cardinals
        
        # Get team roster
        roster = await fetcher.get_team_roster("22")
    ```

Note:
    This client implements several features for production use:
    - Automatic rate limiting
    - Request caching
    - Error recovery with exponential backoff
    - Connection pooling via aiohttp
"""

import os
import aiohttp
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, TypedDict, NoReturn
from functools import lru_cache

logger = logging.getLogger(__name__)

class TeamData(TypedDict):
    """Type definition for team response data."""
    id: str
    name: str
    abbreviation: str
    displayName: str
    location: str

class PlayerData(TypedDict):
    """Type definition for player response data."""
    id: str
    firstName: str
    lastName: str
    position: Dict[str, str]
    jersey: Optional[str]
    status: Dict[str, str]

class NFLDataFetcher:
    """
    Fetches NFL data from RapidAPI with caching and rate limiting.
    
    This class provides methods for accessing various NFL data endpoints
    while handling authentication, rate limiting, and error recovery.
    It should be used as an async context manager to ensure proper
    resource management.
    
    Attributes:
        api_key: RapidAPI key for authentication
        base_url: Base URL for the NFL API
        headers: Request headers including API key
        session: aiohttp ClientSession for connection pooling
        last_request_time: Timestamp of last API request
        min_request_interval: Minimum time between requests
        _cache: In-memory cache for responses
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries
    """
    
    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize fetcher with API key and configuration.
        
        Args:
            api_key: RapidAPI key. If not provided, will attempt to use
                    RAPIDAPI_KEY environment variable.
            max_retries: Maximum number of retries for failed requests.
                        Each retry uses exponential backoff.
            retry_delay: Base delay between retries in seconds.
                        Actual delay will be retry_delay * (2 ** retry_number)
        
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RapidAPI key is required")
            
        self.base_url = "https://nfl-api-data.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "nfl-api-data.p.rapidapi.com"
        }
        self.session = None
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds
        self._cache = {}  # Simple in-memory cache
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    async def __aenter__(self) -> 'NFLDataFetcher':
        """
        Create aiohttp session for connection pooling.
        
        Returns:
            Self reference for use in async with statements
        """
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """
        Close aiohttp session and clean up resources.
        
        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.session:
            await self.session.close()

    async def _wait_for_rate_limit(self) -> None:
        """
        Wait to respect rate limiting.
        
        This method ensures we don't exceed the API's rate limit by
        waiting an appropriate amount of time between requests.
        """
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make API request with error handling and rate limiting.
        
        This method handles all the complexities of making an API request:
        - Rate limiting via _wait_for_rate_limit
        - Error recovery with exponential backoff
        - HTTP error handling
        - Session management
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            JSON response data if successful, empty dict otherwise
            
        Raises:
            RuntimeError: If called outside async context manager
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with context manager.")
            
        retries = 0
        while retries <= self.max_retries:
            try:
                await self._wait_for_rate_limit()
                
                async with self.session.get(
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 404:
                        logger.warning(f"Endpoint {endpoint} not found")
                        return {}
                    elif response.status == 429:
                        if retries < self.max_retries:
                            wait_time = self.retry_delay * (2 ** retries)  # Exponential backoff
                            logger.warning(f"Rate limit exceeded, waiting {wait_time}s before retry {retries + 1}/{self.max_retries}")
                            await asyncio.sleep(wait_time)
                            retries += 1
                            continue
                        else:
                            logger.error("Rate limit exceeded and max retries reached")
                            return {}
                    elif response.status >= 500:
                        if retries < self.max_retries:
                            wait_time = self.retry_delay * (2 ** retries)
                            logger.warning(f"Server error {response.status}, waiting {wait_time}s before retry {retries + 1}/{self.max_retries}")
                            await asyncio.sleep(wait_time)
                            retries += 1
                            continue
                        else:
                            logger.error(f"Server error {response.status} and max retries reached")
                            return {}
                            
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                if retries < self.max_retries:
                    wait_time = self.retry_delay * (2 ** retries)
                    logger.warning(f"Request failed: {e}, waiting {wait_time}s before retry {retries + 1}/{self.max_retries}")
                    await asyncio.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {e}")
                    return {}
                    
        return {}  # All retries failed

    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> str:
        """
        Generate cache key for request.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            Cache key string combining endpoint and sorted params
        """
        key = endpoint
        if params:
            # Sort params to ensure consistent cache keys
            sorted_params = sorted(params.items())
            key += "?" + "&".join(f"{k}={v}" for k, v in sorted_params)
        return key

    async def _cached_request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make cached API request.
        
        This method wraps _make_request with a simple in-memory cache
        to avoid unnecessary API calls for duplicate requests.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            Cached response if available, otherwise fresh API response
        """
        cache_key = self._get_cache_key(endpoint, params)
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # Make request and cache result
        result = await self._make_request(endpoint, params)
        if result:  # Only cache successful responses
            self._cache[cache_key] = result
        return result
            
    async def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get list of all NFL teams.
        
        Returns:
            List of team objects, each containing:
            - team.id: Team ID (str)
            - team.name: Team name (str)
            - team.abbreviation: Team abbreviation (str)
            - team.displayName: Full team name (str)
            - team.location: Team city/location (str)
            
        Example:
            ```python
            teams = await fetcher.get_teams()
            for team in teams:
                print(f"{team['team']['name']} ({team['team']['abbreviation']})")
            ```
        """
        data = await self._cached_request("nfl-team-listing/v1/data")
        if not isinstance(data, list):
            logger.error("Unexpected response format from team listing endpoint")
            return []
        return data

    async def get_team_info(self, team_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific team.
        
        Args:
            team_id: Team ID from get_teams() response
            
        Returns:
            Team details including:
            - name: Team name
            - location: City/location
            - abbreviation: Team abbreviation
            - colors: Team colors
            - logos: Team logo URLs
            - links: Related links (website, social media)
            
        Example:
            ```python
            team_info = await fetcher.get_team_info("22")  # Cardinals
            print(f"Home: {team_info['location']}")
            print(f"Colors: {team_info['color']}")
            ```
        """
        return await self._cached_request("nfl-team-info/v1/data", {"id": team_id})

    async def get_team_roster(self, team_id: str) -> Dict[str, Any]:
        """
        Get complete roster for a specific team.
        
        Args:
            team_id: Team ID from get_teams() response
            
        Returns:
            Dictionary containing:
            - athletes: List of player objects with:
                - id: Player ID
                - firstName/lastName: Player name
                - position: Player position
                - jersey: Jersey number
                - status: Player status
            - coach: List of coach objects
            - team: Team information
            
        Example:
            ```python
            roster = await fetcher.get_team_roster("22")
            for player in roster["athletes"]:
                print(f"{player['firstName']} {player['lastName']}")
            ```
        """
        return await self._cached_request("nfl-team-roster", {"id": team_id})

    def extract_player_id(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract player ID from player data object.
        
        The NFL API uses different ID systems. This method extracts
        the correct ID (SDR) for use with player-specific endpoints.
        
        Args:
            player_data: Player object from roster response
            
        Returns:
            SDR player ID if found, None otherwise
            
        Example:
            ```python
            roster = await fetcher.get_team_roster("22")
            for player in roster["athletes"]:
                player_id = fetcher.extract_player_id(player)
                if player_id:
                    player_info = await fetcher.get_player_info(player_id)
            ```
        """
        alternate_ids = player_data.get("alternateIds", {})
        return alternate_ids.get("sdr")

    async def get_player_info(self, player_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific player.
        
        Args:
            player_id: Player ID from extract_player_id()
            
        Returns:
            Player details including:
            - name: Full name
            - position: Player position
            - number: Jersey number
            - height/weight: Physical attributes
            - experience: Years in NFL
            - college: College attended
            - status: Current status
            
        Example:
            ```python
            player_info = await fetcher.get_player_info("12345")
            print(f"Position: {player_info['position']['name']}")
            print(f"Experience: {player_info['experience']['years']} years")
            ```
        """
        return await self._cached_request("nfl-player-info/v1/data", {"id": player_id})

    async def get_team_stats(self, team_id: str) -> Dict[str, Any]:
        """
        Get team statistics.
        
        Args:
            team_id: Team ID from get_teams() response
            
        Returns:
            Team statistics including:
            - offense: Offensive statistics
            - defense: Defensive statistics
            - special_teams: Special teams statistics
            - record: Win/loss record
            
        Example:
            ```python
            stats = await fetcher.get_team_stats("22")
            print(f"Total yards: {stats['offense']['totalYards']}")
            print(f"Points allowed: {stats['defense']['pointsAllowed']}")
            ```
        """
        return await self._cached_request("nfl-team-stats/v1/data", {"id": team_id})

    async def get_player_details(self, team_id: str, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed player information by name and team.
        
        This is a convenience method that:
        1. Gets team roster
        2. Finds player by name
        3. Gets detailed player information
        
        Args:
            team_id: Team ID from get_teams() response
            player_name: Player's full name (case-insensitive)
            
        Returns:
            Player details if found, None otherwise
            
        Example:
            ```python
            player = await fetcher.get_player_details("22", "Kyler Murray")
            if player:
                print(f"Position: {player['position']['name']}")
            ```
        """
        roster = await self.get_team_roster(team_id)
        if not roster or "athletes" not in roster:
            return None
            
        # Search roster for player
        for player in roster["athletes"]:
            full_name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
            if full_name.lower() == player_name.lower():
                player_id = self.extract_player_id(player)
                if player_id:
                    return await self.get_player_info(player_id)
                    
        return None 