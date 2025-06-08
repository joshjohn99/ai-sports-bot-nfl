#!/usr/bin/env python3
"""
Script to fetch and populate sample data for teams and players.
This will populate the database with real NFL data for testing purposes.
"""

import os
import sys
from pathlib import Path
import requests
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.db.models import db_manager, Team, Player, PlayerStats
from src.sports_bot.config.api_config import api_config

def fetch_sample_data():
    """Fetch and populate sample data."""
    print("Fetching sample NFL data...")
    
    # Initialize database
    db_manager.init_db()
    session = db_manager.get_session()
    
    # Get current season
    current_year = datetime.now().year
    if datetime.now().month < 8:
        current_year -= 1
    season = str(current_year)
    
    try:
        # Get teams from database
        teams = session.query(Team).all()
        if not teams:
            print("No teams found in database. Please run init_database.py first.")
            return
        
        # Sample offensive stats for teams (2023 season approximations)
        team_stats = {
            "49ers": {
                "total_passing_yards": 4050,
                "total_rushing_yards": 2389,
                "total_receiving_yards": 4050,
                "total_touchdowns": 54,
                "total_sacks": 48,
                "total_interceptions": 22,
                "games_played": 17,
                "wins": 12,
                "losses": 5
            },
            "Eagles": {
                "total_passing_yards": 3958,
                "total_rushing_yards": 2245,
                "total_receiving_yards": 3958,
                "total_touchdowns": 47,
                "total_sacks": 43,
                "total_interceptions": 18,
                "games_played": 17,
                "wins": 11,
                "losses": 6
            }
        }
        
        # Add sample players and their stats
        for team in teams:
            if team.name in team_stats:
                print(f"Adding sample data for {team.name}...")
                
                # Create sample QB
                qb = Player(
                    external_id=f"{team.name.lower()}_qb_1",
                    name=f"{team.name} QB1",
                    position="QB",
                    current_team_id=team.id
                )
                session.add(qb)
                session.flush()  # Get the ID
                
                # QB Stats
                qb_stats = PlayerStats(
                    player_id=qb.id,
                    season=season,
                    games_played=17,
                    games_started=17,
                    passing_yards=team_stats[team.name]["total_passing_yards"],
                    passing_touchdowns=32,
                    rushing_yards=200,
                    rushing_touchdowns=3
                )
                session.add(qb_stats)
                
                # Create sample RB
                rb = Player(
                    external_id=f"{team.name.lower()}_rb_1",
                    name=f"{team.name} RB1",
                    position="RB",
                    current_team_id=team.id
                )
                session.add(rb)
                session.flush()
                
                # RB Stats
                rb_stats = PlayerStats(
                    player_id=rb.id,
                    season=season,
                    games_played=17,
                    games_started=15,
                    rushing_yards=team_stats[team.name]["total_rushing_yards"] - 200,  # Subtract QB rushing yards
                    rushing_touchdowns=12,
                    receiving_yards=400,
                    receptions=35,
                    receiving_touchdowns=2
                )
                session.add(rb_stats)
                
                # Create sample WR
                wr = Player(
                    external_id=f"{team.name.lower()}_wr_1",
                    name=f"{team.name} WR1",
                    position="WR",
                    current_team_id=team.id
                )
                session.add(wr)
                session.flush()
                
                # WR Stats
                wr_stats = PlayerStats(
                    player_id=wr.id,
                    season=season,
                    games_played=17,
                    games_started=17,
                    receiving_yards=team_stats[team.name]["total_receiving_yards"] - 400,  # Subtract RB receiving yards
                    receptions=85,
                    receiving_touchdowns=8
                )
                session.add(wr_stats)
        
        session.commit()
        print("Successfully added sample data to the database.")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding sample data: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fetch_sample_data() 