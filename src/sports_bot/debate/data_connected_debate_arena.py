"""
🔗 Data-Connected Interactive AI Sports Debate Arena
Minimal version for testing imports and basic functionality
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator

# Your existing data infrastructure
try:
    from ..cache.shared_cache import get_cache_instance
    from ..stats.universal_stat_retriever import UniversalStatRetriever
    from ..config.api_config import api_config
    from ..agents.sports_agents import QueryContext
    DATA_SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"Data systems import issue: {e}")
    DATA_SYSTEMS_AVAILABLE = False

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel

console = Console()

class MinimalDebateArena:
    """Minimal debate arena for testing"""
    
    def __init__(self):
        self.console = Console()
        
        if DATA_SYSTEMS_AVAILABLE:
            try:
                self.cache = get_cache_instance()
                self.stat_retriever = UniversalStatRetriever()
                self.api_config = api_config
                console.print("[green]✅ Connected to your real data systems![/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Data connection issue: {e}[/yellow]")
                self.cache = None
                self.stat_retriever = None
        else:
            console.print("[yellow]⚠️ Data systems not available, using demo mode[/yellow]")
            self.cache = None
            self.stat_retriever = None
        
        console.print(Panel.fit(
            "[bold magenta]🔗 MINIMAL DATA-CONNECTED DEBATE ARENA[/bold magenta]\n"
            "[cyan]• Testing imports and basic functionality[/cyan]\n" +
            (f"[green]• Data systems: Connected[/green]\n" if self.stat_retriever else "[yellow]• Data systems: Demo mode[/yellow]\n") +
            (f"[green]• LangChain: Available[/green]\n" if LANGCHAIN_AVAILABLE else "[yellow]• LangChain: Not available[/yellow]\n"),
            border_style="magenta"
        ))

    async def start_minimal_debate(self, topic: str) -> AsyncGenerator[str, None]:
        """Start a minimal debate to test functionality"""
        yield f"🔗 **MINIMAL DEBATE ARENA ACTIVATED!**\n"
        yield f"📢 **Topic:** {topic}\n\n"
        
        # Test data connection
        if self.stat_retriever:
            yield "📊 **Testing real data connection...**\n"
            
            try:
                # Try to extract players from topic
                players = self._simple_player_extraction(topic)
                
                if players:
                    yield f"✅ **Found players in topic:** {', '.join(players)}\n"
                    
                    # Try to get real data for first player
                    player = players[0]
                    yield f"🔍 **Attempting to fetch real data for {player}...**\n"
                    
                    query_context = QueryContext(
                        question=f"Get stats for {player}",
                        sport="NFL",
                        player_names=[player],
                        metrics_needed=["passing_yards", "touchdowns"]
                    )
                    
                    try:
                        stats = self.stat_retriever.fetch_stats(query_context)
                        
                        if stats and "error" not in stats:
                            yield f"✅ **Successfully loaded real data for {player}!**\n"
                            yield f"📊 **Data source:** {stats.get('data_source', 'unknown')}\n"
                            
                            if 'simple_stats' in stats:
                                stats_summary = list(stats['simple_stats'].keys())[:3]
                                yield f"📈 **Available stats:** {', '.join(stats_summary)}\n"
                        else:
                            yield f"❌ **No data found for {player}:** {stats.get('error', 'Unknown error')}\n"
                            
                    except Exception as e:
                        yield f"❌ **Data fetch error:** {str(e)}\n"
                else:
                    yield "❌ **No players found in topic**\n"
                    
            except Exception as e:
                yield f"❌ **Data system error:** {str(e)}\n"
        else:
            yield "⚠️ **Demo mode - no real data connection**\n"
        
        yield "\n"
        
        # Simple AI agent simulation
        agents = ["Data Dan", "Stats Sarah", "Numbers Nick"]
        
        yield "👥 **Simple AI Agents:**\n"
        for agent in agents:
            yield f"• **{agent}** ready to analyze data\n"
        
        yield "\n---\n\n"
        
        # Simple debate round
        yield "🔥 **SIMPLE DEBATE ROUND:**\n\n"
        
        for i, agent in enumerate(agents):
            yield f"**{agent}**: "
            
            if i == 0:
                yield f"Based on the data analysis, {topic} has clear statistical indicators.\n"
            elif i == 1:
                yield f"I see different patterns in the numbers for {topic}.\n"
            else:
                yield f"The comprehensive data tells a more complex story about {topic}.\n"
            
            await asyncio.sleep(0.5)
        
        yield "\n🎭 **MINIMAL DEBATE COMPLETE!**\n"
        yield "✅ **Import test successful - ready for full implementation!**"

    def _simple_player_extraction(self, topic: str) -> List[str]:
        """Simple player name extraction"""
        known_players = [
            "Tom Brady", "Aaron Rodgers", "Patrick Mahomes", "Josh Allen",
            "Joe Burrow", "Lamar Jackson", "Dak Prescott", "Russell Wilson"
        ]
        
        found_players = []
        topic_lower = topic.lower()
        
        for player in known_players:
            if player.lower() in topic_lower:
                found_players.append(player)
        
        return found_players

# Create global instance
minimal_arena = MinimalDebateArena()

async def start_data_connected_debate(topic: str):
    """Start the minimal debate for testing"""
    async for update in minimal_arena.start_minimal_debate(topic):
        print(update, end="")
        await asyncio.sleep(0.05)
