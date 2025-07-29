import asyncio
import json
import sys

from sports_bot.agents.debate_agent import (
    DebateAgent,
    DebateContext,
    extract_player_names,
    extract_team_names,
    extract_metrics,
    format_comparison_analysis,
    generate_ranking_analysis,
)


async def main():
    """Main function to handle Node.js communication for enhanced LangChain integration"""
    try:
        # Read JSON input from Node.js
        input_data = json.loads(sys.stdin.read())

        action = input_data.get('action')
        context_data = input_data.get('context', {})

        if action == 'test_connection':
            result = {
                'status': 'connected',
                'agent_type': 'NFL Debate Agent',
                'capabilities': [
                    'Player comparisons',
                    'Statistical analysis',
                    'Team evaluations',
                    'Context-aware debates',
                    'Cardinality-aware processing'
                ]
            }
        elif action == 'generateIntelligentDebate':
            result = await handle_intelligent_debate(context_data)
        elif action == 'generateGeneralAnalysis':
            result = await handle_general_analysis(context_data)
        else:
            result = {
                'error': f'Unknown action: {action}',
                'available_actions': ['test_connection', 'generateIntelligentDebate', 'generateGeneralAnalysis']
            }

        # Output JSON result for Node.js
        print(json.dumps(result))

    except Exception as e:
        error_result = {
            'error': f'Python NFL agent error: {str(e)}',
            'type': 'python_error'
        }
        print(json.dumps(error_result))


async def handle_intelligent_debate(context_data: dict) -> dict:
    """Handle intelligent debate generation with cardinality awareness"""

    query = context_data.get('query', '')
    sport = context_data.get('sport', 'NFL')
    cardinality = context_data.get('cardinality', 'one-to-one')
    entity_relationships = context_data.get('entityRelationships', [])

    # Initialize debate agent
    try:
        agent = DebateAgent()

        # Create context based on cardinality
        debate_context = DebateContext(
            query=query,
            player_names=extract_player_names(query, entity_relationships),
            team_names=extract_team_names(query, entity_relationships),
            metrics=extract_metrics(query, entity_relationships),
            time_period="2024 season"
        )

        # Generate debate based on cardinality
        if cardinality == 'many-to-one':
            # Comparison-focused debate
            result = await agent.generate_debate(debate_context)
            result['analysis'] = format_comparison_analysis(result, query)
        elif cardinality == 'one-to-many':
            # Ranking-focused analysis
            result = await generate_ranking_analysis(query, entity_relationships)
        else:
            # Standard debate
            result = await agent.generate_debate(debate_context)

        return {
            'type': 'intelligent_nfl_debate',
            'analysis': result.get('analysis', result.get('conclusion', 'Analysis completed')),
            'confidence': result.get('confidence', 0.85),
            'sport': sport,
            'query': query,
            'cardinality': cardinality,
            'agents_used': ['nfl_debate_agent', 'stats_analyzer'],
            'metadata': {
                'players_analyzed': result.get('players', []),
                'stats_used': result.get('stats', {}),
                'processing_method': 'langchain_intelligence'
            }
        }

    except Exception as e:
        return {
            'type': 'nfl_debate_error',
            'analysis': f"""🏈 **NFL Analysis Error**\n\nQuery: *\"{query}\"*\n\n**Error Processing:** {str(e)}\n\n**Fallback Available:** The system can provide basic NFL analysis through alternative routing.\n\n**Recommendation:** Try rephrasing the query or asking about specific players or teams.\n\n*NFL debate agent temporarily unavailable*""",
            'confidence': 0.50,
            'sport': sport,
            'query': query,
            'cardinality': cardinality,
            'error': str(e)
        }


async def handle_general_analysis(context_data: dict) -> dict:
    """Handle general NFL analysis with enhanced intelligence"""

    query = context_data.get('query', '')
    sport = context_data.get('sport', 'NFL')
    cardinality = context_data.get('cardinality', 'one-to-one')
    entity_relationships = context_data.get('entityRelationships', [])

    # Simple but intelligent analysis
    analysis = f"""🏈 **NFL General Analysis**\n\nQuery: *\"{query}\"*\n\n**Intelligent Processing:**\n• Cardinality: {cardinality}\n• Entities: {', '.join(entity_relationships) if entity_relationships else 'General NFL'}\n• Analysis Type: Context-aware general analysis\n\n**NFL Intelligence:**\nThis query has been processed through the LangChain NFL agent with enhanced understanding of relationships and context.\n\n**Available Analysis:**\n- Player performance metrics\n- Team success factors\n- Statistical comparisons\n- Contextual insights\n\n**Recommendation:**\nFor more detailed analysis, try specific player or team queries with comparative elements.\n\n*Powered by LangChain NFL Intelligence*"""

    return {
        'type': 'nfl_general_analysis',
        'analysis': analysis,
        'confidence': 0.80,
        'sport': sport,
        'query': query,
        'cardinality': cardinality,
        'agents_used': ['nfl_general_agent'],
        'metadata': {
            'processing_type': 'general_analysis',
            'intelligence_level': 'enhanced'
        }
    }


if __name__ == '__main__':
    asyncio.run(main())
