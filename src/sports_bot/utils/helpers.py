"""
Helper functions for common operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

def is_nfl_season() -> bool:
    """Check if we're currently in NFL season (September through January)."""
    month = datetime.now().month
    return month >= 9 or month <= 1

def get_current_season() -> str:
    """Get the current NFL season year."""
    current_year = datetime.now().year
    if datetime.now().month < 8:
        current_year -= 1
    return str(current_year)

def format_player_name(name: str) -> str:
    """Format player name consistently."""
    # Remove extra spaces
    name = " ".join(name.split())
    # Capitalize each part
    return name.title()

def parse_height(height: str) -> Optional[Dict[str, int]]:
    """Parse height string into feet and inches."""
    try:
        feet, inches = map(int, height.split('-'))
        if 4 <= feet <= 7 and 0 <= inches <= 11:
            return {'feet': feet, 'inches': inches}
    except (ValueError, AttributeError):
        pass
    return None

def format_stats_value(value: Any, stat_type: str) -> str:
    """Format stat value for display."""
    if value is None:
        return "N/A"
    
    if stat_type == "percentage":
        try:
            return f"{float(value):.1f}%"
        except (ValueError, TypeError):
            return str(value)
    
    if stat_type == "yards":
        try:
            return f"{int(value):,} yds"
        except (ValueError, TypeError):
            return str(value)
    
    if stat_type == "decimal":
        try:
            return f"{float(value):.1f}"
        except (ValueError, TypeError):
            return str(value)
    
    return str(value)

def calculate_passer_rating(attempts: int, completions: int, yards: int, touchdowns: int, interceptions: int) -> float:
    """Calculate NFL passer rating."""
    if attempts == 0:
        return 0.0
    
    # Calculate the four components
    comp_per_attempt = ((completions / attempts) * 100 - 30) * 0.05
    yards_per_attempt = ((yards / attempts) - 3) * 0.25
    td_per_attempt = (touchdowns / attempts) * 20
    int_per_attempt = 2.375 - ((interceptions / attempts) * 25)
    
    # Ensure components are between 0 and 2.375
    components = [comp_per_attempt, yards_per_attempt, td_per_attempt, int_per_attempt]
    components = [max(0, min(2.375, c)) for c in components]
    
    # Calculate final rating
    return sum(components) * 100 / 6

def calculate_completion_percentage(completions: int, attempts: int) -> float:
    """Calculate completion percentage."""
    if attempts == 0:
        return 0.0
    return (completions / attempts) * 100

def calculate_field_goal_percentage(made: int, attempted: int) -> float:
    """Calculate field goal percentage."""
    if attempted == 0:
        return 0.0
    return (made / attempted) * 100

def format_game_score(team_score: int, opponent_score: int) -> str:
    """Format game score."""
    return f"{team_score}-{opponent_score}"

def format_record(wins: int, losses: int, ties: int = 0) -> str:
    """Format team record."""
    if ties > 0:
        return f"{wins}-{losses}-{ties}"
    return f"{wins}-{losses}"

def calculate_winning_percentage(wins: int, losses: int, ties: int = 0) -> float:
    """Calculate winning percentage."""
    total_games = wins + losses + ties
    if total_games == 0:
        return 0.0
    return (wins + (ties * 0.5)) / total_games

def format_date(date_str: str) -> str:
    """Format date string consistently."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except ValueError:
        return date_str

def get_season_weeks() -> List[int]:
    """Get list of NFL season weeks."""
    return list(range(1, 19))  # 18-week regular season

def is_valid_week(week: int) -> bool:
    """Check if week number is valid."""
    return 1 <= week <= 18

def get_position_group(position: str) -> str:
    """Get position group for a position."""
    position = position.upper()
    
    offense = {
        'QB': 'Quarterback',
        'RB': 'Running Back',
        'FB': 'Fullback',
        'WR': 'Wide Receiver',
        'TE': 'Tight End',
        'OL': 'Offensive Line',
        'T': 'Offensive Tackle',
        'G': 'Guard',
        'C': 'Center'
    }
    
    defense = {
        'DE': 'Defensive End',
        'DT': 'Defensive Tackle',
        'LB': 'Linebacker',
        'MLB': 'Middle Linebacker',
        'OLB': 'Outside Linebacker',
        'ILB': 'Inside Linebacker',
        'CB': 'Cornerback',
        'S': 'Safety',
        'EDGE': 'Edge Rusher',
        'DL': 'Defensive Line',
        'DB': 'Defensive Back'
    }
    
    special_teams = {
        'K': 'Kicker',
        'P': 'Punter',
        'LS': 'Long Snapper'
    }
    
    if position in offense:
        return 'Offense'
    if position in defense:
        return 'Defense'
    if position in special_teams:
        return 'Special Teams'
    return 'Unknown' 