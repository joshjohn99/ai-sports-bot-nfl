"""
Response formatter for NFL data.

This module provides data structures and formatting utilities for NFL API responses.
It handles the conversion of raw API data into strongly-typed Python objects and
provides consistent formatting for use by the debate agent.

Example:
    ```python
    # Format player data
    player = Player.from_api(api_response)
    formatted = player.to_agent_format()
    
    # Format team data
    team = Team.from_api(api_response)
    formatted = team.to_agent_format()
    ```
"""

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime

class LogoSize(TypedDict):
    """Type definition for logo dimensions."""
    width: int
    height: int

class LogoData(TypedDict):
    """Type definition for formatted logo data."""
    url: str
    type: str
    size: LogoSize

class LinkData(TypedDict):
    """Type definition for formatted link data."""
    type: str
    text: str
    isExternal: bool

@dataclass
class Logo:
    """
    Team logo information.
    
    This class represents a team's logo with its metadata including
    dimensions and usage context.
    
    Attributes:
        href: URL to the logo image
        alt: Alternative text description
        rel: List of relationships/contexts where this logo is used
        width: Logo width in pixels
        height: Logo height in pixels
    """
    href: str
    alt: str
    rel: List[str]
    width: int
    height: int

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Logo':
        """
        Create a Logo instance from API response data.
        
        Args:
            data: Raw API response containing logo information
            
        Returns:
            Logo instance with parsed data
        """
        return cls(
            href=data.get("href", ""),
            alt=data.get("alt", ""),
            rel=data.get("rel", []),
            width=data.get("width", 0),
            height=data.get("height", 0)
        )

@dataclass
class TeamLink:
    """
    Team link information.
    
    This class represents a link associated with a team, such as
    their official website, social media, or related content.
    
    Attributes:
        language: Link content language
        rel: List of relationships/contexts for this link
        href: URL of the link
        text: Display text
        short_text: Abbreviated display text
        is_external: Whether link points to external site
        is_premium: Whether content requires premium access
        is_hidden: Whether link should be hidden in UI
    """
    language: str
    rel: List[str]
    href: str
    text: str
    short_text: str
    is_external: bool
    is_premium: bool
    is_hidden: bool

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamLink':
        """
        Create a TeamLink instance from API response data.
        
        Args:
            data: Raw API response containing link information
            
        Returns:
            TeamLink instance with parsed data
        """
        return cls(
            language=data.get("language", ""),
            rel=data.get("rel", []),
            href=data.get("href", ""),
            text=data.get("text", ""),
            short_text=data.get("shortText", ""),
            is_external=data.get("isExternal", False),
            is_premium=data.get("isPremium", False),
            is_hidden=data.get("isHidden", False)
        )

@dataclass
class PlayerStats:
    """
    Player statistics structure.
    
    This class organizes player statistics into categories
    and provides methods for accessing specific stats.
    
    Attributes:
        passing: Passing statistics (yards, completions, etc.)
        rushing: Rushing statistics (yards, attempts, etc.)
        receiving: Receiving statistics (receptions, yards, etc.)
        defense: Defensive statistics (tackles, sacks, etc.)
        scoring: Scoring statistics (touchdowns, field goals, etc.)
    """
    passing: Dict[str, Any]
    rushing: Dict[str, Any]
    receiving: Dict[str, Any]
    defense: Dict[str, Any]
    scoring: Dict[str, Any]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'PlayerStats':
        """
        Create a PlayerStats instance from API response data.
        
        Args:
            data: Raw API response containing player statistics
            
        Returns:
            PlayerStats instance with parsed data
        """
        return cls(
            passing=data.get("passing", {}),
            rushing=data.get("rushing", {}),
            receiving=data.get("receiving", {}),
            defense=data.get("defense", {}),
            scoring=data.get("scoring", {})
        )

    def get_stat(self, stat_name: str) -> Any:
        """
        Get specific statistic across all categories.
        
        This method searches for the requested statistic in all
        categories and returns its value if found.
        
        Args:
            stat_name: Name of the statistic to retrieve
            
        Returns:
            Value of the statistic if found, None otherwise
            
        Example:
            ```python
            stats = PlayerStats.from_api(data)
            passing_yards = stats.get_stat("passingYards")
            ```
        """
        for category in [self.passing, self.rushing, self.receiving, self.defense, self.scoring]:
            if stat_name in category:
                return category[stat_name]
        return None

@dataclass
class Player:
    """
    Player information structure.
    
    This class represents a player with their personal information,
    team affiliation, and statistics.
    
    Attributes:
        id: Unique player identifier
        full_name: Player's full name
        position: Player's position
        number: Jersey number
        team: Team name
        height: Height in inches
        weight: Weight in pounds
        college: College attended
        experience: Years of NFL experience
        status: Current player status
        stats: Player statistics
    """
    id: str
    full_name: str
    position: str
    number: Optional[str]
    team: Optional[str]
    height: Optional[int]
    weight: Optional[int]
    college: Optional[str]
    experience: Optional[int]
    status: str
    stats: Optional[PlayerStats] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any], stats: Optional[Dict[str, Any]] = None) -> 'Player':
        """
        Create a Player instance from API response data.
        
        Args:
            data: Raw API response containing player information
            stats: Optional statistics data
            
        Returns:
            Player instance with parsed data
        """
        return cls(
            id=data.get("id", ""),
            full_name=data.get("fullName", ""),
            position=data.get("position", {}).get("name", ""),
            number=data.get("jersey"),
            team=data.get("team", {}).get("name"),
            height=data.get("height"),
            weight=data.get("weight"),
            college=data.get("college", {}).get("name"),
            experience=data.get("experience", {}).get("years"),
            status=data.get("status", {}).get("name", "Unknown"),
            stats=PlayerStats.from_api(stats) if stats else None
        )

    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert player data to format for agent consumption.
        
        Returns:
            Dictionary containing formatted player data with
            standardized structure for use by the debate agent.
            
        Example:
            ```python
            player = Player.from_api(data)
            formatted = player.to_agent_format()
            print(formatted["physical"]["height"])
            ```
        """
        return {
            "id": self.id,
            "name": self.full_name,
            "position": self.position,
            "number": self.number,
            "team": self.team,
            "physical": {
                "height": self.height,
                "weight": self.weight
            },
            "background": {
                "college": self.college,
                "experience": self.experience,
                "status": self.status
            },
            "stats": self.stats.__dict__ if self.stats else {}
        }

@dataclass
class Team:
    """
    Team information structure.
    
    This class represents an NFL team with their branding,
    location, and status information.
    
    Attributes:
        id: Unique team identifier
        uid: Alternative unique identifier
        slug: URL-friendly team name
        abbreviation: Team abbreviation (e.g., "ARI")
        display_name: Full display name
        short_display_name: Abbreviated display name
        name: Team name
        nickname: Team nickname
        location: Team location/city
        color: Primary team color
        alternate_color: Secondary team color
        is_active: Whether team is active
        is_all_star: Whether team is an all-star team
        logos: List of team logos
        links: List of team-related links
    """
    id: str
    uid: str
    slug: str
    abbreviation: str
    display_name: str
    short_display_name: str
    name: str
    nickname: str
    location: str
    color: str
    alternate_color: str
    is_active: bool
    is_all_star: bool
    logos: List[Logo]
    links: List[TeamLink]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Team':
        """
        Create a Team instance from API response data.
        
        Args:
            data: Raw API response containing team information
            
        Returns:
            Team instance with parsed data
            
        Note:
            Handles both direct team data and nested team data
            structures from different API endpoints.
        """
        team_data = data.get("team", data)  # Handle both direct team data and nested team data
        return cls(
            id=team_data.get("id", ""),
            uid=team_data.get("uid", ""),
            slug=team_data.get("slug", ""),
            abbreviation=team_data.get("abbreviation", ""),
            display_name=team_data.get("displayName", ""),
            short_display_name=team_data.get("shortDisplayName", ""),
            name=team_data.get("name", ""),
            nickname=team_data.get("nickname", ""),
            location=team_data.get("location", ""),
            color=team_data.get("color", ""),
            alternate_color=team_data.get("alternateColor", ""),
            is_active=team_data.get("isActive", True),
            is_all_star=team_data.get("isAllStar", False),
            logos=[Logo.from_api(logo) for logo in team_data.get("logos", [])],
            links=[TeamLink.from_api(link) for link in team_data.get("links", [])]
        )

    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert team data to format for agent consumption.
        
        Returns:
            Dictionary containing formatted team data with
            standardized structure for use by the debate agent.
            
        Example:
            ```python
            team = Team.from_api(data)
            formatted = team.to_agent_format()
            print(formatted["branding"]["color"])
            ```
        """
        return {
            "id": self.id,
            "uid": self.uid,
            "name": self.name,
            "nickname": self.nickname,
            "abbreviation": self.abbreviation,
            "location": self.location,
            "fullName": self.display_name,
            "shortName": self.short_display_name,
            "branding": {
                "color": self.color,
                "alternateColor": self.alternate_color,
                "logos": [
                    {
                        "url": logo.href,
                        "type": logo.rel[0] if logo.rel else "default",
                        "size": {"width": logo.width, "height": logo.height}
                    }
                    for logo in self.logos
                ]
            },
            "links": [
                {
                    "type": link.rel[0] if link.rel else "unknown",
                    "text": link.text,
                    "isExternal": link.is_external
                }
                for link in self.links
            ],
            "status": {
                "isActive": self.is_active,
                "isAllStar": self.is_all_star
            }
        }

class ResponseFormatter:
    """
    Utility class for formatting API responses.
    
    This class provides static methods for formatting player
    and team data from raw API responses into standardized
    structures for use by the debate agent.
    """
    
    @staticmethod
    def format_player(player_data: Dict[str, Any], stats_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format player data from API response.
        
        Args:
            player_data: Raw player information from API
            stats_data: Optional player statistics from API
            
        Returns:
            Formatted player data in standardized structure
        """
        player = Player.from_api(player_data, stats_data)
        return player.to_agent_format()

    @staticmethod
    def format_team(team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format team data from API response.
        
        Args:
            team_data: Raw team information from API
            
        Returns:
            Formatted team data in standardized structure
        """
        team = Team.from_api(team_data)
        return team.to_agent_format()

    @staticmethod
    def format_player_comparison(
        player1: Dict[str, Any],
        player2: Dict[str, Any],
        stats1: Optional[Dict[str, Any]] = None,
        stats2: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format player comparison from API responses.
        
        Args:
            player1: Raw data for first player
            player2: Raw data for second player
            stats1: Optional statistics for first player
            stats2: Optional statistics for second player
            
        Returns:
            Formatted comparison data including both players'
            information and relevant statistical comparisons
        """
        p1 = Player.from_api(player1, stats1)
        p2 = Player.from_api(player2, stats2)
        
        return {
            "player1": p1.to_agent_format(),
            "player2": p2.to_agent_format(),
            "comparison": {
                "sameTeam": p1.team == p2.team,
                "samePosition": p1.position == p2.position,
                "experienceDiff": (p1.experience or 0) - (p2.experience or 0)
            }
        } 