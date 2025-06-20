#!/usr/bin/env python3
import sys, os, asyncio
sys.path.insert(0, 'src')
from sports_bot.core.agents.sports_agents import QueryContext, run_enhanced_query_processor

async def test_touchdowns():
    query_context = QueryContext(question='Who has the most touchdowns?', sport='NFL')
    result = await run_enhanced_query_processor('Who has the most touchdowns?', query_context)
    print('Result type:', type(result))
    if isinstance(result, dict):
        print('Keys:', list(result.keys()))
        if 'error' in result:
            print('Error:', result['error'])
        else:
            print('Success!')
            print('Leaders:', result.get('leaders', [])[:3])

if __name__ == "__main__":
    asyncio.run(test_touchdowns()) 