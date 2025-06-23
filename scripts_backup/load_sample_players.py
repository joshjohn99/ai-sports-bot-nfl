#!/usr/bin/env python3
"""
Script to load sample player data including real NFL players.
This will populate the database with known players for testing.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.db.models import db_manager, Team, Player, PlayerStats

def load_sample_players():
    """Load sample player data including real NFL players."""
    print("Loading sample player data...")
    
    # Initialize database
    db_manager.init_db()
    session = db_manager.get_session()
    
    try:
        # Get Ravens team
        ravens = session.query(Team).filter_by(abbreviation="BAL").first()
        if not ravens:
            print("Ravens team not found. Please run init_database.py first.")
            return
        
        # Get Bills team
        bills = session.query(Team).filter_by(abbreviation="BUF").first()
        if not bills:
            print("Bills team not found. Please run init_database.py first.")
            return
        
        # Sample real players with real stats (2024 season approximations)
        players_data = [
            {
                "external_id": "3043078",  # Real Lamar Jackson ID
                "name": "Lamar Jackson",
                "position": "QB",
                "team": ravens,
                "stats": {
                    "season": "2024",
                    "games_played": 17,
                    "games_started": 17,
                    "passing_yards": 3678,
                    "passing_touchdowns": 24,
                    "rushing_yards": 915,
                    "rushing_touchdowns": 5,
                    "interceptions": 7
                }
            },
            {
                "external_id": "3916387",  # Real Josh Allen ID  
                "name": "Josh Allen",
                "position": "QB",
                "team": bills,
                "stats": {
                    "season": "2024",
                    "games_played": 17,
                    "games_started": 17,
                    "passing_yards": 4306,
                    "passing_touchdowns": 28,
                    "rushing_yards": 523,
                    "rushing_touchdowns": 15,
                    "interceptions": 18
                }
            },
            {
                "external_id": "9876543",  # Fictional CB Lamar Jackson
                "name": "Lamar Jackson",
                "position": "CB",
                "team": session.query(Team).filter_by(abbreviation="NYJ").first(),
                "stats": {
                    "season": "2024",
                    "games_played": 16,
                    "games_started": 12,
                    "tackles": 68,
                    "interceptions": 3,
                    "forced_fumbles": 1
                }
            }
        ]
        
        for player_data in players_data:
            # Check if player already exists
            existing_player = session.query(Player).filter_by(external_id=player_data["external_id"]).first()
            
            if not existing_player:
                # Create player
                player = Player(
                    external_id=player_data["external_id"],
                    name=player_data["name"],
                    position=player_data["position"],
                    current_team_id=player_data["team"].id if player_data["team"] else None
                )
                session.add(player)
                session.flush()  # Get the ID
                
                # Create player stats
                stats = PlayerStats(
                    player_id=player.id,
                    season=player_data["stats"]["season"],
                    games_played=player_data["stats"].get("games_played"),
                    games_started=player_data["stats"].get("games_started"),
                    passing_yards=player_data["stats"].get("passing_yards"),
                    passing_touchdowns=player_data["stats"].get("passing_touchdowns"),
                    rushing_yards=player_data["stats"].get("rushing_yards"),
                    rushing_touchdowns=player_data["stats"].get("rushing_touchdowns"),
                    receiving_yards=player_data["stats"].get("receiving_yards"),
                    receptions=player_data["stats"].get("receptions"),
                    receiving_touchdowns=player_data["stats"].get("receiving_touchdowns"),
                    sacks=player_data["stats"].get("sacks"),
                    tackles=player_data["stats"].get("tackles"),
                    interceptions=player_data["stats"].get("interceptions"),
                    forced_fumbles=player_data["stats"].get("forced_fumbles")
                )
                session.add(stats)
                
                print(f"Added {player_data['name']} ({player_data['position']}) - {player_data['team'].name if player_data['team'] else 'No Team'}")
            else:
                print(f"Player {player_data['name']} already exists, skipping...")
        
        session.commit()
        print("Successfully loaded sample player data.")
        
        # Verify the data
        print("\nVerifying loaded players:")
        lamar_players = session.query(Player).filter(Player.name.ilike("%Lamar Jackson%")).all()
        for player in lamar_players:
            print(f"- {player.name} ({player.position}) - {player.current_team.abbreviation if player.current_team else 'No Team'}")
        
    except Exception as e:
        session.rollback()
        print(f"Error loading sample data: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_sample_players() 