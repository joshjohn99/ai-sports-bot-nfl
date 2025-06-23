#!/usr/bin/env python3
"""
Migration script to move existing NFL data to sport-specific databases.
This preserves all your existing data while setting up the new architecture.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import old models without sport column
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Create old models that match the existing schema
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sports_bot.config.db_config import get_db_url

OldBase = declarative_base()

class OldPlayer(OldBase):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    position = Column(String, index=True)
    current_team_id = Column(Integer, ForeignKey('teams.id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class OldTeam(OldBase):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    display_name = Column(String)
    abbreviation = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class OldPlayerStats(OldBase):
    __tablename__ = 'player_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), index=True)
    season = Column(String, index=True)
    games_played = Column(Integer)
    games_started = Column(Integer)
    passing_yards = Column(Integer)
    passing_touchdowns = Column(Integer)
    rushing_yards = Column(Integer)
    rushing_touchdowns = Column(Integer)
    receiving_yards = Column(Integer)
    receptions = Column(Integer)
    receiving_touchdowns = Column(Integer)
    sacks = Column(Float)
    tackles = Column(Integer)
    interceptions = Column(Integer)
    forced_fumbles = Column(Integer)
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    extra_points_made = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# Create old database manager
class OldDatabaseManager:
    def __init__(self):
        self.engine = create_engine(get_db_url())
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()

old_db_manager = OldDatabaseManager()
from sports_bot.database.sport_models import sport_db_manager
from sports_bot.config.sport_config import sport_config_manager
from rich.console import Console
from rich.progress import Progress, TaskID
import time

console = Console()

def migrate_nfl_data():
    """Migrate existing NFL data to the new sport-specific database."""
    console.print("[bold blue]🏈 Starting NFL Data Migration[/bold blue]")
    console.print("Moving data from unified database to sport-specific NFL database...")
    print()
    
    # Get old database session
    old_session = old_db_manager.get_session()
    
    # Get new NFL database session and models
    nfl_session = sport_db_manager.get_session('NFL')
    nfl_models = sport_db_manager.get_models('NFL')
    
    if not nfl_session or not nfl_models:
        console.print("[red]❌ Failed to get NFL database session or models[/red]")
        return False
    
    try:
        with Progress() as progress:
            # Migrate Teams
            console.print("[cyan]📋 Migrating Teams...[/cyan]")
            old_teams = old_session.query(OldTeam).all()
            team_task = progress.add_task("Teams", total=len(old_teams))
            
            team_mapping = {}  # old_id -> new_id
            
            for old_team in old_teams:
                # Check if team already exists
                existing_team = nfl_session.query(nfl_models['Team']).filter_by(
                    external_id=old_team.external_id
                ).first()
                
                if not existing_team:
                    new_team = nfl_models['Team'](
                        external_id=old_team.external_id,
                        name=old_team.name,
                        display_name=old_team.display_name,
                        abbreviation=old_team.abbreviation,
                        city=getattr(old_team, 'city', None),
                        conference=None,  # Can be added later
                        division=None,    # Can be added later
                        active=True,
                        created_at=old_team.created_at,
                        updated_at=old_team.updated_at
                    )
                    nfl_session.add(new_team)
                    nfl_session.flush()  # Get the ID
                    team_mapping[old_team.id] = new_team.id
                else:
                    team_mapping[old_team.id] = existing_team.id
                
                progress.update(team_task, advance=1)
            
            nfl_session.commit()
            console.print(f"[green]✅ Migrated {len(old_teams)} teams[/green]")
            
            # Migrate Players
            console.print("[cyan]👥 Migrating Players...[/cyan]")
            old_players = old_session.query(OldPlayer).all()
            player_task = progress.add_task("Players", total=len(old_players))
            
            player_mapping = {}  # old_id -> new_id
            
            for old_player in old_players:
                # Check if player already exists
                existing_player = nfl_session.query(nfl_models['Player']).filter_by(
                    external_id=old_player.external_id
                ).first()
                
                if not existing_player:
                    new_team_id = team_mapping.get(old_player.current_team_id)
                    
                    new_player = nfl_models['Player'](
                        external_id=old_player.external_id,
                        name=old_player.name,
                        position=old_player.position,
                        current_team_id=new_team_id,
                        active=True,
                        created_at=old_player.created_at,
                        updated_at=old_player.updated_at
                    )
                    nfl_session.add(new_player)
                    nfl_session.flush()  # Get the ID
                    player_mapping[old_player.id] = new_player.id
                else:
                    player_mapping[old_player.id] = existing_player.id
                
                progress.update(player_task, advance=1)
            
            nfl_session.commit()
            console.print(f"[green]✅ Migrated {len(old_players)} players[/green]")
            
            # Migrate Player Stats
            console.print("[cyan]📊 Migrating Player Stats...[/cyan]")
            old_stats = old_session.query(OldPlayerStats).all()
            stats_task = progress.add_task("Stats", total=len(old_stats))
            
            for old_stat in old_stats:
                # Check if stats already exist
                new_player_id = player_mapping.get(old_stat.player_id)
                if not new_player_id:
                    progress.update(stats_task, advance=1)
                    continue
                
                existing_stat = nfl_session.query(nfl_models['PlayerStats']).filter_by(
                    player_id=new_player_id,
                    season=old_stat.season
                ).first()
                
                if not existing_stat:
                    new_stat = nfl_models['PlayerStats'](
                        player_id=new_player_id,
                        season=old_stat.season,
                        week=None,  # Can be added later if available
                        games_played=old_stat.games_played,
                        games_started=old_stat.games_started,
                        
                        # Offensive stats
                        passing_yards=old_stat.passing_yards,
                        passing_touchdowns=old_stat.passing_touchdowns,
                        passing_attempts=None,  # Not in old schema
                        passing_completions=None,  # Not in old schema
                        passing_interceptions=None,  # Not in old schema
                        passer_rating=None,  # Not in old schema
                        
                        rushing_yards=old_stat.rushing_yards,
                        rushing_touchdowns=old_stat.rushing_touchdowns,
                        rushing_attempts=None,  # Not in old schema
                        rushing_fumbles=None,  # Not in old schema
                        
                        receiving_yards=old_stat.receiving_yards,
                        receiving_touchdowns=old_stat.receiving_touchdowns,
                        receptions=old_stat.receptions,
                        receiving_targets=None,  # Not in old schema
                        receiving_fumbles=None,  # Not in old schema
                        
                        # Defensive stats
                        sacks=old_stat.sacks,
                        tackles=old_stat.tackles,
                        solo_tackles=None,  # Not in old schema
                        assisted_tackles=None,  # Not in old schema
                        interceptions=old_stat.interceptions,
                        interception_yards=None,  # Not in old schema
                        interception_touchdowns=None,  # Not in old schema
                        forced_fumbles=old_stat.forced_fumbles,
                        fumble_recoveries=None,  # Not in old schema
                        pass_deflections=None,  # Not in old schema
                        
                        # Special teams
                        field_goals_made=old_stat.field_goals_made,
                        field_goals_attempted=old_stat.field_goals_attempted,
                        extra_points_made=old_stat.extra_points_made,
                        extra_points_attempted=None,  # Not in old schema
                        punts=None,  # Not in old schema
                        punt_yards=None,  # Not in old schema
                        punt_average=None,  # Not in old schema
                        
                        created_at=old_stat.created_at,
                        updated_at=old_stat.updated_at
                    )
                    nfl_session.add(new_stat)
                
                progress.update(stats_task, advance=1)
            
            nfl_session.commit()
            console.print(f"[green]✅ Migrated {len(old_stats)} player stats records[/green]")
            
            # Update career stats for all players
            console.print("[cyan]🏆 Calculating Career Stats...[/cyan]")
            players_for_career = list(player_mapping.values())
            career_task = progress.add_task("Career Stats", total=len(players_for_career))
            
            for new_player_id in players_for_career:
                try:
                    sport_db_manager.update_career_stats('NFL', new_player_id)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Failed to update career stats for player {new_player_id}: {e}[/yellow]")
                
                progress.update(career_task, advance=1)
            
            console.print(f"[green]✅ Updated career stats for {len(players_for_career)} players[/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Migration failed: {e}[/red]")
        nfl_session.rollback()
        return False
    finally:
        old_session.close()
        nfl_session.close()
    
    console.print()
    console.print("[bold green]🎉 NFL Data Migration Completed Successfully![/bold green]")
    console.print("[dim]Your existing NFL data is now in the new sport-specific database structure.[/dim]")
    console.print("[dim]The old database remains unchanged as a backup.[/dim]")
    
    return True

def verify_migration():
    """Verify that the migration was successful."""
    console.print()
    console.print("[bold blue]🔍 Verifying Migration...[/bold blue]")
    
    # Get old database counts
    old_session = old_db_manager.get_session()
    old_teams_count = old_session.query(OldTeam).count()
    old_players_count = old_session.query(OldPlayer).count()
    old_stats_count = old_session.query(OldPlayerStats).count()
    old_session.close()
    
    # Get new database counts
    nfl_session = sport_db_manager.get_session('NFL')
    nfl_models = sport_db_manager.get_models('NFL')
    
    if nfl_session and nfl_models:
        new_teams_count = nfl_session.query(nfl_models['Team']).count()
        new_players_count = nfl_session.query(nfl_models['Player']).count()
        new_stats_count = nfl_session.query(nfl_models['PlayerStats']).count()
        career_stats_count = nfl_session.query(nfl_models['CareerStats']).count()
        nfl_session.close()
        
        console.print(f"Teams: {old_teams_count} → {new_teams_count} {'✅' if old_teams_count <= new_teams_count else '❌'}")
        console.print(f"Players: {old_players_count} → {new_players_count} {'✅' if old_players_count <= new_players_count else '❌'}")
        console.print(f"Stats: {old_stats_count} → {new_stats_count} {'✅' if old_stats_count <= new_stats_count else '❌'}")
        console.print(f"Career Stats: 0 → {career_stats_count} {'✅' if career_stats_count > 0 else '❌'}")
        
        if (old_teams_count <= new_teams_count and 
            old_players_count <= new_players_count and 
            old_stats_count <= new_stats_count and 
            career_stats_count > 0):
            console.print("[bold green]✅ Migration verification passed![/bold green]")
            return True
        else:
            console.print("[bold red]❌ Migration verification failed![/bold red]")
            return False
    else:
        console.print("[red]❌ Could not access new NFL database for verification[/red]")
        return False

def create_sample_nba_data():
    """Create some sample NBA data to test the multi-sport functionality."""
    console.print()
    console.print("[bold blue]🏀 Creating Sample NBA Data...[/bold blue]")
    
    nba_session = sport_db_manager.get_session('NBA')
    nba_models = sport_db_manager.get_models('NBA')
    
    if not nba_session or not nba_models:
        console.print("[red]❌ Failed to get NBA database session or models[/red]")
        return False
    
    try:
        # Create sample NBA teams
        teams_data = [
            {"external_id": "nba_lakers", "name": "Lakers", "display_name": "Los Angeles Lakers", "abbreviation": "LAL", "city": "Los Angeles", "conference": "Western", "division": "Pacific"},
            {"external_id": "nba_warriors", "name": "Warriors", "display_name": "Golden State Warriors", "abbreviation": "GSW", "city": "San Francisco", "conference": "Western", "division": "Pacific"},
            {"external_id": "nba_celtics", "name": "Celtics", "display_name": "Boston Celtics", "abbreviation": "BOS", "city": "Boston", "conference": "Eastern", "division": "Atlantic"},
        ]
        
        team_objects = []
        for team_data in teams_data:
            existing_team = nba_session.query(nba_models['Team']).filter_by(external_id=team_data["external_id"]).first()
            if not existing_team:
                team = nba_models['Team'](**team_data)
                nba_session.add(team)
                team_objects.append(team)
        
        nba_session.flush()
        
        # Create sample NBA players
        players_data = [
            {"external_id": "nba_lebron", "name": "LeBron James", "position": "SF", "team_idx": 0},
            {"external_id": "nba_curry", "name": "Stephen Curry", "position": "PG", "team_idx": 1},
            {"external_id": "nba_tatum", "name": "Jayson Tatum", "position": "SF", "team_idx": 2},
        ]
        
        player_objects = []
        for player_data in players_data:
            existing_player = nba_session.query(nba_models['Player']).filter_by(external_id=player_data["external_id"]).first()
            if not existing_player:
                team_id = team_objects[player_data["team_idx"]].id if player_data["team_idx"] < len(team_objects) else None
                player = nba_models['Player'](
                    external_id=player_data["external_id"],
                    name=player_data["name"],
                    position=player_data["position"],
                    current_team_id=team_id,
                    active=True
                )
                nba_session.add(player)
                player_objects.append(player)
        
        nba_session.flush()
        
        # Create sample NBA stats
        for i, player in enumerate(player_objects):
            existing_stats = nba_session.query(nba_models['PlayerStats']).filter_by(
                player_id=player.id,
                season="2023-24"
            ).first()
            
            if not existing_stats:
                # Sample stats (realistic-ish values)
                stats_data = [
                    {"points": 25, "rebounds": 7, "assists": 7, "steals": 1, "blocks": 1, "three_pointers_made": 2, "field_goals_made": 9, "free_throws_made": 5, "minutes_played": 35.0, "games_played": 71},
                    {"points": 27, "rebounds": 4, "assists": 5, "steals": 1, "blocks": 0, "three_pointers_made": 4, "field_goals_made": 10, "free_throws_made": 3, "minutes_played": 33.0, "games_played": 74},
                    {"points": 27, "rebounds": 8, "assists": 5, "steals": 1, "blocks": 1, "three_pointers_made": 3, "field_goals_made": 10, "free_throws_made": 4, "minutes_played": 36.0, "games_played": 74},
                ][i]
                
                stats = nba_models['PlayerStats'](
                    player_id=player.id,
                    season="2023-24",
                    games_played=stats_data["games_played"],
                    games_started=stats_data["games_played"] - 5,  # Assume most are starts
                    minutes_played=stats_data["minutes_played"],
                    points=stats_data["points"],
                    rebounds=stats_data["rebounds"],
                    assists=stats_data["assists"],
                    steals=stats_data["steals"],
                    blocks=stats_data["blocks"],
                    three_pointers_made=stats_data["three_pointers_made"],
                    three_pointers_attempted=stats_data["three_pointers_made"] + 3,  # Assume some misses
                    field_goals_made=stats_data["field_goals_made"],
                    field_goals_attempted=stats_data["field_goals_made"] + 5,  # Assume some misses
                    free_throws_made=stats_data["free_throws_made"],
                    free_throws_attempted=stats_data["free_throws_made"] + 1,  # Assume some misses
                    turnovers=3,
                    personal_fouls=2
                )
                nba_session.add(stats)
        
        nba_session.commit()
        
        # Update career stats
        for player in player_objects:
            sport_db_manager.update_career_stats('NBA', player.id)
        
        console.print(f"[green]✅ Created {len(teams_data)} NBA teams, {len(players_data)} players, and their stats[/green]")
        console.print("[dim]Sample data: LeBron James, Stephen Curry, Jayson Tatum[/dim]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create NBA sample data: {e}[/red]")
        nba_session.rollback()
        return False
    finally:
        nba_session.close()

def main():
    """Main migration function."""
    console.print("[bold cyan]🚀 Sports Database Migration Tool[/bold cyan]")
    console.print("This will migrate your existing NFL data to the new sport-specific architecture.")
    console.print()
    
    # Step 1: Migrate NFL data
    if migrate_nfl_data():
        # Step 2: Verify migration
        if verify_migration():
            # Step 3: Create sample NBA data
            create_sample_nba_data()
            
            console.print()
            console.print("[bold green]🎉 Migration Complete![/bold green]")
            console.print()
            console.print("[bold]What's New:[/bold]")
            console.print("✅ Sport-specific databases (NFL, NBA, MLB, NHL)")
            console.print("✅ Optimized schemas for each sport")
            console.print("✅ Universal stat retriever with cache → database → API fallback")
            console.print("✅ Easy to add new sports")
            console.print("✅ Your existing NFL data preserved and enhanced")
            console.print("✅ Sample NBA data for testing")
            console.print()
            console.print("[bold]You can now ask:[/bold]")
            console.print("🏈 'Who has the most passing yards?' (NFL)")
            console.print("🏀 'Who leads the NBA in points?' (NBA)")
            console.print("🏈 'Lamar Jackson vs Josh Allen' (NFL)")
            console.print("🏀 'LeBron James vs Stephen Curry' (NBA)")
            
        else:
            console.print("[red]Migration verification failed. Please check the logs.[/red]")
            return False
    else:
        console.print("[red]Migration failed. Please check the logs.[/red]")
        return False
    
    return True

if __name__ == "__main__":
    main() 