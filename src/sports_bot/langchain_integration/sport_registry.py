"""
Sport Registry System for Scalable Multi-Sport Support

This module implements a registry pattern that allows easy addition of new sports
while maintaining consistent interfaces and behavior across the system.
"""

from typing import Dict, Any, List, Optional, Type, Protocol
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import importlib
from pathlib import Path


@dataclass
class SportConfiguration:
    """
    Configuration for a specific sport
    
    This encapsulates all sport-specific settings, API endpoints, 
    position mappings, and statistical categories.
    """
    sport_code: str  # e.g., "NFL", "NBA", "MLB"
    display_name: str  # e.g., "National Football League"
    api_config: Dict[str, Any]  # API endpoints and configuration
    positions: Dict[str, str]  # Position name mappings
    stat_categories: Dict[str, List[str]]  # Statistical categories
    season_format: str  # e.g., "YYYY" or "YYYY-YY"
    active_months: List[int]  # Months when sport is active
    team_count: int  # Number of teams in league
    roster_size: int  # Average roster size
    
    # Sport-specific query patterns
    common_queries: List[str] = field(default_factory=list)
    position_groups: Dict[str, List[str]] = field(default_factory=dict)
    
    # Validation rules
    min_season_year: int = 1900
    max_season_year: int = 2030


class SportAdapter(Protocol):
    """
    Protocol defining the interface for sport-specific adapters.
    
    Each sport can implement custom logic while maintaining a consistent interface.
    """
    
    def normalize_player_name(self, name: str) -> str:
        """Normalize player name for consistent lookup"""
        ...
    
    def parse_season(self, season_input: str) -> str:
        """Parse season input to standard format"""
        ...
    
    def get_primary_stats(self, position: str) -> List[str]:
        """Get primary statistics for a position"""
        ...
    
    def format_stat_display(self, stat_name: str, value: Any) -> str:
        """Format statistic for display"""
        ...


class BaseSportAdapter(ABC):
    """
    Base implementation of SportAdapter with common functionality
    """
    
    def __init__(self, config: SportConfiguration):
        self.config = config
    
    def normalize_player_name(self, name: str) -> str:
        """Default player name normalization"""
        return name.strip().title()
    
    def parse_season(self, season_input: str) -> str:
        """Default season parsing"""
        # Handle different season formats
        if self.config.season_format == "YYYY":
            return str(int(season_input))
        elif self.config.season_format == "YYYY-YY":
            year = int(season_input)
            return f"{year}-{str(year + 1)[-2:]}"
        return season_input
    
    @abstractmethod
    def get_primary_stats(self, position: str) -> List[str]:
        """Must be implemented by each sport"""
        pass
    
    def format_stat_display(self, stat_name: str, value: Any) -> str:
        """Default stat formatting"""
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value)


class NFLAdapter(BaseSportAdapter):
    """NFL-specific adapter implementation"""
    
    def get_primary_stats(self, position: str) -> List[str]:
        """Get primary stats for NFL positions"""
        position_stats = {
            "QB": ["passing_yards", "passing_touchdowns", "interceptions", "completion_percentage"],
            "RB": ["rushing_yards", "rushing_touchdowns", "receptions", "receiving_yards"],
            "WR": ["receptions", "receiving_yards", "receiving_touchdowns", "targets"],
            "TE": ["receptions", "receiving_yards", "receiving_touchdowns", "blocks"],
            "K": ["field_goals_made", "field_goal_percentage", "extra_points"],
            "DEF": ["sacks", "interceptions", "forced_fumbles", "tackles"]
        }
        return position_stats.get(position.upper(), ["games_played", "starts"])
    
    def format_stat_display(self, stat_name: str, value: Any) -> str:
        """NFL-specific stat formatting"""
        if "percentage" in stat_name.lower():
            return f"{float(value):.1f}%"
        elif "yards" in stat_name.lower():
            return f"{int(value):,} yards"
        return super().format_stat_display(stat_name, value)


class NBAAdapter(BaseSportAdapter):
    """NBA-specific adapter implementation"""
    
    def get_primary_stats(self, position: str) -> List[str]:
        """Get primary stats for NBA positions"""
        position_stats = {
            "PG": ["points", "assists", "rebounds", "steals", "field_goal_percentage"],
            "SG": ["points", "three_pointers_made", "field_goal_percentage", "free_throw_percentage"],
            "SF": ["points", "rebounds", "assists", "three_pointers_made"],
            "PF": ["points", "rebounds", "blocks", "field_goal_percentage"],
            "C": ["points", "rebounds", "blocks", "field_goal_percentage"]
        }
        return position_stats.get(position.upper(), ["points", "rebounds", "assists"])
    
    def format_stat_display(self, stat_name: str, value: Any) -> str:
        """NBA-specific stat formatting"""
        if "percentage" in stat_name.lower():
            return f"{float(value):.1f}%"
        elif stat_name == "points":
            return f"{float(value):.1f} PPG"
        return super().format_stat_display(stat_name, value)


class SportRegistry:
    """
    Central registry for managing multiple sports
    
    This provides a single point of access for sport configurations and adapters,
    making it easy to add new sports and maintain consistency.
    """
    
    def __init__(self):
        self._sports: Dict[str, SportConfiguration] = {}
        self._adapters: Dict[str, SportAdapter] = {}
        self._initialize_default_sports()
    
    def _initialize_default_sports(self):
        """Initialize default sports configurations"""
        
        # NFL Configuration
        nfl_config = SportConfiguration(
            sport_code="NFL",
            display_name="National Football League",
            api_config={
                "base_url": "https://nfl-api-data.p.rapidapi.com",
                "endpoints": {
                    "AllTeams": "/nfl-team-listing/v1/data",
                    "PlayerStats": "/nfl-player-stats/v1/data",
                    "TeamRoster": "/nfl-team-roster/v1/data"
                },
                "headers": {
                    "X-RapidAPI-Host": "nfl-api-data.p.rapidapi.com"
                }
            },
            positions={
                "quarterback": "QB", "qb": "QB",
                "running back": "RB", "rb": "RB",
                "wide receiver": "WR", "wr": "WR",
                "tight end": "TE", "te": "TE",
                "kicker": "K", "k": "K"
            },
            stat_categories={
                "passing": ["passing_yards", "passing_touchdowns", "interceptions"],
                "rushing": ["rushing_yards", "rushing_touchdowns", "rushing_attempts"],
                "receiving": ["receptions", "receiving_yards", "receiving_touchdowns"],
                "defense": ["sacks", "interceptions", "tackles", "forced_fumbles"]
            },
            season_format="YYYY",
            active_months=[9, 10, 11, 12, 1, 2],  # Sep-Feb
            team_count=32,
            roster_size=53,
            common_queries=[
                "Who leads the league in passing yards?",
                "Compare {player1} vs {player2}",
                "Show me the top rushers this season"
            ],
            position_groups={
                "offense": ["QB", "RB", "WR", "TE"],
                "defense": ["DE", "DT", "LB", "CB", "S"],
                "special_teams": ["K", "P"]
            }
        )
        
        # NBA Configuration
        nba_config = SportConfiguration(
            sport_code="NBA",
            display_name="National Basketball Association",
            api_config={
                "base_url": "https://nba-api-data.p.rapidapi.com",
                "endpoints": {
                    "AllTeams": "/teams",
                    "PlayerStats": "/player-stats",
                    "TeamRoster": "/team-roster"
                },
                "headers": {
                    "X-RapidAPI-Host": "nba-api-data.p.rapidapi.com"
                }
            },
            positions={
                "point guard": "PG", "pg": "PG",
                "shooting guard": "SG", "sg": "SG",
                "small forward": "SF", "sf": "SF",
                "power forward": "PF", "pf": "PF",
                "center": "C", "c": "C"
            },
            stat_categories={
                "scoring": ["points", "field_goals_made", "three_pointers_made"],
                "playmaking": ["assists", "turnovers"],
                "rebounding": ["rebounds", "offensive_rebounds", "defensive_rebounds"],
                "defense": ["steals", "blocks"]
            },
            season_format="YYYY-YY",
            active_months=[10, 11, 12, 1, 2, 3, 4, 5, 6],  # Oct-Jun
            team_count=30,
            roster_size=15,
            common_queries=[
                "Who is the leading scorer?",
                "Compare {player1} and {player2} shooting",
                "Show me assist leaders"
            ],
            position_groups={
                "guards": ["PG", "SG"],
                "forwards": ["SF", "PF"],
                "centers": ["C"]
            }
        )
        
        # Register the sports
        self.register_sport(nfl_config, NFLAdapter(nfl_config))
        self.register_sport(nba_config, NBAAdapter(nba_config))
    
    def register_sport(self, config: SportConfiguration, adapter: SportAdapter):
        """Register a new sport with its configuration and adapter"""
        self._sports[config.sport_code] = config
        self._adapters[config.sport_code] = adapter
    
    def get_sport_config(self, sport_code: str) -> Optional[SportConfiguration]:
        """Get configuration for a specific sport"""
        return self._sports.get(sport_code.upper())
    
    def get_sport_adapter(self, sport_code: str) -> Optional[SportAdapter]:
        """Get adapter for a specific sport"""
        return self._adapters.get(sport_code.upper())
    
    def get_all_sports(self) -> Dict[str, SportConfiguration]:
        """Get all registered sports"""
        return self._sports.copy()
    
    def is_sport_supported(self, sport_code: str) -> bool:
        """Check if a sport is supported"""
        return sport_code.upper() in self._sports
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sport codes"""
        return list(self._sports.keys())
    
    def get_sport_display_names(self) -> Dict[str, str]:
        """Get mapping of sport codes to display names"""
        return {code: config.display_name for code, config in self._sports.items()}
    
    def validate_sport_query(self, sport_code: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a query against sport-specific rules
        
        Returns validation result with any errors or warnings
        """
        if not self.is_sport_supported(sport_code):
            return {
                "valid": False,
                "errors": [f"Sport '{sport_code}' is not supported"],
                "supported_sports": self.get_supported_sports()
            }
        
        config = self.get_sport_config(sport_code)
        adapter = self.get_sport_adapter(sport_code)
        errors = []
        warnings = []
        
        # Validate season if provided
        if "season" in query_data:
            try:
                season = query_data["season"]
                if isinstance(season, str) and season.isdigit():
                    year = int(season)
                    if year < config.min_season_year or year > config.max_season_year:
                        errors.append(f"Season {year} is outside valid range ({config.min_season_year}-{config.max_season_year})")
            except (ValueError, TypeError):
                errors.append("Invalid season format")
        
        # Validate positions if provided
        if "positions" in query_data:
            positions = query_data["positions"]
            if isinstance(positions, list):
                for pos in positions:
                    if pos.lower() not in config.positions:
                        warnings.append(f"Position '{pos}' may not be recognized for {sport_code}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sport_config": config,
            "sport_adapter": adapter
        }
    
    def get_sport_context_help(self, sport_code: str) -> Dict[str, Any]:
        """
        Get contextual help information for a sport
        
        This helps users understand what queries are possible for each sport
        """
        if not self.is_sport_supported(sport_code):
            return {"error": f"Sport '{sport_code}' not supported"}
        
        config = self.get_sport_config(sport_code)
        
        return {
            "sport": config.display_name,
            "positions": list(config.positions.values()),
            "position_groups": config.position_groups,
            "stat_categories": config.stat_categories,
            "common_queries": config.common_queries,
            "season_format": config.season_format,
            "active_season": f"Months {config.active_months}",
            "example_queries": [
                f"Who leads {config.sport_code} in passing yards?",
                f"Compare two {config.sport_code} players",
                f"Show me top {config.sport_code} performers"
            ]
        }
    
    def add_sport_from_config_file(self, config_path: str) -> bool:
        """
        Add a sport from a configuration file
        
        This allows dynamic addition of sports without code changes
        """
        try:
            # This would load from JSON/YAML config file
            # Implementation depends on chosen config format
            pass
        except Exception as e:
            print(f"Failed to load sport config from {config_path}: {e}")
            return False
        
        return True


# Global sport registry instance
sport_registry = SportRegistry()


def get_sport_registry() -> SportRegistry:
    """Get the global sport registry instance"""
    return sport_registry


def register_new_sport(sport_code: str, config_dict: Dict[str, Any], adapter_class: Type[SportAdapter] = None):
    """
    Convenience function to register a new sport
    
    Example usage:
    register_new_sport("NHL", {
        "display_name": "National Hockey League",
        "api_config": {...},
        # ... other config
    })
    """
    config = SportConfiguration(
        sport_code=sport_code,
        **config_dict
    )
    
    if adapter_class:
        adapter = adapter_class(config)
    else:
        # Use base adapter if no custom one provided
        class DefaultAdapter(BaseSportAdapter):
            def get_primary_stats(self, position: str) -> List[str]:
                return ["games_played", "points", "assists"]
        
        adapter = DefaultAdapter(config)
    
    sport_registry.register_sport(config, adapter)


# Example of how to add a new sport (MLB)
def add_mlb_support():
    """Example of adding MLB support to the system"""
    
    class MLBAdapter(BaseSportAdapter):
        def get_primary_stats(self, position: str) -> List[str]:
            position_stats = {
                "P": ["wins", "losses", "era", "strikeouts"],
                "C": ["batting_average", "home_runs", "rbis", "ops"],
                "IF": ["batting_average", "home_runs", "rbis", "fielding_percentage"],
                "OF": ["batting_average", "home_runs", "rbis", "stolen_bases"]
            }
            return position_stats.get(position.upper(), ["batting_average", "home_runs"])
    
    mlb_config = {
        "display_name": "Major League Baseball",
        "api_config": {
            "base_url": "https://mlb-api.p.rapidapi.com",
            "endpoints": {
                "AllTeams": "/teams",
                "PlayerStats": "/player-stats"
            }
        },
        "positions": {
            "pitcher": "P", "catcher": "C",
            "first base": "1B", "second base": "2B",
            "shortstop": "SS", "third base": "3B",
            "outfield": "OF", "designated hitter": "DH"
        },
        "stat_categories": {
            "batting": ["batting_average", "home_runs", "rbis"],
            "pitching": ["era", "wins", "strikeouts"],
            "fielding": ["fielding_percentage", "errors"]
        },
        "season_format": "YYYY",
        "active_months": [3, 4, 5, 6, 7, 8, 9, 10],
        "team_count": 30,
        "roster_size": 26
    }
    
    register_new_sport("MLB", mlb_config, MLBAdapter) 