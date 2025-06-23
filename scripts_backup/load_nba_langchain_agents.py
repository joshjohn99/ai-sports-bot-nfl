#!/usr/bin/env python3
"""
NBA Data Loader using LangChain Agents and Framework
Integrates with existing agent architecture for intelligent data processing
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

# Import LangChain components
try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.cache import InMemoryCache
    from langchain.globals import set_llm_cache
    from langchain.tools import Tool
    from langchain.agents import AgentType, initialize_agent
    from langchain.llms import OpenAI
    
    # Set up LangChain cache
    set_llm_cache(InMemoryCache())
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    console.print("[yellow]⚠ LangChain not available - install with: pip install langchain openai[/yellow]")

# Import existing agent framework
try:
    from src.sports_bot.agents.sports_agents import QueryContext, run_query_planner
    from agents import Agent, Runner
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    console.print("[yellow]⚠ Agent framework not available[/yellow]")

console = Console()
load_dotenv()

class LangChainNBALoader:
    """NBA loader using LangChain agents and tools"""
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://nba-api-free-data.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
        }
        
        # Initialize LangChain components
        if LANGCHAIN_AVAILABLE and self.openai_key:
            self.llm = OpenAI(temperature=0)
            self.embeddings = OpenAIEmbeddings()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            self.setup_tools()
        
        self.divisions = [
            'nba-atlantic-team-list',
            'nba-central-team-list', 
            'nba-southeast-team-list',
            'nba-northwest-team-list',
            'nba-pacific-team-list',
            'nba-southwest-team-list'
        ]
    
    def setup_tools(self):
        """Setup LangChain tools for NBA data processing"""
        if not LANGCHAIN_AVAILABLE:
            return
        
        # Tool for fetching team data
        def fetch_teams_tool(division: str) -> str:
            """Fetch NBA teams from a specific division"""
            try:
                url = f"{self.base_url}/{division}"
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                return f"Error: HTTP {response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Tool for fetching player rosters
        def fetch_players_tool(team_id: str) -> str:
            """Fetch NBA players for a specific team"""
            try:
                url = f"{self.base_url}/nba-player-list"
                params = {'teamid': team_id}
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                return f"Error: HTTP {response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Tool for fetching player stats
        def fetch_stats_tool(player_id: str) -> str:
            """Fetch NBA player statistics"""
            try:
                url = f"{self.base_url}/nba-player-stats"
                params = {'playerid': player_id}
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                return f"Error: HTTP {response.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Create LangChain tools
        self.tools = [
            Tool(
                name="fetch_nba_teams",
                description="Fetch NBA teams from a division (nba-atlantic-team-list, nba-central-team-list, etc.)",
                func=fetch_teams_tool
            ),
            Tool(
                name="fetch_team_players",
                description="Fetch NBA players for a specific team using team ID",
                func=fetch_players_tool
            ),
            Tool(
                name="fetch_player_stats",
                description="Fetch detailed statistics for a specific NBA player using player ID",
                func=fetch_stats_tool
            )
        ]
        
        # Initialize agent
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    async def intelligent_team_processing(self) -> List[Dict]:
        """Use LangChain agents to intelligently process team data"""
        console.print("[cyan]🤖 Using LangChain agents for intelligent team processing...[/cyan]")
        
        if not LANGCHAIN_AVAILABLE:
            # Fallback to simple processing
            return await self.simple_team_processing()
        
        all_teams = []
        
        # Use agent to process each division
        for division in self.divisions:
            try:
                query = f"Fetch NBA teams from {division} and extract team information including id, name, abbreviation"
                result = self.agent.run(query)
                
                # Parse agent result
                if "Error" not in result:
                    try:
                        data = json.loads(result)
                        if data.get('status') == 'success' and 'response' in data:
                            team_list = data['response'].get('teamList', [])
                            for team in team_list:
                                team['division'] = division.replace('-team-list', '').replace('nba-', '')
                                all_teams.append(team)
                            console.print(f"  ✅ {division}: {len(team_list)} teams (via agent)")
                    except json.JSONDecodeError:
                        console.print(f"  ⚠ {division}: Agent returned non-JSON response")
                else:
                    console.print(f"  ❌ {division}: {result}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                console.print(f"  ⚠ {division}: Agent error - {e}")
        
        return all_teams
    
    async def simple_team_processing(self) -> List[Dict]:
        """Fallback simple team processing"""
        console.print("[cyan]�� Using simple team processing (LangChain not available)...[/cyan]")
        
        all_teams = []
        
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
                
                time.sleep(0.5)
                
            except Exception as e:
                console.print(f"  ⚠ {division}: {e}")
        
        return all_teams
    
    def create_player_documents(self, players: List[Dict]) -> List[Document]:
        """Create LangChain documents for player data"""
        if not LANGCHAIN_AVAILABLE:
            return []
        
        documents = []
        
        for player in players:
            # Create rich text content for each player
            content = f"""
            Player: {player.get('name', 'Unknown')}
            ID: {player.get('id', 'N/A')}
            Position: {player.get('position', 'N/A')}
            Team: {player.get('source_team_name', 'N/A')}
            Team ID: {player.get('source_team_id', 'N/A')}
            """
            
            metadata = {
                'player_id': player.get('id', ''),
                'player_name': player.get('name', ''),
                'team': player.get('source_team_name', ''),
                'position': player.get('position', ''),
                'type': 'nba_player'
            }
            
            doc = Document(page_content=content.strip(), metadata=metadata)
            documents.append(doc)
        
        return documents
    
    def create_vector_store(self, documents: List[Document]) -> Optional[FAISS]:
        """Create FAISS vector store for semantic search"""
        if not LANGCHAIN_AVAILABLE or not documents:
            return None
        
        try:
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            
            # Create vector store
            vectorstore = FAISS.from_documents(split_docs, self.embeddings)
            
            console.print(f"[green]✅ Created vector store with {len(split_docs)} document chunks[/green]")
            return vectorstore
            
        except Exception as e:
            console.print(f"[red]❌ Error creating vector store: {e}[/red]")
            return None

async def load_nba_with_langchain_agents():
    """Load NBA data using LangChain agents and framework"""
    
    console.print("[bold blue]🏀 Loading NBA Data with LangChain Agents 🏀[/bold blue]")
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    if not os.getenv('OPENAI_API_KEY') and LANGCHAIN_AVAILABLE:
        console.print("[yellow]⚠ OPENAI_API_KEY not found - some LangChain features disabled[/yellow]")
    
    loader = LangChainNBALoader()
    
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
        # Step 1: Intelligent team processing
        console.print("\n" + "="*60)
        console.print("STEP 1: INTELLIGENT TEAM PROCESSING")
        console.print("="*60)
        
        teams_data = await loader.intelligent_team_processing()
        console.print(f"✅ Processed {len(teams_data)} teams")
        
        # Step 2: Add teams to database (same as before)
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
                        external_id=f"nba_langchain_{team_id}",
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
        
        # Step 3: Create LangChain documents and vector store
        console.print(f"\n" + "="*60)
        console.print("STEP 3: CREATING LANGCHAIN VECTOR STORE")
        console.print("="*60)
        
        # For now, create sample player documents
        sample_players = [
            {'id': '4869342', 'name': 'Sample Player 1', 'position': 'G', 'source_team_name': 'Atlanta Hawks'},
            {'id': '3915511', 'name': 'Sample Player 2', 'position': 'F', 'source_team_name': 'Boston Celtics'},
        ]
        
        documents = loader.create_player_documents(sample_players)
        vectorstore = loader.create_vector_store(documents)
        
        if vectorstore:
            # Test semantic search
            console.print("[cyan]🔍 Testing semantic search...[/cyan]")
            test_query = "Find guards from Hawks"
            results = vectorstore.similarity_search(test_query, k=2)
            
            for i, result in enumerate(results):
                console.print(f"  Result {i+1}: {result.metadata.get('player_name', 'Unknown')}")
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 LANGCHAIN NBA DATA LOAD COMPLETE! 🎉")
        console.print("="*60)
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• LangChain Integration: {'✅ Active' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
        console.print(f"• Agent Framework: {'✅ Active' if AGENTS_AVAILABLE else '❌ Not Available'}")
        console.print(f"• Vector Store: {'✅ Created' if vectorstore else '❌ Not Available'}")
        
        console.print(f"\n[green]✅ NBA system ready with LangChain agent architecture![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(load_nba_with_langchain_agents())
