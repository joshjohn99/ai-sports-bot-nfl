"""
Team data validation module.
"""

from typing import Dict, Any, Tuple, List
from ..utils.logging import get_logger

logger = get_logger(__name__)

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
    
    # Name validation
    if team_data.get('name'):
        name = str(team_data['name']).strip()
        if len(name) < 2:
            errors.append("Team name too short")
        if not all(part.isalpha() or part.isspace() for part in name):
            errors.append("Team name contains invalid characters")
    
    # Display name validation
    if team_data.get('displayName'):
        display_name = str(team_data['displayName']).strip()
        if len(display_name) < 2:
            errors.append("Display name too short")
        if not all(part.isalpha() or part.isspace() for part in display_name):
            errors.append("Display name contains invalid characters")
    
    # Log validation results
    if errors:
        logger.warning(f"Team validation failed: {', '.join(errors)}")
    
    return len(errors) == 0, errors 