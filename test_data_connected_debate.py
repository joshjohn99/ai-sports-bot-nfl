#!/usr/bin/env python3
"""
🔗 Data-Connected Interactive AI Sports Debate Arena Demo
"""

import asyncio
import sys
import os

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

async def demo_data_connected_debate():
    """Demo the data-connected debate arena"""
    
    console.print(Panel.fit(
        "[bold red]🔗 DATA-CONNECTED DEBATE ARENA[/bold red]\n"
        "[yellow]AI Personalities argue with REAL sports data![/yellow]\n"
        "[yellow]Agents can request more data mid-debate![/yellow]\n" 
        "[yellow]Connected to your cache, database, and API![/yellow]",
        border_style="red"
    ))
    
    try:
        # Import with proper path
        from sports_bot.debate.data_connected_debate_arena import start_data_connected_debate
        
        console.print("[green]✅ Successfully imported debate arena![/green]")
        
        # Demo topics with real players
        topics = [
            ("Who is the better quarterback: Tom Brady or Aaron Rodgers?", ["Tom Brady", "Aaron Rodgers"]),
            ("Is Patrick Mahomes already elite?", ["Patrick Mahomes"]),
            ("Who has the best receiving corps in the NFL?", []),
            ("Should Josh Allen be considered a top 3 QB?", ["Josh Allen"])
        ]
        
        console.print("\n🎯 **Choose a data-driven debate:**")
        for i, (topic, players) in enumerate(topics, 1):
            player_info = f" ({', '.join(players)})" if players else " (League-wide analysis)"
            console.print(f"{i}. {topic}{player_info}")
        
        choice = Prompt.ask("Enter your choice (1-4)", choices=["1", "2", "3", "4"], default="1")
        selected_topic, selected_players = topics[int(choice) - 1]
        
        console.print(f"\n🔥 **Starting data-connected debate:**")
        console.print(f"📢 **Topic:** {selected_topic}")
        
        if selected_players:
            console.print(f"👥 **Players:** {', '.join(selected_players)}")
        
        console.print("\n�� **Connecting to your real data systems...**\n")
        
        # Start the data-connected debate
        await start_data_connected_debate(selected_topic)
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        console.print(f"[yellow]💡 Debug info:[/yellow]")
        console.print(f"   Current directory: {os.getcwd()}")
        console.print(f"   Python path: {sys.path}")
        console.print(f"   Looking for: sports_bot.debate.data_connected_debate_arena")
        
        # Try to show what files exist
        if os.path.exists('src/sports_bot/debate'):
            files = os.listdir('src/sports_bot/debate')
            console.print(f"   Files in debate dir: {files}")
        else:
            console.print("   Debate directory doesn't exist!")
            
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_data_connected_debate())
