#!/usr/bin/env python3
"""
Hybrid Sports Bot - LangChain/LangGraph + Custom Logic Demo

This is the main entry point for the hybrid sports bot that demonstrates
the integration of LangChain/LangGraph frameworks with existing custom logic.

Based on the architectural review recommendations, this implementation provides:
1. Strategic adoption of LangGraph for multi-agent orchestration
2. LangChain tools for standardized API integration  
3. Preservation of optimized custom logic where appropriate
4. Scalable architecture for adding new sports

Usage:
    python hybrid_main.py

Example queries to try:
- "Who leads the NFL in passing yards this season?"
- "Compare Tom Brady vs Aaron Rodgers"
- "Show me the top NBA scorers"
- "What are Lamar Jackson's stats?"
"""

import asyncio
import os
import sys
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sports_bot.langchain_integration.hybrid_agent import get_hybrid_agent_manager
from sports_bot.langchain_integration.sport_registry import get_sport_registry


class HybridSportsBotDemo:
    """
    Interactive demo of the hybrid sports bot architecture
    """
    
    def __init__(self):
        self.console = Console()
        self.agent_manager = get_hybrid_agent_manager()
        self.sport_registry = get_sport_registry()
        self.session_id = "demo_session"
    
    def display_welcome(self):
        """Display welcome message and capabilities"""
        
        welcome_text = """
🏈 🏀 ⚾ Welcome to the Hybrid Sports Bot! 🏒 ⚽ 🎾

This bot combines the power of LangChain/LangGraph frameworks with 
optimized custom sports logic to provide intelligent sports analysis.

Architecture Highlights:
• LangGraph workflows for complex multi-agent analysis
• LangChain tools for standardized API integration
• Custom logic preservation for optimized performance
• Scalable design for easy sport addition
        """
        
        self.console.print(Panel(welcome_text, title="🤖 Hybrid Sports Bot", style="bold blue"))
    
    def display_capabilities(self):
        """Display bot capabilities and supported sports"""
        
        capabilities = self.agent_manager.default_agent.get_supported_capabilities()
        
        # Create sports table
        sports_table = Table(title="🏆 Supported Sports")
        sports_table.add_column("Code", style="cyan")
        sports_table.add_column("League", style="green")
        
        for code, name in capabilities["sports"].items():
            sports_table.add_row(code, name)
        
        # Create query types table
        query_table = Table(title="📊 Query Types")
        query_table.add_column("Type", style="cyan")
        query_table.add_column("Processing Method", style="yellow")
        query_table.add_column("Examples", style="green")
        
        examples = {
            "single_player": "What are Lamar Jackson's stats?",
            "player_comparison": "Compare Brady vs Manning",
            "player_debate": "Who's better: LeBron or Jordan?",
            "league_leaders": "Who leads the NFL in sacks?",
            "team_analysis": "Show me the Cowboys roster",
            "historical_trends": "Best QBs of the 2010s"
        }
        
        for query_type in capabilities["query_types"]:
            # Determine processing method
            method = "Custom Logic"
            if query_type in capabilities["processing_methods"]["langgraph_workflows"]:
                method = "LangGraph Workflow"
            elif query_type in capabilities["processing_methods"]["hybrid_tools"]:
                method = "Hybrid Tools"
            
            query_table.add_row(
                query_type.replace("_", " ").title(),
                method,
                examples.get(query_type, "Various queries")
            )
        
        self.console.print(sports_table)
        self.console.print(query_table)
    
    def display_example_queries(self):
        """Display example queries users can try"""
        
        examples = [
            "🏈 NFL Examples:",
            "  • Who leads the NFL in passing yards?",
            "  • Compare Patrick Mahomes vs Josh Allen",
            "  • What are Aaron Donald's defensive stats?",
            "  • Show me the top NFL rushers this season",
            "",
            "🏀 NBA Examples:",
            "  • Who is the leading scorer in the NBA?",
            "  • Compare LeBron James and Stephen Curry",
            "  • Show me Lakers roster information",
            "",
            "🔧 System Commands:",
            "  • 'help' - Show this help",
            "  • 'capabilities' - Show detailed capabilities",
            "  • 'sports' - List supported sports",
            "  • 'quit' or 'exit' - Exit the demo"
        ]
        
        example_text = "\n".join(examples)
        self.console.print(Panel(example_text, title="💡 Example Queries", style="yellow"))
    
    async def process_user_query(self, user_input: str) -> Dict[str, Any]:
        """Process a user query through the hybrid agent"""
        
        with self.console.status("[bold green]Processing your query..."):
            try:
                result = await self.agent_manager.process_query(
                    user_input=user_input,
                    session_id=self.session_id
                )
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Processing failed: {str(e)}"
                }
    
    def display_result(self, result: Dict[str, Any]):
        """Display the query result in a formatted way"""
        
        if not result.get("success", False):
            error_text = f"❌ Error: {result.get('error', 'Unknown error')}"
            self.console.print(Panel(error_text, style="bold red"))
            return
        
        # Display method used
        method = result.get("method", "unknown")
        query_type = result.get("query_type", "unknown")
        
        method_colors = {
            "langgraph_workflow": "bold magenta",
            "hybrid_tools": "bold cyan", 
            "custom_logic": "bold green"
        }
        
        method_style = method_colors.get(method, "white")
        
        header = f"✅ Processed via: [{method_style}]{method.replace('_', ' ').title()}[/{method_style}] | Query Type: {query_type}"
        self.console.print(header)
        
        # Display the actual result
        result_data = result.get("result", {})
        
        if isinstance(result_data, dict):
            if "output" in result_data:
                # LangChain agent result format
                self.console.print(Panel(result_data["output"], title="🤖 Bot Response", style="green"))
            elif "formatted_response" in result_data:
                # LangGraph workflow result format
                self.console.print(Panel(result_data["formatted_response"], title="📊 Analysis Result", style="blue"))
            elif "final_debate" in result_data:
                # Debate workflow result format
                debate = result_data["final_debate"]
                self.console.print(Panel(debate["moderator_conclusion"], title="⚖️ Debate Conclusion", style="purple"))
            else:
                # Generic result display
                self.console.print(Panel(str(result_data), title="📋 Result", style="white"))
        else:
            self.console.print(Panel(str(result_data), title="📋 Result", style="white"))
        
        # Show analysis details if available
        if "analysis" in result:
            analysis = result["analysis"]
            details = f"""
Sport: {analysis.get('sport', 'N/A')}
Confidence: {analysis.get('confidence', 'N/A')}
Players: {', '.join(analysis.get('player_names', []))}
Metrics: {', '.join(analysis.get('metrics', []))}
            """.strip()
            self.console.print(Panel(details, title="🔍 Query Analysis", style="dim"))
    
    def handle_system_command(self, command: str) -> bool:
        """Handle system commands like help, capabilities, etc."""
        
        command = command.lower().strip()
        
        if command in ["help", "h"]:
            self.display_example_queries()
            return True
        
        elif command in ["capabilities", "cap"]:
            self.display_capabilities()
            return True
        
        elif command in ["sports", "sport"]:
            sports = self.sport_registry.get_sport_display_names()
            sports_text = "\n".join([f"• {code}: {name}" for code, name in sports.items()])
            self.console.print(Panel(sports_text, title="🏆 Supported Sports", style="cyan"))
            return True
        
        elif command in ["quit", "exit", "q"]:
            self.console.print("👋 Thanks for trying the Hybrid Sports Bot!")
            return False
        
        return True
    
    async def add_sport_demo(self):
        """Demonstrate adding a new sport dynamically"""
        
        self.console.print("\n🚀 [bold]Dynamic Sport Addition Demo[/bold]")
        
        # Example: Adding NHL support
        nhl_config = {
            "sport_code": "NHL",
            "display_name": "National Hockey League",
            "api_config": {
                "base_url": "https://nhl-api.p.rapidapi.com",
                "endpoints": {
                    "AllTeams": "/teams",
                    "PlayerStats": "/player-stats"
                }
            },
            "positions": {
                "center": "C", "left wing": "LW", "right wing": "RW",
                "defenseman": "D", "goalie": "G"
            },
            "stat_categories": {
                "scoring": ["goals", "assists", "points"],
                "goaltending": ["wins", "saves", "goals_against_average"]
            },
            "season_format": "YYYY-YY",
            "active_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],
            "team_count": 32,
            "roster_size": 23
        }
        
        agent = self.agent_manager.get_agent(self.session_id)
        result = await agent.add_new_sport(nhl_config)
        
        if result["success"]:
            self.console.print(f"✅ {result['message']}")
            self.console.print(f"Available sports: {', '.join(result['available_sports'])}")
        else:
            self.console.print(f"❌ Failed to add NHL: {result['error']}")
    
    async def run_interactive_demo(self):
        """Run the interactive demo loop"""
        
        self.display_welcome()
        self.display_capabilities()
        self.display_example_queries()
        
        # Demonstrate dynamic sport addition
        await self.add_sport_demo()
        
        self.console.print("\n🎯 [bold]Ready for your queries![/bold] (Type 'help' for examples, 'quit' to exit)")
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]Sports Query")
                
                if not user_input.strip():
                    continue
                
                # Handle system commands
                if user_input.startswith(('help', 'capabilities', 'sports', 'quit', 'exit')):
                    if not self.handle_system_command(user_input):
                        break
                    continue
                
                # Process the query
                result = await self.process_user_query(user_input)
                self.display_result(result)
                
            except KeyboardInterrupt:
                self.console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                self.console.print(f"\n❌ Unexpected error: {e}")


async def run_batch_demo():
    """Run a batch of example queries to demonstrate capabilities"""
    
    console = Console()
    agent_manager = get_hybrid_agent_manager()
    
    console.print(Panel("🚀 Running Batch Demo of Hybrid Sports Bot", style="bold blue"))
    
    example_queries = [
        "What are Patrick Mahomes' passing stats?",
        "Compare LeBron James vs Michael Jordan",
        "Who leads the NFL in sacks this season?",
        "Show me the Lakers roster",
    ]
    
    for i, query in enumerate(example_queries, 1):
        console.print(f"\n[bold]Query {i}:[/bold] {query}")
        
        with console.status("[bold green]Processing..."):
            try:
                result = await agent_manager.process_query(query)
                
                if result.get("success"):
                    method = result.get("method", "unknown")
                    console.print(f"✅ Method: {method}")
                    
                    # Display simplified result
                    result_data = result.get("result", {})
                    if isinstance(result_data, dict) and "output" in result_data:
                        console.print(f"📊 Result: {result_data['output'][:200]}...")
                    else:
                        console.print(f"📊 Result: {str(result_data)[:200]}...")
                else:
                    console.print(f"❌ Error: {result.get('error')}")
                    
            except Exception as e:
                console.print(f"❌ Exception: {e}")


def main():
    """Main entry point"""
    
    # Check if we should run in batch mode
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        asyncio.run(run_batch_demo())
    else:
        # Run interactive demo
        demo = HybridSportsBotDemo()
        asyncio.run(demo.run_interactive_demo())


if __name__ == "__main__":
    main() 