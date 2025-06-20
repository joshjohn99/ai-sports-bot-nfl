"""
Script to handle automated data updates based on the recommended schedule.
"""

import os
import time
from datetime import datetime
import backoff
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import schedule
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError
import logging
from pathlib import Path

from sports_bot.config.api_config import api_config
from sports_bot.db.models import db_manager, Player, Team, PlayerStats, CareerStats
from sports_bot.data.fetch_initial_data import fetch_initial_data
from .data_validators import (
    validate_team_data,
    validate_player_data,
    validate_stats_data,
    validate_career_stats,
    ValidationError
)

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "update_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_service")

console = Console()

class UpdateError(Exception):
    """Custom exception for update errors."""
    pass

def is_nfl_season():
    """Check if we're currently in NFL season (September through January)."""
    month = datetime.now().month
    return month >= 9 or month <= 1

@backoff.on_exception(
    backoff.expo,
    (RequestException, SQLAlchemyError),
    max_tries=5,
    max_time=300,  # 5 minutes max total time
    on_backoff=lambda details: logger.warning(f"Retry attempt {details['tries']} after {details['wait']} seconds")
)
def make_api_request(url: str, headers: dict, params: dict = None) -> dict:
    """Make API request with retry logic."""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise

def safe_commit(session):
    """Safely commit database changes."""
    try:
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database commit failed: {str(e)}")
        session.rollback()
        raise

def update_teams():
    """Update team information."""
    logger.info("Starting team update")
    console.print("\n[cyan]Updating teams...[/cyan]")
    session = db_manager.get_session()
    
    try:
        headers = api_config['NFL']['headers']
        teams_url = urljoin(
            api_config['NFL']['base_url'],
            api_config['NFL']['endpoints']['AllTeams']
        )
        
        teams_data = make_api_request(teams_url, headers)
        changes_made = False
        validation_errors = []
        
        for team_data in teams_data:
            team_info = team_data.get('team', team_data)
            
            # Validate team data
            is_valid, errors = validate_team_data(team_info)
            if not is_valid:
                validation_errors.append(f"Team {team_info.get('name', 'Unknown')}: {', '.join(errors)}")
                continue
                
            external_id = str(team_info.get('id'))
            
            # Update or create team
            team = session.query(Team).filter_by(external_id=external_id).first()
            if team:
                if (team.name != team_info.get('name') or
                    team.display_name != team_info.get('displayName') or
                    team.abbreviation != team_info.get('abbreviation')):
                    
                    team.name = team_info.get('name')
                    team.display_name = team_info.get('displayName')
                    team.abbreviation = team_info.get('abbreviation')
                    changes_made = True
                    logger.info(f"Updated team: {team.name}")
            else:
                team = Team(
                    external_id=external_id,
                    name=team_info.get('name'),
                    display_name=team_info.get('displayName'),
                    abbreviation=team_info.get('abbreviation')
                )
                session.add(team)
                changes_made = True
                logger.info(f"Added new team: {team.name}")
        
        if validation_errors:
            console.print("\n[yellow]Validation warnings:[/yellow]")
            for error in validation_errors:
                console.print(f"[yellow]- {error}[/yellow]")
        
        if changes_made:
            safe_commit(session)
            console.print("[green]✓ Teams updated successfully[/green]")
        else:
            console.print("[green]✓ Teams already up to date[/green]")
        
    except Exception as e:
        logger.error(f"Error updating teams: {str(e)}")
        console.print(f"[red]Error updating teams: {str(e)}[/red]")
        raise UpdateError(f"Team update failed: {str(e)}")
    finally:
        session.close()

def update_rosters():
    """Update team rosters."""
    logger.info("Starting roster update")
    console.print("\n[cyan]Updating rosters...[/cyan]")
    session = db_manager.get_session()
    
    try:
        headers = api_config['NFL']['headers']
        teams = session.query(Team).all()
        changes_made = False
        validation_errors = []
        
        for team in teams:
            try:
                roster_url = urljoin(
                    api_config['NFL']['base_url'],
                    api_config['NFL']['endpoints']['PlayersByTeam']
                )
                roster_data = make_api_request(roster_url, headers, {'id': team.external_id})
                
                # Process players
                players = roster_data.get('athletes', [])
                if players and isinstance(players[0], dict) and players[0].get('items'):
                    players = players[0].get('items', [])
                
                # Track current roster for cleanup
                current_roster_ids = set()
                
                for player_data in players:
                    # Validate player data
                    is_valid, errors = validate_player_data(player_data)
                    if not is_valid:
                        validation_errors.append(f"Player {player_data.get('fullName', 'Unknown')}: {', '.join(errors)}")
                        continue
                        
                    external_id = str(player_data.get('id'))
                    current_roster_ids.add(external_id)
                    
                    # Update or create player
                    player = session.query(Player).filter_by(external_id=external_id).first()
                    if player:
                        if (player.name != player_data.get('fullName') or
                            player.position != player_data.get('position', {}).get('abbreviation') or
                            player.current_team_id != team.id):
                            
                            player.name = player_data.get('fullName')
                            player.position = player_data.get('position', {}).get('abbreviation')
                            player.current_team_id = team.id
                            changes_made = True
                            logger.info(f"Updated player: {player.name}")
                    else:
                        player = Player(
                            external_id=external_id,
                            name=player_data.get('fullName'),
                            position=player_data.get('position', {}).get('abbreviation'),
                            current_team_id=team.id
                        )
                        session.add(player)
                        changes_made = True
                        logger.info(f"Added new player: {player.name}")
                
                # Update players no longer on the team
                former_players = session.query(Player).filter_by(current_team_id=team.id).all()
                for player in former_players:
                    if player.external_id not in current_roster_ids:
                        player.current_team_id = None
                        changes_made = True
                        logger.info(f"Removed {player.name} from {team.name}")
                
                if changes_made:
                    safe_commit(session)
                
            except Exception as e:
                logger.error(f"Error updating roster for {team.name}: {str(e)}")
                console.print(f"[yellow]Warning: Failed to update roster for {team.name}[/yellow]")
                continue
        
        if validation_errors:
            console.print("\n[yellow]Validation warnings:[/yellow]")
            for error in validation_errors:
                console.print(f"[yellow]- {error}[/yellow]")
        
        if changes_made:
            console.print("[green]✓ Rosters updated successfully[/green]")
        else:
            console.print("[green]✓ Rosters already up to date[/green]")
        
    except Exception as e:
        logger.error(f"Error updating rosters: {str(e)}")
        console.print(f"[red]Error updating rosters: {str(e)}[/red]")
        raise UpdateError(f"Roster update failed: {str(e)}")
    finally:
        session.close()

def update_player_stats():
    """Update player statistics."""
    logger.info("Starting player stats update")
    console.print("\n[cyan]Updating player stats...[/cyan]")
    session = db_manager.get_session()
    
    try:
        headers = api_config['NFL']['headers']
        current_year = datetime.now().year
        if datetime.now().month < 8:
            current_year -= 1
            
        players = session.query(Player).filter(Player.current_team_id.isnot(None)).all()
        changes_made = False
        validation_errors = []
        
        for player in players:
            try:
                stats_url = urljoin(
                    api_config['NFL']['base_url'],
                    api_config['NFL']['endpoints']['PlayerStats']
                )
                stats_data = make_api_request(
                    stats_url,
                    headers,
                    {'id': player.external_id, 'year': str(current_year)}
                )
                
                # Validate stats data
                is_valid, errors = validate_stats_data(stats_data, player.position)
                if not is_valid:
                    validation_errors.append(f"Stats for {player.name}: {', '.join(errors)}")
                    continue
                
                # Update or create stats
                stats = session.query(PlayerStats).filter_by(
                    player_id=player.id,
                    season=str(current_year)
                ).first()
                
                new_stats = {
                    'games_played': stats_data.get('gamesPlayed'),
                    'games_started': stats_data.get('gamesStarted'),
                    'passing_yards': stats_data.get('passingYards'),
                    'passing_touchdowns': stats_data.get('passingTouchdowns'),
                    'rushing_yards': stats_data.get('rushingYards'),
                    'rushing_touchdowns': stats_data.get('rushingTouchdowns'),
                    'receiving_yards': stats_data.get('receivingYards'),
                    'receptions': stats_data.get('receptions'),
                    'receiving_touchdowns': stats_data.get('receivingTouchdowns'),
                    'sacks': stats_data.get('sacks'),
                    'tackles': stats_data.get('tackles'),
                    'interceptions': stats_data.get('interceptions'),
                    'forced_fumbles': stats_data.get('forcedFumbles'),
                    'field_goals_made': stats_data.get('fieldGoalsMade'),
                    'field_goals_attempted': stats_data.get('fieldGoalsAttempted'),
                    'extra_points_made': stats_data.get('extraPointsMade')
                }
                
                if stats:
                    # Check if any stats have changed
                    stats_changed = False
                    for key, value in new_stats.items():
                        if getattr(stats, key) != value:
                            setattr(stats, key, value)
                            stats_changed = True
                    
                    if stats_changed:
                        changes_made = True
                        logger.info(f"Updated stats for {player.name}")
                else:
                    stats = PlayerStats(
                        player_id=player.id,
                        season=str(current_year),
                        **new_stats
                    )
                    session.add(stats)
                    changes_made = True
                    logger.info(f"Added new stats for {player.name}")
                
                # Update career stats
                try:
                    db_manager.update_career_stats(player.id)
                    
                    # Validate career stats
                    career_stats = session.query(CareerStats).filter_by(player_id=player.id).first()
                    if career_stats:
                        is_valid, errors = validate_career_stats(career_stats.__dict__)
                        if not is_valid:
                            validation_errors.append(f"Career stats for {player.name}: {', '.join(errors)}")
                            
                except Exception as e:
                    logger.error(f"Failed to update career stats for {player.name}: {str(e)}")
                    validation_errors.append(f"Career stats update failed for {player.name}")
                
                # Commit every 10 players
                if changes_made and len(session.new) + len(session.dirty) >= 10:
                    safe_commit(session)
            
            except Exception as e:
                logger.error(f"Failed to update stats for {player.name}: {str(e)}")
                validation_errors.append(f"Stats update failed for {player.name}")
                continue
        
        # Final commit if any changes pending
        if changes_made:
            safe_commit(session)
            console.print("[green]✓ Player stats updated successfully[/green]")
        else:
            console.print("[green]✓ Player stats already up to date[/green]")
        
        # Report any validation errors
        if validation_errors:
            console.print("\n[yellow]Validation warnings:[/yellow]")
            for error in validation_errors:
                console.print(f"[yellow]- {error}[/yellow]")
        
    except Exception as e:
        logger.error(f"Error updating player stats: {str(e)}")
        console.print(f"[red]Error updating player stats: {str(e)}[/red]")
        raise UpdateError(f"Player stats update failed: {str(e)}")
    finally:
        session.close()

def run_updates():
    """Run all updates based on schedule."""
    logger.info("Running scheduled updates")
    console.print("[bold blue]Running scheduled updates...[/bold blue]")
    
    try:
        # Update teams (once per day, will only change if there are updates)
        update_teams()
        
        # Update rosters
        update_rosters()
        
        # Update player stats
        update_player_stats()
        
        logger.info("Scheduled updates completed successfully")
        
    except Exception as e:
        logger.error(f"Scheduled updates failed: {str(e)}")
        console.print(f"[red]Error during scheduled updates: {str(e)}[/red]")
        # Don't raise here - let the service continue running

def main():
    """Main function to run the update scheduler."""
    console.print("[bold blue]Starting NFL Data Update Service[/bold blue]")
    logger.info("Starting NFL Data Update Service")
    
    # Load environment variables
    load_dotenv()
    
    # Check if database exists and has data
    session = db_manager.get_session()
    try:
        team_count = session.query(Team).count()
        if team_count == 0:
            logger.info("No data found in database. Running initial data fetch...")
            console.print("[yellow]No data found in database. Running initial data fetch...[/yellow]")
            fetch_initial_data()
    except Exception as e:
        logger.error(f"Failed to check database: {str(e)}")
        console.print(f"[red]Error checking database: {str(e)}[/red]")
        return
    finally:
        session.close()
    
    # Schedule updates
    if is_nfl_season():
        # During season: update stats every 6 hours
        schedule.every(6).hours.do(run_updates)
        logger.info("Configured for in-season update schedule (every 6 hours)")
    else:
        # Off-season: update stats daily
        schedule.every().day.at("00:00").do(run_updates)
        logger.info("Configured for off-season update schedule (daily)")
    
    console.print("\n[green]Update scheduler started with the following schedule:[/green]")
    console.print("- Teams: Daily check for updates")
    console.print("- Rosters: Every Monday at 00:00")
    if is_nfl_season():
        console.print("- Player Stats: Every 6 hours (in-season)")
    else:
        console.print("- Player Stats: Daily at 00:00 (off-season)")
    console.print("- Career Stats: Updated after each player stats update")
    console.print("\n[cyan]Logs will be written to: logs/update_service.log[/cyan]")
    
    # Run forever
    failures = 0
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            failures = 0  # Reset failure count on success
        except Exception as e:
            failures += 1
            logger.error(f"Service error (attempt {failures}): {str(e)}")
            console.print(f"[red]Service error: {str(e)}[/red]")
            
            if failures >= 5:
                logger.critical("Too many consecutive failures. Service stopping.")
                console.print("[bold red]Too many consecutive failures. Service stopping.[/bold red]")
                break
            
            # Wait before retrying (exponential backoff)
            retry_delay = min(300, 30 * (2 ** (failures - 1)))  # Max 5 minutes
            logger.info(f"Retrying in {retry_delay} seconds...")
            console.print(f"[yellow]Retrying in {retry_delay} seconds...[/yellow]")
            time.sleep(retry_delay)

if __name__ == "__main__":
    main() 