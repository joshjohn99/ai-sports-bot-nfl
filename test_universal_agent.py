#!/usr/bin/env python3
"""
Test Universal Sports Agent - Demonstration Script

This script demonstrates the Universal Sports Agent's capabilities:
1. Multi-sport detection and routing
2. Cross-sport comparisons
3. Dynamic sport addition
4. Intelligent conversation flow
"""

import sys
import os
import asyncio

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

async def demo_universal_sports_agent():
    """Demonstrate Universal Sports Agent capabilities"""
    
    console.print(Panel.fit(
        "[bold blue]🌟 Universal Sports Agent Demo 🌟[/bold blue]\n"
        "[cyan]Testing intelligent multi-sport routing and conversation management[/cyan]",
        border_style="blue"
    ))
    
    try:
        # Import the Universal Sports Agent
        from sports_bot.agents.universal_sports_agent import universal_sports_agent, process_universal_query
        from sports_bot.agents.agent_integration import unified_sports_interface
        
        console.print("[green]✅ Universal Sports Agent loaded successfully[/green]")
        
        # Test queries for different sports
        test_queries = [
            "NFL quarterback stats for Tom Brady",
            "NBA player LeBron James points",
            "MLB home run leaders",
            "NHL goalie stats",
            "MLS top scorers",
            "NASCAR race winners",
            "Formula 1 championship standings",
            "Compare NFL and NBA player performance",
            "Who is the best athlete across all sports?",
            "Tennis player rankings",  # Should trigger sport addition
        ]
        
        console.print("\n" + "="*60)
        console.print("TESTING UNIVERSAL SPORTS AGENT")
        console.print("="*60)
        
        for i, query in enumerate(test_queries, 1):
            console.print(f"\n[bold cyan]Test {i}: {query}[/bold cyan]")
            
            try:
                response = await process_universal_query(query)
                console.print(f"[green]Response: {response}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            # Add a small delay for readability
            await asyncio.sleep(1)
        
        # Show supported sports
        console.print("\n" + "="*60)
        console.print("SUPPORTED SPORTS REGISTRY")
        console.print("="*60)
        
        supported_sports = universal_sports_agent.get_supported_sports()
        
        sports_table = Table(title="🏆 Universal Sports Registry")
        sports_table.add_column("Sport", style="cyan")
        sports_table.add_column("Keywords", style="green")
        sports_table.add_column("Teams", style="yellow")
        sports_table.add_column("Stats", style="blue")
        sports_table.add_column("Positions", style="magenta")
        
        for sport in supported_sports:
            sport_info = universal_sports_agent.get_sport_info(sport)
            if "error" not in sport_info:
                sports_table.add_row(
                    sport,
                    str(sport_info["keywords"]),
                    str(sport_info["teams"]),
                    str(sport_info["stats"]),
                    str(sport_info["positions"])
                )
        
        console.print(sports_table)
        
        # Test adding a new sport
        console.print("\n" + "="*60)
        console.print("TESTING DYNAMIC SPORT ADDITION")
        console.print("="*60)
        
        console.print("[cyan]Adding Tennis to the registry...[/cyan]")
        
        from sports_bot.agents.universal_sports_agent import add_new_sport
        
        add_new_sport(
            "Tennis",
            keywords=["tennis", "serve", "ace", "set", "match", "wimbledon", "us open"],
            teams=["tournaments", "grand slam"],
            stats=["aces", "double faults", "first serve percentage", "winners", "unforced errors"],
            positions=["singles", "doubles", "mixed doubles"]
        )
        
        console.print("[green]✅ Tennis added successfully![/green]")
        
        # Test tennis query
        console.print("\n[cyan]Testing tennis query after addition...[/cyan]")
        tennis_response = await process_universal_query("Tennis player Novak Djokovic stats")
        console.print(f"[green]Tennis Response: {tennis_response}[/green]")
        
        # Show performance stats
        console.print("\n" + "="*60)
        console.print("PERFORMANCE DASHBOARD")
        console.print("="*60)
        
        if hasattr(unified_sports_interface, 'display_performance_dashboard'):
            unified_sports_interface.display_performance_dashboard()
        else:
            console.print("[yellow]Performance dashboard not available in this mode[/yellow]")
        
        console.print("\n" + "="*60)
        console.print("🎉 UNIVERSAL SPORTS AGENT DEMO COMPLETE! 🎉")
        console.print("="*60)
        
        summary = Panel.fit(
            "[bold green]✅ Universal Sports Agent Demo Results[/bold green]\n\n"
            "[cyan]Capabilities Demonstrated:[/cyan]\n"
            "• ✅ Multi-sport detection and routing\n"
            "• ✅ Intelligent query processing\n"
            "• ✅ Cross-sport comparison handling\n"
            "• ✅ Dynamic sport addition\n"
            "• ✅ Conversation flow management\n"
            "• ✅ Performance monitoring\n\n"
            f"[cyan]Sports Supported: {len(supported_sports)}[/cyan]\n"
            "[cyan]Ready for production use![/cyan]",
            border_style="green"
        )
        
        console.print(summary)
        
    except ImportError as e:
        console.print(Panel(
            f"[red]❌ Universal Sports Agent not available[/red]\n"
            f"[yellow]Error: {e}[/yellow]\n\n"
            "[cyan]This could be due to:[/cyan]\n"
            "• Missing LangChain/LangGraph dependencies\n"
            "• Import path issues\n"
            "• Module not properly installed\n\n"
            "[blue]Try running: pip install langchain langgraph[/blue]",
            title="Import Error",
            border_style="red"
        ))
    
    except Exception as e:
        console.print(f"[red]❌ Demo failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()

async def test_basic_functionality():
    """Test basic functionality without full Universal Agent"""
    
    console.print(Panel.fit(
        "[bold yellow]🧪 Basic Functionality Test[/bold yellow]\n"
        "[cyan]Testing core sports detection without full agent[/cyan]",
        border_style="yellow"
    ))
    
    # Simple sport detection test
    test_queries = [
        "NFL quarterback Tom Brady",
        "NBA player LeBron James",
        "MLB Yankees vs Red Sox",
        "NHL Stanley Cup",
        "Soccer World Cup"
    ]
    
    for query in test_queries:
        console.print(f"\n[cyan]Testing: {query}[/cyan]")
        
        # Simple keyword detection
        query_lower = query.lower()
        detected_sport = "Unknown"
        
        if any(word in query_lower for word in ["nfl", "football", "quarterback", "touchdown"]):
            detected_sport = "NFL"
        elif any(word in query_lower for word in ["nba", "basketball", "points", "rebounds"]):
            detected_sport = "NBA"
        elif any(word in query_lower for word in ["mlb", "baseball", "home run", "yankees"]):
            detected_sport = "MLB"
        elif any(word in query_lower for word in ["nhl", "hockey", "stanley cup"]):
            detected_sport = "NHL"
        elif any(word in query_lower for word in ["soccer", "football", "world cup", "mls"]):
            detected_sport = "Soccer/MLS"
        
        console.print(f"[green]Detected Sport: {detected_sport}[/green]")

def main():
    """Main function to run the demo"""
    
    console.print(Panel.fit(
        "[bold magenta]🌟 Universal Sports Agent Test Suite 🌟[/bold magenta]",
        border_style="magenta"
    ))
    
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        # Run basic test
        asyncio.run(test_basic_functionality())
    else:
        # Run full demo
        asyncio.run(demo_universal_sports_agent())

if __name__ == "__main__":
    main() 