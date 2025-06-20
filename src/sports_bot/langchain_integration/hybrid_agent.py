"""
Hybrid Sports Agent - LangChain/LangGraph + Custom Logic Integration

This module implements the main hybrid agent that bridges the LangChain/LangGraph
framework with the existing custom sports bot logic, providing the best of both worlds.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import AgentAction, AgentFinish

from sports_bot.langchain_integration.tools import SPORTS_TOOLS, SportContext
from sports_bot.langchain_integration.workflows import WorkflowOrchestrator
from sports_bot.langchain_integration.sport_registry import get_sport_registry, SportRegistry
from sports_bot.langchain_integration.agent_bridge import get_agent_bridge, AgentBridge
from sports_bot.cache.shared_cache import get_cache_instance


class HybridSportsAgent:
    """
    Main hybrid agent that combines LangChain/LangGraph capabilities with existing custom logic.
    
    This implements the hybrid architecture recommended in the architectural review,
    strategically using LangChain for NLU and workflow orchestration while preserving
    optimized custom logic for sport-specific operations.
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.sport_registry = get_sport_registry()
        self.cache = get_cache_instance()
        
        # Initialize LangChain components
        self.tools = SPORTS_TOOLS
        self.workflow_orchestrator = WorkflowOrchestrator()
        
        # Initialize the agent bridge for connecting systems
        self.agent_bridge = get_agent_bridge()
        
        # Build the hybrid agent
        self.agent_executor = self._build_hybrid_agent()
    
    def _build_hybrid_agent(self) -> AgentExecutor:
        """
        Build the hybrid agent that can route between LangGraph workflows and custom logic
        """
        
        # Create the prompt template that includes sport context
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an intelligent sports analysis agent with access to multiple sports leagues and comprehensive statistical data.
            
            You can handle various types of sports queries:
            1. **Player Statistics**: Individual player performance data
            2. **League Leaders**: Top performers across statistical categories  
            3. **Player Comparisons**: Head-to-head player analysis and debates
            4. **Team Analysis**: Team performance and roster information
            5. **Historical Trends**: Multi-season statistical analysis
            
            Available Sports: {available_sports}
            
            **Instructions:**
            - Always identify the sport being queried first
            - Use appropriate tools to gather statistical evidence
            - For complex analysis, break down the query into manageable steps
            - Provide context and explanation with your statistical findings
            - When comparing players, present balanced perspectives with evidence
            
            **Tool Usage Guidelines:**
            - Use `fetch_player_stats` for individual player data
            - Use `fetch_team_listing` when you need team information
            - Use `fuzzy_player_search` when player names might be misspelled or ambiguous
            - For league leaders or complex workflows, I'll route to specialized workflows
            
            Be conversational, insightful, and back up claims with specific statistics.
            """),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent with tools
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    async def process_query(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for processing sports queries using the hybrid approach
        
        This method implements the intelligent routing between LangGraph workflows
        and custom logic based on query complexity and type.
        """
        
        # Step 1: Use LangChain for initial query analysis and sport detection
        query_analysis = await self._analyze_query(user_input, context or {})
        
        if not query_analysis["success"]:
            return query_analysis
        
        sport = query_analysis["sport"]
        query_type = query_analysis["query_type"]
        complexity = query_analysis["complexity"]
        
        # Step 2: Route to appropriate processing method
        if complexity == "high" and query_type in ["league_leaders", "player_debate"]:
            # Use LangGraph workflows for complex multi-step analysis
            return await self._process_with_langgraph(user_input, query_analysis)
        
        elif complexity == "medium" or query_type in ["single_player", "player_comparison"]:
            # Use hybrid approach: LangChain tools + custom logic
            return await self._process_with_hybrid_tools(user_input, query_analysis)
        
        else:
            # Use existing custom logic for simple, optimized queries
            return await self._process_with_custom_logic(user_input, query_analysis)
    
    async def _analyze_query(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LangChain for intelligent query analysis and classification
        
        This implements the recommendation to use LangChain for enhanced NLU capabilities.
        """
        
        analysis_prompt = f"""
        Analyze this sports query and extract key information:
        
        Query: "{user_input}"
        Context: {context}
        
        Provide a JSON response with:
        {{
            "sport": "detected sport code (NFL, NBA, etc.)",
            "query_type": "single_player|player_comparison|league_leaders|team_analysis|player_debate",
            "complexity": "low|medium|high",
            "player_names": ["list of player names mentioned"],
            "team_names": ["list of team names mentioned"],
            "metrics": ["list of statistics requested"],
            "season": "season if specified",
            "position_filter": "position if specified",
            "confidence": "confidence score 0-1"
        }}
        
        Complexity Guidelines:
        - Low: Simple single-player stats, basic team info
        - Medium: Player comparisons, filtered stats, multi-metric analysis  
        - High: League leaders, complex aggregations, multi-step analysis, debates
        """
        
        try:
            messages = [
                SystemMessage(content="You are a sports query analyzer. Always respond with valid JSON."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the JSON response (simplified for demo)
            # In production, you'd use structured output parsing
            import json
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                analysis = {
                    "sport": "NFL",  # Default
                    "query_type": "single_player",
                    "complexity": "medium",
                    "player_names": [],
                    "team_names": [],
                    "metrics": [],
                    "season": None,
                    "position_filter": None,
                    "confidence": 0.5
                }
            
            # Validate the sport is supported
            if not self.sport_registry.is_sport_supported(analysis.get("sport", "")):
                analysis["sport"] = "NFL"  # Default fallback
            
            analysis["success"] = True
            return analysis
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Query analysis failed: {str(e)}",
                "sport": "NFL",
                "query_type": "unknown",
                "complexity": "medium"
            }
    
    async def _process_with_langgraph(self, user_input: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complex queries using LangGraph workflows
        
        This leverages the multi-agent orchestration capabilities for complex analysis.
        """
        
        try:
            query_type = analysis["query_type"]
            sport = analysis["sport"]
            
            if query_type == "league_leaders":
                result = await self.workflow_orchestrator.execute_query(
                    query=user_input,
                    query_type="league_leaders",
                    sport=sport,
                    season=analysis.get("season")
                )
            
            elif query_type == "player_debate":
                result = await self.workflow_orchestrator.execute_query(
                    query=user_input,
                    query_type="player_debate", 
                    sport=sport,
                    player_names=analysis.get("player_names", [])
                )
            
            else:
                return {
                    "success": False,
                    "error": f"LangGraph workflow not available for query type: {query_type}"
                }
            
            return {
                "success": True,
                "method": "langgraph_workflow",
                "query_type": query_type,
                "result": result,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"LangGraph processing failed: {str(e)}",
                "fallback_suggestion": "Trying hybrid tools approach"
            }
    
    async def _process_with_hybrid_tools(self, user_input: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process queries using LangChain tools combined with custom logic
        
        This provides the middle ground between framework convenience and custom optimization.
        """
        
        try:
            # Prepare the input with sport context
            available_sports = ", ".join(self.sport_registry.get_supported_sports())
            
            # Use the LangChain agent executor
            result = await self.agent_executor.ainvoke({
                "input": user_input,
                "available_sports": available_sports,
                "sport_context": analysis.get("sport", "NFL"),
                "chat_history": []
            })
            
            return {
                "success": True,
                "method": "hybrid_tools",
                "query_type": analysis["query_type"],
                "result": result,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Hybrid tools processing failed: {str(e)}",
                "fallback_suggestion": "Trying custom logic approach"
            }
    
    async def _process_with_custom_logic(self, user_input: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process queries using existing custom sports bot logic via the agent bridge
        
        This preserves the optimized custom implementation for scenarios where it performs best.
        """
        
        try:
            # Use the agent bridge to process with custom logic
            result = await self.agent_bridge.process_query(user_input)
            
            return {
                "success": True,
                "method": "custom_logic_via_bridge",
                "query_type": analysis["query_type"],
                "result": result,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Custom logic processing failed: {str(e)}"
            }
    
    def get_supported_capabilities(self) -> Dict[str, Any]:
        """
        Get information about the agent's capabilities across all sports
        """
        
        capabilities = {
            "sports": self.sport_registry.get_sport_display_names(),
            "query_types": [
                "single_player", "player_comparison", "player_debate",
                "league_leaders", "team_analysis", "historical_trends"
            ],
            "processing_methods": {
                "langgraph_workflows": ["league_leaders", "player_debate"],
                "hybrid_tools": ["single_player", "player_comparison", "team_analysis"],
                "custom_logic": ["optimized_queries", "cached_results"]
            },
            "available_tools": [tool.name for tool in self.tools],
            "workflow_types": self.workflow_orchestrator.get_available_workflows()
        }
        
        # Add sport-specific help
        for sport_code in self.sport_registry.get_supported_sports():
            capabilities[f"{sport_code}_help"] = self.sport_registry.get_sport_context_help(sport_code)
        
        return capabilities
    
    async def add_new_sport(self, sport_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically add support for a new sport
        
        This demonstrates the scalability of the hybrid architecture.
        """
        
        try:
            from sports_bot.langchain_integration.sport_registry import register_new_sport
            
            sport_code = sport_config["sport_code"]
            
            # Register the new sport
            register_new_sport(sport_code, sport_config)
            
            # Update agent's sport registry reference
            self.sport_registry = get_sport_registry()
            
            return {
                "success": True,
                "message": f"Successfully added support for {sport_code}",
                "available_sports": self.sport_registry.get_supported_sports()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add sport: {str(e)}"
            }
    
    async def get_sport_help(self, sport_code: str) -> Dict[str, Any]:
        """Get contextual help for a specific sport"""
        return self.sport_registry.get_sport_context_help(sport_code)


class HybridAgentManager:
    """
    Manager class for multiple hybrid agents and session management
    
    This provides the interface for managing multiple user sessions and agent instances.
    """
    
    def __init__(self):
        self.agents: Dict[str, HybridSportsAgent] = {}
        self.default_agent = HybridSportsAgent()
    
    def get_agent(self, session_id: str = "default") -> HybridSportsAgent:
        """Get or create an agent for a specific session"""
        
        if session_id not in self.agents:
            self.agents[session_id] = HybridSportsAgent()
        
        return self.agents[session_id]
    
    async def process_query(self, user_input: str, session_id: str = "default", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query using the appropriate agent"""
        
        agent = self.get_agent(session_id)
        return await agent.process_query(user_input, context)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions and usage"""
        
        return {
            "active_sessions": len(self.agents),
            "session_ids": list(self.agents.keys()),
            "total_capabilities": self.default_agent.get_supported_capabilities()
        }


# Global manager instance
hybrid_agent_manager = HybridAgentManager()


def get_hybrid_agent_manager() -> HybridAgentManager:
    """Get the global hybrid agent manager"""
    return hybrid_agent_manager 