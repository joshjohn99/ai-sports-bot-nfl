#!/usr/bin/env python3
"""
Test script to demonstrate team and player comparison functionality.
"""

import sys
import asyncio
sys.path.insert(0, 'src')

from sports_bot.core.agents.sports_agents import run_query_planner, run_enhanced_query_processor, format_enhanced_response
from sports_bot.config.api_config import api_config

async def test_queries():
    """Test various query types."""
    print("🧪 Testing Sports Bot Query System")
    print("=" * 50)
    
    # Test 1: Team Comparison
    print("\n🏈 Test 1: Team Comparison")
    print("Query: 'Compare 49ers and Eagles offensive stats'")
    print("-" * 40)
    
    query_context = await run_query_planner("Compare 49ers and Eagles offensive stats")
    results = await run_enhanced_query_processor("Compare 49ers and Eagles offensive stats", query_context)
    response = format_enhanced_response(results)
    print(response[:500] + "..." if len(response) > 500 else response)
    
    print("\n" + "=" * 50)
    
    # Test 2: Player Comparison  
    print("\n🏈 Test 2: Player Comparison")
    print("Query: 'Who has more passing yards Lamar Jackson or Joe Burrow?'")
    print("-" * 40)
    
    query_context = await run_query_planner("Who has more passing yards Lamar Jackson or Joe Burrow?")
    results = await run_enhanced_query_processor("Who has more passing yards Lamar Jackson or Joe Burrow?", query_context)
    response = format_enhanced_response(results)
    print(response[:500] + "..." if len(response) > 500 else response)
    
    print("\n🎯 Query Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_queries()) 