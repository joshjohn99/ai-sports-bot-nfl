"""
Migration script to populate the database from existing JSON files.
"""

import os
import json
from datetime import datetime
from sports_bot.core.database import db_manager, Player, Team, PlayerStats, CareerStats

def migrate_data():
    """Migrate data from JSON files to SQLite database."""
    print("Starting data migration...")
    
    # Initialize database
    db_manager.init_db()
    session = db_manager.get_session()
    
    try:
        # Get paths
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'daily_store')
        sports = ['nfl']  # Add more sports as needed
        
        for sport in sports:
            sport_dir = os.path.join(base_dir, sport.lower())
            if not os.path.exists(sport_dir):
                print(f"No data directory found for {sport}")
                continue
                
            print(f"\nProcessing {sport.upper()} data...")
            
            # Migrate teams
            teams_file = os.path.join(sport_dir, 'all_teams.json')
            if os.path.exists(teams_file):
                print("Migrating teams...")
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                
                for team_data in teams_data:
                    team_info = team_data.get('team', team_data)
                    team = Team(
                        external_id=str(team_info.get('id')),
                        name=team_info.get('name'),
                        display_name=team_info.get('displayName'),
                        abbreviation=team_info.get('abbreviation')
                    )
                    session.add(team)
                session.commit()
                print(f"Migrated {len(teams_data)} teams")
            
            # Migrate players and their stats
            stats_dir = os.path.join(sport_dir, 'player_stats')
            if not os.path.exists(stats_dir):
                print("No player stats directory found")
                continue
                
            # Process each season directory
            for season_dir in os.listdir(stats_dir):
                season_path = os.path.join(stats_dir, season_dir)
                if not os.path.isdir(season_path):
                    continue
                    
                print(f"\nProcessing season {season_dir}...")
                
                # Process each player file
                for player_file in os.listdir(season_path):
                    if not player_file.startswith('player_') or not player_file.endswith('.json'):
                        continue
                        
                    player_path = os.path.join(season_path, player_file)
                    try:
                        with open(player_path, 'r') as f:
                            player_data = json.load(f)
                            
                        # Extract player info
                        player_info = player_data.get('player', {})
                        if not player_info:
                            continue
                            
                        # Get or create player
                        player = session.query(Player).filter_by(external_id=str(player_info.get('id'))).first()
                        if not player:
                            player = Player(
                                external_id=str(player_info.get('id')),
                                name=player_info.get('fullName'),
                                position=player_info.get('position', {}).get('abbreviation')
                            )
                            session.add(player)
                            session.flush()  # Get player.id
                        
                        # Create season stats
                        stats = PlayerStats(
                            player_id=player.id,
                            season=season_dir,
                            games_played=player_data.get('gamesPlayed'),
                            games_started=player_data.get('gamesStarted'),
                            passing_yards=player_data.get('passingYards'),
                            passing_touchdowns=player_data.get('passingTouchdowns'),
                            rushing_yards=player_data.get('rushingYards'),
                            rushing_touchdowns=player_data.get('rushingTouchdowns'),
                            receiving_yards=player_data.get('receivingYards'),
                            receptions=player_data.get('receptions'),
                            receiving_touchdowns=player_data.get('receivingTouchdowns'),
                            sacks=player_data.get('sacks'),
                            tackles=player_data.get('tackles'),
                            interceptions=player_data.get('interceptions'),
                            forced_fumbles=player_data.get('forcedFumbles'),
                            field_goals_made=player_data.get('fieldGoalsMade'),
                            field_goals_attempted=player_data.get('fieldGoalsAttempted'),
                            extra_points_made=player_data.get('extraPointsMade')
                        )
                        session.add(stats)
                        
                        # Commit every 100 players to avoid memory issues
                        if session.new:
                            session.commit()
                            
                    except Exception as e:
                        print(f"Error processing {player_file}: {str(e)}")
                        session.rollback()
                        continue
            
            # Update career stats for all players
            print("\nUpdating career stats...")
            players = session.query(Player).all()
            for player in players:
                try:
                    db_manager.update_career_stats(player.id)
                except Exception as e:
                    print(f"Error updating career stats for player {player.name}: {str(e)}")
                    continue
            
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate_data() 