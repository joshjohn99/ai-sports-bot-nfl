#!/usr/bin/env python3
"""
AI Sports Bot NFL - Main Entry Point
Run this script to start the interactive sports bot.
"""

import sys
import os

# No longer needed after installing with 'pip install -e .'

# Import and run the main sports agent
from sports_bot.core.agents.sports_agents import main as sports_agent_main
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

if __name__ == "__main__":
    console = Console()
    
    # Create a welcoming panel
    welcome_message = Text("\n🏈 Welcome to the AI Sports Bot NFL! 🏈\n", style="bold magenta on white", justify="center")
    instructions = Text("Type 'exit' or 'quit' to stop the bot.\nAsk me anything about NFL players or teams!", style="cyan")
    info_panel = Panel(
        Text.assemble(welcome_message, "\n", instructions),
        title="[bold green]AI Sports Bot NFL[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print(info_panel)
    console.print("-" * 50, style="dim green")
    
    # Run the main function from sports_agents
    sports_agent_main() 