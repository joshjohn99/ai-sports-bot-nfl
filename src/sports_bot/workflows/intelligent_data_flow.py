"""
🧠 Intelligent Data Flow Workflow
LangGraph-powered backend that automatically handles all data retrieval scenarios
Eliminates edge cases and provides robust, self-managing data gathering
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import logging
from dataclasses import dataclass, field

# Your existing imports
from ..stats.universal_stat_retriever import UniversalStatRetriever
from ..cache.shared_cache import get_cache_instance
from ..config.api_config import api_config

logger = logging.getLogger(__name__)

class DataFlowState(TypedDict):
    """State for the intelligent data flow workflow"""
    # Input
    query_context: Dict[str, Any]
    debate_topic: str
    
    # Data Requirements Analysis
    required_data_types: List[str]
    data_sources_needed: List[str]
    priority_order: List[str]
    
    # Data Gathering Progress
    gathered_data: Dict[str, Any]
    missing_data: List[str]
    failed_attempts: Dict[str, List[str]]
    
    # Workflow Control
    current_step: str
    retry_count: int
    max_retries: int
    workflow_complete: bool
    final_result: Optional[Dict[str, Any]]

@dataclass
class DataRequirement:
    """Represents a specific data requirement"""
    data_type: str
    entity_name: str  # player name, team name, etc.
    metrics_needed: List[str]
    priority: int = 1
    source_preference: List[str] = field(default_factory=lambda: ["database", "api", "cache"])

class IntelligentDataFlow:
    """
    LangGraph-powered intelligent data flow manager
    Automatically handles all backend data retrieval scenarios
    """
    
    def __init__(self):
        self.workflow = self._build_workflow()
        self.stat_retriever = UniversalStatRetriever()
        self.cache = get_cache_instance()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for intelligent data retrieval"""
        
        workflow = StateGraph(DataFlowState)
        
        # Add nodes (each represents a step in data gathering)
        workflow.add_node("analyze_requirements", self._analyze_data_requirements)
        workflow.add_node("try_cache", self._try_cache_retrieval)
        workflow.add_node("try_database", self._try_database_retrieval)
        workflow.add_node("try_api", self._try_api_retrieval)
        workflow.add_node("validate_data", self._validate_gathered_data)
        workflow.add_node("enrich_data", self._enrich_data_if_needed)
        workflow.add_node("finalize_result", self._finalize_result)
        
        # Define the flow logic
        workflow.set_entry_point("analyze_requirements")
        
        # FIXED: Add stop conditions to prevent infinite loops
        workflow.add_conditional_edges(
            "analyze_requirements",
            self._route_data_strategy,
            {
                "cache_first": "try_cache",
                "database_first": "try_database", 
                "api_only": "try_api",
                "insufficient_context": "finalize_result"  # Direct to end
            }
        )
        
        # FIXED: Simplified routing with clear stop conditions
        workflow.add_conditional_edges(
            "try_cache", 
            self._check_cache_success,
            {
                "success": "validate_data",
                "partial": "try_database",
                "failed": "try_database"
            }
        )
        
        workflow.add_conditional_edges(
            "try_database", 
            self._check_database_success,
            {
                "success": "validate_data", 
                "partial": "finalize_result",  # Stop here instead of API
                "failed": "try_api"
            }
        )
        
        workflow.add_conditional_edges(
            "try_api",
            self._check_api_success,
            {
                "success": "validate_data",
                "retry": "finalize_result",  # Stop retrying to prevent loops
                "failed": "finalize_result"
            }
        )
        
        # FIXED: Always go to finalize after validation
        workflow.add_edge("validate_data", "finalize_result")
        workflow.add_edge("enrich_data", "finalize_result") 
        workflow.add_edge("finalize_result", END)
        
        # FIXED: Compile with recursion limit
        return workflow.compile(
            checkpointer=MemorySaver(),
            # Set explicit recursion limit
            interrupt_before=[],
            interrupt_after=[]
        )
    
    async def _analyze_data_requirements(self, state: DataFlowState) -> DataFlowState:
        """Intelligently analyze what data is needed for the debate topic"""
        
        query_context = state["query_context"]
        topic = state["debate_topic"]
        
        logger.info(f"🧠 Analyzing data requirements for: {topic}")
        
        # Determine required data types based on query context
        required_types = []
        sources_needed = ["cache", "database", "api"]  # Try in this order
        
        # Player-related requirements
        if query_context.get("player_names"):
            required_types.extend(["player_stats", "player_details"])
            logger.info(f"   🏃 Need player data for: {query_context['player_names']}")
            
        # Team-related requirements  
        if query_context.get("team_names"):
            required_types.extend(["team_stats", "team_roster"])
            logger.info(f"   🏟️ Need team data for: {query_context['team_names']}")
            
        # Comparison requirements
        if query_context.get("comparison_target"):
            required_types.append("comparative_analysis")
            logger.info(f"   ⚖️ Need comparison data for: {query_context['comparison_target']}")
            
        # League-wide requirements
        if query_context.get("strategy") == "leaderboard_query":
            required_types.append("league_leaders")
            logger.info(f"   🏆 Need league leaders data")
        
        # Update state with analysis
        state.update({
            "required_data_types": required_types,
            "data_sources_needed": sources_needed,
            "priority_order": ["cache", "database", "api"],
            "current_step": "requirements_analyzed",
            "gathered_data": {},
            "missing_data": required_types.copy(),
            "failed_attempts": {},
            "retry_count": 0,
            "max_retries": 3
        })
        
        logger.info(f"   ✅ Analysis complete: {len(required_types)} data types identified")
        return state
    
    def _route_data_strategy(self, state: DataFlowState) -> str:
        """Determine the best data gathering strategy"""
        
        if not state["required_data_types"]:
            logger.warning("❌ No data requirements identified")
            return "insufficient_context"
            
        # Always try cache first for speed
        if "cache" in state["data_sources_needed"]:
            logger.info("🔄 Strategy: Cache-first approach")
            return "cache_first"
        elif "database" in state["data_sources_needed"]:
            logger.info("🗄️ Strategy: Database-first approach")
            return "database_first"
        else:
            logger.info("🌐 Strategy: API-only approach")
            return "api_only"
    
    async def _try_cache_retrieval(self, state: DataFlowState) -> DataFlowState:
        """Try to get data from cache first (fastest)"""
        
        query_context = state["query_context"]
        gathered_data = state["gathered_data"]
        
        logger.info("🔍 Attempting cache retrieval...")
        
        try:
            # Check cache for player data - USE CORRECT CACHE METHODS
            if "player_stats" in state["required_data_types"]:
                sport = query_context.get("sport", "NFL")
                for player_name in query_context.get("player_names", []):
                    # Use the correct cache interface
                    cached_player = self.cache.get_player(sport, player_name)
                    if cached_player:
                        # Try to get stats too
                        player_id = cached_player.get("id", cached_player.get("external_id"))
                        if player_id:
                            cached_stats = self.cache.get_stats(
                                sport, 
                                str(player_id), 
                                "2024", 
                                query_context.get("metrics_needed", [])
                            )
                            if cached_stats:
                                gathered_data[f"player_{player_name}"] = cached_stats
                                logger.info(f"   ✅ Cache hit for {player_name}")
                            else:
                                logger.info(f"   ❌ Cache miss for {player_name} stats")
                        else:
                            logger.info(f"   ❌ Cache miss for {player_name} - no player ID")
                    else:
                        logger.info(f"   ❌ Cache miss for {player_name}")
            
            state["gathered_data"] = gathered_data
            state["current_step"] = "cache_attempted"
            
        except Exception as e:
            logger.error(f"❌ Cache retrieval failed: {e}")
            state["failed_attempts"]["cache"] = [str(e)]
        
        return state
    
    def _check_cache_success(self, state: DataFlowState) -> str:
        """Check if cache retrieval was successful"""
        
        gathered_data = state["gathered_data"]
        total_entities = len(state["query_context"].get("player_names", [])) + len(state["query_context"].get("team_names", []))
        
        if len(gathered_data) == total_entities:
            logger.info("✅ Complete cache success!")
            return "success"
        elif len(gathered_data) > 0:
            logger.info(f"⚠️ Partial cache success: {len(gathered_data)}/{total_entities}")
            return "partial"
        else:
            logger.info("❌ Cache failed - trying database")
            return "failed"
    
    async def _try_database_retrieval(self, state: DataFlowState) -> DataFlowState:
        """Try to get data from database"""
        
        query_context = state["query_context"]
        gathered_data = state["gathered_data"]
        
        logger.info("🗄️ Attempting database retrieval...")
        
        try:
            # Get missing player data
            if "player_stats" in state["required_data_types"]:
                for player_name in query_context.get("player_names", []):
                    if f"player_{player_name}" not in gathered_data:
                        
                        # Create mock query context for stat retriever
                        mock_context = type('MockContext', (), {
                            'sport': query_context.get("sport", "NFL"),
                            'player_names': [player_name],
                            'metrics_needed': query_context.get("metrics_needed", []),
                            'season_years': query_context.get("season_years", []),
                            'strategy': query_context.get("strategy", ""),
                        })()
                        
                        player_data = self.stat_retriever.fetch_stats(mock_context)
                        
                        if player_data and "error" not in player_data:
                            gathered_data[f"player_{player_name}"] = player_data
                            logger.info(f"   ✅ Database hit for {player_name}")
                            
                            # Cache for next time
                            sport = query_context.get("sport", "NFL")
                            player_id = player_data.get("player_id", "")
                            if player_id:
                                self.cache.set_stats(
                                    sport, 
                                    player_id, 
                                    "2024", 
                                    query_context.get("metrics_needed", []), 
                                    player_data
                                )
                        else:
                            logger.info(f"   ❌ Database miss for {player_name}")
            
            # Handle league leaders separately
            if "league_leaders" in state["required_data_types"]:
                mock_context = type('MockContext', (), {
                    'sport': query_context.get("sport", "NFL"),
                    'player_names': [],
                    'metrics_needed': query_context.get("metrics_needed", []),
                    'season_years': query_context.get("season_years", []),
                    'strategy': "leaderboard_query",
                })()
                
                leaders_data = self.stat_retriever.fetch_league_leaders(mock_context)
                if leaders_data and "error" not in leaders_data:
                    gathered_data["league_leaders"] = leaders_data
                    logger.info("   ✅ Database hit for league leaders")
            
            state["gathered_data"] = gathered_data
            state["current_step"] = "database_attempted"
            
        except Exception as e:
            logger.error(f"❌ Database retrieval failed: {e}")
            state["failed_attempts"]["database"] = [str(e)]
        
        return state
    
    def _check_database_success(self, state: DataFlowState) -> str:
        """Check if database retrieval was successful"""
        
        gathered_data = state["gathered_data"]
        query_context = state["query_context"]
        
        # Calculate expected entities
        expected_players = len(query_context.get("player_names", []))
        expected_teams = len(query_context.get("team_names", []))
        expected_leaders = 1 if "league_leaders" in state["required_data_types"] else 0
        total_expected = expected_players + expected_teams + expected_leaders
        
        if len(gathered_data) >= total_expected:
            logger.info("✅ Complete database success!")
            return "success"
        elif len(gathered_data) > 0:
            logger.info(f"⚠️ Partial database success: {len(gathered_data)}/{total_expected}")
            return "partial"
        else:
            logger.info("❌ Database failed - trying API")
            return "failed"
    
    async def _try_api_retrieval(self, state: DataFlowState) -> DataFlowState:
        """Try to get missing data from API"""
        
        query_context = state["query_context"]
        gathered_data = state["gathered_data"]
        
        logger.info("🌐 Attempting API retrieval...")
        
        try:
            # This would integrate with your API client
            # For now, we'll simulate API calls
            
            for player_name in query_context.get("player_names", []):
                if f"player_{player_name}" not in gathered_data:
                    # Simulate API call
                    api_data = await self._simulate_api_call(player_name, query_context)
                    if api_data:
                        gathered_data[f"player_{player_name}"] = api_data
                        logger.info(f"   ✅ API hit for {player_name}")
                        
                        # Cache the API result
                        sport = query_context.get("sport", "NFL")
                        player_id = api_data.get("player_id", "")
                        if player_id:
                            self.cache.set_stats(
                                sport, 
                                player_id, 
                                "2024", 
                                query_context.get("metrics_needed", []), 
                                api_data
                            )
                    else:
                        logger.info(f"   ❌ API miss for {player_name}")
            
            state["gathered_data"] = gathered_data
            state["current_step"] = "api_attempted"
            
        except Exception as e:
            logger.error(f"❌ API retrieval failed: {e}")
            state["failed_attempts"]["api"] = state["failed_attempts"].get("api", []) + [str(e)]
            state["retry_count"] = state["retry_count"] + 1
        
        return state
    
    async def _simulate_api_call(self, player_name: str, query_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Simulate an API call (replace with real API integration)"""
        
        # This is where you'd integrate with your actual API client
        # For now, return None to simulate API failure
        # In real implementation, use your api_config and endpoints
        
        return None
    
    def _check_api_success(self, state: DataFlowState) -> str:
        """Check if API retrieval was successful"""
        
        if state["retry_count"] >= state["max_retries"]:
            logger.warning("❌ Max retries reached")
            return "failed"
        
        gathered_data = state["gathered_data"]
        query_context = state["query_context"]
        expected_entities = len(query_context.get("player_names", [])) + len(query_context.get("team_names", []))
        
        if len(gathered_data) >= expected_entities:
            logger.info("✅ API success!")
            return "success"
        elif state["retry_count"] < state["max_retries"]:
            logger.info(f"🔄 Retrying API (attempt {state['retry_count'] + 1})")
            return "retry"
        else:
            logger.warning("❌ API failed after retries")
            return "failed"
    
    async def _validate_gathered_data(self, state: DataFlowState) -> DataFlowState:
        """Validate the quality and completeness of gathered data"""
        
        gathered_data = state["gathered_data"]
        logger.info(f"🔍 Validating {len(gathered_data)} data items...")
        
        # Check data quality
        valid_data = {}
        for key, data in gathered_data.items():
            if self._is_data_valid(data):
                valid_data[key] = data
                logger.info(f"   ✅ Valid: {key}")
            else:
                logger.warning(f"   ❌ Invalid: {key}")
        
        state["gathered_data"] = valid_data
        state["current_step"] = "data_validated"
        
        logger.info(f"✅ Validation complete: {len(valid_data)}/{len(gathered_data)} items valid")
        return state
    
    def _check_data_completeness(self, state: DataFlowState) -> str:
        """Check if we have enough data for the debate"""
        
        gathered_data = state["gathered_data"]
        query_context = state["query_context"]
        
        required_players = len(query_context.get("player_names", []))
        required_teams = len(query_context.get("team_names", []))
        required_total = required_players + required_teams
        
        # Add league leaders requirement
        if "league_leaders" in state["required_data_types"]:
            required_total += 1
        
        gathered_count = len(gathered_data)
        
        if gathered_count >= required_total:
            logger.info("✅ Complete data set!")
            return "complete"
        elif gathered_count >= (required_total * 0.5):  # At least 50%
            logger.info(f"⚠️ Sufficient data: {gathered_count}/{required_total}")
            return "sufficient"
        else:
            logger.warning(f"❌ Insufficient data: {gathered_count}/{required_total}")
            return "needs_more"
    
    async def _enrich_data_if_needed(self, state: DataFlowState) -> DataFlowState:
        """Enrich existing data with additional context if needed"""
        
        gathered_data = state["gathered_data"]
        logger.info("🔧 Enriching data with computed metrics...")
        
        for key, data in gathered_data.items():
            # Add computed metrics, rankings, etc.
            enriched_data = await self._compute_additional_metrics(data, state["query_context"])
            gathered_data[key] = enriched_data
        
        state["gathered_data"] = gathered_data
        state["current_step"] = "data_enriched"
        
        logger.info("✅ Data enrichment complete")
        return state
    
    async def _finalize_result(self, state: DataFlowState) -> DataFlowState:
        """Finalize the data gathering result"""
        
        success_sources = []
        for source in ["cache", "database", "api"]:
            if source not in state["failed_attempts"]:
                success_sources.append(source)
        
        final_result = {
            "status": "complete" if state["gathered_data"] else "failed",
            "data": state["gathered_data"],
            "metadata": {
                "sources_used": success_sources,
                "sources_failed": list(state["failed_attempts"].keys()),
                "retry_count": state["retry_count"],
                "data_types_gathered": list(state["gathered_data"].keys()),
                "workflow_path": state["current_step"]
            },
            "summary": {
                "entities_requested": len(state["query_context"].get("player_names", [])) + len(state["query_context"].get("team_names", [])),
                "entities_gathered": len(state["gathered_data"]),
                "success_rate": len(state["gathered_data"]) / max(1, len(state["query_context"].get("player_names", [])) + len(state["query_context"].get("team_names", [])))
            }
        }
        
        state["final_result"] = final_result
        state["workflow_complete"] = True
        
        logger.info(f"🎯 Workflow complete - Status: {final_result['status']}")
        logger.info(f"   📊 Success rate: {final_result['summary']['success_rate']:.1%}")
        
        return state
    
    def _is_data_valid(self, data: Any) -> bool:
        """Check if data is valid for use"""
        if not data:
            return False
        if isinstance(data, dict) and "error" in data:
            return False
        if isinstance(data, dict) and not data.get("simple_stats") and not data.get("player_stats"):
            return False
        return True
    
    async def _compute_additional_metrics(self, data: Dict[str, Any], query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Add computed metrics to the data"""
        
        # Add comparative rankings, efficiency metrics, etc.
        if isinstance(data, dict) and "simple_stats" in data:
            simple_stats = data["simple_stats"]
            
            # Add computed efficiency metrics
            computed_metrics = {}
            
            # Example: Add yards per game if games played is available
            if "passing_yards" in simple_stats and "games_played" in simple_stats:
                try:
                    yards = float(simple_stats["passing_yards"])
                    games = float(simple_stats["games_played"])
                    if games > 0:
                        computed_metrics["passing_yards_per_game"] = round(yards / games, 1)
                except (ValueError, TypeError):
                    pass
            
            if computed_metrics:
                data["computed_metrics"] = computed_metrics
        
        return data
    
    async def gather_debate_data(self, query_context: Dict[str, Any], debate_topic: str) -> Dict[str, Any]:
        """
        Main entry point - intelligently gather all data needed for a debate
        """
        
        logger.info(f"🚀 Starting intelligent data flow for: {debate_topic}")
        
        initial_state = DataFlowState(
            query_context=query_context,
            debate_topic=debate_topic,
            required_data_types=[],
            data_sources_needed=[],
            priority_order=[],
            gathered_data={},
            missing_data=[],
            failed_attempts={},
            current_step="starting",
            retry_count=0,
            max_retries=2,  # REDUCED to prevent loops
            workflow_complete=False,
            final_result=None
        )
        
        # Run the workflow with recursion limit
        config = {
            "configurable": {"thread_id": f"debate_{hash(debate_topic)}"},
            "recursion_limit": 10  # EXPLICIT LIMIT
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state, config)
            return result["final_result"]
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            # Return fallback result
            return {
                "status": "failed",
                "data": initial_state["gathered_data"],
                "error": str(e),
                "metadata": {"workflow_error": True}
            }

class LangGraphDataConnector:
    """Connects the LangGraph data flow to your debate system"""
    
    def __init__(self):
        self.data_flow = IntelligentDataFlow()
    
    async def prepare_debate_data(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare all data needed for a debate topic"""
        
        print(f"🧠 **LangGraph Data Flow**: Analyzing '{topic}'")
        print(f"📝 **Context**: {context.get('player_names', [])} players, {context.get('sport', 'Unknown')} sport")
        
        # Let the intelligent workflow handle everything
        result = await self.data_flow.gather_debate_data(context, topic)
        
        if result["status"] == "complete":
            print(f"✅ **Data Ready**: {len(result['data'])} data sources gathered")
            print(f"📊 **Success Rate**: {result['summary']['success_rate']:.1%}")
            print(f"🔄 **Sources Used**: {', '.join(result['metadata']['sources_used'])}")
        else:
            print(f"⚠️ **Partial Data**: Some data sources failed")
            print(f"❌ **Failed Sources**: {', '.join(result['metadata']['sources_failed'])}")
        
        return result
