#!/usr/bin/env python3
"""
Complete NBA Data Loader - Gets all teams and their players
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from dotenv import load_dotenv
import requests
import time
from typing import Dict, List, Any, Optional

# Fix the path setup
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class CompleteNBALoader:
    """Complete NBA loader that gets teams and all their players"""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.base_url = "https://nba-api-free-data.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
        }
        
        # NBA divisions
        self.divisions = [
            'nba-atlantic-team-list',
            'nba-central-team-list', 
            'nba-southeast-team-list',
            'nba-northwest-team-list',
            'nba-pacific-team-list',
            'nba-southwest-team-list'
        ]
    
    def fetch_all_teams(self) -> List[Dict]:
        """Fetch all NBA teams from all divisions"""
        all_teams = []
        
        console.print("[cyan]🏀 Fetching NBA teams from all divisions...[/cyan]")
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Loading divisions...", total=len(self.divisions))
            
            for division in self.divisions:
                try:
                    url = f"{self.base_url}/{division}"
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('status') == 'success' and 'response' in data:
                            team_list = data['response'].get('teamList', [])
                            
                            for team in team_list:
                                team['division'] = division.replace('-team-list', '').replace('nba-', '')
                                all_teams.append(team)
                            
                            console.print(f"  ✅ {division}: {len(team_list)} teams")
                        else:
                            console.print(f"  ❌ {division}: Invalid response format")
                    else:
                        console.print(f"  ❌ {division}: HTTP {response.status_code}")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    console.print(f"  ⚠ {division}: {e}")
                
                progress.advance(task)
        
        console.print(f"✅ Total teams found: {len(all_teams)}")
        return all_teams
    
    def fetch_team_players(self, team_id: str) -> List[Dict]:
        """Fetch all players for a specific team"""
        try:
            url = f"{self.base_url}/nba-player-list"
            params = {'teamid': team_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'response' in data:
                    player_list = data['response'].get('playerList', [])
                    return player_list
                else:
                    console.print(f"    ❌ Team {team_id}: Invalid response format")
                    return []
            else:
                console.print(f"    ❌ Team {team_id}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            console.print(f"    ⚠ Team {team_id}: {e}")
            return []
    
    def fetch_player_stats(self, player_id: str) -> Optional[Dict]:
        """Fetch detailed stats for a specific player"""
        try:
            url = f"{self.base_url}/nba-player-stats"
            params = {'playerid': player_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data
            return None
                
        except Exception as e:
            return None
    
    def extract_player_info_from_stats(self, stats_response: Dict, player_id: str, player_name: str = None) -> Optional[Dict]:
        """Extract player information and stats from the API response"""
        if not stats_response or stats_response.get('status') != 'success':
            return None
        
        stats_data = stats_response.get('response', {}).get('stats', {})
        
        # Extract player info from the latest season stats
        player_info = {
            'id': player_id,
            'name': player_name or f'Player_{player_id}',
            'position': '',
            'current_team_id': None,
            'current_team_name': '',
            'stats': {}
        }
        
        # Look for averages in categories
        categories = stats_data.get('categories', [])
        for category in categories:
            if category.get('name') == 'averages' and category.get('statistics'):
                # Get most recent season
                latest_stats = category['statistics'][-1]
                
                # Extract basic info
                player_info['position'] = latest_stats.get('position', '')
                player_info['current_team_id'] = latest_stats.get('teamId')
                player_info['current_team_name'] = latest_stats.get('teamSlug', '')
                
                # Map stats
                labels = category.get('labels', [])
                values = latest_stats.get('stats', [])
                
                for i, label in enumerate(labels):
                    if i < len(values) and values[i] != '--':
                        try:
                            value = values[i]
                            if '-' in str(value) and label in ['FG', '3PT', 'FT']:
                                # Handle "made-attempted" format
                                made, attempted = value.split('-')
                                player_info['stats'][f"{label.lower()}_made"] = float(made)
                                player_info['stats'][f"{label.lower()}_attempted"] = float(attempted)
                            else:
                                # Convert to appropriate type
                                if '.' in str(value):
                                    player_info['stats'][label.lower()] = float(value)
                                else:
                                    player_info['stats'][label.lower()] = int(value)
                        except (ValueError, AttributeError):
                            player_info['stats'][label.lower()] = str(value)
                
                break
        
        return player_info

def load_nba_complete():
    """Load complete NBA data - teams and all their players"""
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    console.print("[bold blue]🏀 Loading Complete NBA Data (Teams + Players) 🏀[/bold blue]")
    
    loader = CompleteNBALoader()
    
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
        console.print("STEP 1: FETCHING ALL NBA TEAMS")
        console.print("="*60)
        
        teams_data = loader.fetch_all_teams()
        if not teams_data:
            console.print("[red]❌ No teams found[/red]")
            return
        
        # Step 2: Add teams to database
        console.print(f"\n" + "="*60)
        console.print("STEP 2: ADDING TEAMS TO DATABASE")
        console.print("="*60)
        
        teams_added = 0
        team_mapping = {}
        
        for team_data in teams_data:
            team_name = team_data.get('name', '')
            team_abbrev = team_data.get('abbrev', '')
            team_id = team_data.get('id', '')
            
            if team_name and team_abbrev:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbrev.upper()).first()
                
                if not existing_team:
                    db_team = Team(
                        external_id=f"nba_api_{team_id}",
                        name=team_data.get('shortName', team_name),
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
                
                team_mapping[team_id] = db_team.id
        
        session.commit()
        console.print(f"\n✅ Added {teams_added} new teams")
        
        # Step 3: Fetch players for each team
        console.print(f"\n" + "="*60)
        console.print("STEP 3: FETCHING PLAYERS FOR ALL TEAMS")
        console.print("="*60)
        
        all_players = []
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching team rosters...", total=len(teams_data))
            
            for team_data in teams_data:
                team_id = team_data.get('id', '')
                team_name = team_data.get('name', '')
                
                console.print(f"  🔄 Fetching roster for {team_name} (ID: {team_id})...")
                
                team_players = loader.fetch_team_players(team_id)
                if team_players:
                    console.print(f"    ✅ Found {len(team_players)} players")
                    for player in team_players:
                        player['source_team_id'] = team_id
                        player['source_team_name'] = team_name
                        all_players.append(player)
                else:
                    console.print(f"    ❌ No players found")
                
                progress.advance(task)
                time.sleep(0.5)  # Rate limiting
        
        console.print(f"\n✅ Total players found: {len(all_players)}")
        
        # Step 4: Load top 75% of players
        top_75_count = int(len(all_players) * 0.75)
        top_players = all_players[:top_75_count]
        
        console.print(f"\n" + "="*60)
        console.print(f"STEP 4: LOADING TOP {top_75_count} PLAYERS (75%)")
        console.print("="*60)
        
        players_added = 0
        players_cached = 0
        stats_added = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Loading player stats...", total=len(top_players))
            
            for player_data in top_players:
                player_id = player_data.get('id', '')
                player_name = player_data.get('name', player_data.get('displayName', f'Player_{player_id}'))
                
                if not player_id:
                    progress.advance(task)
                    continue
                
                # Check if player exists
                existing_player = session.query(Player).filter_by(external_id=f"nba_api_{player_id}").first()
                
                if existing_player:
                    progress.advance(task)
                    continue
                
                # Fetch player stats
                stats_response = loader.fetch_player_stats(player_id)
                
                # Create player even if no stats (roster player)
                db_player = Player(
                    external_id=f"nba_api_{player_id}",
                    name=player_name,
                    position=player_data.get('position', ''),
                    current_team_id=team_mapping.get(player_data.get('source_team_id')),
                    active=True
                )
                session.add(db_player)
                session.flush()
                players_added += 1
                
                # Add stats if available
                if stats_response:
                    player_info = loader.extract_player_info_from_stats(stats_response, player_id, player_name)
                    if player_info and player_info.get('stats', {}).get('pts'):
                        stats = player_info['stats']
                        player_stats = PlayerStats(
                            player_id=db_player.id,
                            season='2024-25',
                            games_played=int(stats.get('gp', 0)) if stats.get('gp') else 0,
                            points=float(stats.get('pts', 0)) if stats.get('pts') else 0,
                            assists=float(stats.get('ast', 0)) if stats.get('ast') else 0,
                            rebounds=float(stats.get('reb', 0)) if stats.get('reb') else 0,
                            steals=float(stats.get('stl', 0)) if stats.get('stl') else 0,
                            blocks=float(stats.get('blk', 0)) if stats.get('blk') else 0,
                            minutes_played=float(stats.get('min', 0)) if stats.get('min') else 0
                        )
                        session.add(player_stats)
                        stats_added += 1
                        
                        # Cache player with stats
                        cache_data = {
                            'id': db_player.id,
                            'name': player_name,
                            'position': player_info.get('position', ''),
                            'team': player_data.get('source_team_name', ''),
                            'team_id': team_mapping.get(player_data.get('source_team_id')),
                            'stats': stats
                        }
                        sports_cache.set_player('NBA', player_name, cache_data)
                        players_cached += 1
                        
                        console.print(f"    ✅ {player_name} ({stats.get('pts', 0)} PPG)")
                    else:
                        console.print(f"    ➕ {player_name} (roster only)")
                else:
                    console.print(f"    ➕ {player_name} (roster only)")
                
                progress.advance(task)
                
                # Commit periodically and add rate limiting
                if players_added % 10 == 0:
                    session.commit()
                    time.sleep(1)  # Rate limiting
        
        session.commit()
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 COMPLETE NBA DATA LOAD FINISHED! 🎉")
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
        console.print(f"• New Stats Added: {stats_added}")
        console.print(f"• Players Cached: {players_cached}")
        
        console.print(f"\n[green]✅ NBA system ready with complete roster data![/green]")
        console.print(f"[yellow]🏀 Top 75% of NBA players loaded and cached![/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_nba_complete()
