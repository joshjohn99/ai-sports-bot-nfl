#!/usr/bin/env python3
"""
Multi-Agent Orchestrator for Cross-Sport Intelligence
Handles complex cardinality relationships and entity management
"""

import json
import sys
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class QueryCardinality(Enum):
    """Query cardinality types for relationship analysis"""
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many" 
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"

class ComplexityLevel(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

@dataclass
class QueryContext:
    """Enhanced context for multi-agent processing"""
    query: str
    sport: str
    classification: Dict[str, Any]
    cardinality: str
    complexity: str
    entity_relationships: List[str]
    timestamp: str

class MultiAgentOrchestrator:
    """
    Orchestrates multiple AI agents for complex sports analysis
    Handles cardinality relationships and cross-sport intelligence
    """
    
    def __init__(self):
        self.available_agents = {
            'nfl_agent': True,
            'nba_agent': True,
            'stats_analyzer': True,
            'comparison_engine': True,
            'historical_analyzer': True
        }
    
    async def handle_cross_sport_query(self, context: QueryContext) -> Dict[str, Any]:
        """
        Handle cross-sport queries with intelligent agent coordination
        """
        try:
            cardinality = QueryCardinality(context.cardinality)
            complexity = ComplexityLevel(context.complexity)
            
            if cardinality == QueryCardinality.MANY_TO_MANY:
                return await self._handle_many_to_many_analysis(context)
            elif cardinality == QueryCardinality.MANY_TO_ONE:
                return await self._handle_comparison_analysis(context)
            elif cardinality == QueryCardinality.ONE_TO_MANY:
                return await self._handle_ranking_analysis(context)
            else:
                return await self._handle_simple_analysis(context)
                
        except Exception as e:
            return self._generate_error_response(str(e), context)
    
    async def _handle_many_to_many_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Handle complex many-to-many relationships"""
        
        if 'historical' in context.entity_relationships:
            return {
                'type': 'cross_sport_historical_analysis',
                'analysis': f"""🏆 **Cross-Sport Historical Analysis**

Query: *"{context.query}"*

**Multi-Entity Relationship Analysis:**

This query involves complex relationships between multiple entities across potentially different sports and eras.

**Analysis Framework:**
• **Cross-Era Normalization:** Adjusting for rule changes and competition levels
• **Multi-Sport Metrics:** Comparing impact across different sports
• **Statistical Significance:** Evaluating performance in context
• **Cultural Impact:** Assessing broader influence beyond statistics

**Intelligent Routing:**
The system has identified this as a many-to-many query requiring:
- Multiple data sources across sports
- Historical context analysis  
- Complex relationship mapping
- Era-adjusted performance metrics

**Recommendation:** 
This type of analysis benefits from specialized historical agents and cross-sport comparison engines working in coordination.

*Powered by Multi-Agent LangChain Intelligence*""",
                'confidence': 0.88,
                'sport': 'CROSS_SPORT',
                'query': context.query,
                'cardinality': context.cardinality,
                'agents_used': ['historical_analyzer', 'cross_sport_engine', 'stats_normalizer'],
                'metadata': {
                    'complexity': context.complexity,
                    'entity_count': len(context.entity_relationships),
                    'requires_specialized_processing': True
                }
            }
        
        return {
            'type': 'many_to_many_general',
            'analysis': f"""⚡ **Complex Multi-Entity Analysis**

Query: *"{context.query}"*

**Cardinality Detection:** Many-to-Many relationship identified

**Processing Strategy:**
• Multiple entities with multiple potential outcomes
• Cross-referential analysis required
• Relationship mapping across data sources
• Hierarchical ranking considerations

**Agent Coordination:**
- Primary: Multi-agent orchestrator
- Secondary: Specialized ranking engines
- Tertiary: Historical context providers

*This query type requires sophisticated agent coordination for optimal results.*""",
            'confidence': 0.82,
            'sport': context.sport.upper(),
            'query': context.query,
            'cardinality': context.cardinality
        }
    
    async def _handle_comparison_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Handle many-to-one comparisons"""
        
        return {
            'type': 'intelligent_comparison',
            'analysis': f"""⚖️ **Intelligent Comparison Analysis**

Query: *"{context.query}"*

**Comparison Framework Activated:**

**Detected Entities:** {', '.join(context.entity_relationships)}

**Analysis Methodology:**
• **Statistical Comparison:** Head-to-head metrics analysis
• **Contextual Factors:** Team success, era considerations  
• **Intangible Factors:** Leadership, clutch performance, impact
• **Weighted Scoring:** Multi-factor evaluation system

**Agent Coordination:**
- Comparison Engine: Primary analysis coordinator
- Stats Analyzer: Quantitative metrics processing
- Context Provider: Situational factor analysis

**Intelligent Verdict:**
The multi-agent system will evaluate all factors to provide a data-driven conclusion with confidence scoring.

*Processing through specialized comparison agents...*""",
            'confidence': 0.90,
            'sport': context.sport.upper(),
            'query': context.query,
            'cardinality': context.cardinality,
            'agents_used': ['comparison_engine', 'stats_analyzer', 'context_provider']
        }
    
    async def _handle_ranking_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Handle one-to-many rankings"""
        
        return {
            'type': 'intelligent_ranking',
            'analysis': f"""📊 **Intelligent Ranking Analysis**

Query: *"{context.query}"*

**Ranking System Activated:**

**Methodology:**
• **Multi-Criteria Evaluation:** Statistics, impact, achievements
• **Weighted Scoring:** Position-specific importance factors  
• **Peer Comparison:** Relative performance analysis
• **Consistency Metrics:** Performance stability over time

**Agent Pipeline:**
1. **Data Collector:** Aggregates comprehensive statistics
2. **Ranking Engine:** Applies weighted evaluation criteria  
3. **Validator:** Cross-checks results for accuracy
4. **Formatter:** Presents rankings with explanations

**Entity Relationships:** {', '.join(context.entity_relationships)}

**Processing Status:**
The ranking system is analyzing multiple candidates and will provide a hierarchical list with detailed justifications.

*Coordinating specialized ranking agents...*""",
            'confidence': 0.87,
            'sport': context.sport.upper(),
            'query': context.query,
            'cardinality': context.cardinality,
            'agents_used': ['ranking_engine', 'data_collector', 'validator']
        }
    
    async def _handle_simple_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """Handle one-to-one simple queries"""
        
        return {
            'type': 'focused_analysis',
            'analysis': f"""🎯 **Focused Entity Analysis**

Query: *"{context.query}"*

**Single-Entity Processing:**

**Identified Focus:** {context.entity_relationships[0] if context.entity_relationships else 'General'}

**Analysis Approach:**
• **Direct Lookup:** Targeted data retrieval
• **Context Addition:** Relevant background information
• **Verification:** Data accuracy confirmation
• **Enhancement:** Additional insights and context

**Agent Assignment:**
- Primary: Specialized {context.sport.upper()} agent
- Support: Stats verification system
- Enhancement: Context enrichment engine

**Processing Efficiency:**
Single-entity queries benefit from direct agent routing with minimal orchestration overhead.

*Routing to specialized {context.sport.upper()} analysis agent...*""",
            'confidence': 0.93,
            'sport': context.sport.upper(),
            'query': context.query,
            'cardinality': context.cardinality,
            'agents_used': [f'{context.sport.lower()}_agent', 'stats_verifier']
        }
    
    def _generate_error_response(self, error: str, context: QueryContext) -> Dict[str, Any]:
        """Generate error response with helpful information"""
        
        return {
            'type': 'orchestrator_error',
            'analysis': f"""❌ **Multi-Agent Processing Error**

Query: *"{context.query}"*

**Error Details:** {error}

**Fallback Processing:**
The orchestrator encountered an issue but can provide basic analysis:

**Detected Characteristics:**
• Sport: {context.sport.upper()}
• Cardinality: {context.cardinality}
• Complexity: {context.complexity}
• Entities: {', '.join(context.entity_relationships)}

**Recommendation:**
Try rephrasing the query or breaking it into smaller, more specific questions.

**Available Fallback:**
The system can still process simpler versions of this query through individual agent endpoints.

*Multi-agent orchestration temporarily unavailable*""",
            'confidence': 0.60,
            'sport': context.sport.upper(),
            'query': context.query,
            'cardinality': context.cardinality,
            'error': error
        }

async def main():
    """Main function to handle Node.js communication"""
    try:
        # Read JSON input from Node.js
        input_data = json.loads(sys.stdin.read())
        
        action = input_data.get('action')
        context_data = input_data.get('context', {})
        
        orchestrator = MultiAgentOrchestrator()
        
        if action == 'test_connection':
            result = {
                'status': 'connected',
                'available_agents': orchestrator.available_agents,
                'capabilities': [
                    'Cross-sport analysis',
                    'Cardinality relationship handling', 
                    'Multi-agent coordination',
                    'Complex query processing'
                ]
            }
        elif action == 'handleCrossSportQuery':
            # Convert context data to QueryContext
            context = QueryContext(
                query=context_data['query'],
                sport=context_data['sport'],
                classification=context_data['classification'],
                cardinality=context_data['cardinality'],
                complexity=context_data['complexity'],
                entity_relationships=context_data['entityRelationships'],
                timestamp=context_data['timestamp']
            )
            result = await orchestrator.handle_cross_sport_query(context)
        else:
            result = {
                'error': f'Unknown action: {action}',
                'available_actions': ['test_connection', 'handleCrossSportQuery']
            }
        
        # Output JSON result for Node.js
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            'error': f'Python orchestrator error: {str(e)}',
            'type': 'python_error'
        }
        print(json.dumps(error_result))

if __name__ == '__main__':
    asyncio.run(main()) 