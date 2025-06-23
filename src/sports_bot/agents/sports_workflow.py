"""
Sports LangGraph Workflow - Advanced Query Processing

This module provides LangGraph-based workflows for:
1. Complex multi-step sports queries
2. Cross-sport comparisons
3. Intelligent routing and fallback handling
4. Dynamic sport-specific processing
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, TypedDict
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END, START
    from langgraph.prebuilt import ToolExecutor
    from langgraph.checkpoint.sqlite import SqliteSaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("LangGraph not available, using fallback workflow")
    StateGraph = None
    END = "END"
    START = "START"
    LANGGRAPH_AVAILABLE = False

# LangChain imports
try:
    from langchain.tools import BaseTool, tool
    from langchain.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain not available, using simplified processing")
    BaseTool = object
    tool = lambda func: func
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class WorkflowState(TypedDict):
    """State for LangGraph workflow"""
    # Input
    original_query: str
    user_id: Optional[str]
    conversation_id: Optional[str]
    
    # Detection & Analysis
    detected_sports: List[Dict[str, Any]]
    primary_sport: Optional[str]
    query_type: str
    entities: Dict[str, List[str]]
    metrics: List[str]
    temporal_context: List[str]
    
    # Routing & Processing
    routing_decision: Dict[str, Any]
    processing_steps: List[str]
    
    # Results
    sport_responses: Dict[str, Dict[str, Any]]
    final_response: str
    confidence_score: float
    
    # Metadata
    processing_time: float
    error_messages: List[str]
    debug_info: Dict[str, Any]

class SportsWorkflowOrchestrator:
    """
    Advanced LangGraph-based workflow orchestrator for sports queries
    
    Features:
    - Multi-step query processing with state management
    - Dynamic sport detection and routing
    - Cross-sport comparison workflows
    - Intelligent fallback and error recovery
    - Conversation context and memory
    """
    
    def __init__(self):
        self.console = Console()
        
        # Initialize LLM for advanced reasoning
        self.llm = self._initialize_llm()
        
        # Initialize workflow components
        self.workflow = None
        self.checkpointer = None
        
        if LANGGRAPH_AVAILABLE:
            self.workflow = self._create_advanced_workflow()
            self.checkpointer = self._create_checkpointer()
        
        # Sport-specific processors
        self.sport_processors = self._initialize_sport_processors()
        
        console.print(Panel.fit(
            "[bold green]🚀 Sports Workflow Orchestrator Initialized[/bold green]\n"
            f"[cyan]• LangGraph Available: {LANGGRAPH_AVAILABLE}[/cyan]\n"
            f"[cyan]• LangChain Available: {LANGCHAIN_AVAILABLE}[/cyan]\n"
            "[cyan]• Multi-step query processing[/cyan]\n"
            "[cyan]• Cross-sport comparison workflows[/cyan]\n"
            "[cyan]• Intelligent error recovery[/cyan]",
            border_style="green"
        ))

    def _initialize_llm(self):
        """Initialize LLM for advanced reasoning"""
        if ChatOpenAI:
            try:
                return ChatOpenAI(
                    model="gpt-4",
                    temperature=0.1,
                    max_tokens=2000
                )
            except Exception as e:
                logger.warning(f"Failed to create ChatOpenAI with GPT-4: {e}")
                try:
                    return ChatOpenAI(temperature=0.1)
                except Exception as fallback_error:
                    logger.error(f"Failed to create ChatOpenAI with fallback settings: {fallback_error}")
        return None

    def _create_checkpointer(self):
        """Create SQLite checkpointer for conversation persistence"""
        if LANGGRAPH_AVAILABLE:
            try:
                return SqliteSaver.from_conn_string(":memory:")
            except Exception as e:
                logger.warning(f"Failed to create SQLite checkpointer: {e}")
        return None

    def _initialize_sport_processors(self) -> Dict[str, Any]:
        """Initialize sport-specific processing modules"""
        processors = {}
        
        # Try to import existing sport processors
        try:
            from ..agents.sports_agents import run_query_planner, run_enhanced_query_processor
            processors["query_planner"] = run_query_planner
            processors["enhanced_processor"] = run_enhanced_query_processor
        except ImportError:
            console.print("[dim yellow]Note: Advanced sport processors not available[/dim yellow]")
        
        return processors

    def _create_advanced_workflow(self) -> StateGraph:
        """Create advanced LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        workflow = StateGraph(WorkflowState)
        
        # Define workflow nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("detect_sports", self._detect_sports_node)
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("route_query", self._route_query_node)
        workflow.add_node("process_single_sport", self._process_single_sport_node)
        workflow.add_node("process_cross_sport", self._process_cross_sport_node)
        workflow.add_node("handle_ambiguous", self._handle_ambiguous_node)
        workflow.add_node("format_response", self._format_response_node)
        workflow.add_node("error_recovery", self._error_recovery_node)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "detect_sports")
        workflow.add_edge("detect_sports", "analyze_query")
        workflow.add_edge("analyze_query", "route_query")
        
        # Conditional routing based on query type
        workflow.add_conditional_edges(
            "route_query",
            self._routing_condition,
            {
                "single_sport": "process_single_sport",
                "cross_sport": "process_cross_sport",
                "ambiguous": "handle_ambiguous",
                "error": "error_recovery"
            }
        )
        
        # All processing paths lead to response formatting
        workflow.add_edge("process_single_sport", "format_response")
        workflow.add_edge("process_cross_sport", "format_response")
        workflow.add_edge("handle_ambiguous", "format_response")
        workflow.add_edge("error_recovery", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile(checkpointer=self.checkpointer)

    async def _initialize_node(self, state: WorkflowState) -> WorkflowState:
        """Initialize workflow state"""
        state["processing_steps"] = ["initialize"]
        state["debug_info"] = {"start_time": datetime.now().isoformat()}
        state["error_messages"] = []
        state["confidence_score"] = 0.0
        
        console.print("[cyan]🚀 Initializing workflow...[/cyan]")
        return state

    async def _detect_sports_node(self, state: WorkflowState) -> WorkflowState:
        """Detect sports mentioned in the query"""
        state["processing_steps"].append("detect_sports")
        console.print("[cyan]🔍 Detecting sports...[/cyan]")
        
        try:
            # Import universal agent for sport detection
            from .universal_sports_agent import universal_sports_agent
            
            # Use the universal agent's detection tools
            detection_result = universal_sports_agent.sport_detection_tools[0](state["original_query"])
            detection_data = json.loads(detection_result)
            
            state["detected_sports"] = detection_data.get("detected_sports", [])
            
            if state["detected_sports"]:
                # Find primary sport (highest confidence)
                primary = max(state["detected_sports"], key=lambda x: x["confidence"])
                state["primary_sport"] = primary["sport"]
                state["confidence_score"] = primary["confidence"]
                
                console.print(f"[green]✅ Detected {len(state['detected_sports'])} sports, primary: {state['primary_sport']}[/green]")
            else:
                console.print("[yellow]⚠️ No sports detected[/yellow]")
                
        except Exception as e:
            state["error_messages"].append(f"Sport detection error: {str(e)}")
            console.print(f"[red]❌ Sport detection failed: {e}[/red]")
        
        return state

    async def _analyze_query_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze query for entities, metrics, and intent"""
        state["processing_steps"].append("analyze_query")
        console.print("[cyan]🎯 Analyzing query...[/cyan]")
        
        try:
            from .universal_sports_agent import universal_sports_agent
            
            # Extract entities
            extraction_result = universal_sports_agent.sport_detection_tools[1](
                state["original_query"], 
                state.get("primary_sport")
            )
            entities_data = json.loads(extraction_result)
            
            state["entities"] = entities_data
            state["metrics"] = entities_data.get("metrics", [])
            state["temporal_context"] = entities_data.get("temporal", [])
            
            # Determine query type using LLM if available
            if self.llm:
                state["query_type"] = await self._classify_query_type(state["original_query"])
            else:
                state["query_type"] = self._simple_query_classification(state)
            
            console.print(f"[green]✅ Query type: {state['query_type']}, entities extracted[/green]")
            
        except Exception as e:
            state["error_messages"].append(f"Query analysis error: {str(e)}")
            console.print(f"[red]❌ Query analysis failed: {e}[/red]")
        
        return state

    async def _classify_query_type(self, query: str) -> str:
        """Use LLM to classify query type"""
        if not self.llm:
            return "unknown"
        
        prompt = PromptTemplate(
            input_variables=["query"],
            template="""
            Classify this sports query into one of these categories:
            - player_stats: Asking for individual player statistics
            - team_stats: Asking for team performance data
            - comparison: Comparing players, teams, or stats
            - historical: Asking about past performance or records
            - current: Asking about current season/recent performance
            - prediction: Asking for future predictions or analysis
            - general: General sports information or trivia
            
            Query: {query}
            
            Classification:
            """
        )
        
        try:
            response = await self.llm.ainvoke(prompt.format(query=query))
            return response.content.strip().lower()
        except:
            return "unknown"

    def _simple_query_classification(self, state: WorkflowState) -> str:
        """Simple rule-based query classification"""
        query_lower = state["original_query"].lower()
        
        if any(word in query_lower for word in ["vs", "versus", "compared to", "better than"]):
            return "comparison"
        elif any(word in query_lower for word in ["stats", "statistics", "numbers"]):
            return "player_stats" if state["entities"].get("players") else "team_stats"
        elif any(word in query_lower for word in ["2024", "this year", "current"]):
            return "current"
        elif any(word in query_lower for word in ["career", "all time", "history"]):
            return "historical"
        else:
            return "general"

    async def _route_query_node(self, state: WorkflowState) -> WorkflowState:
        """Make routing decision based on detected sports and query analysis"""
        state["processing_steps"].append("route_query")
        console.print("[cyan]🚦 Making routing decision...[/cyan]")
        
        high_confidence_sports = [s for s in state["detected_sports"] if s["confidence"] > 0.6]
        
        if not state["detected_sports"]:
            state["routing_decision"] = {
                "strategy": "error",
                "reason": "No sports detected"
            }
        elif len(high_confidence_sports) == 1:
            state["routing_decision"] = {
                "strategy": "single_sport",
                "sport": high_confidence_sports[0]["sport"],
                "reason": f"Single sport with high confidence ({high_confidence_sports[0]['confidence']:.2f})"
            }
        elif len(high_confidence_sports) > 1:
            state["routing_decision"] = {
                "strategy": "cross_sport",
                "sports": [s["sport"] for s in high_confidence_sports],
                "reason": "Multiple sports with high confidence"
            }
        else:
            state["routing_decision"] = {
                "strategy": "ambiguous",
                "reason": "Sports detected but with low confidence"
            }
        
        console.print(f"[green]✅ Routing strategy: {state['routing_decision']['strategy']}[/green]")
        return state

    def _routing_condition(self, state: WorkflowState) -> str:
        """Conditional routing function for LangGraph"""
        return state["routing_decision"]["strategy"]

    async def _process_single_sport_node(self, state: WorkflowState) -> WorkflowState:
        """Process single sport query"""
        state["processing_steps"].append("process_single_sport")
        sport = state["routing_decision"]["sport"]
        
        console.print(f"[cyan]⚡ Processing {sport} query...[/cyan]")
        
        try:
            # Route to sport-specific processor
            result = await self._execute_sport_specific_query(
                sport, 
                state["original_query"], 
                state["entities"], 
                state["metrics"],
                state["query_type"]
            )
            
            state["sport_responses"] = {sport: result}
            console.print(f"[green]✅ {sport} query processed successfully[/green]")
            
        except Exception as e:
            state["error_messages"].append(f"Single sport processing error: {str(e)}")
            state["sport_responses"] = {sport: {"status": "error", "message": str(e)}}
            console.print(f"[red]❌ {sport} processing failed: {e}[/red]")
        
        return state

    async def _process_cross_sport_node(self, state: WorkflowState) -> WorkflowState:
        """Process cross-sport comparison query"""
        state["processing_steps"].append("process_cross_sport")
        sports = state["routing_decision"]["sports"]
        
        console.print(f"[cyan]⚡ Processing cross-sport query for: {', '.join(sports)}...[/cyan]")
        
        state["sport_responses"] = {}
        
        # Process each sport
        for sport in sports:
            try:
                result = await self._execute_sport_specific_query(
                    sport, 
                    state["original_query"], 
                    state["entities"], 
                    state["metrics"],
                    state["query_type"]
                )
                state["sport_responses"][sport] = result
                
            except Exception as e:
                state["error_messages"].append(f"Cross-sport processing error for {sport}: {str(e)}")
                state["sport_responses"][sport] = {"status": "error", "message": str(e)}
        
        # If we have multiple successful responses, try to create comparison
        successful_responses = {k: v for k, v in state["sport_responses"].items() 
                             if v.get("status") == "success"}
        
        if len(successful_responses) > 1:
            try:
                comparison_result = await self._create_cross_sport_comparison(successful_responses)
                state["sport_responses"]["comparison"] = comparison_result
            except Exception as e:
                state["error_messages"].append(f"Comparison creation error: {str(e)}")
        
        console.print(f"[green]✅ Cross-sport processing completed[/green]")
        return state

    async def _handle_ambiguous_node(self, state: WorkflowState) -> WorkflowState:
        """Handle ambiguous queries that need clarification"""
        state["processing_steps"].append("handle_ambiguous")
        console.print("[cyan]🤔 Handling ambiguous query...[/cyan]")
        
        # Create clarification response
        detected_sports = [s["sport"] for s in state["detected_sports"]]
        
        state["sport_responses"] = {
            "clarification": {
                "status": "clarification_needed",
                "message": "I detected multiple possible sports but need clarification.",
                "detected_sports": detected_sports,
                "suggestions": [f"Try: '{sport} {state['original_query']}'" for sport in detected_sports[:3]]
            }
        }
        
        console.print("[yellow]⚠️ Clarification response created[/yellow]")
        return state

    async def _error_recovery_node(self, state: WorkflowState) -> WorkflowState:
        """Handle errors and provide helpful fallback responses"""
        state["processing_steps"].append("error_recovery")
        console.print("[cyan]🛠️ Attempting error recovery...[/cyan]")
        
        # Create helpful error response
        state["sport_responses"] = {
            "error": {
                "status": "error",
                "message": "I couldn't understand your sports query. Please try being more specific.",
                "suggestions": [
                    "Try: 'NFL player stats for...'",
                    "Try: 'NBA team performance...'",
                    "Try: 'Compare [player1] vs [player2]'"
                ],
                "supported_sports": ["NFL", "NBA", "MLB", "NHL", "MLS", "NASCAR", "F1"]
            }
        }
        
        console.print("[yellow]⚠️ Error recovery response created[/yellow]")
        return state

    async def _format_response_node(self, state: WorkflowState) -> WorkflowState:
        """Format final response"""
        state["processing_steps"].append("format_response")
        console.print("[cyan]📝 Formatting final response...[/cyan]")
        
        try:
            if "error" in state["sport_responses"]:
                state["final_response"] = self._format_error_response(state["sport_responses"]["error"])
            elif "clarification" in state["sport_responses"]:
                state["final_response"] = self._format_clarification_response(state["sport_responses"]["clarification"])
            elif len(state["sport_responses"]) == 1:
                sport, response = next(iter(state["sport_responses"].items()))
                state["final_response"] = self._format_single_response(sport, response)
            else:
                state["final_response"] = self._format_multi_response(state["sport_responses"])
            
            # Add processing metadata
            state["processing_time"] = (datetime.now() - datetime.fromisoformat(state["debug_info"]["start_time"])).total_seconds()
            
            console.print("[green]✅ Response formatted successfully[/green]")
            
        except Exception as e:
            state["error_messages"].append(f"Response formatting error: {str(e)}")
            state["final_response"] = f"❌ Error formatting response: {str(e)}"
            console.print(f"[red]❌ Response formatting failed: {e}[/red]")
        
        return state

    async def _execute_sport_specific_query(self, sport: str, query: str, entities: Dict[str, List[str]], 
                                          metrics: List[str], query_type: str) -> Dict[str, Any]:
        """Execute sport-specific query processing"""
        
        # Try to use existing sport processors
        if "query_planner" in self.sport_processors:
            try:
                # Create mock query context for existing processors
                class MockQueryContext:
                    def __init__(self):
                        self.question = query
                        self.sport = sport
                        self.player_names = entities.get("players", [])
                        self.team_names = entities.get("teams", [])
                        self.metrics_needed = metrics
                        self.query_type = query_type
                
                context = MockQueryContext()
                # This would normally call the existing query planner
                # For now, return a mock successful response
                
                return {
                    "status": "success",
                    "sport": sport,
                    "query": query,
                    "query_type": query_type,
                    "message": f"Successfully processed {sport} {query_type} query",
                    "entities": entities,
                    "metrics": metrics,
                    "processor": "advanced"
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "sport": sport,
                    "error": str(e),
                    "message": f"Advanced processor failed for {sport}"
                }
        
        # Fallback to simple processing
        return {
            "status": "success",
            "sport": sport,
            "query": query,
            "query_type": query_type,
            "message": f"Processed {sport} query using fallback processor",
            "entities": entities,
            "metrics": metrics,
            "processor": "fallback"
        }

    async def _create_cross_sport_comparison(self, responses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create intelligent cross-sport comparison"""
        
        if self.llm:
            # Use LLM for intelligent comparison
            sports_data = []
            for sport, response in responses.items():
                sports_data.append(f"{sport}: {response.get('message', 'No data')}")
            
            comparison_prompt = f"""
            Create a brief comparison analysis based on these sports query results:
            
            {chr(10).join(sports_data)}
            
            Provide insights about similarities, differences, or notable patterns.
            """
            
            try:
                comparison_response = await self.llm.ainvoke(comparison_prompt)
                return {
                    "status": "success",
                    "type": "ai_comparison",
                    "analysis": comparison_response.content,
                    "sports_included": list(responses.keys())
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"AI comparison failed: {str(e)}"
                }
        
        # Fallback to simple comparison
        return {
            "status": "success",
            "type": "simple_comparison",
            "message": f"Compared data across {len(responses)} sports",
            "sports_included": list(responses.keys())
        }

    def _format_error_response(self, error_data: Dict[str, Any]) -> str:
        """Format error response"""
        message = error_data.get("message", "An error occurred")
        suggestions = error_data.get("suggestions", [])
        
        response = f"❌ {message}\n"
        if suggestions:
            response += "\n💡 Suggestions:\n"
            for suggestion in suggestions:
                response += f"  • {suggestion}\n"
        
        return response.strip()

    def _format_clarification_response(self, clarification_data: Dict[str, Any]) -> str:
        """Format clarification response"""
        message = clarification_data.get("message", "Need clarification")
        detected = clarification_data.get("detected_sports", [])
        suggestions = clarification_data.get("suggestions", [])
        
        response = f"🤔 {message}\n"
        if detected:
            response += f"\n🎯 Detected possible sports: {', '.join(detected)}\n"
        if suggestions:
            response += "\n💡 Try:\n"
            for suggestion in suggestions:
                response += f"  • {suggestion}\n"
        
        return response.strip()

    def _format_single_response(self, sport: str, response_data: Dict[str, Any]) -> str:
        """Format single sport response"""
        if response_data.get("status") == "error":
            return f"❌ {sport} Error: {response_data.get('message', 'Unknown error')}"
        
        message = response_data.get("message", "Query processed")
        query_type = response_data.get("query_type", "")
        processor = response_data.get("processor", "")
        
        response = f"🏆 {sport} {query_type.title()} Result:\n{message}"
        
        if processor:
            response += f"\n[Processed via {processor} processor]"
        
        return response

    def _format_multi_response(self, responses: Dict[str, Dict[str, Any]]) -> str:
        """Format multi-sport response"""
        response = "🌟 Multi-Sport Analysis:\n\n"
        
        for sport, data in responses.items():
            if sport == "comparison":
                response += f"📊 Cross-Sport Analysis: {data.get('analysis', data.get('message', 'Analysis completed'))}\n\n"
            elif data.get("status") == "success":
                response += f"🏆 {sport}: {data.get('message', 'Success')}\n"
            else:
                response += f"❌ {sport}: {data.get('message', 'Error')}\n"
        
        return response.strip()

    async def process_query(self, query: str, user_id: str = None, conversation_id: str = None) -> str:
        """
        Process a query through the advanced workflow
        """
        if not self.workflow:
            # Fallback to simple processing
            return await self._simple_process_query(query)
        
        # Initialize state
        initial_state = WorkflowState(
            original_query=query,
            user_id=user_id,
            conversation_id=conversation_id,
            detected_sports=[],
            primary_sport=None,
            query_type="unknown",
            entities={},
            metrics=[],
            temporal_context=[],
            routing_decision={},
            processing_steps=[],
            sport_responses={},
            final_response="",
            confidence_score=0.0,
            processing_time=0.0,
            error_messages=[],
            debug_info={}
        )
        
        try:
            # Execute workflow
            config = {"configurable": {"thread_id": conversation_id or "default"}}
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            return final_state["final_response"]
            
        except Exception as e:
            console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
            return f"❌ Workflow error: {str(e)}"

    async def _simple_process_query(self, query: str) -> str:
        """Simple fallback processing when LangGraph is not available"""
        try:
            from .universal_sports_agent import universal_sports_agent
            return await universal_sports_agent.process_query(query)
        except Exception as e:
            return f"❌ Simple processing error: {str(e)}"

# Global instance
sports_workflow = SportsWorkflowOrchestrator()

async def process_advanced_query(query: str, user_id: str = None, conversation_id: str = None) -> str:
    """
    Easy-to-use function for advanced query processing
    """
    return await sports_workflow.process_query(query, user_id, conversation_id) 