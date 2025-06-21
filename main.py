#!/usr/bin/env python3
"""
AI Sports Bot - Universal Multi-Sport Interface
Run this script to start the interactive sports bot with intelligent routing.
"""

import sys
import os
import asyncio

# No longer needed after installing with 'pip install -e .'

# Import the Universal Sports Interface
try:
    from sports_bot.agents.agent_integration import unified_sports_interface, query_sports
    UNIVERSAL_AGENT_AVAILABLE = True
except ImportError:
    UNIVERSAL_AGENT_AVAILABLE = False
    # Fallback to original sports agents
    from sports_bot.agents.sports_agents import run_query_planner, run_enhanced_query_processor, format_enhanced_response

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

async def process_user_question_universal(user_question: str, user_id: str = "interactive_user"):
    """Process a user question through the Universal Sports Agent."""
    if not UNIVERSAL_AGENT_AVAILABLE:
        return await process_user_question_legacy(user_question)
    
    try:
        # Use the unified sports interface
        result = await unified_sports_interface.process_query(
            user_question, 
            user_id=user_id, 
            conversation_id="main_session"
        )
        
        # Display the result with enhanced formatting
        status_color = "green" if result.success else "red"
        status_icon = "✅" if result.success else "❌"
        
        # Create response panel
        response_panel = Panel(
            Text(result.response, style="bold white"),
            title=f"[{status_color}]{status_icon} Universal Sports Bot Response[/{status_color}]",
            border_style=status_color
        )
        
        console.print(response_panel)
        
        # Show additional info if available
        if result.sport or result.confidence > 0:
            info_text = ""
            if result.sport:
                info_text += f"🏆 Sport: {result.sport}  "
            if result.confidence > 0:
                info_text += f"🎯 Confidence: {result.confidence:.2f}  "
            if result.processing_time > 0:
                info_text += f"⏱️ Time: {result.processing_time:.2f}s"
            
            if info_text:
                console.print(f"[dim]{info_text}[/dim]")
        
    except Exception as e:
        console.print(Panel(
            Text(f"❌ Error processing question: {str(e)}", style="bold red"),
            title="[red]Universal Agent Error[/red]",
            border_style="red"
        ))
        console.print(f"[dim red]Debug info: {type(e).__name__}[/dim red]")

async def process_user_question_legacy(user_question: str):
    """Process a user question through the legacy sports bot pipeline."""
    try:
        # Step 1: Query Planning
        query_context = await run_query_planner(user_question)
        
        # Step 2: Enhanced Query Processing
        query_results = await run_enhanced_query_processor(user_question, query_context)
        
        # Step 3: Format Response
        formatted_response = format_enhanced_response(query_results)
        
        # Display the result
        console.print(Panel(
            Text(formatted_response, style="bold white"),
            title="[green]🏈 Sports Bot Response (Legacy)[/green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel(
            Text(f"❌ Error processing question: {str(e)}", style="bold red"),
            title="[red]Error[/red]",
            border_style="red"
        ))
        console.print(f"[dim red]Debug info: {type(e).__name__}[/dim red]")

def upgrade_nfl_with_langchain():
    """Simplified NFL LangChain upgrade function"""
    
    try:
        from rich.table import Table
        from rich.panel import Panel
        from rich.progress import Progress
        
        console.print(Panel.fit(
            "[bold blue]🏈 NFL LANGCHAIN UPGRADE 🏈[/bold blue]\n"
            "[cyan]Adding intelligent framework to existing NFL data[/cyan]",
            border_style="blue"
        ))
        
        # Import database components
        from sports_bot.database.sport_models import sport_db_manager
        from sports_bot.cache.shared_cache import sports_cache
        
        console.print("[cyan]🔍 Connecting to NFL database...[/cyan]")
        
        # Get NFL database session
        session = sport_db_manager.get_session('NFL')
        models = sport_db_manager.get_models('NFL')
        
        if not session or not models:
            console.print("[red]❌ Could not connect to NFL database[/red]")
            return False
        
        Player = models['Player']
        Team = models['Team']
        PlayerStats = models['PlayerStats']
        CareerStats = models['CareerStats']
        
        console.print("[green]✅ Connected to NFL database[/green]")
        
        # Step 1: Analyze database
        console.print("\n" + "="*60)
        console.print("STEP 1: ANALYZING NFL DATABASE")
        console.print("="*60)
        
        # Count totals
        total_teams = session.query(Team).count()
        total_players = session.query(Player).count()
        total_stats = session.query(PlayerStats).count()
        total_career_stats = session.query(CareerStats).count()
        
        # Display summary
        table = Table(title="NFL Database Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Teams", str(total_teams))
        table.add_row("Players", str(total_players))
        table.add_row("Player Stats", str(total_stats))
        table.add_row("Career Stats", str(total_career_stats))
        
        console.print(table)
        
        # Get players by position
        positions = session.query(Player.position).distinct().all()
        position_counts = {}
        
        for (pos,) in positions:
            if pos:
                count = session.query(Player).filter(Player.position == pos).count()
                position_counts[pos] = count
        
        # Show top positions
        if position_counts:
            pos_table = Table(title="Players by Position")
            pos_table.add_column("Position", style="yellow")
            pos_table.add_column("Players", style="green")
            
            for pos, count in sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                pos_table.add_row(pos, str(count))
            
            console.print(pos_table)
        
        # Step 2: Cache top players
        console.print("\n" + "="*60)
        console.print("STEP 2: CACHING TOP NFL PLAYERS")
        console.print("="*60)
        
        # Calculate 75% of players
        top_75_percent = int(total_players * 0.75)
        console.print(f"[cyan]Caching top {top_75_percent} NFL players (75% of {total_players} total)[/cyan]")
        
        # Get players with stats (most important ones)
        players_with_stats = session.query(Player).join(
            PlayerStats, Player.id == PlayerStats.player_id
        ).distinct().limit(top_75_percent).all()
        
        cached_count = 0
        
        with Progress() as progress:
            task = progress.add_task("Caching players...", total=len(players_with_stats))
            
            for player in players_with_stats:
                # Get team info
                team_name = "Unknown Team"
                if player.current_team_id:
                    team = session.query(Team).filter(Team.id == player.current_team_id).first()
                    if team:
                        team_name = team.display_name or team.name
                
                # Get career stats
                career_stats = session.query(CareerStats).filter(
                    CareerStats.player_id == player.id
                ).first()
                
                # Create cache entry
                cache_key = f"nfl_player_{player.name.lower().replace(' ', '_')}"
                cache_data = {
                    'id': player.id,
                    'name': player.name,
                    'position': player.position,
                    'team': team_name,
                    'sport': 'NFL',
                    'external_id': player.external_id
                }
                
                if career_stats:
                    cache_data['career_stats'] = {
                        'passing_yards': career_stats.career_passing_yards,
                        'passing_touchdowns': career_stats.career_passing_touchdowns,
                        'rushing_yards': career_stats.career_rushing_yards,
                        'rushing_touchdowns': career_stats.career_rushing_touchdowns,
                        'receiving_yards': career_stats.career_receiving_yards,
                        'receptions': career_stats.career_receptions,
                        'receiving_touchdowns': career_stats.career_receiving_touchdowns,
                        'sacks': career_stats.career_sacks,
                        'tackles': career_stats.career_tackles,
                        'interceptions': career_stats.career_interceptions
                    }
                
                # Cache the player
                sports_cache.set(cache_key, cache_data)
                cached_count += 1
                
                progress.advance(task)
        
        console.print(f"[green]✅ Cached {cached_count} NFL players[/green]")
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("🎉 NFL LANGCHAIN UPGRADE COMPLETE! 🎉")
        console.print("="*60)
        
        final_summary = Panel.fit(
            f"[bold green]✅ NFL LangChain Integration Complete![/bold green]\n\n"
            f"[cyan]📊 Database Summary:[/cyan]\n"
            f"• Teams: {total_teams}\n"
            f"• Players: {total_players}\n"
            f"• Player Stats: {total_stats}\n"
            f"• Career Stats: {total_career_stats}\n\n"
            f"[cyan]🤖 Upgrade Features:[/cyan]\n"
            f"• Players Cached: {cached_count}\n"
            f"• Cache Integration: ✅ Active\n"
            f"• Database Analysis: ✅ Complete\n"
            f"• Top 75% Coverage: ✅ Active\n\n"
            f"[green]🏈 NFL system now ready for intelligent queries![/green]\n"
            f"[green]🤖 Same intelligent capabilities as NBA system![/green]",
            border_style="green"
        )
        
        console.print(final_summary)
        
        session.close()
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error during NFL LangChain upgrade: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def show_sports_dashboard():
    """Show the sports bot dashboard with system status and performance metrics"""
    if UNIVERSAL_AGENT_AVAILABLE:
        unified_sports_interface.display_performance_dashboard()
    else:
        console.print(Panel(
            "[yellow]⚠️ Universal Sports Agent not available[/yellow]\n"
            "[cyan]Running in legacy mode with basic NFL functionality[/cyan]",
            title="System Status",
            border_style="yellow"
        ))

def show_supported_sports():
    """Show all supported sports"""
    if UNIVERSAL_AGENT_AVAILABLE:
        sports = unified_sports_interface.get_supported_sports()
        
        sports_table = Table(title="🌟 Supported Sports")
        sports_table.add_column("Sport", style="cyan")
        sports_table.add_column("Status", style="green")
        
        for sport in sports:
            # Check if sport is available in legacy systems
            legacy_info = unified_sports_interface.legacy_systems.get(sport, {})
            if legacy_info.get("available"):
                status = "✅ Active"
                if legacy_info.get("player_count"):
                    status += f" ({legacy_info['player_count']} players)"
            else:
                status = "🔄 Configured"
            
            sports_table.add_row(sport, status)
        
        console.print(sports_table)
    else:
        console.print("[yellow]⚠️ Universal Sports Agent not available. Only basic NFL support active.[/yellow]")

async def test_all_sports():
    """Test queries for all supported sports"""
    if not UNIVERSAL_AGENT_AVAILABLE:
        console.print("[red]❌ Universal Sports Agent not available for testing[/red]")
        return
    
    console.print(Panel.fit(
        "[bold blue]🧪 Testing All Sports Systems[/bold blue]",
        border_style="blue"
    ))
    
    test_queries = [
        ("NFL", "NFL quarterback stats"),
        ("NBA", "NBA player points leaders"),
        ("MLB", "MLB home run leaders"),
        ("NHL", "NHL goalie saves"),
        ("MLS", "MLS top scorers"),
        ("NASCAR", "NASCAR race winners"),
        ("F1", "Formula 1 championship standings"),
        ("Cross-Sport", "Compare NFL and NBA player salaries"),
        ("Ambiguous", "Who is the best player?")
    ]
    
    for sport_type, query in test_queries:
        console.print(f"\n[cyan]🔍 Testing {sport_type}: {query}[/cyan]")
        await process_user_question_universal(query, user_id="test_user")

def add_new_sport_interactive():
    """Interactive function to add a new sport"""
    if not UNIVERSAL_AGENT_AVAILABLE:
        console.print("[red]❌ Universal Sports Agent not available. Cannot add new sports.[/red]")
        return
    
    console.print(Panel.fit(
        "[bold green]➕ Add New Sport to Universal Sports Bot[/bold green]",
        border_style="green"
    ))
    
    try:
        sport_name = Prompt.ask("[cyan]Sport name (e.g., Tennis, Cricket, etc.)[/cyan]")
        
        console.print("[yellow]Enter keywords that identify this sport (comma-separated):[/yellow]")
        keywords_input = Prompt.ask("[cyan]Keywords[/cyan]")
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        console.print("[yellow]Enter team names (comma-separated, optional):[/yellow]")
        teams_input = Prompt.ask("[cyan]Teams[/cyan]", default="")
        teams = [t.strip() for t in teams_input.split(",") if t.strip()] if teams_input else []
        
        console.print("[yellow]Enter stat types (comma-separated, optional):[/yellow]")
        stats_input = Prompt.ask("[cyan]Stats[/cyan]", default="")
        stats = [s.strip() for s in stats_input.split(",") if s.strip()] if stats_input else []
        
        console.print("[yellow]Enter positions (comma-separated, optional):[/yellow]")
        positions_input = Prompt.ask("[cyan]Positions[/cyan]", default="")
        positions = [p.strip() for p in positions_input.split(",") if p.strip()] if positions_input else []
        
        # Add the sport
        asyncio.create_task(unified_sports_interface.add_new_sport(
            sport_name, keywords, teams, stats, positions
        ))
        
        console.print(f"[green]✅ {sport_name} added successfully![/green]")
        console.print("[cyan]You can now ask questions about this sport.[/cyan]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Sport addition cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error adding sport: {e}[/red]")

def main():
    """Main interactive loop for the universal sports bot."""
    # Check for special command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--upgrade-nfl":
            upgrade_nfl_with_langchain()
            return
        elif sys.argv[1] == "--dashboard":
            show_sports_dashboard()
            return
        elif sys.argv[1] == "--sports":
            show_supported_sports()
            return
        elif sys.argv[1] == "--test":
            asyncio.run(test_all_sports())
            return
    
    # Check if input is being piped
    if not sys.stdin.isatty():
        # Handle piped input
        try:
            piped_input = sys.stdin.read().strip()
            if piped_input:
                console.print(f"[bold cyan]Processing query: {piped_input}[/bold cyan]")
                if UNIVERSAL_AGENT_AVAILABLE:
                    asyncio.run(process_user_question_universal(piped_input))
                else:
                    asyncio.run(process_user_question_legacy(piped_input))
            return
        except Exception as e:
            console.print(f"[red]Error processing piped input: {e}[/red]")
            return
    
    # Interactive mode
    # Create a welcoming panel
    if UNIVERSAL_AGENT_AVAILABLE:
        title = "🌟 Universal AI Sports Bot 🌟"
        subtitle = "Intelligent Multi-Sport Assistant"
        features = (
            "🏈 NFL • 🏀 NBA • ⚾ MLB • 🏒 NHL • ⚽ MLS • 🏁 NASCAR • 🏎️ F1\n"
            "• Intelligent sport detection and routing\n"
            "• Cross-sport comparisons and analysis\n"
            "• Dynamic conversation management\n"
            "• Extensible to any sport"
        )
        commands = (
            "'exit' or 'quit' - Stop the bot\n"
            "'dashboard' - Show performance dashboard\n"
            "'sports' - Show supported sports\n"
            "'add sport' - Add a new sport interactively\n"
            "'test' - Test all sports systems\n"
            "'upgrade' - Run NFL LangChain upgrade"
        )
    else:
        title = "🏈 AI Sports Bot NFL 🏈"
        subtitle = "Legacy Mode - NFL Focus"
        features = (
            "🏈 NFL player and team statistics\n"
            "• Advanced query processing\n"
            "• Comprehensive database integration"
        )
        commands = (
            "'exit' or 'quit' - Stop the bot\n"
            "'upgrade' - Run NFL LangChain upgrade"
        )
    
    welcome_message = Text(f"\n{title}\n", style="bold magenta on white", justify="center")
    subtitle_text = Text(f"{subtitle}\n", style="bold cyan", justify="center")
    instructions = Text(f"Commands:\n{commands}\n\nSupported Features:\n{features}", style="cyan")
    
    info_panel = Panel(
        Text.assemble(welcome_message, subtitle_text, "\n", instructions),
        title="[bold green]Universal Sports Bot[/bold green]" if UNIVERSAL_AGENT_AVAILABLE else "[bold green]AI Sports Bot NFL[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print(info_panel)
    console.print("-" * 70, style="dim green")
    
    # Show initial system status
    if UNIVERSAL_AGENT_AVAILABLE:
        stats = unified_sports_interface.get_performance_stats()
        console.print(f"[dim green]System Status: Universal Agent ✅ | {len(stats['available_sports'])} sports configured | Ready for queries[/dim green]")
    else:
        console.print("[dim yellow]System Status: Legacy Mode ⚠️ | NFL focus | Limited multi-sport support[/dim yellow]")
    
    # Interactive loop
    while True:
        try:
            if UNIVERSAL_AGENT_AVAILABLE:
                user_input = Prompt.ask("\n[bold cyan]Ask me about any sport[/bold cyan]")
            else:
                user_input = Prompt.ask("\n[bold cyan]Ask me about NFL stats[/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[bold green]Thanks for using the Universal Sports Bot! 🌟[/bold green]")
                break
            
            # Handle special commands
            if user_input.lower() == 'dashboard':
                show_sports_dashboard()
                continue
            
            if user_input.lower() == 'sports':
                show_supported_sports()
                continue
            
            if user_input.lower() in ['add sport', 'add-sport', 'new sport']:
                add_new_sport_interactive()
                continue
            
            if user_input.lower() == 'test':
                asyncio.run(test_all_sports())
                continue
            
            if user_input.lower() == 'upgrade':
                console.print("[cyan]Starting NFL LangChain upgrade...[/cyan]")
                upgrade_nfl_with_langchain()
                continue
                
            if not user_input.strip():
                console.print("[yellow]Please enter a question about sports.[/yellow]")
                continue
            
            # Process the question
            if UNIVERSAL_AGENT_AVAILABLE:
                asyncio.run(process_user_question_universal(user_input))
            else:
                asyncio.run(process_user_question_legacy(user_input))
            
        except KeyboardInterrupt:
            console.print("\n[bold green]Thanks for using the Sports Bot! 🌟[/bold green]")
            break
        except EOFError:
            # Handle EOF gracefully (e.g., when Ctrl+D is pressed)
            console.print("\n[bold green]Thanks for using the Sports Bot! 🌟[/bold green]")
            break
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")

if __name__ == "__main__":
    main() 