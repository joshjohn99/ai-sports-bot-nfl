#!/usr/bin/env python3
"""
Test Enhanced Processing System with Real Queries
"""

import asyncio
from sports_agents import run_query_planner, run_enhanced_query_processor, format_enhanced_response

async def test_enhanced_processing():
    print('🧪 Testing Enhanced Processing with Real Query...')
    print()
    
    # Test with a simple query
    user_question = 'Micah Parsons sacks'
    print(f'Query: {user_question}')
    print()
    
    try:
        # Step 1: Run NLU + Query Planner
        print('Step 1: Running NLU + Query Planner...')
        query_context = await run_query_planner(user_question)
        print(f'✅ Query Context created: {query_context.sport}, {query_context.player_names}, {query_context.metrics_needed}')
        print()
        
        # Step 2: Run Enhanced Processor  
        print('Step 2: Running Enhanced Processor...')
        query_results = await run_enhanced_query_processor(user_question, query_context)
        print(f'✅ Enhanced Processing completed')
        print(f'Result keys: {list(query_results.keys())}')
        print()
        
        # Step 3: Format Response
        print('Step 3: Formatting Response...')
        formatted_response = format_enhanced_response(query_results)
        print('🎯 Final Formatted Response:')
        print(formatted_response)
        
    except Exception as e:
        print(f'❌ Error during testing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_processing()) 