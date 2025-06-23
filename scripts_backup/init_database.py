#!/usr/bin/env python3
"""
Database initialization script.
Run this script to create and initialize the database with required tables and initial data.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.db.models import db_manager, Team
from src.sports_bot.config.db_config import DATABASE_PATH

def init_database():
    """Initialize the database and create all tables."""
    print(f"Initializing database at {DATABASE_PATH}...")
    
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Initialize database schema
    db_manager.init_db()
    
    # Create initial teams
    session = db_manager.get_session()
    
    # NFL Teams data
    nfl_teams = [
        {"name": "49ers", "display_name": "San Francisco 49ers", "abbreviation": "SF"},
        {"name": "Bears", "display_name": "Chicago Bears", "abbreviation": "CHI"},
        {"name": "Bengals", "display_name": "Cincinnati Bengals", "abbreviation": "CIN"},
        {"name": "Bills", "display_name": "Buffalo Bills", "abbreviation": "BUF"},
        {"name": "Broncos", "display_name": "Denver Broncos", "abbreviation": "DEN"},
        {"name": "Browns", "display_name": "Cleveland Browns", "abbreviation": "CLE"},
        {"name": "Buccaneers", "display_name": "Tampa Bay Buccaneers", "abbreviation": "TB"},
        {"name": "Cardinals", "display_name": "Arizona Cardinals", "abbreviation": "ARI"},
        {"name": "Chargers", "display_name": "Los Angeles Chargers", "abbreviation": "LAC"},
        {"name": "Chiefs", "display_name": "Kansas City Chiefs", "abbreviation": "KC"},
        {"name": "Colts", "display_name": "Indianapolis Colts", "abbreviation": "IND"},
        {"name": "Commanders", "display_name": "Washington Commanders", "abbreviation": "WAS"},
        {"name": "Cowboys", "display_name": "Dallas Cowboys", "abbreviation": "DAL"},
        {"name": "Dolphins", "display_name": "Miami Dolphins", "abbreviation": "MIA"},
        {"name": "Eagles", "display_name": "Philadelphia Eagles", "abbreviation": "PHI"},
        {"name": "Falcons", "display_name": "Atlanta Falcons", "abbreviation": "ATL"},
        {"name": "Giants", "display_name": "New York Giants", "abbreviation": "NYG"},
        {"name": "Jaguars", "display_name": "Jacksonville Jaguars", "abbreviation": "JAX"},
        {"name": "Jets", "display_name": "New York Jets", "abbreviation": "NYJ"},
        {"name": "Lions", "display_name": "Detroit Lions", "abbreviation": "DET"},
        {"name": "Packers", "display_name": "Green Bay Packers", "abbreviation": "GB"},
        {"name": "Panthers", "display_name": "Carolina Panthers", "abbreviation": "CAR"},
        {"name": "Patriots", "display_name": "New England Patriots", "abbreviation": "NE"},
        {"name": "Raiders", "display_name": "Las Vegas Raiders", "abbreviation": "LV"},
        {"name": "Rams", "display_name": "Los Angeles Rams", "abbreviation": "LAR"},
        {"name": "Ravens", "display_name": "Baltimore Ravens", "abbreviation": "BAL"},
        {"name": "Saints", "display_name": "New Orleans Saints", "abbreviation": "NO"},
        {"name": "Seahawks", "display_name": "Seattle Seahawks", "abbreviation": "SEA"},
        {"name": "Steelers", "display_name": "Pittsburgh Steelers", "abbreviation": "PIT"},
        {"name": "Texans", "display_name": "Houston Texans", "abbreviation": "HOU"},
        {"name": "Titans", "display_name": "Tennessee Titans", "abbreviation": "TEN"},
        {"name": "Vikings", "display_name": "Minnesota Vikings", "abbreviation": "MIN"},
    ]
    
    try:
        # Add teams if they don't exist
        for team_data in nfl_teams:
            existing_team = session.query(Team).filter_by(name=team_data["name"]).first()
            if not existing_team:
                team = Team(
                    external_id=team_data["abbreviation"],  # Using abbreviation as external_id for now
                    name=team_data["name"],
                    display_name=team_data["display_name"],
                    abbreviation=team_data["abbreviation"]
                )
                session.add(team)
        
        session.commit()
        print("Successfully initialized database and added NFL teams.")
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_database() 