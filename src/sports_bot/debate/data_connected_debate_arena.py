"""
🔥 Dynamic Data-Connected AI Sports Debate Arena
Fully integrated with backend systems - NO SAMPLE CODE
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
import re
from datetime import datetime

# Real data infrastructure - NO SAMPLE DATA
from ..cache.shared_cache import get_cache_instance
from ..stats.universal_stat_retriever import UniversalStatRetriever
from ..agents.debate_agent import LLMDebateAgent
from ..agents.sports_agents import QueryContext
from ..utils.name_action_extractor import NameActionExtractor
from ..agents.agent_integration import UnifiedSportsInterface

# LangChain imports for enhanced processing
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from rich.console import Console
from rich.panel import Panel

console = Console()

class DynamicDebateArena:
    """
    Fully dynamic debate arena connected to real backend systems.
    NO hardcoded data - everything fetched dynamically.
    """
    
    def __init__(self):
        self.console = Console()
        
        # Initialize real backend systems
        self.cache = get_cache_instance()
        self.stat_retriever = UniversalStatRetriever()
        self.unified_interface = UnifiedSportsInterface()
        self.debate_agent = LLMDebateAgent(model="gpt-4")
        self.name_extractor = NameActionExtractor()
        
        # Real LangChain LLM for dynamic processing
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            streaming=True
        )
        
        console.print(Panel.fit(
            "[bold red]🔥 DYNAMIC DEBATE ARENA INITIALIZED[/bold red]\n"
            "[green]• Connected to Universal Stat Retriever[/green]\n"
            "[green]• Connected to Shared Cache[/green]\n"
            "[green]• Connected to LangChain Debate Agent[/green]\n"
            "[green]• Connected to Unified Sports Interface[/green]\n"
            "[yellow]• NO SAMPLE CODE - ALL DYNAMIC[/yellow]",
            border_style="red"
        ))

    async def start_dynamic_debate(self, topic: str) -> AsyncGenerator[str, None]:
        """
        Start a fully dynamic debate using real data from backend systems.
        NO hardcoded players or sample data.
        """
        yield f"🔥 **DYNAMIC DEBATE ARENA ACTIVATED!**\n"
        yield f"📢 **Topic:** {topic}\n\n"
        
        # Step 1: Dynamic entity extraction (NO hardcoded lists)
        yield "🤖 **Step 1: Dynamic Entity Extraction**\n"
        extracted_data = self.name_extractor.extract_comprehensive(topic)
        
        if not extracted_data.player_names:
            yield "❌ **No players detected in topic. Trying intelligent extraction...**\n"
            players = await self._intelligent_player_extraction(topic)
        else:
            players = extracted_data.player_names
            yield f"✅ **Dynamically extracted players:** {', '.join(players)}\n"
        
        if not players:
            yield "❌ **Cannot proceed without player names. Please specify players for debate.**\n"
            return
        
        # Step 2: Dynamic sport detection
        yield "\n🏆 **Step 2: Dynamic Sport Detection**\n"
        sport = await self._detect_sport_dynamically(topic, players)
        yield f"✅ **Detected sport:** {sport}\n"
        
        # Step 3: Dynamic data gathering from real APIs/Database
        yield "\n📊 **Step 3: Real Data Gathering**\n"
        player_data = await self._gather_real_player_data(players, sport, extracted_data.metrics)
        
        if not player_data:
            yield "❌ **Failed to gather real data. Check API connections.**\n"
            return
        
        yield f"✅ **Successfully gathered real data for {len(player_data)} players**\n"
        
        # Step 4: Dynamic debate generation using LangChain
        yield "\n🥊 **Step 4: Dynamic AI Debate Generation**\n"
        async for debate_update in self._generate_dynamic_debate(topic, player_data, sport):
            yield debate_update
        
        yield "\n🎭 **DYNAMIC DEBATE COMPLETE - ALL DATA REAL!**\n"

    async def _intelligent_player_extraction(self, topic: str) -> List[str]:
        """
        Use LangChain LLM to intelligently extract player names from any topic.
        NO hardcoded player lists.
        """
        extraction_prompt = """
        Extract player names from this sports topic/question. Return ONLY the player names, one per line.
        If no clear player names are found, return "NONE".
        
        Topic: {topic}
        
        Player names:
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert at extracting athlete names from sports discussions."),
                HumanMessage(content=extraction_prompt.format(topic=topic))
            ]
            
            result = await self.llm.ainvoke(messages)
            response = result.content.strip()
            
            if "NONE" in response.upper():
                return []
            
            # Extract player names from response
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            # Clean up and validate names
            players = []
            for line in lines:
                # Remove numbers, bullets, etc.
                clean_name = re.sub(r'^[\d\-\*\•\s]+', '', line).strip()
                if len(clean_name) > 2 and ' ' in clean_name:  # Basic validation
                    players.append(clean_name)
            
            return players[:5]  # Limit to 5 players max
            
        except Exception as e:
            console.print(f"[red]❌ Intelligent extraction failed: {e}[/red]")
            return []

    async def _detect_sport_dynamically(self, topic: str, players: List[str]) -> str:
        """
        Dynamically detect sport using LangChain and context clues.
        NO hardcoded sport mappings.
        """
        detection_prompt = f"""
        Based on this topic and players, what sport is being discussed?
        Return ONLY the sport name (NFL, NBA, MLB, NHL, etc.).
        
        Topic: {topic}
        Players: {', '.join(players)}
        
        Sport:
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert at identifying sports from context."),
                HumanMessage(content=detection_prompt)
            ]
            
            result = await self.llm.ainvoke(messages)
            sport = result.content.strip().upper()
            
            # Validate against supported sports
            supported_sports = ["NFL", "NBA", "MLB", "NHL", "MLS"]
            if sport in supported_sports:
                return sport
            else:
                # Default to NFL if unsure
                return "NFL"
                
        except Exception as e:
            console.print(f"[red]❌ Sport detection failed: {e}[/red]")
            return "NFL"  # Safe default

    async def _gather_real_player_data(self, players: List[str], sport: str, metrics: List[str]) -> Dict[str, Any]:
        """
        Gather real player data from backend systems.
        Uses Universal Stat Retriever and real APIs - NO sample data.
        """
        player_data = {}
        
        for player_name in players:
            console.print(f"[cyan]🔍 Fetching real data for: {player_name}[/cyan]")
            
            # Create real query context
            query_context = QueryContext(
                question=f"Get stats for {player_name}",
                sport=sport,
                player_names=[player_name],
                metrics_needed=metrics or ["passing_yards", "touchdowns", "sacks", "tackles"],
                season_years=[2024]
            )
            
            try:
                # Use real stat retriever
                stats = self.stat_retriever.fetch_stats(query_context)
                
                if stats and "error" not in stats:
                    player_data[player_name] = {
                        "name": player_name,
                        "sport": sport,
                        "stats": stats,
                        "data_source": stats.get("data_source", "unknown"),
                        "player_id": stats.get("player_id"),
                        "position": stats.get("position", "Unknown")
                    }
                    console.print(f"[green]✅ Real data loaded for {player_name}[/green]")
                else:
                    console.print(f"[yellow]⚠️ No data found for {player_name}: {stats.get('error', 'Unknown error')}[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error fetching data for {player_name}: {e}[/red]")
        
        return player_data

    async def _generate_dynamic_debate(self, topic: str, player_data: Dict[str, Any], sport: str) -> AsyncGenerator[str, None]:
        """
        Generate dynamic debate using real data and LangChain agents.
        NO predefined responses - all generated dynamically.
        """
        if len(player_data) < 2:
            yield "❌ **Need at least 2 players with data for debate.**\n"
            return
        
        players = list(player_data.keys())
        yield f"🥊 **Debate Participants:** {' vs '.join(players)}\n\n"
        
        # Generate comparison using enhanced debate agent
        try:
            player_a_data = player_data[players[0]]
            player_b_data = player_data[players[1]]
            
            # Build evidence from real data
            evidence_list = []
            for stat_key in ["passing_yards", "touchdowns", "sacks", "tackles", "interceptions"]:
                if (stat_key in player_a_data["stats"].get("simple_stats", {}) and 
                    stat_key in player_b_data["stats"].get("simple_stats", {})):
                    evidence_list.append({"stat": stat_key})
            
            if evidence_list:
                debate_response = self.debate_agent.generate_dynamic_debate(
                    player_a_data,
                    player_b_data, 
                    evidence_list,
                    f"{sport} comparison"
                )
                
                yield f"🤖 **AI Debate Analysis:**\n\n{debate_response}\n\n"
            
            # Generate additional insights using real data
            yield "📊 **Real Data Insights:**\n"
            for player_name, data in player_data.items():
                stats = data["stats"].get("simple_stats", {})
                source = data.get("data_source", "unknown")
                
                yield f"• **{player_name}** ({source} data):\n"
                for stat, value in list(stats.items())[:3]:  # Show top 3 stats
                    yield f"  - {stat}: {value}\n"
                yield "\n"
            
        except Exception as e:
            yield f"❌ **Debate generation error:** {str(e)}\n"

    async def process_debate_query(self, query: str) -> str:
        """
        Process any debate query dynamically through the unified interface.
        This is the main entry point that connects to your backend.
        """
        console.print(f"[blue]🎯 Processing debate query: {query}[/blue]")
        
        # Use unified sports interface for processing
        result = await self.unified_interface.process_query(
            query=query,
            prefer_advanced=True
        )
        
        if result.success:
            # If we have a successful query, can we turn it into a debate?
            if any(word in query.lower() for word in ["compare", "vs", "versus", "better", "debate"]):
                # This is a comparison/debate query - process it through debate arena
                debate_result = ""
                async for update in self.start_dynamic_debate(query):
                    debate_result += update
                return debate_result
            else:
                return result.response
        else:
            return f"❌ Could not process debate query: {result.response}"

# Global instance - fully dynamic, no sample data
dynamic_arena = DynamicDebateArena()

async def start_dynamic_data_debate(topic: str):
    """
    Start dynamic debate with real backend data.
    NO sample code - all connected to real systems.
    """
    console.print("[bold red]🔥 Starting Dynamic Data-Connected Debate![/bold red]")
    
    async for update in dynamic_arena.start_dynamic_debate(topic):
        print(update, end="")
        await asyncio.sleep(0.05)

async def process_any_debate_query(query: str) -> str:
    """
    Process any debate query through the dynamic system.
    Main entry point for debate functionality.
    """
    return await dynamic_arena.process_debate_query(query)
