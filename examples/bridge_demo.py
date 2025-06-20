#!/usr/bin/env python3
"""
Agent Bridge Demo - Hybrid Architecture in Action

This demo showcases how the Agent Bridge connects the existing custom sports agents
with the new LangChain/LangGraph integration, providing intelligent routing and
graceful fallbacks between systems.
"""

import asyncio
import sys
import os
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the agent bridge
from sports_bot.langchain_integration.agent_bridge import (
    process_sports_query, 
    get_integration_status,
    get_agent_bridge
)

console = Console()


def display_header():
    """Display the demo header"""
    header_text = Text("🏈 Sports Bot Agent Bridge Demo 🏀", style="bold blue")
    subtitle = Text("Hybrid Architecture: Custom Agents + LangChain Integration", style="italic")
    
    panel = Panel.fit(
        f"{header_text}\n{subtitle}",
        border_style="blue"
    )
    console.print(panel)
    console.print()


def display_integration_status():
    """Display the current integration status"""
    status = get_integration_status()
    
    console.print("[bold green]🔗 Integration Status[/bold green]")
    
    # Systems table
    systems_table = Table(title="Integrated Systems")
    systems_table.add_column("System", style="cyan")
    systems_table.add_column("Status", style="green")
    systems_table.add_column("Purpose", style="yellow")
    
    system_purposes = {
        "custom_nlu_agents": "Query understanding & planning",
        "langgraph_workflows": "Complex multi-agent analysis",
        "langchain_tools": "Standardized API operations", 
        "custom_stat_retriever": "Optimized data retrieval"
    }
    
    for system in status["systems_integrated"]:
        systems_table.add_row(
            system.replace("_", " ").title(),
            "✅ Active",
            system_purposes.get(system, "Core functionality")
        )
    
    console.print(systems_table)
    console.print()


def display_routing_decision(result: Dict[str, Any]):
    """Display how the query was routed and processed"""
    if not result.get("success"):
        console.print(f"[red]❌ Error: {result.get('error', 'Unknown error')}[/red]")
        return
    
    method = result.get("method", "unknown")
    routing_reason = result.get("routing_reason", "No reason provided")
    
    # Method color coding
    method_colors = {
        "langgraph_workflow": "magenta",
        "hybrid_tools": "blue", 
        "custom_enhanced": "green",
        "custom_basic_fallback": "yellow"
    }
    
    method_color = method_colors.get(method, "white")
    
    routing_panel = Panel(
        f"[bold {method_color}]Processing Method:[/bold {method_color}] {method.replace('_', ' ').title()}\n"
        f"[bold]Routing Reason:[/bold] {routing_reason}",
        title="🧠 Intelligent Routing Decision",
        border_style=method_color
    )
    
    console.print(routing_panel)


async def run_demo_queries():
    """Run a series of demo queries to showcase different routing decisions"""
    
    demo_queries = [
        {
            "query": "Who are the top 5 NFL quarterbacks by passing yards this season?",
            "description": "Complex leaderboard query → Should route to LangGraph workflow",
            "expected_method": "langgraph_workflow"
        },
        {
            "query": "Compare Josh Allen and Patrick Mahomes passing stats",
            "description": "Player comparison → Should route to hybrid tools",
            "expected_method": "hybrid_tools"
        },
        {
            "query": "What are Lamar Jackson's rushing yards?",
            "description": "Simple player stat → Should route to custom enhanced",
            "expected_method": "custom_enhanced"
        },
        {
            "query": "Who is better, Tom Brady or Peyton Manning?",
            "description": "Debate-style query → Should route to LangGraph workflow",
            "expected_method": "langgraph_workflow"
        }
    ]
    
    console.print("[bold blue]🚀 Running Demo Queries[/bold blue]\n")
    
    for i, demo in enumerate(demo_queries, 1):
        console.print(f"[bold]Query {i}:[/bold] {demo['query']}")
        console.print(f"[dim]{demo['description']}[/dim]\n")
        
        try:
            # Process the query through the bridge
            result = await process_sports_query(demo["query"])
            
            # Display routing decision
            display_routing_decision(result)
            
            # Show if routing matched expectation
            actual_method = result.get("method", "unknown")
            expected_method = demo["expected_method"]
            
            if expected_method in actual_method:
                console.print("[green]✅ Routing decision matches expectation[/green]")
            else:
                console.print(f"[yellow]⚠️  Expected {expected_method}, got {actual_method}[/yellow]")
            
            # Show brief result summary
            if result.get("success"):
                console.print(f"[dim]Result preview: {str(result.get('result', {}))[:100]}...[/dim]")
            
        except Exception as e:
            console.print(f"[red]❌ Query failed: {str(e)}[/red]")
        
        console.print("-" * 60)
        console.print()


def display_routing_statistics():
    """Display routing statistics after running queries"""
    bridge = get_agent_bridge()
    stats = bridge.get_routing_statistics()
    
    if stats.get("message"):
        console.print(f"[yellow]{stats['message']}[/yellow]")
        return
    
    console.print("[bold green]📊 Routing Statistics[/bold green]")
    
    # Create statistics table
    stats_table = Table(title="Query Processing Breakdown")
    stats_table.add_column("Processing Method", style="cyan")
    stats_table.add_column("Count", style="green")
    stats_table.add_column("Percentage", style="yellow")
    stats_table.add_column("Description", style="white")
    
    method_descriptions = {
        "custom_nlu": "Used custom NLU for query analysis",
        "langgraph_workflow": "Complex multi-agent workflows",
        "hybrid_tools": "LangChain tools + custom logic",
        "fallback": "Basic stat retrieval fallback"
    }
    
    for method, data in stats["routing_breakdown"].items():
        stats_table.add_row(
            method.replace("_", " ").title(),
            str(data["count"]),
            f"{data['percentage']}%",
            method_descriptions.get(method, "Processing method")
        )
    
    console.print(stats_table)
    
    # Efficiency metrics
    efficiency = stats["efficiency_metrics"]
    console.print(f"\n[bold]Efficiency Metrics:[/bold]")
    console.print(f"• LangGraph Usage: {efficiency['langgraph_usage']}%")
    console.print(f"• Hybrid Tools Usage: {efficiency['hybrid_tools_usage']}%") 
    console.print(f"• Custom System Usage: {efficiency['custom_system_usage']}%")
    console.print()


def display_capabilities():
    """Display the comprehensive capabilities of the integrated system"""
    bridge = get_agent_bridge()
    capabilities = bridge.get_supported_capabilities()
    
    console.print("[bold blue]🎯 System Capabilities[/bold blue]")
    
    # Architecture overview
    arch_table = Table(title="Hybrid Architecture Components")
    arch_table.add_column("Component", style="cyan")
    arch_table.add_column("Technology", style="green") 
    arch_table.add_column("Purpose", style="yellow")
    
    arch_table.add_row("NLU System", capabilities["nlu_system"], "Query understanding")
    arch_table.add_row("Workflow Engine", capabilities["workflow_engine"], "Complex analysis")
    arch_table.add_row("API Integration", capabilities["api_integration"], "Standardized operations")
    arch_table.add_row("Fallback System", capabilities["fallback_system"], "Reliability & performance")
    
    console.print(arch_table)
    
    # Processing methods
    console.print(f"\n[bold]Supported Query Types:[/bold] {', '.join(capabilities['query_types'])}")
    console.print(f"[bold]Supported Sports:[/bold] {', '.join(capabilities['supported_sports'])}")
    
    # Routing intelligence features
    routing_features = capabilities["routing_intelligence"]
    console.print(f"\n[bold green]🧠 Routing Intelligence Features:[/bold green]")
    for feature, enabled in routing_features.items():
        status = "✅" if enabled else "❌"
        console.print(f"  {status} {feature.replace('_', ' ').title()}")
    
    console.print()


async def interactive_mode():
    """Interactive mode for testing custom queries"""
    console.print("[bold yellow]🎮 Interactive Mode[/bold yellow]")
    console.print("Enter your sports queries to see how they're routed and processed.")
    console.print("Type 'quit' to exit, 'stats' to see routing statistics, or 'help' for capabilities.\n")
    
    while True:
        try:
            query = input("🏈 Enter your sports query: ").strip()
            
            if query.lower() == 'quit':
                break
            elif query.lower() == 'stats':
                display_routing_statistics()
                continue
            elif query.lower() == 'help':
                display_capabilities()
                continue
            elif not query:
                continue
            
            console.print(f"\n[bold]Processing:[/bold] {query}")
            
            result = await process_sports_query(query)
            display_routing_decision(result)
            
            if result.get("success"):
                # Display formatted result
                formatted_result = result.get("result", {})
                if isinstance(formatted_result, dict) and "formatted_response" in formatted_result:
                    console.print(f"\n[bold green]Response:[/bold green]")
                    console.print(formatted_result["formatted_response"])
                else:
                    console.print(f"\n[bold green]Result:[/bold green] {formatted_result}")
            
            console.print("\n" + "-" * 60 + "\n")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting interactive mode...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


async def main():
    """Main demo function"""
    display_header()
    
    # Check if we should run in batch mode
    if "--batch" in sys.argv:
        console.print("[yellow]Running in batch mode...[/yellow]\n")
        
        display_integration_status()
        await run_demo_queries()
        display_routing_statistics()
        display_capabilities()
        
    else:
        # Interactive mode
        console.print("[bold]Choose demo mode:[/bold]")
        console.print("1. 🤖 Automated Demo (batch mode)")
        console.print("2. 🎮 Interactive Mode")
        console.print("3. 📊 Show System Status Only")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            display_integration_status()
            await run_demo_queries()
            display_routing_statistics()
            display_capabilities()
            
        elif choice == "2":
            display_integration_status()
            display_capabilities()
            await interactive_mode()
            display_routing_statistics()
            
        elif choice == "3":
            display_integration_status()
            display_capabilities()
            
        else:
            console.print("[red]Invalid choice. Exiting.[/red]")
            return
    
    console.print("[bold green]🎉 Demo completed! The agent bridge successfully connects both systems.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main()) 