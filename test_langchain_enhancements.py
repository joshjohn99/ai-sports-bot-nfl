#!/usr/bin/env python3
"""
Test Script for LangChain Enhancements
Tests the new LangChain-powered components to ensure they work correctly.
"""

import asyncio
import sys
import os

# Add the source directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.sports_bot.agents.sports_agents import LangChainSportsAgent, enhanced_sports_agent
from src.sports_bot.agents.debate_agent import LLMDebateAgent
from src.sports_bot.core.stats.response_formatter import LangChainResponseFormatter
from src.sports_bot.api.client import enhanced_api_client
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

async def test_enhanced_debate_agent():
    """Test the enhanced debate agent with LangChain"""
    console.print(Panel("🥊 Testing Enhanced Debate Agent", style="bold blue"))
    
    try:
        debate_agent = LLMDebateAgent()
        
        # Test basic debate functionality
        query = "Who is the better quarterback: Tom Brady or Aaron Rodgers?"
        result = await debate_agent.debate_async(query)
        
        console.print(f"✅ Debate Agent Test: {result[:100]}...")
        return True
    except Exception as e:
        console.print(f"❌ Debate Agent Test Failed: {e}")
        return False

async def test_enhanced_sports_agent():
    """Test the enhanced sports agent with LangChain chains"""
    console.print(Panel("🏈 Testing Enhanced Sports Agent", style="bold green"))
    
    try:
        # Test query processing
        test_query = "Who has the most passing touchdowns this season?"
        result = await enhanced_sports_agent.process_query_enhanced(test_query)
        
        console.print(f"✅ Sports Agent Test: Query processed successfully")
        console.print(f"Strategy: {result.strategy}")
        console.print(f"Metrics: {result.metrics_needed}")
        return True
    except Exception as e:
        console.print(f"❌ Sports Agent Test Failed: {e}")
        return False

async def test_enhanced_response_formatter():
    """Test the enhanced response formatter with LangChain"""
    console.print(Panel("📝 Testing Enhanced Response Formatter", style="bold yellow"))
    
    try:
        formatter = LangChainResponseFormatter()
        
        # Create mock query results
        mock_results = {
            "query_type": "player_comparison",
            "players": ["Josh Allen", "Lamar Jackson"],
            "comparison": {
                "winner_by_metric": {
                    "passing_yards": {
                        "winner": "Josh Allen",
                        "all_values": {"Josh Allen": "4200", "Lamar Jackson": "3800"}
                    }
                }
            }
        }
        
        result = await formatter.format_response_enhanced(mock_results)
        console.print(f"✅ Response Formatter Test: {result[:100]}...")
        return True
    except Exception as e:
        console.print(f"❌ Response Formatter Test Failed: {e}")
        return False

def test_langchain_api_tools():
    """Test the LangChain API tools"""
    console.print(Panel("🔧 Testing LangChain API Tools", style="bold magenta"))
    
    try:
        # Test tool availability
        tools = enhanced_api_client.get_available_tools()
        tool_descriptions = enhanced_api_client.get_tool_descriptions()
        
        console.print(f"✅ API Tools Test: {len(tools)} tools available")
        for name, desc in tool_descriptions.items():
            console.print(f"  • {name}: {desc}")
        
        return True
    except Exception as e:
        console.print(f"❌ API Tools Test Failed: {e}")
        return False

async def run_comprehensive_test():
    """Run all LangChain enhancement tests"""
    console.print(Panel("🚀 LangChain Enhancement Test Suite", style="bold cyan", expand=True))
    
    results = []
    
    # Test 1: Enhanced Debate Agent
    results.append(await test_enhanced_debate_agent())
    
    # Test 2: Enhanced Sports Agent
    results.append(await test_enhanced_sports_agent())
    
    # Test 3: Enhanced Response Formatter
    results.append(await test_enhanced_response_formatter())
    
    # Test 4: LangChain API Tools
    results.append(test_langchain_api_tools())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    console.print(Panel(
        f"Test Results: {passed}/{total} tests passed\n" +
        ("🎉 All tests passed!" if passed == total else f"⚠️ {total - passed} tests failed"),
        style="bold green" if passed == total else "bold red",
        title="Test Summary"
    ))
    
    if passed == total:
        console.print("\n🚀 Your LangChain enhancements are working correctly!")
        console.print("✅ Ready to deploy improved sports bot with:")
        console.print("  • Enhanced conversation memory")
        console.print("  • Structured output parsing")
        console.print("  • Better error handling") 
        console.print("  • Standardized API tools")
        console.print("  • Improved response formatting")
    else:
        console.print("\n🔧 Some enhancements need attention before deployment.")
    
    return passed == total

def show_langchain_improvements():
    """Show the improvements made with LangChain"""
    console.print(Panel("📊 LangChain Improvements Summary", style="bold blue", expand=True))
    
    improvements = [
        ("🧠 Debate Agent", "Direct OpenAI → LangChain ChatOpenAI + Chains"),
        ("🏈 Sports Agents", "Manual processing → Structured chains with memory"),
        ("📝 Response Formatter", "Manual formatting → Pydantic output parsers"),
        ("🔧 API Tools", "Basic requests → LangChain tools with caching"),
        ("💾 Memory", "No memory → Conversation buffer memory"),
        ("🛡️ Error Handling", "Basic try/catch → LangChain retry mechanisms"),
        ("📊 Structured Output", "Manual parsing → Pydantic schemas"),
        ("🔄 Async Support", "Limited async → Full async chains")
    ]
    
    for component, improvement in improvements:
        console.print(f"{component}: {improvement}")

if __name__ == "__main__":
    console.print("🔗 LangChain Enhancement Test Suite")
    console.print("=" * 50)
    
    # Show improvements first
    show_langchain_improvements()
    console.print()
    
    # Run tests
    try:
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 