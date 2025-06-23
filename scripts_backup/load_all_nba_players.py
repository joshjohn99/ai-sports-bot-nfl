#!/usr/bin/env python3
"""
Full-scale NBA loader - Load all 30 teams and top 75% of players
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
import time
import asyncio
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class FullScaleNBALoader:
    """Full-scale NBA loader for all teams and players"""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.base_url = "https://nba-api-free-data.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
        }
        
        self.divisions = [
            'nba-atlantic-team-list',
            'nba-central-team-list', 
            'nba-southeast-team-list',
            'nba-northwest-team-list',
            'nba-pacific-team-list',
            'nba-southwest-team-list'
        ]
    
    def fetch_division_teams_direct(self, division: str) -> Dict[str, Any]:
        """Fetch teams from a division"""
        try:
            url = f"{self.base_url}/{division}"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'response' in data:
                    team_list = data['response'].get('teamList', [])
                    
                    parsed_teams = []
                    for team in team_list:
                        parsed_teams.append({
                            'id': team.get('id'),
                            'name': team.get('name'),
                            'short_name': team.get('shortName'),
                            'abbreviation': team.get('abbrev'),
                            'division': division.replace('-team-list', '').replace('nba-', ''),
                        })
                    
                    return {
                        'success': True,
                        'division': division,
                        'teams': parsed_teams,
                        'count': len(parsed_teams)
                    }
            
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_team_players_direct(self, team_id: str, team_name: str = "Unknown") -> Dict[str, Any]:
        """Fetch players for a team"""
        try:
            url = f"{self.base_url}/nba-player-list"
            params = {'teamid': team_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'response' in data:
                    player_list = data['response'].get('PlayerList', [])
                    
                    parsed_players = []
                    for player in player_list:
                        parsed_players.append({
                            'id': player.get('id'),
                            'name': player.get('fullName', f"{player.get('firstName', '')} {player.get('lastName', '')}").strip(),
                            'first_name': player.get('firstName', ''),
                            'last_name': player.get('lastName', ''),
                            'height': player.get('displayHeight', ''),
                            'weight': player.get('displayWeight', ''),
                            'age': player.get('age', 0),
                            'salary': player.get('salary', 0),
                            'team_id': team_id,
                            'team_name': team_name
                        })
                    
                    return {
                        'success': True,
                        'team_id': team_id,
                        'team_name': team_name,
                        'players': parsed_players,
                        'count': len(parsed_players)
                    }
            
            return {'success': False, 'error': f'HTTP {response.status_code}', 'team_id': team_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'team_id': team_id}

async def load_all_nba_players():
    """Load all NBA teams and top 75% of players"""
    
    console.print("[bold blue]🏀 Loading ALL NBA Players (Full Scale) 🏀[/bold blue]")
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    loader = FullScaleNBALoader()
    
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
        # Step 1: Fetch all teams
        console.print("\n" + "="*60)
        console.print("STEP 1: FETCHING ALL 30 NBA TEAMS")
        console.print("="*60)
        
        all_teams = []
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Loading divisions...", total=len(loader.divisions))
            
            for division in loader.divisions:
                result = loader.fetch_division_teams_direct(division)
                
                if result['success']:
                    teams = result['teams']
                    all_teams.extend(teams)
                    console.print(f"  ✅ {division}: {result['count']} teams")
                else:
                    console.print(f"  ❌ {division}: {result.get('error', 'Unknown error')}")
                
                progress.advance(task)
                time.sleep(0.3)  # Faster rate limiting
        
        console.print(f"\n✅ Total teams found: {len(all_teams)}")
        
        # Step 2: Fetch players for ALL teams
        console.print(f"\n" + "="*60)
        console.print("STEP 2: FETCHING PLAYERS FOR ALL 30 TEAMS")
        console.print("="*60)
        
        all_players = []
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching all team rosters...", total=len(all_teams))
            
            for team_data in all_teams:
                team_id = team_data.get('id', '')
                team_name = team_data.get('name', '')
                
                if team_id:
                    result = loader.fetch_team_players_direct(team_id, team_name)
                    
                    if result['success']:
                        players = result['players']
                        all_players.extend(players)
                        console.print(f"    ✅ {team_name}: {result['count']} players")
                    else:
                        console.print(f"    ❌ {team_name}: {result.get('error', 'No players found')}")
                
                progress.advance(task)
                time.sleep(0.7)  # Rate limiting to avoid hitting API limits
        
        console.print(f"\n✅ Total players found: {len(all_players)}")
        
        # Step 3: Load top 75% of players
        top_75_count = int(len(all_players) * 0.75)
        top_players = all_players[:top_75_count]
        
        console.print(f"\n" + "="*60)
        console.print(f"STEP 3: LOADING TOP {top_75_count} PLAYERS (75%)")
        console.print("="*60)
        
        # Get team mapping
        team_mapping = {}
        for team_data in all_teams:
            team_id = team_data.get('id', '')
            team_abbrev = team_data.get('abbreviation', '')
            if team_id and team_abbrev:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbrev.upper()).first()
                if existing_team:
                    team_mapping[team_id] = existing_team.id
        
        players_added = 0
        players_cached = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Loading top players...", total=len(top_players))
            
            for player_data in top_players:
                player_id = player_data.get('id', '')
                player_name = player_data.get('name', '')
                team_id = player_data.get('team_id', '')
                
                if player_id and player_name:
                    # Check if player exists
                    existing_player = session.query(Player).filter_by(external_id=f"nba_full_{player_id}").first()
                    
                    if not existing_player:
                        db_player = Player(
                            external_id=f"nba_full_{player_id}",
                            name=player_name,
                            position='',
                            current_team_id=team_mapping.get(team_id),
                            active=True
                        )
                        session.add(db_player)
                        session.flush()
                        players_added += 1
                        
                        # Cache player
                        cache_data = {
                            'id': db_player.id,
                            'name': player_name,
                            'team': player_data.get('team_name', ''),
                            'team_id': team_mapping.get(team_id),
                            'external_id': player_id,
                            'height': player_data.get('height', ''),
                            'weight': player_data.get('weight', ''),
                            'age': player_data.get('age', 0),
                            'salary': player_data.get('salary', 0)
                        }
                        sports_cache.set_player('NBA', player_name, cache_data)
                        players_cached += 1
                
                progress.advance(task)
                
                # Commit periodically
                if players_added % 50 == 0:
                    session.commit()
                    console.print(f"    ✅ Processed {players_added} players...")
        
        session.commit()
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 FULL-SCALE NBA DATA LOAD COMPLETE! 🎉")
        console.print("="*60)
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• New Players Added: {players_added}")
        console.print(f"• Players Cached: {players_cached}")
        console.print(f"• Teams Processed: {len(all_teams)}")
        console.print(f"• Total Players Found: {len(all_players)}")
        console.print(f"• Top 75% Players Loaded: {top_75_count}")
        
        console.print(f"\n[green]✅ NBA system ready with comprehensive data![/green]")
        console.print(f"[yellow]🏀 {top_75_count} NBA players cached for lightning-fast queries![/yellow]")
        console.print(f"[cyan]🤖 LangChain framework ready for intelligent sports queries![/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(load_all_nba_players())
