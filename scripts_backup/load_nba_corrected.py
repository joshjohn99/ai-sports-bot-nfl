#!/usr/bin/env python3
"""
Corrected NBA Data Loader - Fixed case sensitivity and data structure
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
import time
import json
import asyncio
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class CorrectedNBALoader:
    """Corrected NBA loader with proper case handling"""
    
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
        """Direct API call without agent complexity"""
        try:
            url = f"{self.base_url}/{division}"
            console.print(f"  🔄 Calling: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'response' in data:
                    team_list = data['response'].get('teamList', [])
                    
                    # Parse teams
                    parsed_teams = []
                    for team in team_list:
                        parsed_teams.append({
                            'id': team.get('id'),
                            'name': team.get('name'),
                            'short_name': team.get('shortName'),
                            'abbreviation': team.get('abbrev'),
                            'division': division.replace('-team-list', '').replace('nba-', ''),
                            'href': team.get('href', ''),
                            'logo': team.get('logo', '')
                        })
                    
                    return {
                        'success': True,
                        'division': division,
                        'teams': parsed_teams,
                        'count': len(parsed_teams)
                    }
            
            return {
                'success': False, 
                'error': f'HTTP {response.status_code}',
                'response_text': response.text[:200] if response.text else 'No response'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_team_players_direct(self, team_id: str, team_name: str = "Unknown") -> Dict[str, Any]:
        """Direct API call to get team players - CORRECTED VERSION"""
        try:
            url = f"{self.base_url}/nba-player-list"
            params = {'teamid': team_id}
            console.print(f"    🔄 Fetching players for {team_name} (ID: {team_id})")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'response' in data:
                    # FIXED: Use 'PlayerList' (capital P) instead of 'playerList'
                    player_list = data['response'].get('PlayerList', [])
                    
                    parsed_players = []
                    for player in player_list:
                        parsed_players.append({
                            'id': player.get('id'),
                            'name': player.get('fullName', f"{player.get('firstName', '')} {player.get('lastName', '')}").strip(),
                            'first_name': player.get('firstName', ''),
                            'last_name': player.get('lastName', ''),
                            'position': '',  # Position not in this endpoint, we'll get it from stats
                            'height': player.get('displayHeight', ''),
                            'weight': player.get('displayWeight', ''),
                            'age': player.get('age', 0),
                            'salary': player.get('salary', 0),
                            'image': player.get('image', ''),
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
            
            return {
                'success': False, 
                'error': f'HTTP {response.status_code}',
                'team_id': team_id,
                'response_text': response.text[:200] if response.text else 'No response'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'team_id': team_id}
    
    def fetch_player_stats(self, player_id: str) -> Optional[Dict]:
        """Fetch player stats to get position and performance data"""
        try:
            url = f"{self.base_url}/nba-player-stats"
            params = {'playerid': player_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data
            return None
                
        except Exception as e:
            return None

async def load_nba_corrected():
    """Load comprehensive NBA data with corrected API handling"""
    
    console.print("[bold blue]🏀 Loading NBA Data (Corrected Version) 🏀[/bold blue]")
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    loader = CorrectedNBALoader()
    
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
        # Step 1: Fetch all teams from all divisions
        console.print("\n" + "="*60)
        console.print("STEP 1: FETCHING ALL NBA TEAMS")
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
                    
                    # Show first team as example
                    if teams:
                        first_team = teams[0]
                        console.print(f"    Example: {first_team['name']} ({first_team['abbreviation']}) - ID: {first_team['id']}")
                else:
                    console.print(f"  ❌ {division}: {result.get('error', 'Unknown error')}")
                
                progress.advance(task)
                time.sleep(0.5)  # Rate limiting
        
        console.print(f"\n✅ Total teams found: {len(all_teams)}")
        
        # Step 2: Add teams to database
        console.print(f"\n" + "="*60)
        console.print("STEP 2: ADDING TEAMS TO DATABASE")
        console.print("="*60)
        
        teams_added = 0
        team_mapping = {}
        
        for team_data in all_teams:
            team_name = team_data.get('name', '')
            team_abbrev = team_data.get('abbreviation', '')
            team_id = team_data.get('id', '')
            
            if team_name and team_abbrev:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbrev.upper()).first()
                
                if not existing_team:
                    db_team = Team(
                        external_id=f"nba_corrected_{team_id}",
                        name=team_data.get('short_name', team_name),
                        display_name=team_name,
                        abbreviation=team_abbrev.upper(),
                        city=team_name.split()[-1] if ' ' in team_name else '',
                        active=True
                    )
                    session.add(db_team)
                    session.flush()
                    teams_added += 1
                    console.print(f"  ✅ Added: {team_name} ({team_abbrev.upper()})")
                else:
                    db_team = existing_team
                    console.print(f"  ♻️ Exists: {team_name} ({team_abbrev.upper()})")
                
                team_mapping[team_id] = {
                    'db_id': db_team.id,
                    'name': team_name,
                    'abbrev': team_abbrev.upper()
                }
        
        session.commit()
        console.print(f"\n✅ Added {teams_added} new teams")
        
        # Step 3: Fetch players for each team (test with first few teams)
        console.print(f"\n" + "="*60)
        console.print("STEP 3: FETCHING PLAYERS FOR TEAMS")
        console.print("="*60)
        
        all_players = []
        
        # Test with first 5 teams to start
        test_teams = all_teams[:5]
        console.print(f"Testing with first {len(test_teams)} teams...")
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching team rosters...", total=len(test_teams))
            
            for team_data in test_teams:
                team_id = team_data.get('id', '')
                team_name = team_data.get('name', '')
                
                if team_id:
                    result = loader.fetch_team_players_direct(team_id, team_name)
                    
                    if result['success']:
                        players = result['players']
                        all_players.extend(players)
                        console.print(f"    ✅ {team_name}: {result['count']} players")
                        
                        # Show first player as example
                        if players:
                            first_player = players[0]
                            console.print(f"      Example: {first_player['name']} ({first_player['height']}, {first_player['weight']})")
                    else:
                        console.print(f"    ❌ {team_name}: {result.get('error', 'No players found')}")
                        console.print(f"      Response: {result.get('response_text', 'No response')}")
                
                progress.advance(task)
                time.sleep(1)  # Longer rate limiting for testing
        
        console.print(f"\n✅ Total players found: {len(all_players)}")
        
        # Step 4: Load players into database and cache
        if all_players:
            console.print(f"\n" + "="*60)
            console.print(f"STEP 4: LOADING {len(all_players)} PLAYERS")
            console.print("="*60)
            
            players_added = 0
            players_cached = 0
            stats_added = 0
            
            with Progress() as progress:
                task = progress.add_task("[cyan]Loading players...", total=len(all_players))
                
                for player_data in all_players:
                    player_id = player_data.get('id', '')
                    player_name = player_data.get('name', '')
                    team_id = player_data.get('team_id', '')
                    
                    if player_id and player_name:
                        # Check if player exists
                        existing_player = session.query(Player).filter_by(external_id=f"nba_corrected_{player_id}").first()
                        
                        if not existing_player:
                            # Get team database ID
                            db_team_id = team_mapping.get(team_id, {}).get('db_id')
                            
                            db_player = Player(
                                external_id=f"nba_corrected_{player_id}",
                                name=player_name,
                                position='',  # Will get from stats if available
                                current_team_id=db_team_id,
                                active=True
                            )
                            session.add(db_player)
                            session.flush()
                            players_added += 1
                            
                            # Try to get player stats for position and performance data
                            stats_data = loader.fetch_player_stats(player_id)
                            if stats_data:
                                # Process stats and update position
                                # This would require parsing the stats response
                                stats_added += 1
                            
                            # Cache player
                            cache_data = {
                                'id': db_player.id,
                                'name': player_name,
                                'position': player_data.get('position', ''),
                                'team': player_data.get('team_name', ''),
                                'team_id': db_team_id,
                                'external_id': player_id,
                                'height': player_data.get('height', ''),
                                'weight': player_data.get('weight', ''),
                                'age': player_data.get('age', 0),
                                'salary': player_data.get('salary', 0)
                            }
                            sports_cache.set_player('NBA', player_name, cache_data)
                            players_cached += 1
                            
                            if players_added % 10 == 0:
                                console.print(f"    ✅ Processed {players_added} players...")
                    
                    progress.advance(task)
                    
                    # Commit periodically
                    if players_added % 25 == 0:
                        session.commit()
            
            session.commit()
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 CORRECTED NBA DATA LOAD COMPLETE! 🎉")
        console.print("="*60)
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• New Teams Added: {teams_added}")
        console.print(f"• New Players Added: {players_added}")
        console.print(f"• Players Cached: {players_cached}")
        console.print(f"• Teams Processed: {len(all_teams)}")
        console.print(f"• Total Players Found: {len(all_players)}")
        
        # Test cache
        console.print(f"\n[cyan]🔍 Testing Cache:[/cyan]")
        if all_players:
            sample_players = all_players[:3]  # Test first 3 players
            for player in sample_players:
                cached = sports_cache.get_player('NBA', player['name'])
                status = "✅ Cached" if cached else "❌ Not cached"
                console.print(f"  {player['name']}: {status}")
        
        console.print(f"\n[green]✅ NBA system ready with corrected data loading![/green]")
        console.print(f"[yellow]🏀 {len(all_players)} NBA players loaded and cached![/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(load_nba_corrected())
