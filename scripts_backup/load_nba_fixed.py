#!/usr/bin/env python3
"""
NBA Data Loader using NBA API Free Data (nba-api-free-data.p.rapidapi.com)
Follows the correct API pattern: divisions -> teams -> players -> player stats
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
from typing import Dict, List, Any, Optional

# Fix the path setup
current_dir = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(current_dir))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class NBAFreeDataLoader:
    """NBA loader using NBA API Free Data with correct endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.console = Console()
        self.base_url = "https://nba-api-free-data.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
        }
        
        # NBA divisions - CORRECTED URLs (all follow same pattern as atlantic)
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
                    console.print(f"  🔄 Fetching: {url}")
                    
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        division_data = response.json()
                        console.print(f"  📊 Response keys: {list(division_data.keys())}")
                        
                        # Handle different response formats
                        teams = []
                        if 'response' in division_data:
                            if 'teams' in division_data['response']:
                                teams_data = division_data['response']['teams']
                            else:
                                teams_data = division_data['response']
                        elif 'teams' in division_data:
                            teams_data = division_data['teams']
                        else:
                            teams_data = division_data
                        
                        # Extract team data
                        if isinstance(teams_data, dict):
                            for team_key, team_data in teams_data.items():
                                if isinstance(team_data, dict) and team_data.get('id'):
                                    team_data['division'] = division
                                    teams.append(team_data)
                                    all_teams.append(team_data)
                        elif isinstance(teams_data, list):
                            for team_data in teams_data:
                                if isinstance(team_data, dict) and team_data.get('id'):
                                    team_data['division'] = division
                                    teams.append(team_data)
                                    all_teams.append(team_data)
                        
                        console.print(f"  ✅ {division}: {len(teams)} teams")
                        
                        # Show first team as example
                        if teams:
                            first_team = teams[0]
                            console.print(f"    Example: {first_team.get('displayName', 'Unknown')} ({first_team.get('abbreviation', 'N/A')})")
                        
                    else:
                        console.print(f"  ❌ {division}: HTTP {response.status_code}")
                        if response.status_code == 403:
                            console.print(f"    Check your RapidAPI key and subscription")
                        console.print(f"    Response: {response.text[:200]}")
                    
                    time.sleep(1)  # Rate limiting - be more conservative
                    
                except Exception as e:
                    console.print(f"  ⚠ {division}: {e}")
                
                progress.advance(task)
        
        console.print(f"✅ Total teams found: {len(all_teams)}")
        return all_teams
    
    def get_sample_player_ids(self) -> List[str]:
        """Get sample player IDs for testing (from your examples)"""
        return [
            '4869342',  # From your example
            '3915511',  # From your sample files
            '3916387',  # From your sample files
            '3929630',  # From your sample files
        ]
    
    def fetch_player_stats(self, player_id: str) -> Optional[Dict]:
        """Fetch detailed stats for a specific player using the correct endpoint"""
        try:
            url = f"{self.base_url}/nba-player-stats"
            params = {'playerid': player_id}
            
            console.print(f"  🔄 Fetching stats for player {player_id}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                stats_data = response.json()
                console.print(f"  ✅ Got stats for player {player_id}")
                return stats_data
            else:
                console.print(f"  ❌ Failed to get stats for player {player_id}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            console.print(f"  ⚠ Error fetching stats for player {player_id}: {e}")
            return None
    
    def process_player_stats(self, stats_response: Dict) -> Dict:
        """Process the player stats response into our format"""
        if not stats_response or 'response' not in stats_response:
            return {}
        
        stats_data = stats_response['response']['stats']
        processed_stats = {}
        player_name = "Unknown Player"
        
        # Extract averages (most recent season)
        if 'categories' in stats_data:
            for category in stats_data['categories']:
                if category['name'] == 'averages' and category.get('statistics'):
                    # Get most recent season stats
                    latest_stats = category['statistics'][-1]  # Last entry is most recent
                    
                    # Map the stats to our format
                    stats_labels = category['labels']
                    stats_values = latest_stats['stats']
                    
                    for i, label in enumerate(stats_labels):
                        if i < len(stats_values) and stats_values[i] != '--':
                            try:
                                # Handle different value formats
                                value = stats_values[i]
                                if '-' in str(value) and label in ['FG', '3PT', 'FT']:
                                    # Handle "made-attempted" format like "6.0-12.1"
                                    made, attempted = value.split('-')
                                    processed_stats[f"{label.lower()}_made"] = float(made)
                                    processed_stats[f"{label.lower()}_attempted"] = float(attempted)
                                else:
                                    processed_stats[label.lower()] = float(value) if '.' in str(value) else int(value)
                            except (ValueError, AttributeError):
                                processed_stats[label.lower()] = str(value)
                    
                    # Add team and season info
                    processed_stats['team_id'] = latest_stats.get('teamId')
                    processed_stats['team_slug'] = latest_stats.get('teamSlug')
                    processed_stats['season'] = latest_stats.get('season', {}).get('displayName', '2024-25')
                    processed_stats['position'] = latest_stats.get('position', '')
                    
                    break
        
        return processed_stats

def load_nba_from_correct_api():
    """Load NBA data using the correct NBA API Free Data endpoints"""
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        console.print("[yellow]Please add your RapidAPI key to the .env file:[/yellow]")
        console.print("[yellow]RAPIDAPI_KEY=your_key_here[/yellow]")
        return
    
    console.print("[bold blue]🏀 Loading NBA Data from NBA API Free Data 🏀[/bold blue]")
    console.print("[cyan]Using correct division URLs (all follow nba-*-team-list pattern)[/cyan]")
    
    loader = NBAFreeDataLoader()
    
    # Show the URLs we'll be using
    console.print("\n[yellow]Division URLs to fetch:[/yellow]")
    for division in loader.divisions:
        console.print(f"  • {loader.base_url}/{division}")
    
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
        console.print("STEP 1: FETCHING NBA TEAMS")
        console.print("="*60)
        
        teams_data = loader.fetch_all_teams()
        if not teams_data:
            console.print("[red]❌ No teams found. Check API key and endpoints.[/red]")
            return
        
        # Step 2: Add teams to database
        console.print(f"\n" + "="*60)
        console.print("STEP 2: ADDING TEAMS TO DATABASE")
        console.print("="*60)
        
        teams_added = 0
        team_mapping = {}
        
        for team_data in teams_data:
            team_abbr = team_data.get('abbreviation', '')
            team_name = team_data.get('displayName', team_data.get('name', ''))
            
            if team_abbr and team_name:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbr).first()
                if not existing_team:
                    db_team = Team(
                        external_id=f"nba_free_{team_data['id']}",
                        name=team_data.get('name', ''),
                        display_name=team_name,
                        abbreviation=team_abbr,
                        city=team_data.get('location', ''),
                        active=True
                    )
                    session.add(db_team)
                    session.flush()
                    teams_added += 1
                    console.print(f"  ✅ Added: {team_name} ({team_abbr})")
                else:
                    db_team = existing_team
                    console.print(f"  ♻️ Exists: {team_name} ({team_abbr})")
                
                team_mapping[team_data['id']] = db_team.id
        
        session.commit()
        console.print(f"\n✅ Added {teams_added} new teams")
        
        # Step 3: Process sample players (since we can't get full rosters easily)
        console.print(f"\n" + "="*60)
        console.print("STEP 3: FETCHING PLAYER STATS")
        console.print("="*60)
        
        sample_player_ids = loader.get_sample_player_ids()
        console.print(f"Processing {len(sample_player_ids)} sample players...")
        
        players_added = 0
        players_cached = 0
        stats_added = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching player stats...", total=len(sample_player_ids))
            
            for player_id in sample_player_ids:
                # Fetch detailed stats for this player
                stats_response = loader.fetch_player_stats(player_id)
                if not stats_response:
                    progress.advance(task)
                    continue
                
                # Process the stats
                processed_stats = loader.process_player_stats(stats_response)
                if not processed_stats:
                    progress.advance(task)
                    continue
                
                # Extract player info
                player_name = f"NBA_Player_{player_id}"  # We'll improve this when we get name from API
                position = processed_stats.get('position', 'G')
                team_id = processed_stats.get('team_id', '')
                
                # Check if player exists
                existing_player = session.query(Player).filter_by(external_id=f"nba_free_{player_id}").first()
                
                if not existing_player:
                    db_player = Player(
                        external_id=f"nba_free_{player_id}",
                        name=player_name,
                        position=position,
                        current_team_id=team_mapping.get(team_id),
                        active=True
                    )
                    session.add(db_player)
                    session.flush()
                    players_added += 1
                    
                    # Add stats
                    if processed_stats.get('pts'):  # Points per game
                        player_stats = PlayerStats(
                            player_id=db_player.id,
                            season=processed_stats.get('season', '2024-25'),
                            games_played=int(float(processed_stats.get('gp', 0))) if processed_stats.get('gp') else 0,
                            points=float(processed_stats.get('pts', 0)) if processed_stats.get('pts') else 0,
                            assists=float(processed_stats.get('ast', 0)) if processed_stats.get('ast') else 0,
                            rebounds=float(processed_stats.get('reb', 0)) if processed_stats.get('reb') else 0,
                            steals=float(processed_stats.get('stl', 0)) if processed_stats.get('stl') else 0,
                            blocks=float(processed_stats.get('blk', 0)) if processed_stats.get('blk') else 0,
                            minutes_played=float(processed_stats.get('min', 0)) if processed_stats.get('min') else 0
                        )
                        session.add(player_stats)
                        stats_added += 1
                    
                    # Cache player
                    cache_data = {
                        'id': db_player.id,
                        'name': player_name,
                        'position': position,
                        'team': processed_stats.get('team_slug', ''),
                        'team_id': team_mapping.get(team_id),
                        'stats': processed_stats
                    }
                    sports_cache.set_player('NBA', player_name, cache_data)
                    players_cached += 1
                    
                    console.print(f"  ✅ Added: {player_name} ({processed_stats.get('pts', 0)} PPG)")
                
                progress.advance(task)
                time.sleep(1)  # Rate limiting
        
        session.commit()
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 NBA DATA LOAD COMPLETE! ��")
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
        
        console.print(f"\n[green]✅ NBA system ready with live API data![/green]")
        console.print(f"[yellow]💡 To add more players, add their IDs to the sample_player_ids list[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_nba_from_correct_api()
