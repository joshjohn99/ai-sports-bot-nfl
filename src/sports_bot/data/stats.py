"""
Statistics validation module.
"""

from typing import Dict, Any, Tuple, List
from datetime import datetime
from .player import validate_position_for_stats
from ..utils.logging import get_logger

logger = get_logger(__name__)

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
                if not validate_position_for_stats('QB', stat):
                    errors.append(f"{stat} is not valid for position QB")
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
                if not validate_position_for_stats(position_upper, stat):
                    errors.append(f"{stat} is not valid for position {position_upper}")
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
                if not validate_position_for_stats(position_upper, stat):
                    errors.append(f"{stat} is not valid for position {position_upper}")
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
                if not validate_position_for_stats(position_upper, stat):
                    errors.append(f"{stat} is not valid for position {position_upper}")
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
                if not validate_position_for_stats('K', stat):
                    errors.append(f"{stat} is not valid for position K")
            except (ValueError, TypeError):
                errors.append(f"{stat} must be an integer")
        
        # Validate field goal percentage
        fg_made = stats_data.get('fieldGoalsMade', 0)
        fg_attempted = stats_data.get('fieldGoalsAttempted', 0)
        if fg_attempted > 0 and fg_made > fg_attempted:
            errors.append("Field goals made cannot exceed attempts")
    
    # Log validation results
    if errors:
        logger.warning(f"Stats validation failed for position {position_upper}: {', '.join(errors)}")
    
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
    
    # Log validation results
    if errors:
        logger.warning(f"Career stats validation failed: {', '.join(errors)}")
    
    return len(errors) == 0, errors 