"""
Script to fetch initial data from the NFL API and store it in the database.

Update Schedule:
- Teams: Once per season (or when there's expansion/relocation news)
- Rosters: Weekly (teams make roster moves throughout the season)
- Player Stats: 
  - During season (Sept-Jan): Every 6 hours
  - Off-season: Daily
- Career Stats: Recalculated after each player stats update
"""

import os
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
from datetime import datetime
from urllib.parse import urljoin

from sports_bot.config.api_config import api_config
from sports_bot.db.models import db_manager, Player, Team, PlayerStats

console = Console()

def fetch_initial_data():
    """Fetch initial data from the API and store it in the database."""
    console.print("[bold blue]Starting Initial Data Fetch[/bold blue]")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    db_manager.init_db()
    session = db_manager.get_session()
    
    try:
        # 1. Fetch all teams
        console.print("\n[cyan]Fetching teams...[/cyan]")
        headers = api_config['NFL']['headers']
        teams_url = urljoin(
            api_config['NFL']['base_url'],
            api_config['NFL']['endpoints']['AllTeams']
        )
        
        response = requests.get(teams_url, headers=headers)
        response.raise_for_status()
        teams_data = response.json()
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing teams...", total=len(teams_data))
            
            for team_data in teams_data:
                team_info = team_data.get('team', team_data)
                team = Team(
                    external_id=str(team_info.get('id')),
                    name=team_info.get('name'),
                    display_name=team_info.get('displayName'),
                    abbreviation=team_info.get('abbreviation')
                )
                session.add(team)
                progress.advance(task)
            
            session.commit()
        
        console.print(f"[green]✓ Successfully imported {len(teams_data)} teams[/green]")
        
        # 2. Fetch players for each team
        console.print("\n[cyan]Fetching players by team...[/cyan]")
        teams = session.query(Team).all()
        
        with Progress() as progress:
            team_task = progress.add_task("[cyan]Processing teams...", total=len(teams))
            
            for team in teams:
                roster_url = urljoin(
                    api_config['NFL']['base_url'],
                    api_config['NFL']['endpoints']['PlayersByTeam']
                )
                response = requests.get(
                    roster_url,
                    headers=headers,
                    params={'id': team.external_id}
                )
                response.raise_for_status()
                roster_data = response.json()
                
                # Process players
                players = roster_data.get('athletes', [])
                if players and isinstance(players[0], dict) and players[0].get('items'):
                    players = players[0].get('items', [])
                
                for player_data in players:
                    player = Player(
                        external_id=str(player_data.get('id')),
                        name=player_data.get('fullName'),
                        position=player_data.get('position', {}).get('abbreviation'),
                        current_team_id=team.id
                    )
                    session.add(player)
                
                session.commit()
                progress.advance(team_task)
        
        # 3. Fetch stats for current season
        console.print("\n[cyan]Fetching player stats...[/cyan]")
        current_year = datetime.now().year
        if datetime.now().month < 8:
            current_year -= 1
        
        players = session.query(Player).all()
        total_players = len(players)
        processed = 0
        
        with Progress() as progress:
            player_task = progress.add_task("[cyan]Processing players...", total=total_players)
            
            for player in players:
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
                    }
                )
                
                if response.status_code == 200:
                    stats_data = response.json()
                    
                    stats = PlayerStats(
                        player_id=player.id,
                        season=str(current_year),
                        games_played=stats_data.get('gamesPlayed'),
                        games_started=stats_data.get('gamesStarted'),
                        passing_yards=stats_data.get('passingYards'),
                        passing_touchdowns=stats_data.get('passingTouchdowns'),
                        rushing_yards=stats_data.get('rushingYards'),
                        rushing_touchdowns=stats_data.get('rushingTouchdowns'),
                        receiving_yards=stats_data.get('receivingYards'),
                        receptions=stats_data.get('receptions'),
                        receiving_touchdowns=stats_data.get('receivingTouchdowns'),
                        sacks=stats_data.get('sacks'),
                        tackles=stats_data.get('tackles'),
                        interceptions=stats_data.get('interceptions'),
                        forced_fumbles=stats_data.get('forcedFumbles'),
                        field_goals_made=stats_data.get('fieldGoalsMade'),
                        field_goals_attempted=stats_data.get('fieldGoalsAttempted'),
                        extra_points_made=stats_data.get('extraPointsMade')
                    )
                    session.add(stats)
                    
                    # Commit every 10 players to avoid memory issues
                    processed += 1
                    if processed % 10 == 0:
                        session.commit()
                
                progress.advance(player_task)
            
            # Final commit
            session.commit()
        
        # 4. Update career stats
        console.print("\n[cyan]Updating career stats...[/cyan]")
        with Progress() as progress:
            career_task = progress.add_task("[cyan]Processing career stats...", total=total_players)
            
            for player in players:
                db_manager.update_career_stats(player.id)
                progress.advance(career_task)
        
        console.print("\n[bold green]✓ Initial data fetch completed successfully![/bold green]")
        console.print("\nRecommended Update Schedule:")
        console.print("- Teams: Once per season (or when there's expansion/relocation news)")
        console.print("- Rosters: Weekly (teams make roster moves throughout the season)")
        console.print("- Player Stats:")
        console.print("  • During season (Sept-Jan): Every 6 hours")
        console.print("  • Off-season: Daily")
        console.print("- Career Stats: Recalculated after each player stats update")
        
    except Exception as e:
        console.print(f"[bold red]Error during data fetch: {str(e)}[/bold red]")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fetch_initial_data() 