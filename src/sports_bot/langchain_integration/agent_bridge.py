"""
Agent Bridge - Connecting Custom Agents with LangChain Integration

This module provides the bridge between the existing custom sports agents
and the new LangChain/LangGraph hybrid system, ensuring seamless integration.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
from dataclasses import asdict

# Import existing custom agents
from sports_bot.agents.sports_agents import (
    QueryContext as CustomQueryContext,
    run_query_planner,
    run_enhanced_query_processor,
    format_enhanced_response,
    console
)

# Import LangChain components
from sports_bot.langchain_integration.tools import SPORTS_TOOLS, SportContext
from sports_bot.langchain_integration.workflows import WorkflowOrchestrator
from sports_bot.langchain_integration.sport_registry import get_sport_registry

# Import core components
from sports_bot.core.query.query_types import QueryType, QueryClassifier, QueryPlan
from sports_bot.core.stats.stat_retriever import StatRetrieverApiAgent
from sports_bot.config.api_config import api_config
from sports_bot.cache.shared_cache import get_cache_instance


class AgentBridge:
    """
    Bridge class that connects existing custom agents with LangChain integration.
    
    This provides a unified interface that can leverage both systems based on
    query complexity and requirements.
    """
    
    def __init__(self):
        self.sport_registry = get_sport_registry()
        self.cache = get_cache_instance()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self.query_classifier = QueryClassifier()
        self.stat_retriever = StatRetrieverApiAgent(api_config)
        
        # Track which system handled each query for analytics
        self.query_routing_stats = {
            "custom_nlu": 0,
            "langgraph_workflow": 0,
            "hybrid_tools": 0,
            "fallback": 0
        }
    
    async def process_query(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point that intelligently routes queries between systems.
        
        This implements the hybrid architecture decision tree:
        1. Use existing custom NLU for query understanding (proven and optimized)
        2. Route to LangGraph for complex multi-agent workflows
        3. Use LangChain tools for standardized API operations
        4. Fall back to custom logic for simple optimized operations
        """
        
        try:
            # Step 1: Use existing custom NLU system (it's proven and works well)
            query_context = await self._analyze_with_custom_nlu(user_input)
            
            # Step 2: Determine routing strategy based on query analysis
            routing_decision = self._determine_routing_strategy(query_context)
            
            # Step 3: Route to appropriate system
            if routing_decision["method"] == "langgraph_workflow":
                return await self._process_with_langgraph(user_input, query_context, routing_decision)
                
            elif routing_decision["method"] == "hybrid_tools":
                return await self._process_with_hybrid_tools(user_input, query_context, routing_decision)
                
            elif routing_decision["method"] == "custom_enhanced":
                return await self._process_with_custom_enhanced(user_input, query_context)
                
            else:  # fallback to basic custom
                return await self._process_with_custom_basic(user_input, query_context)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent bridge processing failed: {str(e)}",
                "method": "error_fallback"
            }
    
    async def _analyze_with_custom_nlu(self, user_input: str) -> CustomQueryContext:
        """
        Use the existing proven NLU system for query analysis.
        
        This leverages the custom agents that are already working well.
        """
        
        try:
            # Use the existing run_query_planner which includes NLU + Query Planning
            query_context = await run_query_planner(user_input)
            self.query_routing_stats["custom_nlu"] += 1
            
            return query_context
            
        except Exception as e:
            # If the custom NLU fails, create a basic QueryContext manually
            console.print(f"[yellow]Custom NLU failed: {str(e)}. Creating basic QueryContext.[/yellow]")
            
            # Create a minimal QueryContext that should work
            basic_context = CustomQueryContext(
                question=user_input,
                sport="NFL",  # Default to NFL
                player_names=[],
                team_names=[],
                metrics_needed=[],
                strategy="basic_query"
            )
            
            return basic_context
    
    def _determine_routing_strategy(self, query_context: CustomQueryContext) -> Dict[str, Any]:
        """
        Intelligent routing decision based on query characteristics.
        
        This implements the hybrid architecture routing logic.
        """
        
        # Extract key characteristics
        has_multiple_players = len(query_context.player_names) > 1
        is_leaderboard_query = (query_context.strategy == "leaderboard_query" or 
                               not query_context.player_names and query_context.metrics_needed)
        is_complex_comparison = (query_context.comparison_target and 
                               len(query_context.player_names) > 2)
        requires_debate_analysis = ("better" in query_context.question.lower() or 
                                  "best" in query_context.question.lower() or
                                  "debate" in query_context.question.lower())
        
        # Routing decision tree
        if is_leaderboard_query and query_context.metrics_needed:
            return {
                "method": "langgraph_workflow",
                "workflow_type": "league_leaders",
                "reason": "Complex leaderboard query requiring multi-step aggregation"
            }
        
        elif (has_multiple_players and requires_debate_analysis) or is_complex_comparison:
            return {
                "method": "langgraph_workflow", 
                "workflow_type": "player_debate",
                "reason": "Multi-player comparison requiring debate-style analysis"
            }
        
        elif (has_multiple_players or query_context.comparison_target or 
              len(query_context.metrics_needed) > 2):
            return {
                "method": "hybrid_tools",
                "reason": "Medium complexity query benefiting from LangChain tools"
            }
        
        elif query_context.strategy in ["requires_player_name", "requires_team_name"]:
            return {
                "method": "custom_enhanced",
                "reason": "Validation/disambiguation needed - custom system handles this well"
            }
        
        else:
            return {
                "method": "custom_enhanced",
                "reason": "Standard query - use optimized custom system"
            }
    
    async def _process_with_langgraph(self, user_input: str, query_context: CustomQueryContext, 
                                    routing_decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using LangGraph workflows for complex multi-agent analysis.
        """
        
        try:
            workflow_type = routing_decision["workflow_type"]
            
            if workflow_type == "league_leaders":
                result = await self.workflow_orchestrator.execute_query(
                    query=user_input,
                    query_type="league_leaders",
                    sport=query_context.sport or "NFL",
                    season=query_context.season
                )
            
            elif workflow_type == "player_debate":
                result = await self.workflow_orchestrator.execute_query(
                    query=user_input,
                    query_type="player_debate",
                    sport=query_context.sport or "NFL", 
                    player_names=query_context.player_names
                )
            
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            self.query_routing_stats["langgraph_workflow"] += 1
            
            return {
                "success": True,
                "method": "langgraph_workflow",
                "workflow_type": workflow_type,
                "result": result,
                "query_context": asdict(query_context) if hasattr(query_context, '__dict__') else query_context.dict(),
                "routing_reason": routing_decision["reason"]
            }
            
        except Exception as e:
            # Graceful fallback to hybrid tools
            return await self._process_with_hybrid_tools(user_input, query_context, 
                                                       {"reason": f"LangGraph fallback: {str(e)}"})
    
    async def _process_with_hybrid_tools(self, user_input: str, query_context: CustomQueryContext,
                                       routing_decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using LangChain tools combined with custom logic.
        
        This provides a middle ground between framework convenience and optimization.
        """
        
        try:
            # Convert custom QueryContext to format suitable for LangChain tools
            sport_context = SportContext(
                sport=query_context.sport or "NFL",
                season=query_context.season
            )
            
            # Use LangChain tools for API operations
            results = {}
            
            # If we need player stats, use the LangChain tool
            if query_context.player_names:
                from sports_bot.langchain_integration.tools import FetchPlayerStatsTool
                
                stats_tool = FetchPlayerStatsTool()
                for player_name in query_context.player_names:
                    player_result = stats_tool._run(
                        player_name=player_name,
                        sport_context=sport_context,
                        metrics=query_context.metrics_needed or []
                    )
                    results[player_name] = player_result
            
            # If we need team data, use the team listing tool
            if query_context.team_names or not query_context.player_names:
                from sports_bot.langchain_integration.tools import FetchTeamListingTool
                
                team_tool = FetchTeamListingTool()
                team_result = team_tool._run(sport_context=sport_context)
                results["teams"] = team_result
            
            self.query_routing_stats["hybrid_tools"] += 1
            
            return {
                "success": True,
                "method": "hybrid_tools",
                "result": results,
                "query_context": query_context.dict() if hasattr(query_context, 'dict') else str(query_context),
                "routing_reason": routing_decision["reason"]
            }
            
        except Exception as e:
            # Graceful fallback to custom enhanced processing
            return await self._process_with_custom_enhanced(user_input, query_context)
    
    async def _process_with_custom_enhanced(self, user_input: str, 
                                          query_context: CustomQueryContext) -> Dict[str, Any]:
        """
        Process using the existing enhanced custom system.
        
        This leverages the proven custom logic that's already optimized.
        """
        
        try:
            # Use the existing enhanced query processor
            query_results = await run_enhanced_query_processor(user_input, query_context)
            
            # Format the response using existing formatter
            formatted_response = format_enhanced_response(query_results)
            
            return {
                "success": True,
                "method": "custom_enhanced",
                "result": {
                    "formatted_response": formatted_response,
                    "raw_results": query_results
                },
                "query_context": query_context.dict() if hasattr(query_context, 'dict') else str(query_context),
                "routing_reason": "Using optimized custom enhanced processing"
            }
            
        except Exception as e:
            # Final fallback to basic custom processing
            return await self._process_with_custom_basic(user_input, query_context)
    
    async def _process_with_custom_basic(self, user_input: str, 
                                       query_context: CustomQueryContext) -> Dict[str, Any]:
        """
        Final fallback using basic custom stat retrieval.
        """
        
        try:
            # Use basic stat retriever
            result = self.stat_retriever.fetch_stats(query_context)
            
            self.query_routing_stats["fallback"] += 1
            
            return {
                "success": True,
                "method": "custom_basic_fallback",
                "result": result,
                "query_context": query_context.dict() if hasattr(query_context, 'dict') else str(query_context),
                "routing_reason": "Final fallback to basic stat retrieval"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"All processing methods failed. Final error: {str(e)}",
                "method": "complete_failure"
            }
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about query routing decisions."""
        
        total_queries = sum(self.query_routing_stats.values())
        
        if total_queries == 0:
            return {"message": "No queries processed yet"}
        
        return {
            "total_queries": total_queries,
            "routing_breakdown": {
                method: {
                    "count": count,
                    "percentage": round((count / total_queries) * 100, 2)
                }
                for method, count in self.query_routing_stats.items()
            },
            "efficiency_metrics": {
                "langgraph_usage": round((self.query_routing_stats["langgraph_workflow"] / total_queries) * 100, 2),
                "hybrid_tools_usage": round((self.query_routing_stats["hybrid_tools"] / total_queries) * 100, 2),
                "custom_system_usage": round(((self.query_routing_stats["custom_nlu"] + self.query_routing_stats["fallback"]) / total_queries) * 100, 2)
            }
        }
    
    def get_supported_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive capabilities across all integrated systems."""
        
        return {
            "integration_approach": "hybrid_bridge",
            "nlu_system": "custom_proven_agents",
            "workflow_engine": "langgraph_multi_agent",
            "api_integration": "langchain_tools",
            "fallback_system": "custom_optimized_logic",
            
            "supported_sports": self.sport_registry.get_sport_display_names(),
            "query_types": [
                "single_player_stats", "player_comparisons", "league_leaders",
                "team_analysis", "player_debates", "historical_trends"
            ],
            "processing_methods": {
                "langgraph_workflows": ["league_leaders", "player_debates", "complex_analysis"],
                "hybrid_tools": ["player_comparisons", "team_analysis", "multi_metric_queries"],
                "custom_enhanced": ["optimized_queries", "disambiguation", "validation"],
                "custom_basic": ["fallback_operations", "simple_stats"]
            },
            
            "routing_intelligence": {
                "automatic_complexity_detection": True,
                "graceful_fallbacks": True,
                "performance_optimization": True,
                "error_recovery": True
            }
        }


# Global bridge instance
agent_bridge = AgentBridge()


def get_agent_bridge() -> AgentBridge:
    """Get the global agent bridge instance."""
    return agent_bridge


# Convenience functions for easy integration
async def process_sports_query(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function for processing sports queries through the bridge.
    
    This is the main entry point for external systems.
    """
    bridge = get_agent_bridge()
    return await bridge.process_query(user_input, context)


def get_integration_status() -> Dict[str, Any]:
    """Get status of the integration between systems."""
    
    bridge = get_agent_bridge()
    
    return {
        "bridge_status": "active",
        "systems_integrated": [
            "custom_nlu_agents",
            "langgraph_workflows", 
            "langchain_tools",
            "custom_stat_retriever"
        ],
        "routing_statistics": bridge.get_routing_statistics(),
        "capabilities": bridge.get_supported_capabilities()
    } 