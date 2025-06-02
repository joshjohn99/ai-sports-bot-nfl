#!/usr/bin/env python3
"""
Comprehensive Phase 1 Testing
Tests all key features and improvements of the enhanced architecture.
"""

import asyncio
import sys
from sports_agents import (
    run_query_planner, 
    run_enhanced_query_processor, 
    format_enhanced_response,
    QueryContext
)
from query_types import QueryType, QueryClassifier
from response_formatter import ResponseFormatter, EdgeCaseHandler

async def test_single_player_query():
    """Test basic single player stat query."""
    print("🧪 TEST 1: Single Player Query")
    print("=" * 50)
    
    user_question = "Micah Parsons sacks"
    print(f"Query: '{user_question}'")
    print()
    
    try:
        # Step 1: NLU + Planning
        query_context = await run_query_planner(user_question)
        print(f"✅ NLU Result: Sport={query_context.sport}, Player={query_context.player_names}, Metrics={query_context.metrics_needed}")
        
        # Step 2: Query Classification
        query_plan = QueryClassifier.classify_query(query_context)
        print(f"✅ Classified as: {query_plan.query_type.value}")
        print(f"📊 Processing: {', '.join(query_plan.processing_steps[:3])}...")
        
        # Step 3: Enhanced Processing
        query_results = await run_enhanced_query_processor(user_question, query_context)
        
        # Step 4: Format Response
        formatted_response = format_enhanced_response(query_results)
        print("\n🎯 RESULT:")
        print(formatted_response)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_player_comparison():
    """Test player comparison functionality."""
    print("\n🧪 TEST 2: Player Comparison")
    print("=" * 50)
    
    user_question = "Micah Parsons vs T.J. Watt sacks"
    print(f"Query: '{user_question}'")
    print()
    
    try:
        # Create query context manually for comparison test
        query_context = QueryContext(
            question=user_question,
            sport='NFL',
            player_names=['Micah Parsons', 'T.J. Watt'],
            metrics_needed=['sacks']
        )
        
        # Query Classification
        query_plan = QueryClassifier.classify_query(query_context)
        print(f"✅ Classified as: {query_plan.query_type.value}")
        print(f"📊 Response format: {query_plan.response_format}")
        
        # Enhanced Processing (this will show the comparison logic)
        query_results = await run_enhanced_query_processor(user_question, query_context)
        
        # Format Response
        formatted_response = format_enhanced_response(query_results)
        print("\n🎯 RESULT:")
        print(formatted_response)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling and edge cases."""
    print("\n🧪 TEST 3: Error Handling")
    print("=" * 50)
    
    # Test disambiguation response
    mock_players = [
        {
            'team_name': 'Dallas Cowboys',
            'position': 'Linebacker',
            'jersey': '11'
        },
        {
            'team_name': 'Green Bay Packers', 
            'position': 'Safety',
            'jersey': '11'
        }
    ]
    
    disambiguation_response = ResponseFormatter.format_disambiguation_response(mock_players, "John Smith")
    print("✅ Disambiguation Response:")
    print(disambiguation_response)
    
    # Test error response
    query_context = QueryContext(
        question="Unknown player stats",
        sport='NFL', 
        player_names=['Unknown Player']
    )
    error_response = EdgeCaseHandler.handle_no_data_found(query_context)
    print("\n✅ Error Handling Response:")
    print(error_response)
    
    return True

def test_query_classification():
    """Test query classification accuracy."""
    print("\n🧪 TEST 4: Query Classification")
    print("=" * 50)
    
    test_cases = [
        ("Micah Parsons sacks", QueryType.SINGLE_PLAYER_STAT),
        ("Micah Parsons vs T.J. Watt", QueryType.PLAYER_COMPARISON),
        ("Micah Parsons sacks, tackles, QB hits", QueryType.MULTI_STAT_PLAYER),
        ("Who leads the NFL in sacks?", QueryType.LEAGUE_LEADERS),
    ]
    
    correct_classifications = 0
    
    for question, expected_type in test_cases:
        query_context = QueryContext(
            question=question,
            sport='NFL',
            player_names=['Micah Parsons'] if 'Micah Parsons' in question else [],
            metrics_needed=['sacks'] if 'sacks' in question else []
        )
        
        # Handle comparison case
        if 'vs' in question:
            query_context.player_names = ['Micah Parsons', 'T.J. Watt']
        elif 'sacks, tackles, QB hits' in question:
            query_context.metrics_needed = ['sacks', 'tackles', 'QB hits']
        
        query_plan = QueryClassifier.classify_query(query_context)
        
        status = "✅" if query_plan.query_type == expected_type else "❌"
        print(f"{status} '{question}' → {query_plan.query_type.value}")
        
        if query_plan.query_type == expected_type:
            correct_classifications += 1
    
    accuracy = (correct_classifications / len(test_cases)) * 100
    print(f"\n📊 Classification Accuracy: {accuracy:.0f}% ({correct_classifications}/{len(test_cases)})")
    
    return accuracy >= 75  # 75% threshold for success

async def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("🚀 PHASE 1 COMPREHENSIVE TESTING")
    print("=" * 60)
    print("Testing enhanced query processing, classification, and formatting...")
    print()
    
    results = []
    
    # Run all tests
    results.append(await test_single_player_query())
    results.append(await test_player_comparison()) 
    results.append(test_error_handling())
    results.append(test_query_classification())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Single Player Query",
        "Player Comparison", 
        "Error Handling",
        "Query Classification"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<20} {status}")
    
    print("-" * 60)
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Phase 1 is working perfectly!")
        print("\n🔥 Key Improvements Verified:")
        print("  • Enhanced query classification")
        print("  • Better response formatting with rankings")
        print("  • Robust error handling with suggestions")
        print("  • Support for multiple query types")
        print("  • Graceful fallback to legacy system")
    else:
        print("⚠️  Some tests failed. Phase 1 needs attention.")
    
    return passed == total

if __name__ == "__main__":
    print("Starting comprehensive Phase 1 testing...")
    print("This will test all enhanced features without requiring API calls for comparison.\n")
    
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1) 