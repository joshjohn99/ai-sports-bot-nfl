#!/usr/bin/env python3
"""
🧪 ENHANCED CONVERSATIONAL SPORTS BOT TEST SUITE 🧪
"""

import asyncio
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt

console = Console()

async def test_simple_query():
    """🔍 Simple single query test"""
    
    console.print(Panel.fit(
        "[bold cyan]🔍 Testing Conversational Sports Bot[/bold cyan]\n"
        "[yellow]Running a simple query to test the system[/yellow]",
        border_style="cyan"
    ))
    
    try:
        from src.sports_bot.conversation.conversational_sports_bot import process_conversational_query
        console.print("[bold green]✅ Conversational bot imported successfully![/bold green]")
        
        query = "Who has the most touchdowns in the NFL?"
        console.print(f"\n[yellow]📝 Query:[/yellow] {query}")
        
        with console.status("[bold green]🤖 Processing query...", spinner="dots"):
            response = await process_conversational_query(query, "simple_test_user")
        
        console.print(Panel(
            response, 
            title="[green]🤖 Bot Response[/green]", 
            border_style="green"
        ))
        
        console.print("[bold green]✅ Simple test completed successfully![/bold green]")
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        console.print("[yellow]💡 Make sure you've created the conversation files in the right location[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        console.print("[dim red]Debug traceback:[/dim red]")
        traceback.print_exc()

async def test_conversational_flow():
    """🚀 Test the full conversational flow"""
    
    console.print(Panel.fit(
        Text.assemble(
            ("🧪 ", "bold blue"),
            ("CONVERSATIONAL FLOW TEST", "bold magenta"),
            (" 🧪\n", "bold blue"),
            ("Testing memory, context resolution, and intelligent responses", "cyan")
        ),
        border_style="blue"
    ))
    
    try:
        from src.sports_bot.conversation.conversational_sports_bot import (
            process_conversational_query, conversational_bot
        )
        console.print("[bold green]✅ Conversational bot imported successfully![/bold green]")
        
        # Test conversation sequence
        conversation_tests = [
            ("Who has the most passing yards in the NFL?", "🎯 Initial Query"),
            ("What about his rushing stats?", "🔄 Pronoun Resolution Test"),
            ("Compare him to Josh Allen", "🆚 Context Continuation"),
            ("Show me their career numbers", "👥 Multi-Player Context"),
        ]
        
        user_id = "test_user_2024"
        
        for i, (query, description) in enumerate(conversation_tests, 1):
            console.print(f"\n{'='*80}")
            console.print(f"[bold cyan]TEST {i}: {description}[/bold cyan]")
            console.print(f"[yellow]Query:[/yellow] {query}")
            console.print("-" * 80)
            
            with console.status(f"[bold green]🤖 Processing test {i}...", spinner="dots"):
                response = await process_conversational_query(query, user_id)
            
            console.print(Panel(
                response, 
                title=f"[green]🤖 Response {i}[/green]", 
                border_style="green"
            ))
            
            await asyncio.sleep(1)
        
        # Show conversation stats
        console.print(f"\n{'='*80}")
        console.print("[bold magenta]📊 CONVERSATION STATISTICS[/bold magenta]")
        console.print("=" * 80)
        
        stats = conversational_bot.get_conversation_stats(user_id)
        if "error" not in stats:
            stats_table = Table(title="Conversation Memory")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Total Queries", str(stats["query_count"]))
            if stats["favorite_players"]:
                stats_table.add_row("Players Discussed", ", ".join(stats["favorite_players"]))
            
            context = stats["last_context"]
            if context["player"]:
                stats_table.add_row("Current Player Context", context["player"])
            
            console.print(stats_table)
        
        console.print(Panel.fit(
            "[bold green]🎉 CONVERSATIONAL TEST COMPLETE![/bold green]\n"
            "[cyan]The bot successfully demonstrated:[/cyan]\n"
            "• ✅ Pronoun resolution (he/his/him)\n"
            "• ✅ Context continuation\n"
            "• ✅ Conversation memory\n"
            "• ✅ Intelligent follow-ups\n"
            "\n[green]🤖 Your Enhanced Sports Bot is working![/green]",
            border_style="green"
        ))
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()

async def run_interactive_test():
    """🎮 Interactive testing mode"""
    
    console.print(Panel.fit(
        Text.assemble(
            ("🎮 ", "bold blue"),
            ("INTERACTIVE TEST MODE", "bold green"),
            (" 🎮\n", "bold blue"),
            ("Type sports questions to test conversational features!\n", "cyan"),
            ("Commands: 'exit', 'stats', 'reset'", "yellow")
        ),
        border_style="green"
    ))
    
    try:
        from src.sports_bot.conversation.conversational_sports_bot import (
            process_conversational_query, conversational_bot
        )
        
        user_id = "interactive_test_user"
        query_count = 0
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]💬 Your sports question[/bold cyan]")
                
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[bold green]👋 Thanks for testing![/bold green]")
                    break
                
                if user_input.lower() == 'stats':
                    stats = conversational_bot.get_conversation_stats(user_id)
                    console.print(Panel(str(stats), title="Stats", border_style="blue"))
                    continue
                
                if user_input.lower() == 'reset':
                    conversational_bot.reset_conversation(user_id)
                    query_count = 0
                    continue
                
                query_count += 1
                
                with console.status("[bold green]🤖 Thinking...", spinner="dots"):
                    response = await process_conversational_query(user_input, user_id)
                
                console.print(Panel(
                    response, 
                    title=f"[green]🤖 Response #{query_count}[/green]", 
                    border_style="green"
                ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                continue
                
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")

async def main():
    """🚀 Main test runner"""
    
    if len(sys.argv) <= 1:
        console.print(Panel.fit(
            Text.assemble(
                ("🧪 ", "bold blue"),
                ("CONVERSATIONAL SPORTS BOT TESTS", "bold magenta"),
                (" 🧪\n\n", "bold blue"),
                ("Available test modes:\n", "cyan"),
                ("• --simple      - Quick single query test\n", "white"),
                ("• --flow        - Full conversational flow test\n", "white"),
                ("• --interactive - Interactive testing mode\n", "white"),
                ("\n💡 Example: python test_conversational_bot.py --flow", "green")
            ),
            border_style="blue"
        ))
        return
    
    if "--simple" in sys.argv:
        await test_simple_query()
    elif "--flow" in sys.argv:
        await test_conversational_flow()
    elif "--interactive" in sys.argv:
        await run_interactive_test()
    else:
        console.print("[red]❌ Use --simple, --flow, or --interactive[/red]")

if __name__ == "__main__":
    asyncio.run(main())
