"""
Data validation module for ensuring data quality and consistency.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger("data_validators")

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_team_data(team_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate team data before update/insert.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    # Required fields
    required_fields = ['id', 'name', 'displayName', 'abbreviation']
    for field in required_fields:
        if not team_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Field type validation
    if team_data.get('id') and not str(team_data['id']).strip():
        errors.append("Team ID cannot be empty")
    
    if team_data.get('abbreviation') and len(str(team_data['abbreviation'])) > 5:
        errors.append("Team abbreviation too long (max 5 characters)")
    
    # NFL-specific validation
    if team_data.get('abbreviation'):
        if not team_data['abbreviation'].isalpha():
            errors.append("Team abbreviation must contain only letters")
    
    return len(errors) == 0, errors

def validate_player_data(player_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate player data before update/insert.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    # Required fields
    required_fields = ['id', 'fullName', 'position']
    for field in required_fields:
        if not player_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Name validation
    if player_data.get('fullName'):
        name = str(player_data['fullName']).strip()
        if len(name) < 2:
            errors.append("Player name too short")
        if not all(part.isalpha() or part.isspace() or part in ".-'" for part in name):
            errors.append("Player name contains invalid characters")
    
    # Position validation
    valid_positions = {
        'QB', 'RB', 'WR', 'TE', 'FB', 'OL', 'T', 'G', 'C',
        'DE', 'DT', 'LB', 'CB', 'S', 'MLB', 'OLB', 'ILB',
        'EDGE', 'DL', 'DB', 'K', 'P', 'LS'
    }
    if player_data.get('position'):
        position = str(player_data.get('position', {}).get('abbreviation', '')).upper()
        if position not in valid_positions:
            errors.append(f"Invalid position: {position}")
    
    return len(errors) == 0, errors

def validate_stats_data(stats_data: Dict[str, Any], player_position: str) -> Tuple[bool, List[str]]:
    """
    Validate player statistics before update/insert.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    # Basic validation
    if not isinstance(stats_data, dict):
        return False, ["Stats data must be a dictionary"]
    
    # Season validation
    current_year = datetime.now().year
    season = stats_data.get('season', str(current_year))
    try:
        season_year = int(season)
        if season_year < 1920 or season_year > current_year:
            errors.append(f"Invalid season year: {season}")
    except (ValueError, TypeError):
        errors.append(f"Invalid season format: {season}")
    
    # Games validation
    games_played = stats_data.get('gamesPlayed', 0)
    games_started = stats_data.get('gamesStarted', 0)
    
    try:
        games_played = int(games_played)
        games_started = int(games_started)
        
        if games_played < 0 or games_played > 17:  # NFL regular season
            errors.append(f"Invalid games played: {games_played}")
        if games_started < 0 or games_started > games_played:
            errors.append(f"Invalid games started: {games_started}")
    except (ValueError, TypeError):
        errors.append("Games played/started must be integers")
    
    # Position-specific stat validation
    position_upper = player_position.upper()
    
    if position_upper == 'QB':
        # QB stat validation
        passing_stats = {
            'passingYards': (0, 7000),
            'passingTouchdowns': (0, 70),
            'interceptions': (0, 40)
        }
        for stat, (min_val, max_val) in passing_stats.items():
            value = stats_data.get(stat, 0)
            try:
                value = int(value)
                if value < min_val or value > max_val:
                    errors.append(f"Invalid {stat}: {value}")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be an integer")
    
    elif position_upper in {'RB', 'FB'}:
        # Running back stat validation
        rushing_stats = {
            'rushingYards': (0, 3000),
            'rushingTouchdowns': (0, 35)
        }
        for stat, (min_val, max_val) in rushing_stats.items():
            value = stats_data.get(stat, 0)
            try:
                value = int(value)
                if value < min_val or value > max_val:
                    errors.append(f"Invalid {stat}: {value}")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be an integer")
    
    elif position_upper in {'WR', 'TE'}:
        # Receiver stat validation
        receiving_stats = {
            'receivingYards': (0, 2500),
            'receptions': (0, 150),
            'receivingTouchdowns': (0, 30)
        }
        for stat, (min_val, max_val) in receiving_stats.items():
            value = stats_data.get(stat, 0)
            try:
                value = int(value)
                if value < min_val or value > max_val:
                    errors.append(f"Invalid {stat}: {value}")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be an integer")
    
    elif position_upper in {'DE', 'DT', 'LB', 'MLB', 'OLB', 'ILB', 'EDGE', 'DL'}:
        # Defensive stat validation
        defensive_stats = {
            'sacks': (0, 30),
            'tackles': (0, 200),
            'interceptions': (0, 15),
            'forcedFumbles': (0, 15)
        }
        for stat, (min_val, max_val) in defensive_stats.items():
            value = stats_data.get(stat, 0)
            try:
                value = float(value) if stat == 'sacks' else int(value)
                if value < min_val or value > max_val:
                    errors.append(f"Invalid {stat}: {value}")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be a {'float' if stat == 'sacks' else 'integer'}")
    
    elif position_upper == 'K':
        # Kicker stat validation
        kicking_stats = {
            'fieldGoalsMade': (0, 50),
            'fieldGoalsAttempted': (0, 60),
            'extraPointsMade': (0, 80)
        }
        for stat, (min_val, max_val) in kicking_stats.items():
            value = stats_data.get(stat, 0)
            try:
                value = int(value)
                if value < min_val or value > max_val:
                    errors.append(f"Invalid {stat}: {value}")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be an integer")
        
        # Validate field goal percentage
        fg_made = stats_data.get('fieldGoalsMade', 0)
        fg_attempted = stats_data.get('fieldGoalsAttempted', 0)
        if fg_attempted > 0 and fg_made > fg_attempted:
            errors.append("Field goals made cannot exceed attempts")
    
    return len(errors) == 0, errors

def validate_career_stats(career_stats: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate career statistics before update/insert.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    # Basic validation
    if not isinstance(career_stats, dict):
        return False, ["Career stats must be a dictionary"]
    
    # Career totals validation
    total_stats = {
        'total_games': (0, 400),  # 25 seasons max
        'total_starts': (0, 400),
        'seasons_played': (0, 25)
    }
    
    for stat, (min_val, max_val) in total_stats.items():
        value = career_stats.get(stat, 0)
        try:
            value = int(value)
            if value < min_val or value > max_val:
                errors.append(f"Invalid {stat}: {value}")
        except (ValueError, TypeError):
            errors.append(f"{stat} must be an integer")
    
    # Validate career stats don't exceed reasonable limits
    career_limits = {
        'career_passing_yards': 100000,
        'career_passing_touchdowns': 700,
        'career_rushing_yards': 25000,
        'career_rushing_touchdowns': 200,
        'career_receiving_yards': 25000,
        'career_receptions': 1500,
        'career_receiving_touchdowns': 200,
        'career_sacks': 250,
        'career_tackles': 2500,
        'career_interceptions': 100,
        'career_forced_fumbles': 100,
        'career_field_goals_made': 700,
        'career_field_goals_attempted': 900,
        'career_extra_points_made': 1200
    }
    
    for stat, max_val in career_limits.items():
        value = career_stats.get(stat, 0)
        try:
            value = float(value) if stat == 'career_sacks' else int(value)
            if value < 0 or value > max_val:
                errors.append(f"Invalid {stat}: {value}")
        except (ValueError, TypeError):
            errors.append(f"{stat} must be a {'float' if stat == 'career_sacks' else 'integer'}")
    
    # Validate field goal career stats
    fg_made = career_stats.get('career_field_goals_made', 0)
    fg_attempted = career_stats.get('career_field_goals_attempted', 0)
    if fg_attempted > 0 and fg_made > fg_attempted:
        errors.append("Career field goals made cannot exceed attempts")
    
    return len(errors) == 0, errors 