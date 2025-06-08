"""
Player data validation module.
"""

from typing import Dict, Any, Tuple, List, Set
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Valid NFL positions
VALID_POSITIONS: Set[str] = {
    'QB', 'RB', 'WR', 'TE', 'FB', 'OL', 'T', 'G', 'C',
    'DE', 'DT', 'LB', 'CB', 'S', 'MLB', 'OLB', 'ILB',
    'EDGE', 'DL', 'DB', 'K', 'P', 'LS'
}

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
        
        # Name format validation (FirstName LastName)
        name_parts = name.split()
        if len(name_parts) < 2:
            errors.append("Player name must include both first and last name")
        elif any(len(part) < 2 for part in name_parts):
            errors.append("Name parts must be at least 2 characters long")
    
    # Position validation
    if player_data.get('position'):
        position = str(player_data.get('position', {}).get('abbreviation', '')).upper()
        if position not in VALID_POSITIONS:
            errors.append(f"Invalid position: {position}")
    
    # Jersey number validation (if provided)
    if jersey_number := player_data.get('jerseyNumber'):
        try:
            number = int(jersey_number)
            if number < 0 or number > 99:
                errors.append("Jersey number must be between 0 and 99")
        except (ValueError, TypeError):
            errors.append("Jersey number must be a valid integer")
    
    # Status validation (if provided)
    if status := player_data.get('status'):
        valid_statuses = {'Active', 'Inactive', 'Injured Reserve', 'Practice Squad', 'Suspended'}
        if status not in valid_statuses:
            errors.append(f"Invalid status: {status}")
    
    # Team validation (if provided)
    if team_data := player_data.get('team'):
        if not isinstance(team_data, dict):
            errors.append("Team data must be a dictionary")
        elif not team_data.get('id'):
            errors.append("Team ID is required when team data is provided")
    
    # Height validation (if provided)
    if height := player_data.get('height'):
        try:
            feet, inches = map(int, height.split('-'))
            if feet < 4 or feet > 7 or inches < 0 or inches > 11:
                errors.append("Invalid height format (must be between 4-0 and 7-11)")
        except (ValueError, AttributeError):
            errors.append("Height must be in format 'feet-inches' (e.g., '6-2')")
    
    # Weight validation (if provided)
    if weight := player_data.get('weight'):
        try:
            weight_val = int(weight)
            if weight_val < 150 or weight_val > 400:
                errors.append("Weight must be between 150 and 400 pounds")
        except (ValueError, TypeError):
            errors.append("Weight must be a valid integer")
    
    # Log validation results
    if errors:
        logger.warning(f"Player validation failed for {player_data.get('fullName', 'Unknown')}: {', '.join(errors)}")
    
    return len(errors) == 0, errors

def validate_position_for_stats(position: str, stat_name: str) -> bool:
    """
    Validate if a statistic is valid for a given position.
    """
    position = position.upper()
    
    # Position-specific stat mapping
    position_stats = {
        'QB': {'passingYards', 'passingTouchdowns', 'interceptions', 'rushingYards', 'rushingTouchdowns'},
        'RB': {'rushingYards', 'rushingTouchdowns', 'receptions', 'receivingYards', 'receivingTouchdowns'},
        'WR': {'receptions', 'receivingYards', 'receivingTouchdowns'},
        'TE': {'receptions', 'receivingYards', 'receivingTouchdowns', 'rushingYards'},
        'FB': {'rushingYards', 'rushingTouchdowns', 'receptions'},
        'K': {'fieldGoalsMade', 'fieldGoalsAttempted', 'extraPointsMade'},
        'P': {'punts', 'puntYards', 'puntsInside20'},
    }
    
    # Defensive positions share the same stats
    defensive_positions = {'DE', 'DT', 'LB', 'CB', 'S', 'MLB', 'OLB', 'ILB', 'EDGE', 'DL', 'DB'}
    defensive_stats = {'sacks', 'tackles', 'interceptions', 'forcedFumbles', 'fumblesRecovered', 'passesDefended'}
    
    if position in defensive_positions:
        return stat_name in defensive_stats
    
    return position in position_stats and stat_name in position_stats[position] 