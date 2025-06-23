#!/usr/bin/env python3
"""
NBA Data Loader using working APIs
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
import time

# Fix the path setup
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class WorkingNBALoader:
    """NBA loader using verified working APIs"""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.console = Console()
    
    def load_from_nba_stats_api(self):
        """Load from the free NBA Stats API (no auth required)"""
        try:
            console.print("[cyan]🔄 Using NBA Stats API (no auth required)...[/cyan]")
            
            # This API works without authentication
            url = "http://rest.nbaapi.com/api/PlayerDataTotals/query"
            params = {
                'season': 2025,
                'pageSize': 200  # Get many players
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                players_data = response.json()
                console.print(f"✅ Found {len(players_data)} players from NBA Stats API")
                return players_data
            else:
                console.print(f"❌ NBA Stats API failed: {response.status_code}")
                return []
                
        except Exception as e:
            console.print(f"❌ Error with NBA Stats API: {e}")
            return []
    
    def load_from_api_nba(self):
        """Load from API-NBA (requires auth)"""
        if not self.api_key:
            return []
        
        try:
            console.print("[cyan]🔄 Using API-NBA (authenticated)...[/cyan]")
            
            headers = {
                'X-RapidAPI-Key': self.api_key,
                'X-RapidAPI-Host': 'api-nba-v1.p.rapidapi.com'
            }
            
            # Get teams first
            teams_response = requests.get(
                'https://api-nba-v1.p.rapidapi.com/teams',
                headers=headers,
                timeout=15
            )
            
            if teams_response.status_code == 200:
                teams_data = teams_response.json()
                teams = teams_data.get('response', [])
                nba_teams = [t for t in teams if t.get('nbaFranchise') == '1']
                console.print(f"✅ Found {len(nba_teams)} NBA teams from API-NBA")
                
                # Get players for a few teams as sample
                all_players = []
                for team in nba_teams[:5]:  # Test with first 5 teams
                    try:
                        players_response = requests.get(
                            'https://api-nba-v1.p.rapidapi.com/players',
                            headers=headers,
                            params={'team': team['id'], 'season': '2024'},
                            timeout=10
                        )
                        
                        if players_response.status_code == 200:
                            players_data = players_response.json()
                            team_players = players_data.get('response', [])
                            all_players.extend(team_players)
                            console.print(f"  ✅ {team['name']}: {len(team_players)} players")
                        
                        time.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        console.print(f"  ⚠ Failed to get players for {team['name']}: {e}")
                
                return all_players, nba_teams
            else:
                console.print(f"❌ API-NBA teams failed: {teams_response.status_code}")
                return [], []
                
        except Exception as e:
            console.print(f"❌ Error with API-NBA: {e}")
            return [], []

def load_nba_working_apis():
    """Load NBA data using working APIs"""
    console.print("[bold blue]🏀 Loading NBA Data from Working APIs 🏀[/bold blue]")
    
    loader = WorkingNBALoader()
    
    # Get database session
    session = sport_db_manager.get_session('NBA')
    models = sport_db_manager.get_models('NBA')
    
    if not session or not models:
        console.print("[red]❌ Could not connect to NBA database[/red]")
        return
    
    Team = models['Team']
    Player = models['Player']
    PlayerStats = models['PlayerStats']
    
    try:
        players_data = []
        teams_data = []
        
        # Try NBA Stats API first (no auth required)
        nba_stats_players = loader.load_from_nba_stats_api()
        if nba_stats_players:
            players_data.extend(nba_stats_players)
            
            # Extract teams from player data
            unique_teams = {}
            for player in nba_stats_players:
                team_abbr = player.get('team')
                if team_abbr and team_abbr not in unique_teams:
                    unique_teams[team_abbr] = {
                        'abbreviation': team_abbr,
                        'name': team_abbr,  # We'll improve this
                        'id': team_abbr.lower()
                    }
            teams_data = list(unique_teams.values())
        
        # Try API-NBA if we have an API key
        if loader.api_key:
            api_nba_players, api_nba_teams = loader.load_from_api_nba()
            if api_nba_teams:
                teams_data = api_nba_teams  # Use better team data from API-NBA
            if api_nba_players:
                players_data.extend(api_nba_players)
        
        if not players_data:
            console.print("[red]❌ No player data found from any API[/red]")
            return
        
        console.print(f"\n[green]✅ Total data collected:[/green]")
        console.print(f"• Players: {len(players_data)}")
        console.print(f"• Teams: {len(teams_data)}")
        
        # Add teams to database
        teams_added = 0
        team_mapping = {}
        
        for team_data in teams_data:
            team_abbr = team_data.get('abbreviation', team_data.get('nickname', ''))
            if team_abbr:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbr).first()
                if not existing_team:
                    db_team = Team(
                        external_id=f"nba_{team_data.get('id', team_abbr.lower())}",
                        name=team_data.get('name', team_abbr),
                        display_name=team_data.get('fullName', team_data.get('name', team_abbr)),
                        abbreviation=team_abbr,
                        city=team_data.get('city', ''),
                        active=True
                    )
                    session.add(db_team)
                    session.flush()
                    teams_added += 1
                else:
                    db_team = existing_team
                
                team_mapping[team_abbr] = db_team.id
        
        session.commit()
        console.print(f"✅ Added {teams_added} new teams")
        
        # Process players (top 75%)
        active_players = [p for p in players_data if p.get('team') or p.get('playerName')]
        top_75_count = int(len(active_players) * 0.75)
        top_players = active_players[:top_75_count]
        
        console.print(f"\n[cyan]👥 Processing top {len(top_players)} players (75% of {len(active_players)})...[/cyan]")
        
        players_added = 0
        players_cached = 0
        stats_added = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing players...", total=len(top_players))
            
            for player_data in top_players:
                # Handle different API formats
                if 'playerName' in player_data:  # NBA Stats API format
                    name = player_data.get('playerName', '')
                    team_abbr = player_data.get('team', '')
                    position = player_data.get('position', '')
                else:  # API-NBA format
                    firstname = player_data.get('firstname', '')
                    lastname = player_data.get('lastname', '')
                    name = f"{firstname} {lastname}".strip()
                    team_abbr = ''  # Will need to map team ID
                    position = ''
                
                if name and team_abbr and team_abbr in team_mapping:
                    # Check if player exists
                    existing_player = session.query(Player).filter(
                        Player.name.ilike(f"%{name}%")
                    ).first()
                    
                    if not existing_player:
                        db_player = Player(
                            external_id=f"nba_multi_{player_data.get('id', players_added)}",
                            name=name,
                            position=position,
                            current_team_id=team_mapping[team_abbr],
                            active=True
                        )
                        session.add(db_player)
                        session.flush()
                        players_added += 1
                        
                        # Add stats if available
                        if player_data.get('season') and player_data.get('points') is not None:
                            player_stats = PlayerStats(
                                player_id=db_player.id,
                                season=str(player_data.get('season', '2025')),
                                games_played=player_data.get('games', 0),
                                points=player_data.get('points', 0),
                                assists=player_data.get('assists', 0),
                                rebounds=player_data.get('totalRb', 0),
                                steals=player_data.get('steals', 0),
                                blocks=player_data.get('blocks', 0),
                                minutes_played=player_data.get('minutesPg', 0)
                            )
                            session.add(player_stats)
                            stats_added += 1
                        
                        # Cache player
                        cache_data = {
                            'id': db_player.id,
                            'name': name,
                            'position': position,
                            'team': team_abbr,
                            'team_id': team_mapping[team_abbr]
                        }
                        sports_cache.set_player('NBA', name, cache_data)
                        players_cached += 1
                
                progress.advance(task)
        
        session.commit()
        
        # Final summary
        console.print("\n[bold green]�� NBA Data Load Complete! 🎉[/bold green]")
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• New Teams Added: {teams_added}")
        console.print(f"• New Players Added: {players_added}")
        console.print(f"• New Stats Added: {stats_added}")
        console.print(f"• Players Cached: {players_cached}")
        
        # Show cache stats
        cache_stats = sports_cache.get_cache_stats()
        console.print(f"\n[bold cyan]📊 Cache Performance:[/bold cyan]")
        console.print(f"• Total Cached Players: {cache_stats['cached_players']}")
        console.print(f"• API Calls Saved: {cache_stats['api_calls_saved']}")
        
        console.print(f"\n[green]✅ NBA system ready with real API data![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_nba_working_apis()
