#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sports_bot.core.sports_agents import run_query_planner, run_enhanced_query_processor, format_enhanced_response
from sports_bot.config.api_config import api_config

async def test_comparison():
    query = "who had the most touchdowns between Micah Parsons and Justin Jefferson"
    print(f"🧪 Testing: {query}")
    print("=" * 80)
    
    try:
        # Step 1: NLU Processing
        print("📝 Step 1: NLU Processing...")
        query_context = await run_query_planner(query)
        print(f"✅ Player names extracted: {query_context.player_names}")
        print(f"✅ Comparison target: {query_context.comparison_target}")
        print(f"✅ Output expectation: {query_context.output_expectation}")
        print()
        
        # Step 2: Enhanced Query Processing
        print("🚀 Step 2: Enhanced Query Processing...")
        query_results = await run_enhanced_query_processor(query, query_context)
        print(f"✅ Query type: {query_results.get('query_type')}")
        print(f"✅ Players processed: {query_results.get('players', [])}")
        print()
        
        # Step 3: Response Formatting
        print("📊 Step 3: Response Formatting...")
        formatted_response = format_enhanced_response(query_results)
        print("=" * 80)
        print("🏆 FINAL RESULT:")
        print("=" * 80)
        print(formatted_response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comparison()) 