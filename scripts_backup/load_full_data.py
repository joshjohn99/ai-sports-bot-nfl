#!/usr/bin/env python3
"""
Comprehensive script to load all NFL data into the database.
This will fetch teams, rosters, and player stats for the current season.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
from datetime import datetime
from urllib.parse import urljoin
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.db.models import db_manager, Player, Team, PlayerStats, CareerStats
from src.sports_bot.config.api_config import api_config

console = Console()

def extract_stat_value(stats_data, stat_name):
    """Extract a specific stat value from the complex API response structure."""
    try:
        # The API response has a complex nested structure
        # Navigate through: statistics -> splits -> categories -> stats
        if isinstance(stats_data, dict):
            splits = stats_data.get('statistics', {}).get('splits', {})
            categories = splits.get('categories', [])
            
            for category in categories:
                stats = category.get('stats', [])
                for stat in stats:
                    if stat.get('name') == stat_name:
                        return stat.get('value', 0)
        
        return 0  # Default value if stat not found
    except (KeyError, AttributeError, TypeError):
        return 0

def load_full_nfl_data():
    """Load comprehensive NFL data into the database."""
    console.print("[bold blue]🏈 Starting Comprehensive NFL Data Load 🏈[/bold blue]")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    db_manager.init_db()
    session = db_manager.get_session()
    
    try:
        # 1. FETCH ALL TEAMS
        console.print("\n[cyan]📋 Step 1: Fetching all NFL teams...[/cyan]")
        headers = api_config['NFL']['headers']
        teams_url = urljoin(
            api_config['NFL']['base_url'],
            api_config['NFL']['endpoints']['AllTeams']
        )
        
        console.print(f"[dim]Making request to: {teams_url}[/dim]")
        response = requests.get(teams_url, headers=headers, timeout=30)
        response.raise_for_status()
        teams_data = response.json()
        
        console.print(f"[green]✓ Retrieved {len(teams_data)} teams from API[/green]")
        
        teams_added = 0
        teams_updated = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing teams...", total=len(teams_data))
            
            for team_data in teams_data:
                team_info = team_data.get('team', team_data)
                external_id = str(team_info.get('id'))
                
                # Check if team already exists
                existing_team = session.query(Team).filter_by(external_id=external_id).first()
                
                if existing_team:
                    # Update existing team
                    if (existing_team.name != team_info.get('name') or
                        existing_team.display_name != team_info.get('displayName') or
                        existing_team.abbreviation != team_info.get('abbreviation')):
                        
                        existing_team.name = team_info.get('name')
                        existing_team.display_name = team_info.get('displayName')
                        existing_team.abbreviation = team_info.get('abbreviation')
                        teams_updated += 1
                else:
                    # Add new team
                    team = Team(
                        external_id=external_id,
                        name=team_info.get('name'),
                        display_name=team_info.get('displayName'),
                        abbreviation=team_info.get('abbreviation')
                    )
                    session.add(team)
                    teams_added += 1
                
                progress.advance(task)
            
            session.commit()
        
        console.print(f"[green]✓ Teams processed: {teams_added} added, {teams_updated} updated[/green]")
        
        # 2. FETCH PLAYERS FOR EACH TEAM
        console.print("\n[cyan]👥 Step 2: Fetching players for all teams...[/cyan]")
        teams = session.query(Team).all()
        
        total_players_added = 0
        total_players_updated = 0
        
        with Progress() as progress:
            team_task = progress.add_task("[cyan]Processing team rosters...", total=len(teams))
            
            for team in teams:
                console.print(f"[dim]Fetching roster for {team.name} ({team.abbreviation})...[/dim]")
                
                roster_url = urljoin(
                    api_config['NFL']['base_url'],
                    api_config['NFL']['endpoints']['PlayersByTeam']
                )
                
                try:
                    response = requests.get(
                        roster_url,
                        headers=headers,
                        params={'id': team.external_id},
                        timeout=30
                    )
                    response.raise_for_status()
                    roster_data = response.json()
                    
                    # Process players - handle different API response structures
                    players = []
                    if isinstance(roster_data, list):
                        players = roster_data
                    elif isinstance(roster_data, dict):
                        athletes = roster_data.get('athletes', [])
                        if athletes and isinstance(athletes[0], dict):
                            if 'items' in athletes[0]:
                                # Grouped by position structure
                                for group in athletes:
                                    players.extend(group.get('items', []))
                            else:
                                # Direct list structure
                                players = athletes
                    
                    players_added_this_team = 0
                    players_updated_this_team = 0
                    
                    for player_data in players:
                        external_id = str(player_data.get('id'))
                        
                        # Check if player already exists
                        existing_player = session.query(Player).filter_by(external_id=external_id).first()
                        
                        if existing_player:
                            # Update existing player
                            if (existing_player.name != player_data.get('fullName') or
                                existing_player.position != player_data.get('position', {}).get('abbreviation') or
                                existing_player.current_team_id != team.id):
                                
                                existing_player.name = player_data.get('fullName')
                                existing_player.position = player_data.get('position', {}).get('abbreviation')
                                existing_player.current_team_id = team.id
                                players_updated_this_team += 1
                        else:
                            # Add new player
                            player = Player(
                                external_id=external_id,
                                name=player_data.get('fullName'),
                                position=player_data.get('position', {}).get('abbreviation'),
                                current_team_id=team.id
                            )
                            session.add(player)
                            players_added_this_team += 1
                    
                    total_players_added += players_added_this_team
                    total_players_updated += players_updated_this_team
                    
                    console.print(f"[green]✓ {team.abbreviation}: {players_added_this_team} added, {players_updated_this_team} updated[/green]")
                    
                except Exception as e:
                    console.print(f"[yellow]⚠ Warning: Failed to fetch roster for {team.name}: {str(e)}[/yellow]")
                
                # Commit after each team to avoid memory issues
                session.commit()
                progress.advance(team_task)
                
                # Small delay to be respectful to the API
                time.sleep(0.5)
        
        console.print(f"[green]✓ Players processed: {total_players_added} added, {total_players_updated} updated[/green]")
        
        # 3. FETCH PLAYER STATS FOR CURRENT SEASON
        console.print("\n[cyan]📊 Step 3: Fetching player stats for current season...[/cyan]")
        current_year = datetime.now().year
        if datetime.now().month < 8:  # Before August = previous season
            current_year -= 1
        
        console.print(f"[dim]Fetching stats for {current_year} season...[/dim]")
        
        players = session.query(Player).filter(Player.current_team_id.isnot(None)).all()
        total_players = len(players)
        stats_added = 0
        stats_updated = 0
        stats_failed = 0
        
        with Progress() as progress:
            player_task = progress.add_task("[cyan]Processing player stats...", total=total_players)
            
            for i, player in enumerate(players):
                # Check if player stats already exist for this season
                existing_stats = session.query(PlayerStats).filter_by(
                    player_id=player.id,
                    season=str(current_year)
                ).first()
                
                if existing_stats:
                    # Skip if stats already exist for this season
                    progress.advance(player_task)
                    continue
                
                try:
                    stats_url = urljoin(
                        api_config['NFL']['base_url'],
                        api_config['NFL']['endpoints']['PlayerStats']
                    )
                    response = requests.get(
                        stats_url,
                        headers=headers,
                        params={
                            'id': player.external_id,
                            'year': str(current_year)
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        stats_data = response.json()
                        
                        # Create player stats
                        stats = PlayerStats(
                            player_id=player.id,
                            season=str(current_year),
                            games_played=extract_stat_value(stats_data, 'gamesPlayed'),
                            games_started=extract_stat_value(stats_data, 'gamesStarted'),
                            passing_yards=extract_stat_value(stats_data, 'passingYards'),
                            passing_touchdowns=extract_stat_value(stats_data, 'passingTouchdowns'),
                            rushing_yards=extract_stat_value(stats_data, 'rushingYards'),
                            rushing_touchdowns=extract_stat_value(stats_data, 'rushingTouchdowns'),
                            receiving_yards=extract_stat_value(stats_data, 'receivingYards'),
                            receptions=extract_stat_value(stats_data, 'receptions'),
                            receiving_touchdowns=extract_stat_value(stats_data, 'receivingTouchdowns'),
                            sacks=extract_stat_value(stats_data, 'sacks'),
                            tackles=extract_stat_value(stats_data, 'tackles'),
                            interceptions=extract_stat_value(stats_data, 'interceptions'),
                            forced_fumbles=extract_stat_value(stats_data, 'forcedFumbles'),
                            field_goals_made=extract_stat_value(stats_data, 'fieldGoalsMade'),
                            field_goals_attempted=extract_stat_value(stats_data, 'fieldGoalsAttempted'),
                            extra_points_made=extract_stat_value(stats_data, 'extraPointsMade')
                        )
                        session.add(stats)
                        stats_added += 1
                        
                        if i % 50 == 0:  # Show progress every 50 players
                            console.print(f"[dim]Processed {i}/{total_players} players...[/dim]")
                    else:
                        stats_failed += 1
                        
                except Exception as e:
                    stats_failed += 1
                    if stats_failed <= 5:  # Only show first few errors
                        console.print(f"[yellow]⚠ Warning: Failed to fetch stats for {player.name}: {str(e)}[/yellow]")
                
                progress.advance(player_task)
                
                # Commit every 25 players to avoid memory issues
                if (i + 1) % 25 == 0:
                    session.commit()
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
            
            # Final commit
            session.commit()
        
        console.print(f"[green]✓ Player stats processed: {stats_added} added, {stats_failed} failed[/green]")
        
        # 4. UPDATE CAREER STATS
        console.print("\n[cyan]🏆 Step 4: Updating career stats...[/cyan]")
        players_with_stats = session.query(Player).join(PlayerStats).distinct().all()
        
        with Progress() as progress:
            career_task = progress.add_task("[cyan]Processing career stats...", total=len(players_with_stats))
            
            for player in players_with_stats:
                try:
                    db_manager.update_career_stats(player.id)
                except Exception as e:
                    console.print(f"[yellow]⚠ Warning: Failed to update career stats for {player.name}: {str(e)}[/yellow]")
                
                progress.advance(career_task)
        
        # FINAL SUMMARY
        console.print("\n[bold green]🎉 NFL Data Load Complete! 🎉[/bold green]")
        
        # Get final counts
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats Records: {final_stats}")
        
        # Test the disambiguation
        console.print(f"\n[bold cyan]🔍 Testing Player Search:[/bold cyan]")
        lamar_players = session.query(Player).filter(Player.name.ilike("%Lamar Jackson%")).all()
        if lamar_players:
            console.print("Found Lamar Jackson players:")
            for player in lamar_players:
                team_name = player.current_team.abbreviation if player.current_team else "No Team"
                console.print(f"• {player.name} ({player.position}) - {team_name}")
        else:
            console.print("No Lamar Jackson players found - this might indicate an issue with data loading")
        
        console.print(f"\n[green]✅ Database is now ready for queries![/green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error during data load: {str(e)}[/bold red]")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_full_nfl_data() 