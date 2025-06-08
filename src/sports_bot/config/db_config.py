"""
Database configuration settings.
"""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Database settings
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'sports_stats.db')

def get_db_url():
    """Get the database URL."""
    return f'sqlite:///{DATABASE_PATH}' 