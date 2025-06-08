#!/usr/bin/env python3
"""
Comprehensive Sports Bot Test Suite
Tests leaderboards, comparisons, and error handling
"""

import sys
import os
import asyncio
import traceback
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sports_bot.core.agents.sports_agents import QueryContext, run_enhanced_query_processor

console = Console()

class SportsBookTestSuite:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    async def run_test(self, test_name: str, query: str, expected_type: str = None):
        """Run a single test query and capture results"""
        console.print(f"\n🧪 [bold blue]Testing:[/bold blue] {test_name}")
        console.print(f"📝 [dim]Query:[/dim] {query}")
        
        try:
            # Create query context
            query_context = QueryContext(
                question=query,
                sport='NFL'
            )
            
            # Run the enhanced query processor
            result = await run_enhanced_query_processor(query, query_context)
            
            # Check for errors
            if isinstance(result, dict) and "error" in result:
                console.print(f"❌ [red]FAILED:[/red] {result['error']}")
                self.failed_tests += 1
                self.test_results.append({
                    "test": test_name,
                    "query": query,
                    "status": "FAILED",
                    "error": result['error']
                })
                return False
            
            # Check for expected content
            if result and isinstance(result, dict):
                query_type = result.get('query_type', 'unknown')
                console.print(f"✅ [green]PASSED:[/green] Query Type: {query_type}")
                
                # Show sample data
                if 'leaders' in result:
                    leaders = result['leaders'][:3]  # Show top 3
                    console.print(f"🏆 [yellow]Top Leaders:[/yellow]")
                    for leader in leaders:
                        name = leader.get('player_name', 'Unknown')
                        position = leader.get('position', 'Unknown')
                        value = leader.get('value', 0)
                        console.print(f"   {leader.get('rank', '?')}. {name} ({position}): {value}")
                
                elif 'comparison' in result:
                    console.print(f"⚔️ [yellow]Comparison Results:[/yellow] Found comparison data")
                    
                elif 'teams' in result:
                    teams = result.get('teams', [])
                    console.print(f"🏈 [yellow]Team Analysis:[/yellow] {', '.join(teams)}")
                
                self.passed_tests += 1
                self.test_results.append({
                    "test": test_name,
                    "query": query,
                    "status": "PASSED",
                    "query_type": query_type
                })
                return True
            else:
                console.print(f"❌ [red]FAILED:[/red] No valid result returned")
                self.failed_tests += 1
                self.test_results.append({
                    "test": test_name,
                    "query": query,
                    "status": "FAILED",
                    "error": "No valid result"
                })
                return False
                
        except Exception as e:
            console.print(f"❌ [red]EXCEPTION:[/red] {str(e)}")
            console.print(f"[dim red]Traceback:[/dim red] {traceback.format_exc()}")
            self.failed_tests += 1
            self.test_results.append({
                "test": test_name,
                "query": query,
                "status": "EXCEPTION",
                "error": str(e)
            })
            return False

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        
        console.print(Panel(
            "[bold green]🏈 AI Sports Bot Comprehensive Test Suite 🏈[/bold green]\n"
            "Testing offensive/defensive leaderboards, comparisons, and error handling",
            title="Test Suite Started",
            border_style="green"
        ))
        
        # OFFENSIVE LEADERBOARDS
        console.print("\n" + "="*60)
        console.print("[bold yellow]📈 OFFENSIVE LEADERBOARD TESTS[/bold yellow]")
        console.print("="*60)
        
        await self.run_test("QB Passing Yards Leaders", "Who has the most passing yards in the NFL?")
        await self.run_test("QB Passing TDs Leaders", "Who leads in passing touchdowns?")
        await self.run_test("RB Rushing Yards Leaders", "Who has the most rushing yards?")
        await self.run_test("RB Rushing TDs Leaders", "Best running back rushing touchdowns")
        await self.run_test("WR Receiving Yards Leaders", "Who leads in receiving yards?")
        await self.run_test("WR Receiving TDs Leaders", "Top receivers receiving touchdowns")
        await self.run_test("Overall Touchdown Leaders", "Who has the most touchdowns?")
        
        # DEFENSIVE LEADERBOARDS
        console.print("\n" + "="*60)
        console.print("[bold red]🛡️ DEFENSIVE LEADERBOARD TESTS[/bold red]")
        console.print("="*60)
        
        await self.run_test("Sack Leaders", "Who has the most sacks in the NFL?")
        await self.run_test("Tackle Leaders", "Who leads in tackles?")
        await self.run_test("Interception Leaders", "Who has the most interceptions?")
        await self.run_test("Forced Fumble Leaders", "Who leads in forced fumbles?")
        
        # SPECIAL TEAMS
        console.print("\n" + "="*60)
        console.print("[bold blue]🦶 SPECIAL TEAMS TESTS[/bold blue]")
        console.print("="*60)
        
        await self.run_test("Field Goal Leaders", "Who has made the most field goals?")
        await self.run_test("Kicker Accuracy", "Best kickers field goals made")
        
        # PLAYER COMPARISONS
        console.print("\n" + "="*60)
        console.print("[bold purple]⚔️ PLAYER COMPARISON TESTS[/bold purple]")
        console.print("="*60)
        
        await self.run_test("QB Comparison", "Compare Lamar Jackson vs Josh Allen")
        await self.run_test("RB Comparison", "Compare Derrick Henry vs Nick Chubb")
        await self.run_test("WR Comparison", "Compare Tyreek Hill vs Davante Adams")
        await self.run_test("Pass Rusher Comparison", "Micah Parsons vs T.J. Watt sacks")
        
        # TEAM COMPARISONS
        console.print("\n" + "="*60)
        console.print("[bold cyan]🏟️ TEAM COMPARISON TESTS[/bold cyan]")
        console.print("="*60)
        
        await self.run_test("AFC Powerhouses", "Compare Ravens vs Bills")
        await self.run_test("NFC Rivals", "Cowboys vs Giants team stats")
        await self.run_test("Championship Teams", "Chiefs vs 49ers comparison")
        await self.run_test("Defensive Comparison", "Ravens vs Bills defensive stats")
        
        # EDGE CASES & ERROR HANDLING
        console.print("\n" + "="*60)
        console.print("[bold orange_red1]⚠️ EDGE CASE & ERROR TESTS[/bold orange_red1]")
        console.print("="*60)
        
        await self.run_test("Nonexistent Player", "Compare Fake Player vs Josh Allen")
        await self.run_test("Nonexistent Team", "Compare Fake Team vs Ravens")
        await self.run_test("Vague Query", "Who is the best?")
        await self.run_test("Invalid Metric", "Who has the most super bowl rings?")
        
        # PRINT FINAL RESULTS
        self.print_final_results()

    def print_final_results(self):
        """Print comprehensive test results"""
        console.print("\n" + "="*80)
        console.print("[bold green]📊 FINAL TEST RESULTS[/bold green]")
        console.print("="*80)
        
        # Summary table
        table = Table(title="Test Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta") 
        table.add_column("Percentage", style="green")
        
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        table.add_row("Total Tests", str(total_tests), "100%")
        table.add_row("Passed", str(self.passed_tests), f"{pass_rate:.1f}%")
        table.add_row("Failed", str(self.failed_tests), f"{100 - pass_rate:.1f}%")
        
        console.print(table)
        
        # Detailed results
        if self.failed_tests > 0:
            console.print("\n[bold red]❌ FAILED TESTS:[/bold red]")
            for result in self.test_results:
                if result['status'] in ['FAILED', 'EXCEPTION']:
                    console.print(f"• [red]{result['test']}[/red]: {result.get('error', 'Unknown error')}")
                    console.print(f"  Query: [dim]{result['query']}[/dim]")
        
        if self.passed_tests > 0:
            console.print(f"\n[bold green]✅ {self.passed_tests} TESTS PASSED![/bold green]")
        
        # Overall status
        if pass_rate >= 90:
            console.print(Panel(
                f"🎉 [bold green]EXCELLENT![/bold green] {pass_rate:.1f}% pass rate\n"
                "Your sports bot is in championship form! 🏆",
                title="Test Suite Complete",
                border_style="green"
            ))
        elif pass_rate >= 70:
            console.print(Panel(
                f"👍 [bold yellow]GOOD![/bold yellow] {pass_rate:.1f}% pass rate\n"
                "Most features working, some issues to address 📋",
                title="Test Suite Complete",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                f"⚠️ [bold red]NEEDS WORK![/bold red] {pass_rate:.1f}% pass rate\n"
                "Several issues found that need fixing 🔧",
                title="Test Suite Complete",
                border_style="red"
            ))

async def main():
    """Run the comprehensive test suite"""
    test_suite = SportsBookTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 