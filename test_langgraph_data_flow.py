"""
🧪 Test the LangGraph Intelligent Data Flow System
"""

import asyncio
import json
from src.sports_bot.workflows.simple_data_flow import SimpleLangGraphConnector

async def test_langgraph_data_flow():
    """Test the new LangGraph-powered data flow"""
    
    print("=" * 60)
    print("🧠 TESTING LANGGRAPH INTELLIGENT DATA FLOW")
    print("=" * 60)
    
    # Initialize the connector
    connector = SimpleLangGraphConnector()
    
    # Test Case 1: Simple player query
    print("\n🎯 **Test 1: Simple Player Query**")
    context1 = {
        "sport": "NFL",
        "player_names": ["Josh Allen"],
        "metrics_needed": ["passing_yards", "passing_touchdowns"],
        "strategy": "single_player_stat"
    }
    
    result1 = await connector.prepare_debate_data(
        "Josh Allen's passing performance", 
        context1
    )
    
    print(f"Result: {json.dumps(result1, indent=2)}")
    
    # Test Case 2: Player comparison
    print("\n🎯 **Test 2: Player Comparison**")
    context2 = {
        "sport": "NFL", 
        "player_names": ["Josh Allen", "Patrick Mahomes"],
        "metrics_needed": ["passing_yards", "passing_touchdowns"],
        "comparison_target": "player_comparison",
        "strategy": "player_comparison"
    }
    
    result2 = await connector.prepare_debate_data(
        "Josh Allen vs Patrick Mahomes", 
        context2
    )
    
    print(f"Result status: {result2['status']}")
    print(f"Data gathered: {len(result2['data'])} items")
    
    # Test Case 3: League leaders query
    print("\n🎯 **Test 3: League Leaders Query**")
    context3 = {
        "sport": "NFL",
        "player_names": [],
        "metrics_needed": ["passing_yards"],
        "strategy": "leaderboard_query"
    }
    
    result3 = await connector.prepare_debate_data(
        "Who leads the NFL in passing yards?",
        context3
    )
    
    print(f"Result status: {result3['status']}")
    print(f"Metadata: {result3['metadata']}")
    
    print("\n✅ **LangGraph Testing Complete!**")
    return result1, result2, result3

if __name__ == "__main__":
    asyncio.run(test_langgraph_data_flow())
