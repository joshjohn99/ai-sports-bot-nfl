"""
API response schemas and data models.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PlayerInfo:
    """Player basic information."""
    id: str
    full_name: str
    position: str
    team_id: Optional[str] = None
    jersey_number: Optional[str] = None
    status: Optional[str] = None

@dataclass
class TeamInfo:
    """Team basic information."""
    id: str
    name: str
    display_name: str
    abbreviation: str
    location: Optional[str] = None
    division: Optional[str] = None
    conference: Optional[str] = None

@dataclass
class PlayerStats:
    """Player statistics."""
    player_id: str
    season: str
    games_played: int
    games_started: int
    passing_yards: Optional[int] = None
    passing_touchdowns: Optional[int] = None
    rushing_yards: Optional[int] = None
    rushing_touchdowns: Optional[int] = None
    receiving_yards: Optional[int] = None
    receptions: Optional[int] = None
    receiving_touchdowns: Optional[int] = None
    sacks: Optional[float] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    forced_fumbles: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    extra_points_made: Optional[int] = None

@dataclass
class CareerStats:
    """Career statistics."""
    player_id: str
    total_games: int
    total_starts: int
    seasons_played: int
    career_passing_yards: Optional[int] = None
    career_passing_touchdowns: Optional[int] = None
    career_rushing_yards: Optional[int] = None
    career_rushing_touchdowns: Optional[int] = None
    career_receiving_yards: Optional[int] = None
    career_receptions: Optional[int] = None
    career_receiving_touchdowns: Optional[int] = None
    career_sacks: Optional[float] = None
    career_tackles: Optional[int] = None
    career_interceptions: Optional[int] = None
    career_forced_fumbles: Optional[int] = None
    career_field_goals_made: Optional[int] = None
    career_field_goals_attempted: Optional[int] = None
    career_extra_points_made: Optional[int] = None

def parse_player_info(data: Dict) -> PlayerInfo:
    """Parse raw API data into PlayerInfo object."""
    return PlayerInfo(
        id=str(data.get('id')),
        full_name=data.get('fullName', ''),
        position=data.get('position', {}).get('abbreviation', ''),
        team_id=str(data.get('team', {}).get('id')) if data.get('team') else None,
        jersey_number=data.get('jerseyNumber'),
        status=data.get('status')
    )

def parse_team_info(data: Dict) -> TeamInfo:
    """Parse raw API data into TeamInfo object."""
    return TeamInfo(
        id=str(data.get('id')),
        name=data.get('name', ''),
        display_name=data.get('displayName', ''),
        abbreviation=data.get('abbreviation', ''),
        location=data.get('location'),
        division=data.get('division'),
        conference=data.get('conference')
    )

def parse_player_stats(data: Dict, season: str) -> PlayerStats:
    """Parse raw API data into PlayerStats object."""
    return PlayerStats(
        player_id=str(data.get('player', {}).get('id')),
        season=season,
        games_played=data.get('gamesPlayed', 0),
        games_started=data.get('gamesStarted', 0),
        passing_yards=data.get('passingYards'),
        passing_touchdowns=data.get('passingTouchdowns'),
        rushing_yards=data.get('rushingYards'),
        rushing_touchdowns=data.get('rushingTouchdowns'),
        receiving_yards=data.get('receivingYards'),
        receptions=data.get('receptions'),
        receiving_touchdowns=data.get('receivingTouchdowns'),
        sacks=data.get('sacks'),
        tackles=data.get('tackles'),
        interceptions=data.get('interceptions'),
        forced_fumbles=data.get('forcedFumbles'),
        field_goals_made=data.get('fieldGoalsMade'),
        field_goals_attempted=data.get('fieldGoalsAttempted'),
        extra_points_made=data.get('extraPointsMade')
    ) 