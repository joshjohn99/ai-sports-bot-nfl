#!/usr/bin/env python3
"""
NBA Data Loader with RapidAPI Authentication
Fetches top 75% of NBA players using authenticated APIs
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

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache

console = Console()
load_dotenv()

class AuthenticatedNBAFetcher:
    """Fetches NBA data using RapidAPI authentication"""
    
    def __init__(self):
        self.console = Console()
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        # API configurations with authentication
        self.apis = {
            'free_nba': {
                'base_url': 'https://free-nba.p.rapidapi.com',
                'headers': {
                    'X-RapidAPI-Key': self.rapidapi_key,
                    'X-RapidAPI-Host': 'free-nba.p.rapidapi.com'
                }
            },
            'api_nba': {
                'base_url': 'https://api-nba-v1.p.rapidapi.com',
                'headers': {
                    'X-RapidAPI-Key': self.rapidapi_key,
                    'X-RapidAPI-Host': 'api-nba-v1.p.rapidapi.com'
                }
            }
        }
    
    def fetch_all_teams(self):
        """Fetch all NBA teams using API-NBA"""
        try:
            url = f"{self.apis['api_nba']['base_url']}/teams"
            response = requests.get(url, headers=self.apis['api_nba']['headers'], timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                teams = data.get('response', [])
                
                # Filter to only NBA teams (exclude G-League, etc.)
                nba_teams = []
                for team in teams:
                    if team.get('nbaFranchise') == '1':  # Only NBA franchise teams
                        nba_teams.append({
                            'id': str(team.get('id')),
                            'name': team.get('name', ''),
                            'full_name': team.get('fullName', ''),
                            'abbreviation': team.get('nickname', ''),
                            'city': team.get('city', ''),
                            'conference': self._get_conference(team.get('nickname', '')),
                            'division': 'Unknown'  # API doesn't provide division
                        })
                
                self.console.print(f"✅ Fetched {len(nba_teams)} NBA teams")
                return nba_teams
            else:
                self.console.print(f"❌ Teams API failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.console.print(f"❌ Error fetching teams: {e}")
            return []
    
    def fetch_all_players(self):
        """Fetch all NBA players using Free NBA API with pagination"""
        all_players = []
        
        try:
            page = 1
            per_page = 100
            max_pages = 20  # Limit to prevent infinite loops
            
            while page <= max_pages:
                url = f"{self.apis['free_nba']['base_url']}/players"
                params = {'page': page, 'per_page': per_page}
                
                response = requests.get(
                    url, 
                    headers=self.apis['free_nba']['headers'], 
                    params=params, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    players_data = data.get('data', [])
                    
                    if not players_data:  # No more players
                        break
                    
                    active_count = 0
                    for player_data in players_data:
                        # Only include players with teams (active players)
                        if player_data.get('team') and player_data.get('team', {}).get('full_name'):
                            player = {
                                'id': str(player_data.get('id')),
                                'name': f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                                'first_name': player_data.get('first_name', ''),
                                'last_name': player_data.get('last_name', ''),
                                'position': player_data.get('position', ''),
                                'team_name': player_data.get('team', {}).get('full_name', ''),
                                'team_abbreviation': player_data.get('team', {}).get('abbreviation', ''),
                                'height_feet': player_data.get('height_feet'),
                                'height_inches': player_data.get('height_inches'),
                                'weight_pounds': player_data.get('weight_pounds')
                            }
                            all_players.append(player)
                            active_count += 1
                    
                    # Fixed the f-string syntax error
                    self.console.print(f"📄 Fetched page {page}: {len(players_data)} players ({active_count} active)")
                    
                    # Check if we've reached the end
                    meta = data.get('meta', {})
                    total_pages = meta.get('total_pages', 0)
                    if page >= total_pages or len(players_data) < per_page:
                        break
                    
                    page += 1
                    time.sleep(0.3)  # Rate limiting
                    
                else:
                    self.console.print(f"❌ Players API failed on page {page}: {response.status_code}")
                    if response.status_code == 429:  # Rate limited
                        time.sleep(2)
                        continue
                    break
                    
        except Exception as e:
            self.console.print(f"❌ Error fetching players: {e}")
        
        return all_players
    
    def _get_conference(self, team_nickname):
        """Determine conference based on team nickname"""
        eastern_teams = [
            'Hawks', 'Celtics', 'Nets', 'Hornets', 'Bulls', 'Cavaliers',
            'Pistons', 'Pacers', 'Heat', 'Bucks', 'Knicks', '76ers',
            'Magic', 'Raptors', 'Wizards'
        ]
        return 'Eastern' if team_nickname in eastern_teams else 'Western'

def load_nba_authenticated():
    """Main function to load NBA data with authentication"""
    console.print("[bold blue]🏀 Loading NBA Data with RapidAPI Authentication 🏀[/bold blue]")
    
    try:
        fetcher = AuthenticatedNBAFetcher()
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return
    
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
        # 1. FETCH ALL TEAMS
        console.print("\n[cyan]📋 Step 1: Fetching all NBA teams...[/cyan]")
        teams_data = fetcher.fetch_all_teams()
        
        if not teams_data:
            console.print("[red]❌ No teams found[/red]")
            return
        
        # Add teams to database
        teams_added = 0
        team_mapping = {}
        
        for team_data in teams_data:
            existing_team = session.query(Team).filter_by(external_id=f"nba_{team_data['id']}").first()
            if not existing_team:
                db_team = Team(
                    external_id=f"nba_{team_data['id']}",
                    name=team_data['name'],
                    display_name=team_data['full_name'],
                    abbreviation=team_data['abbreviation'],
                    city=team_data['city'],
                    conference=team_data['conference'],
                    division=team_data['division'],
                    active=True
                )
                session.add(db_team)
                session.flush()
                teams_added += 1
            else:
                db_team = existing_team
            
            team_mapping[team_data['abbreviation']] = db_team.id
        
        session.commit()
        console.print(f"✅ Added {teams_added} new teams to database")
        
        # Cache teams
        sports_cache.set_team_list('NBA', teams_data)
        
        # 2. FETCH ALL PLAYERS
        console.print("\n[cyan]👥 Step 2: Fetching all NBA players...[/cyan]")
        all_players = fetcher.fetch_all_players()
        
        if not all_players:
            console.print("[red]❌ No players found[/red]")
            return
        
        console.print(f"✅ Fetched {len(all_players)} total active players")
        
        # 3. SELECT TOP 75% OF PLAYERS
        # Sort by position importance and team (starters more likely to be important)
        position_priority = {'PG': 5, 'SG': 4, 'SF': 3, 'PF': 2, 'C': 1, '': 0}
        
        def player_score(player):
            pos_score = position_priority.get(player['position'], 0)
            has_team_score = 10 if player['team_name'] else 0
            return pos_score + has_team_score
        
        all_players.sort(key=player_score, reverse=True)
        
        top_75_count = int(len(all_players) * 0.75)
        top_players = all_players[:top_75_count]
        
        console.print(f"📊 Selected top {len(top_players)} players (75% of {len(all_players)} total)")
        
        # 4. ADD PLAYERS TO DATABASE AND CACHE
        console.print("\n[cyan]💾 Step 3: Adding players to database and cache...[/cyan]")
        
        players_added = 0
        players_cached = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing players...", total=len(top_players))
            
            for player in top_players:
                # Find team
                team_id = None
                for abbr, tid in team_mapping.items():
                    if abbr.lower() == player['team_abbreviation'].lower():
                        team_id = tid
                        break
                
                if team_id and player['name']:
                    # Check if player exists
                    existing_player = session.query(Player).filter(
                        Player.name.ilike(f"%{player['name']}%")
                    ).first()
                    
                    if not existing_player:
                        db_player = Player(
                            external_id=f"nba_free_{player['id']}",
                            name=player['name'],
                            position=player['position'],
                            current_team_id=team_id,
                            active=True
                        )
                        session.add(db_player)
                        session.flush()
                        players_added += 1
                        
                        # Cache player
                        cache_data = {
                            'id': db_player.id,
                            'name': player['name'],
                            'position': player['position'],
                            'team': player['team_name'],
                            'team_id': team_id,
                            'team_abbr': player['team_abbreviation'],
                            'api_id': player['id']
                        }
                        sports_cache.set_player('NBA', player['name'], cache_data)
                        players_cached += 1
                
                progress.advance(task)
        
        session.commit()
        
        # FINAL SUMMARY
        console.print("\n[bold green]🎉 NBA Authenticated Data Load Complete! 🎉[/bold green]")
        
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
        
        # Show cache stats
        cache_stats = sports_cache.get_cache_stats()
        console.print(f"\n[bold cyan]📊 Cache Performance:[/bold cyan]")
        console.print(f"• Total Cached Players: {cache_stats['cached_players']}")
        console.print(f"• Total Cached Teams: {cache_stats['cached_teams']}")
        console.print(f"• API Calls Saved: {cache_stats['api_calls_saved']}")
        
        # Test cache with popular players
        console.print(f"\n[cyan]🔍 Sample Players Added:[/cyan]")
        for i, player in enumerate(top_players[:10]):  # Show first 10 players
            console.print(f"{i+1}. {player['name']} ({player['position']}) - {player['team_abbreviation']}")
        
        console.print(f"\n[green]✅ NBA system ready with top 75% of players from authenticated APIs![/green]")
        console.print(f"[dim]Total API calls made: ~{len(teams_data) + (len(all_players) // 100) + 1}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_nba_authenticated()
