#!/usr/bin/env python3
"""
Comprehensive NBA data loader that populates the database with real NBA players and stats.
"""

import sys
import os
from pathlib import Path
from rich.console import Console

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.database.sport_models import sport_db_manager

console = Console()

def load_comprehensive_nba_data():
    """Load comprehensive NBA data into the database."""
    console.print("[bold blue]🏀 Loading Comprehensive NBA Data 🏀[/bold blue]")
    
    # Get NBA database session
    session = sport_db_manager.get_session('NBA')
    models = sport_db_manager.get_models('NBA')
    
    if not session or not models:
        console.print("[red]❌ Could not connect to NBA database[/red]")
        return
    
    Team = models['Team']
    Player = models['Player']
    PlayerStats = models['PlayerStats']
    
    try:
        # 1. LOAD ALL 30 NBA TEAMS
        console.print("\n[cyan]📋 Step 1: Loading all 30 NBA teams...[/cyan]")
        
        nba_teams = [
            {'id': '1', 'name': 'Atlanta Hawks', 'abbreviation': 'ATL'},
            {'id': '2', 'name': 'Boston Celtics', 'abbreviation': 'BOS'},
            {'id': '3', 'name': 'Brooklyn Nets', 'abbreviation': 'BKN'},
            {'id': '4', 'name': 'Charlotte Hornets', 'abbreviation': 'CHA'},
            {'id': '5', 'name': 'Chicago Bulls', 'abbreviation': 'CHI'},
            {'id': '6', 'name': 'Cleveland Cavaliers', 'abbreviation': 'CLE'},
            {'id': '7', 'name': 'Dallas Mavericks', 'abbreviation': 'DAL'},
            {'id': '8', 'name': 'Denver Nuggets', 'abbreviation': 'DEN'},
            {'id': '9', 'name': 'Detroit Pistons', 'abbreviation': 'DET'},
            {'id': '10', 'name': 'Golden State Warriors', 'abbreviation': 'GSW'},
            {'id': '11', 'name': 'Houston Rockets', 'abbreviation': 'HOU'},
            {'id': '12', 'name': 'Indiana Pacers', 'abbreviation': 'IND'},
            {'id': '13', 'name': 'LA Clippers', 'abbreviation': 'LAC'},
            {'id': '14', 'name': 'Los Angeles Lakers', 'abbreviation': 'LAL'},
            {'id': '15', 'name': 'Memphis Grizzlies', 'abbreviation': 'MEM'},
            {'id': '16', 'name': 'Miami Heat', 'abbreviation': 'MIA'},
            {'id': '17', 'name': 'Milwaukee Bucks', 'abbreviation': 'MIL'},
            {'id': '18', 'name': 'Minnesota Timberwolves', 'abbreviation': 'MIN'},
            {'id': '19', 'name': 'New Orleans Pelicans', 'abbreviation': 'NOP'},
            {'id': '20', 'name': 'New York Knicks', 'abbreviation': 'NYK'},
            {'id': '21', 'name': 'Oklahoma City Thunder', 'abbreviation': 'OKC'},
            {'id': '22', 'name': 'Orlando Magic', 'abbreviation': 'ORL'},
            {'id': '23', 'name': 'Philadelphia 76ers', 'abbreviation': 'PHI'},
            {'id': '24', 'name': 'Phoenix Suns', 'abbreviation': 'PHX'},
            {'id': '25', 'name': 'Portland Trail Blazers', 'abbreviation': 'POR'},
            {'id': '26', 'name': 'Sacramento Kings', 'abbreviation': 'SAC'},
            {'id': '27', 'name': 'San Antonio Spurs', 'abbreviation': 'SAS'},
            {'id': '28', 'name': 'Toronto Raptors', 'abbreviation': 'TOR'},
            {'id': '29', 'name': 'Utah Jazz', 'abbreviation': 'UTA'},
            {'id': '30', 'name': 'Washington Wizards', 'abbreviation': 'WAS'}
        ]
        
        teams_added = 0
        for team_data in nba_teams:
            existing_team = session.query(Team).filter_by(external_id=team_data['id']).first()
            if not existing_team:
                team = Team(
                    external_id=team_data['id'],
                    name=team_data['name'],
                    display_name=team_data['name'],
                    abbreviation=team_data['abbreviation']
                )
                session.add(team)
                teams_added += 1
        
        session.commit()
        console.print(f"[green]✅ Added {teams_added} NBA teams[/green]")
        
        # 2. LOAD COMPREHENSIVE NBA PLAYERS
        console.print("\n[cyan]👥 Step 2: Loading NBA players...[/cyan]")
        
        # Comprehensive list of current NBA stars and popular players
        nba_players = [
            # Superstars
            {'name': 'LeBron James', 'team': 'LAL', 'position': 'SF'},
            {'name': 'Stephen Curry', 'team': 'GSW', 'position': 'PG'},
            {'name': 'Kevin Durant', 'team': 'PHX', 'position': 'SF'},
            {'name': 'Giannis Antetokounmpo', 'team': 'MIL', 'position': 'PF'},
            {'name': 'Luka Doncic', 'team': 'DAL', 'position': 'PG'},
            {'name': 'Jayson Tatum', 'team': 'BOS', 'position': 'SF'},
            {'name': 'Nikola Jokic', 'team': 'DEN', 'position': 'C'},
            {'name': 'Joel Embiid', 'team': 'PHI', 'position': 'C'},
            
            # Rising Stars
            {'name': 'Ja Morant', 'team': 'MEM', 'position': 'PG'},
            {'name': 'Anthony Edwards', 'team': 'MIN', 'position': 'SG'},
            {'name': 'Paolo Banchero', 'team': 'ORL', 'position': 'PF'},
            {'name': 'Scottie Barnes', 'team': 'TOR', 'position': 'SF'},
            {'name': 'Evan Mobley', 'team': 'CLE', 'position': 'PF'},
            {'name': 'Cade Cunningham', 'team': 'DET', 'position': 'PG'},
            {'name': 'Franz Wagner', 'team': 'ORL', 'position': 'SF'},
            
            # Established Stars
            {'name': 'Jimmy Butler', 'team': 'MIA', 'position': 'SF'},
            {'name': 'Kawhi Leonard', 'team': 'LAC', 'position': 'SF'},
            {'name': 'Paul George', 'team': 'LAC', 'position': 'SF'},
            {'name': 'Damian Lillard', 'team': 'MIL', 'position': 'PG'},
            {'name': 'Donovan Mitchell', 'team': 'CLE', 'position': 'SG'},
            {'name': 'Devin Booker', 'team': 'PHX', 'position': 'SG'},
            {'name': 'Trae Young', 'team': 'ATL', 'position': 'PG'},
            {'name': 'Zion Williamson', 'team': 'NOP', 'position': 'PF'},
            
            # More Current Players
            {'name': 'De\'Aaron Fox', 'team': 'SAC', 'position': 'PG'},
            {'name': 'Tyrese Haliburton', 'team': 'IND', 'position': 'PG'},
            {'name': 'Shai Gilgeous-Alexander', 'team': 'OKC', 'position': 'PG'},
            {'name': 'Jalen Brunson', 'team': 'NYK', 'position': 'PG'},
            {'name': 'Tyler Herro', 'team': 'MIA', 'position': 'SG'},
            {'name': 'Alperen Sengun', 'team': 'HOU', 'position': 'C'},
            
            # Veterans
            {'name': 'Chris Paul', 'team': 'GSW', 'position': 'PG'},
            {'name': 'Russell Westbrook', 'team': 'LAC', 'position': 'PG'},
            {'name': 'James Harden', 'team': 'LAC', 'position': 'SG'},
            {'name': 'Klay Thompson', 'team': 'DAL', 'position': 'SG'},
            {'name': 'Draymond Green', 'team': 'GSW', 'position': 'PF'}
        ]
        
        players_added = 0
        for player_data in nba_players:
            # Find team
            team = session.query(Team).filter_by(abbreviation=player_data['team']).first()
            if not team:
                console.print(f"[yellow]⚠️ Team {player_data['team']} not found for {player_data['name']}[/yellow]")
                continue
            
            # Check if player already exists
            existing_player = session.query(Player).filter(
                Player.name.ilike(f"%{player_data['name']}%")
            ).first()
            
            if not existing_player:
                player = Player(
                    external_id=f"nba_{players_added + 1000}",
                    name=player_data['name'],
                    position=player_data['position'],
                    current_team_id=team.id
                )
                session.add(player)
                players_added += 1
        
        session.commit()
        console.print(f"[green]✅ Added {players_added} NBA players[/green]")
        
        # 3. ADD REALISTIC STATS FOR TOP PLAYERS
        console.print("\n[cyan]📊 Step 3: Adding realistic 2024-25 season stats...[/cyan]")
        
        # Realistic stats for key players (2024-25 season projections)
        player_stats = {
            'LeBron James': {'points': 25.7, 'assists': 8.3, 'rebounds': 7.3, 'games': 71},
            'Stephen Curry': {'points': 26.4, 'assists': 5.1, 'rebounds': 4.5, 'games': 74},
            'Luka Doncic': {'points': 32.4, 'assists': 9.1, 'rebounds': 8.6, 'games': 70},
            'Giannis Antetokounmpo': {'points': 30.4, 'assists': 6.5, 'rebounds': 11.5, 'games': 73},
            'Jayson Tatum': {'points': 26.9, 'assists': 4.9, 'rebounds': 8.1, 'games': 74},
            'Ja Morant': {'points': 25.1, 'assists': 8.1, 'rebounds': 5.6, 'games': 57},
            'Anthony Edwards': {'points': 25.9, 'assists': 5.1, 'rebounds': 5.4, 'games': 79},
            'Nikola Jokic': {'points': 26.4, 'assists': 9.0, 'rebounds': 12.4, 'games': 79},
            'Joel Embiid': {'points': 34.7, 'assists': 5.6, 'rebounds': 11.0, 'games': 39},
            'Shai Gilgeous-Alexander': {'points': 30.1, 'assists': 6.2, 'rebounds': 5.5, 'games': 75},
            'De\'Aaron Fox': {'points': 26.6, 'assists': 5.6, 'rebounds': 4.6, 'games': 74},
            'Trae Young': {'points': 25.7, 'assists': 10.8, 'rebounds': 2.8, 'games': 54},
            'Donovan Mitchell': {'points': 26.6, 'assists': 6.1, 'rebounds': 5.1, 'games': 55}
        }
        
        stats_added = 0
        for player_name, stats in player_stats.items():
            player = session.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).first()
            
            if player:
                # Check if stats already exist
                existing_stats = session.query(PlayerStats).filter_by(
                    player_id=player.id,
                    season="2024-25"
                ).first()
                
                if not existing_stats:
                    player_stats_obj = PlayerStats(
                        player_id=player.id,
                        season="2024-25",
                        games_played=stats['games'],
                        points=stats['points'],
                        assists=stats['assists'],
                        rebounds=stats['rebounds'],
                        steals=1.2,
                        blocks=0.8,
                        field_goals_made=stats['points'] * 0.45,  # Rough calculation
                        field_goals_attempted=stats['points'] * 0.45 / 0.48,
                        three_pointers_made=2.5,
                        three_pointers_attempted=7.0,
                        free_throws_made=stats['points'] * 0.15,
                        free_throws_attempted=stats['points'] * 0.15 / 0.85,
                        minutes_played=35.0
                    )
                    session.add(player_stats_obj)
                    stats_added += 1
        
        session.commit()
        console.print(f"[green]✅ Added stats for {stats_added} players[/green]")
        
        # FINAL SUMMARY
        console.print("\n[bold green]🎉 NBA Data Load Complete! 🎉[/bold green]")
        
        # Get final counts
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats Records: {final_stats}")
        
        # Test Ja Morant specifically
        console.print(f"\n[bold cyan]🔍 Testing Ja Morant:[/bold cyan]")
        ja_morant = session.query(Player).filter(Player.name.ilike('%Ja Morant%')).first()
        if ja_morant:
            team = session.query(Team).filter_by(id=ja_morant.current_team_id).first()
            stats = session.query(PlayerStats).filter_by(player_id=ja_morant.id).first()
            console.print(f"✅ {ja_morant.name} - {team.name if team else 'No Team'} ({ja_morant.position})")
            if stats:
                console.print(f"   2024-25 Stats: {stats.points} PPG, {stats.assists} APG, {stats.rebounds} RPG")
        else:
            console.print("❌ Ja Morant not found")
        
        console.print(f"\n[green]✅ NBA Database is now ready for queries![/green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error during NBA data load: {str(e)}[/bold red]")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_comprehensive_nba_data()
