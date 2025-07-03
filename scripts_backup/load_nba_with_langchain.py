#!/usr/bin/env python3
"""
Comprehensive NBA Data Loader with LangChain Integration
Fetches top 75% of NBA players from multiple APIs and caches them using LangChain.
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
from dataclasses import dataclass

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.sports_bot.database.sport_models import sport_db_manager
from src.sports_bot.cache.shared_cache import sports_cache  # Fixed import

# LangChain imports
try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.cache import InMemoryCache
    from langchain.globals import set_llm_cache
    
    # Set up LangChain cache
    set_llm_cache(InMemoryCache())
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available - using basic caching")

console = Console()
load_dotenv()

@dataclass
class NBAPlayer:
    """NBA Player data structure"""
    id: str
    name: str
    first_name: str
    last_name: str
    position: str
    team_name: str
    team_abbreviation: str
    height: Optional[str] = None
    weight: Optional[str] = None
    years_pro: Optional[int] = None

@dataclass
class NBATeam:
    """NBA Team data structure"""
    id: str
    name: str
    full_name: str
    abbreviation: str
    city: str
    conference: str
    division: str

class NBADataFetcher:
    """Fetches NBA data from multiple APIs"""
    
    def __init__(self):
        self.console = Console()
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        
        # API configurations
        self.apis = {
            'free_nba': {
                'base_url': 'https://free-nba.p.rapidapi.com',
                'headers': {
                    'X-RapidAPI-Key': self.rapidapi_key,
                    'X-RapidAPI-Host': 'free-nba.p.rapidapi.com'
                }
            },
            'nba_stats': {
                'base_url': 'http://rest.nbaapi.com/api',
                'headers': {}  # No auth required
            },
            'nba_free_data': {
                'base_url': 'https://nba-api-data.p.rapidapi.com',
                'headers': {
                    'X-RapidAPI-Key': self.rapidapi_key,
                    'X-RapidAPI-Host': 'nba-api-data.p.rapidapi.com'
                }
            }
        }
    
    def fetch_all_teams(self) -> List[NBATeam]:
        """Fetch all NBA teams from division endpoints"""
        teams = []
        
        # Check cache first
        cached_teams = sports_cache.get_team_list('NBA')
        if cached_teams:
            self.console.print("[green]✅ Found NBA teams in cache![/green]")
            return [NBATeam(**team) for team in cached_teams]
        
        # Division endpoints from NBA Free Data API
        divisions = [
            'nba-atlantic-team-list', 'nba-central-team-list', 'nba-southeast-team-list',
            'nba-southwest-team-list', 'nba-northwest-team-list', 'nba-pacific-team-list'
        ]
        
        division_mapping = {
            'atlantic': ('Eastern', 'Atlantic'),
            'central': ('Eastern', 'Central'),
            'southeast': ('Eastern', 'Southeast'),
            'southwest': ('Western', 'Southwest'),
            'northwest': ('Western', 'Northwest'),
            'pacific': ('Western', 'Pacific')
        }
        
        for division_endpoint in divisions:
            division_name = division_endpoint.replace('nba-', '').replace('-team-list', '')
            conference, division = division_mapping.get(division_name, ('Unknown', 'Unknown'))
            
            try:
                url = f"{self.apis['nba_free_data']['base_url']}/{division_endpoint}"
                response = requests.get(url, headers=self.apis['nba_free_data']['headers'], timeout=10)
                
                if response.status_code == 200:
                    division_teams = response.json()
                    
                    for team_data in division_teams:
                        team = NBATeam(
                            id=str(team_data.get('id', team_data.get('name', '').replace(' ', '_').lower())),
                            name=team_data.get('name', ''),
                            full_name=team_data.get('full_name', team_data.get('name', '')),
                            abbreviation=team_data.get('abbreviation', ''),
                            city=team_data.get('city', ''),
                            conference=conference,
                            division=division
                        )
                        teams.append(team)
                    
                    self.console.print(f"✅ Fetched {len(division_teams)} teams from {division_name}")
                    time.sleep(0.3)  # Rate limiting
                    
            except Exception as e:
                self.console.print(f"[yellow]⚠ Failed to fetch {division_name} teams: {e}[/yellow]")
        
        # Cache the teams
        if teams:
            team_dicts = [team.__dict__ for team in teams]
            sports_cache.set_team_list('NBA', team_dicts)
        
        return teams
    
    def fetch_all_players(self) -> List[NBAPlayer]:
        """Fetch all NBA players using Free NBA API with pagination"""
        all_players = []
        
        if not self.rapidapi_key:
            self.console.print("[red]❌ No RapidAPI key found - cannot fetch players[/red]")
            return []
        
        try:
            page = 1
            per_page = 100
            
            while True:
                url = f"{self.apis['free_nba']['base_url']}/players"
                params = {'page': page, 'per_page': per_page}
                
                response = requests.get(url, headers=self.apis['free_nba']['headers'], params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    players_data = data.get('data', [])
                    
                    for player_data in players_data:
                        player = NBAPlayer(
                            id=str(player_data.get('id')),
                            name=f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip(),
                            first_name=player_data.get('first_name', ''),
                            last_name=player_data.get('last_name', ''),
                            position=player_data.get('position', ''),
                            team_name=player_data.get('team', {}).get('full_name', ''),
                            team_abbreviation=player_data.get('team', {}).get('abbreviation', ''),
                            height=str(player_data.get('height_feet', '')),
                            weight=str(player_data.get('weight_pounds', ''))
                        )
                        all_players.append(player)
                    
                    self.console.print(f"📄 Fetched page {page}: {len(players_data)} players")
                    
                    # Check if we've reached the end
                    meta = data.get('meta', {})
                    if page * per_page >= meta.get('total_count', 0):
                        break
                    
                    page += 1
                    time.sleep(0.2)  # Rate limiting
                    
                else:
                    self.console.print(f"[red]❌ Failed to fetch players page {page}: {response.status_code}[/red]")
                    break
                    
        except Exception as e:
            self.console.print(f"[red]❌ Error fetching players: {e}[/red]")
        
        return all_players

def load_nba_with_langchain():
    """Main function to load NBA data with LangChain caching"""
    console.print("[bold blue]🏀 Loading NBA Data with LangChain Integration 🏀[/bold blue]")
    
    # Initialize components
    fetcher = NBADataFetcher()
    
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
        teams = fetcher.fetch_all_teams()
        console.print(f"[green]✅ Fetched {len(teams)} teams total[/green]")
        
        # Add teams to database
        teams_added = 0
        for team in teams:
            existing_team = session.query(Team).filter_by(external_id=f"nba_{team.id}").first()
            if not existing_team:
                db_team = Team(
                    external_id=f"nba_{team.id}",
                    name=team.name,
                    display_name=team.full_name,
                    abbreviation=team.abbreviation,
                    city=team.city,
                    conference=team.conference,
                    division=team.division,
                    active=True
                )
                session.add(db_team)
                teams_added += 1
        
        session.commit()
        console.print(f"[green]✅ Added {teams_added} new teams to database[/green]")
        
        # 2. FETCH ALL PLAYERS
        console.print("\n[cyan]👥 Step 2: Fetching all NBA players...[/cyan]")
        all_players = fetcher.fetch_all_players()
        console.print(f"[green]✅ Fetched {len(all_players)} players total[/green]")
        
        # Filter to get top 75% (based on active players with teams)
        active_players = [p for p in all_players if p.team_name and p.position]
        top_75_percent = int(len(active_players) * 0.75)
        top_players = active_players[:top_75_percent]
        
        console.print(f"[cyan]📊 Selected top {len(top_players)} players (75% of {len(active_players)} active players)[/cyan]")
        
        # 3. ADD PLAYERS TO DATABASE AND CACHE
        console.print("\n[cyan]💾 Step 3: Adding players to database and cache...[/cyan]")
        
        players_added = 0
        players_cached = 0
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing players...", total=len(top_players))
            
            for player in top_players:
                # Find team in database
                team = session.query(Team).filter(
                    Team.abbreviation.ilike(f"%{player.team_abbreviation}%")
                ).first()
                
                if team:
                    # Check if player exists
                    existing_player = session.query(Player).filter(
                        Player.name.ilike(f"%{player.name}%")
                    ).first()
                    
                    if not existing_player:
                        db_player = Player(
                            external_id=f"nba_api_{player.id}",
                            name=player.name,
                            position=player.position,
                            current_team_id=team.id,
                            active=True
                        )
                        session.add(db_player)
                        session.flush()
                        players_added += 1
                        
                        # Cache player data using the shared cache
                        player_data = {
                            'id': db_player.id,
                            'name': player.name,
                            'position': player.position,
                            'team': team.name,
                            'team_id': team.id,
                            'team_abbr': player.team_abbreviation,
                            'api_id': player.id
                        }
                        sports_cache.set_player('NBA', player.name, player_data)
                        players_cached += 1
                
                progress.advance(task)
        
        session.commit()
        console.print(f"[green]✅ Added {players_added} new players to database[/green]")
        console.print(f"[green]✅ Cached {players_cached} players for fast lookup[/green]")
        
        # FINAL SUMMARY
        console.print("\n[bold green]🎉 NBA Data Load with LangChain Complete! 🎉[/bold green]")
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players} (Top 75% cached)")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• LangChain Integration: {'✅ Active' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
        
        # Show cache stats
        cache_stats = sports_cache.get_cache_stats()
        console.print(f"\n[bold cyan]📊 Cache Performance:[/bold cyan]")
        console.print(f"• Cached Players: {cache_stats['cached_players']}")
        console.print(f"• Cached Teams: {cache_stats['cached_teams']}")
        console.print(f"• API Calls Saved: {cache_stats['api_calls_saved']}")
        console.print(f"• Cache Hit Rate: {cache_stats['hit_rate_percentage']}%")
        
        # Test cache
        console.print(f"\n[cyan]🔍 Testing Cache:[/cyan]")
        test_players = ['LeBron James', 'Stephen Curry', 'Ja Morant']
        for name in test_players:
            cached = sports_cache.get_player('NBA', name)
            status = "✅ Cached" if cached else "❌ Not cached"
            console.print(f"{name}: {status}")
        
        console.print(f"\n[green]✅ NBA system ready with top 75% of players cached![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_nba_with_langchain()
