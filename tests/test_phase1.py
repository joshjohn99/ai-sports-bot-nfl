#!/usr/bin/env python3
"""
Test Phase 1 Architecture Integration
Testing query classification and basic functionality.
"""

import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print('🧪 Testing Phase 1 Architecture Integration...')
print('=' * 50)

# Try to import the main components
try:
    from src.sports_bot.core.agents.sports_agents import QueryContext
    print('✅ Successfully imported QueryContext')
except ImportError as e:
    print(f'❌ QueryContext import error: {e}')
    exit(1)

# Test import of new modules
try:
    from src.sports_bot.core.query.query_types import QueryType, QueryClassifier, QueryPlan
    print('✅ Successfully imported QueryType, QueryClassifier, QueryPlan')
    new_components_available = True
except ImportError as e:
    print(f'❌ Query types import error: {e}')
    new_components_available = False

try:
    from src.sports_bot.core.stats.response_formatter import ResponseFormatter, EdgeCaseHandler
    print('✅ Successfully imported ResponseFormatter, EdgeCaseHandler')
    response_formatter_available = True
except ImportError as e:
    print(f'❌ Response formatter import error: {e}')
    response_formatter_available = False

# Test 1: Single player stat query
print('\n🧪 Test 1: Single Player Stat Query')
test_query_1 = QueryContext(
    question='Micah Parsons sacks',
    sport='NFL',
    player_names=['Micah Parsons'],
    metrics_needed=['sacks']
)

query_plan_1 = QueryClassifier.classify_query(test_query_1)
print(f'📋 Query Type: {query_plan_1.query_type.value}')
print(f'📊 Processing Steps: {query_plan_1.processing_steps}')
print(f'📦 Data Sources: {query_plan_1.data_sources_needed}')
print(f'📝 Response Format: {query_plan_1.response_format}')

# Test 2: Player comparison query
print('\n🧪 Test 2: Player Comparison Query')
test_query_2 = QueryContext(
    question='Micah Parsons vs T.J. Watt sacks',
    sport='NFL',
    player_names=['Micah Parsons', 'T.J. Watt'],
    metrics_needed=['sacks']
)

query_plan_2 = QueryClassifier.classify_query(test_query_2)
print(f'📋 Query Type: {query_plan_2.query_type.value}')
print(f'📊 Processing Steps: {query_plan_2.processing_steps}')
print(f'📦 Data Sources: {query_plan_2.data_sources_needed}')
print(f'📝 Response Format: {query_plan_2.response_format}')

# Test 3: Multi-stat query
print('\n🧪 Test 3: Multi-Stat Player Query')
test_query_3 = QueryContext(
    question='Micah Parsons sacks, tackles, and QB hits',
    sport='NFL',
    player_names=['Micah Parsons'],
    metrics_needed=['sacks', 'tackles', 'QB hits']
)

query_plan_3 = QueryClassifier.classify_query(test_query_3)
print(f'📋 Query Type: {query_plan_3.query_type.value}')
print(f'📊 Processing Steps: {query_plan_3.processing_steps}')
print(f'📦 Data Sources: {query_plan_3.data_sources_needed}')
print(f'📝 Response Format: {query_plan_3.response_format}')

# Test 4: Response formatting
print('\n🧪 Test 4: Response Formatting')
mock_result = {
    "query_type": "single_player_stat",
    "player": "Micah Parsons",
    "stats": {
        "simple_stats": {"sacks": 14, "tackles": 64},
        "player_fullName": "Micah Parsons"
    },
    "response_format": "simple"
}

formatted_response = ResponseFormatter.format_response(mock_result)
print("Formatted Response:")
print(formatted_response)

# Test 5: Error handling
print('\n🧪 Test 5: Error Handling')
error_response = EdgeCaseHandler.handle_no_data_found(test_query_1)
print("Error Response:")
print(error_response)

print('\n✅ Phase 1 Architecture components working!')
print('🚀 Ready to integrate with main sports_agents.py flow') 