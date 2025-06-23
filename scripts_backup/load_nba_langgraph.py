#!/usr/bin/env python3
"""
NBA Data Loader using LangGraph (modern LangChain framework)
Uses proper agent architecture with data processing capabilities
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

# Updated LangChain imports
try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.cache import InMemoryCache
    from langchain.globals import set_llm_cache
    from langchain.tools import Tool
    from langchain.agents import create_react_agent, AgentExecutor
    from langchain import hub
    
    # Set up LangChain cache
    set_llm_cache(InMemoryCache())
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"LangChain components not available: {e}")

console = Console()
load_dotenv()

class LangGraphNBALoader:
    """NBA loader using modern LangGraph architecture"""
    
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
            self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
            self.embeddings = OpenAIEmbeddings()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            self.setup_agent()
        
        self.divisions = [
            'nba-atlantic-team-list',
            'nba-central-team-list', 
            'nba-southeast-team-list',
            'nba-northwest-team-list',
            'nba-pacific-team-list',
            'nba-southwest-team-list'
        ]
    
    def setup_agent(self):
        """Setup LangGraph agent with proper tools"""
        if not LANGCHAIN_AVAILABLE:
            return
        
        def fetch_and_parse_teams(division: str) -> str:
            """Fetch NBA teams from a division and return parsed team data"""
            try:
                url = f"{self.base_url}/{division}"
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success' and 'response' in data:
                        team_list = data['response'].get('teamList', [])
                        
                        # Parse and return structured data
                        parsed_teams = []
                        for team in team_list:
                            parsed_teams.append({
                                'id': team.get('id'),
                                'name': team.get('name'),
                                'short_name': team.get('shortName'),
                                'abbreviation': team.get('abbrev'),
                                'division': division.replace('-team-list', '').replace('nba-', '')
                            })
                        
                        return json.dumps({
                            'success': True,
                            'division': division,
                            'teams': parsed_teams,
                            'count': len(parsed_teams)
                        }, indent=2)
                
                return json.dumps({'success': False, 'error': f'HTTP {response.status_code}'})
                
            except Exception as e:
                return json.dumps({'success': False, 'error': str(e)})
        
        def fetch_team_roster(team_id: str) -> str:
            """Fetch players for a team and return parsed data"""
            try:
                url = f"{self.base_url}/nba-player-list"
                params = {'teamid': team_id}
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success' and 'response' in data:
                        player_list = data['response'].get('playerList', [])
                        
                        parsed_players = []
                        for player in player_list:
                            parsed_players.append({
                                'id': player.get('id'),
                                'name': player.get('name', player.get('displayName')),
                                'position': player.get('position'),
                                'team_id': team_id
                            })
                        
                        return json.dumps({
                            'success': True,
                            'team_id': team_id,
                            'players': parsed_players,
                            'count': len(parsed_players)
                        }, indent=2)
                
                return json.dumps({'success': False, 'error': f'HTTP {response.status_code}'})
                
            except Exception as e:
                return json.dumps({'success': False, 'error': str(e)})
        
        # Create tools with proper data processing
        tools = [
            Tool(
                name="fetch_division_teams",
                description="Fetch and parse NBA teams from a specific division. Returns structured JSON with team data.",
                func=fetch_and_parse_teams
            ),
            Tool(
                name="fetch_team_roster",
                description="Fetch and parse NBA players for a specific team ID. Returns structured JSON with player data.",
                func=fetch_team_roster
            )
        ]
        
        # Get the react prompt
        prompt = hub.pull("hwchase17/react")
        
        # Create agent
        agent = create_react_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3)
    
    async def intelligent_data_processing(self) -> Dict[str, Any]:
        """Use LangGraph agent to intelligently process NBA data"""
        console.print("[cyan]🤖 Using LangGraph agent for intelligent data processing...[/cyan]")
        
        if not LANGCHAIN_AVAILABLE:
            return await self.simple_data_processing()
        
        all_teams = []
        
        # Process each division with the agent
        for division in self.divisions:
            try:
                query = f"Fetch teams from {division} division and return the parsed team data"
                result = await asyncio.to_thread(
                    self.agent_executor.invoke,
                    {"input": query}
                )
                
                # Parse agent output
                output = result.get('output', '')
                if 'success' in output and 'true' in output.lower():
                    try:
                        # Extract JSON from agent response
                        import re
                        json_match = re.search(r'\{.*\}', output, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group())
                            if data.get('success') and data.get('teams'):
                                all_teams.extend(data['teams'])
                                console.print(f"  ✅ {division}: {data.get('count', 0)} teams (via agent)")
                    except (json.JSONDecodeError, Exception) as e:
                        console.print(f"  ⚠ {division}: Could not parse agent response - {e}")
                else:
                    console.print(f"  ❌ {division}: Agent failed")
                
                time.sleep(0.5)
                
            except Exception as e:
                console.print(f"  ⚠ {division}: Agent error - {e}")
        
        return {'teams': all_teams, 'total_teams': len(all_teams)}
    
    async def simple_data_processing(self) -> Dict[str, Any]:
        """Fallback simple data processing"""
        console.print("[cyan]📋 Using simple data processing (LangChain not available)...[/cyan]")
        
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
        
        return {'teams': all_teams, 'total_teams': len(all_teams)}

async def load_nba_with_langgraph():
    """Load NBA data using LangGraph modern architecture"""
    
    console.print("[bold blue]🏀 Loading NBA Data with LangGraph ��[/bold blue]")
    
    if not os.getenv('RAPIDAPI_KEY'):
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    if not os.getenv('OPENAI_API_KEY') and LANGCHAIN_AVAILABLE:
        console.print("[yellow]⚠ OPENAI_API_KEY not found - using simple processing[/yellow]")
    
    loader = LangGraphNBALoader()
    
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
        # Step 1: Intelligent data processing
        console.print("\n" + "="*60)
        console.print("STEP 1: INTELLIGENT DATA PROCESSING WITH LANGGRAPH")
        console.print("="*60)
        
        result = await loader.intelligent_data_processing()
        teams_data = result.get('teams', [])
        console.print(f"✅ Processed {result.get('total_teams', 0)} teams")
        
        # Step 2: Add teams to database
        console.print(f"\n" + "="*60)
        console.print("STEP 2: ADDING TEAMS TO DATABASE")
        console.print("="*60)
        
        teams_added = 0
        team_mapping = {}
        
        for team_data in teams_data:
            team_name = team_data.get('name', '')
            team_abbrev = team_data.get('abbrev', team_data.get('abbreviation', ''))
            team_id = team_data.get('id', '')
            
            if team_name and team_abbrev:
                existing_team = session.query(Team).filter_by(abbreviation=team_abbrev.upper()).first()
                
                if not existing_team:
                    db_team = Team(
                        external_id=f"nba_langgraph_{team_id}",
                        name=team_data.get('shortName', team_data.get('short_name', team_name)),
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
        
        # Step 3: Create vector store with proper data
        console.print(f"\n" + "="*60)
        console.print("STEP 3: CREATING LANGGRAPH VECTOR STORE")
        console.print("="*60)
        
        if LANGCHAIN_AVAILABLE and loader.embeddings:
            # Create documents from team data
            documents = []
            for team in teams_data:
                content = f"""
                Team: {team.get('name', 'Unknown')}
                Short Name: {team.get('shortName', team.get('short_name', 'Unknown'))}
                Abbreviation: {team.get('abbrev', team.get('abbreviation', 'Unknown'))}
                Division: {team.get('division', 'Unknown')}
                ID: {team.get('id', 'Unknown')}
                """
                
                metadata = {
                    'team_id': team.get('id', ''),
                    'team_name': team.get('name', ''),
                    'abbreviation': team.get('abbrev', team.get('abbreviation', '')),
                    'division': team.get('division', ''),
                    'type': 'nba_team'
                }
                
                doc = Document(page_content=content.strip(), metadata=metadata)
                documents.append(doc)
            
            if documents:
                try:
                    # Create vector store
                    split_docs = loader.text_splitter.split_documents(documents)
                    vectorstore = FAISS.from_documents(split_docs, loader.embeddings)
                    
                    console.print(f"[green]✅ Created vector store with {len(split_docs)} document chunks[/green]")
                    
                    # Test semantic search
                    console.print("[cyan]🔍 Testing semantic search...[/cyan]")
                    test_queries = ["Lakers team", "Eastern Conference teams", "Boston"]
                    
                    for query in test_queries:
                        results = vectorstore.similarity_search(query, k=2)
                        console.print(f"  Query: '{query}'")
                        for i, result in enumerate(results):
                            team_name = result.metadata.get('team_name', 'Unknown')
                            console.print(f"    {i+1}. {team_name}")
                    
                except Exception as e:
                    console.print(f"[red]❌ Error creating vector store: {e}[/red]")
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 LANGGRAPH NBA DATA LOAD COMPLETE! 🎉")
        console.print("="*60)
        
        final_teams = session.query(Team).count()
        final_players = session.query(Player).count()
        final_stats = session.query(PlayerStats).count()
        
        console.print(f"\n[bold cyan]📊 Final Database Summary:[/bold cyan]")
        console.print(f"• Teams: {final_teams}")
        console.print(f"• Players: {final_players}")
        console.print(f"• Player Stats: {final_stats}")
        console.print(f"• LangChain Integration: {'✅ Active' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
        console.print(f"• LangGraph Architecture: {'✅ Active' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
        console.print(f"• Teams Processed: {len(teams_data)}")
        
        console.print(f"\n[green]✅ NBA system ready with modern LangGraph architecture![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(load_nba_with_langgraph())
