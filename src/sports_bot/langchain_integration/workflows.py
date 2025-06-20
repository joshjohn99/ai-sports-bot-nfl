"""
LangGraph Workflows for Sports Bot - Multi-Agent Orchestration

This module implements the LangGraph workflows recommended in the architectural review
for complex sports analysis tasks like league leaders, player rankings, and debates.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import asyncio

from sports_bot.langchain_integration.tools import (
    SPORTS_TOOLS, 
    SportContext,
    FetchPlayerStatsTool,
    FetchTeamListingTool,
    FuzzyPlayerSearchTool
)


class WorkflowState(TypedDict):
    """
    Shared state for LangGraph workflows.
    
    This implements the "shared state mechanism" mentioned in the architectural review,
    allowing agents to collaborate dynamically and track context across the workflow.
    """
    messages: List[Dict[str, Any]]
    sport: str
    season: Optional[str]
    query_type: str
    player_names: List[str]
    team_names: List[str]
    metrics: List[str]
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any]
    results: Dict[str, Any]
    errors: List[str]
    step_count: int
    max_steps: int


class LeagueLeadersWorkflow:
    """
    LangGraph workflow for League Leaders queries.
    
    This implements the comprehensive workflow described in the architectural review:
    1. Initial Node: Extract desired statistic
    2. Team Fetch Node: Get all teams
    3. Player Roster Fetch Node: Get rosters (parallel)
    4. Player Stats Fetch Node: Get stats (parallel)
    5. Aggregation Node: Filter, aggregate, and sort
    6. Response Formatting Node: Format results
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.tools = SPORTS_TOOLS
        self.tool_node = ToolNode(self.tools)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for league leaders"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("extract_query", self._extract_query_details)
        workflow.add_node("fetch_teams", self._fetch_teams)
        workflow.add_node("fetch_player_data", self._fetch_player_data)
        workflow.add_node("aggregate_stats", self._aggregate_stats)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("tools", self.tool_node)
        
        # Define the flow
        workflow.set_entry_point("extract_query")
        workflow.add_edge("extract_query", "fetch_teams")
        workflow.add_edge("fetch_teams", "fetch_player_data")
        workflow.add_edge("fetch_player_data", "aggregate_stats")
        workflow.add_edge("aggregate_stats", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def _extract_query_details(self, state: WorkflowState) -> WorkflowState:
        """
        Initial Node: Extract the desired statistic and query details
        """
        messages = [
            SystemMessage(content="""
            You are analyzing a sports query to extract key details for league leaders analysis.
            
            Extract:
            1. The main statistic being requested (e.g., "sacks", "touchdowns", "passing yards")
            2. Any position filters (e.g., "quarterbacks", "defensive ends")
            3. Season/time filters
            4. The sport being queried
            
            Respond with a JSON object containing these details.
            """),
            HumanMessage(content=f"Query: {state.get('messages', [])[-1].get('content', '')}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse the LLM response (simplified for now)
        # In a full implementation, you'd use structured output parsing
        state["step_count"] = state.get("step_count", 0) + 1
        state["processed_data"]["query_analysis"] = response.content
        
        return state
    
    async def _fetch_teams(self, state: WorkflowState) -> WorkflowState:
        """
        Team Fetch Node: Get all teams for the sport
        """
        sport_context = SportContext(sport=state["sport"], season=state.get("season"))
        
        # Use the LangChain tool
        team_tool = FetchTeamListingTool()
        teams_result = team_tool._run(sport_context)
        
        if teams_result["success"]:
            state["raw_data"]["teams"] = teams_result["teams"]
        else:
            state["errors"].append(f"Failed to fetch teams: {teams_result.get('error')}")
        
        state["step_count"] += 1
        return state
    
    async def _fetch_player_data(self, state: WorkflowState) -> WorkflowState:
        """
        Player Data Fetch Node: Get player statistics (parallel processing)
        
        This would ideally use parallel processing for multiple players,
        but simplified here for demonstration.
        """
        teams = state["raw_data"].get("teams", [])
        sport_context = SportContext(sport=state["sport"], season=state.get("season"))
        
        player_stats = []
        stats_tool = FetchPlayerStatsTool()
        
        # In a real implementation, this would be parallelized
        # and would fetch rosters first, then individual player stats
        for team in teams[:3]:  # Limit for demo
            # This is simplified - normally you'd fetch team rosters first
            team_name = team.get("name", "")
            if team_name:
                # Mock player data for demonstration
                mock_players = [f"{team_name} Player 1", f"{team_name} Player 2"]
                
                for player_name in mock_players:
                    try:
                        result = stats_tool._run(
                            player_name=player_name,
                            sport_context=sport_context,
                            metrics=state.get("metrics", [])
                        )
                        if result["success"]:
                            player_stats.append(result)
                    except Exception as e:
                        state["errors"].append(f"Error fetching {player_name}: {str(e)}")
        
        state["raw_data"]["player_stats"] = player_stats
        state["step_count"] += 1
        return state
    
    async def _aggregate_stats(self, state: WorkflowState) -> WorkflowState:
        """
        Aggregation Node: Filter, aggregate, and sort player statistics
        
        This is where your existing custom aggregation logic would be integrated.
        """
        player_stats = state["raw_data"].get("player_stats", [])
        metrics = state.get("metrics", [])
        
        # Simplified aggregation logic
        # In reality, this would use your existing StatRetrieverApiAgent logic
        aggregated_results = []
        
        for stat_data in player_stats:
            if stat_data.get("success"):
                # Extract relevant metrics
                player_name = stat_data.get("player_name")
                data = stat_data.get("data", {})
                
                # This would be replaced with your actual stat extraction logic
                aggregated_results.append({
                    "player": player_name,
                    "sport": state["sport"],
                    "metrics": data  # Simplified
                })
        
        # Sort by the primary metric (simplified)
        # Your existing logic would handle complex sorting
        state["processed_data"]["aggregated_stats"] = aggregated_results
        state["step_count"] += 1
        return state
    
    async def _format_response(self, state: WorkflowState) -> WorkflowState:
        """
        Response Formatting Node: Format results for user presentation
        """
        aggregated_stats = state["processed_data"].get("aggregated_stats", [])
        
        # Use LLM to format the response
        format_prompt = f"""
        Format these league leader statistics into a user-friendly response:
        
        Sport: {state['sport']}
        Query Type: League Leaders
        Data: {aggregated_stats}
        
        Create a clear, engaging summary of the top performers.
        """
        
        messages = [
            SystemMessage(content="You are a sports analyst creating engaging summaries of statistical data."),
            HumanMessage(content=format_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["results"]["formatted_response"] = response.content
        state["results"]["raw_stats"] = aggregated_stats
        state["step_count"] += 1
        
        return state
    
    async def execute(self, query: str, sport: str, season: str = None) -> Dict[str, Any]:
        """
        Execute the league leaders workflow
        """
        initial_state = WorkflowState(
            messages=[{"role": "user", "content": query}],
            sport=sport,
            season=season,
            query_type="league_leaders",
            player_names=[],
            team_names=[],
            metrics=[],
            raw_data={},
            processed_data={},
            results={},
            errors=[],
            step_count=0,
            max_steps=10
        )
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state


class DebateWorkflow:
    """
    LangGraph workflow for Player Debate/Comparison.
    
    This implements the multi-agent debate engine described in the architectural review,
    with specialized agents for different perspectives.
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)  # Higher temp for creativity
        self.tools = SPORTS_TOOLS
        self.workflow = self._build_debate_workflow()
    
    def _build_debate_workflow(self) -> StateGraph:
        """Build the debate workflow with specialized agents"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add specialized agent nodes
        workflow.add_node("prepare_debate", self._prepare_debate)
        workflow.add_node("advocate_agent", self._advocate_agent)
        workflow.add_node("critic_agent", self._critic_agent)
        workflow.add_node("moderator_agent", self._moderator_agent)
        workflow.add_node("evidence_collector", self._evidence_collector)
        
        # Define the debate flow
        workflow.set_entry_point("prepare_debate")
        workflow.add_edge("prepare_debate", "evidence_collector")
        workflow.add_edge("evidence_collector", "advocate_agent")
        workflow.add_edge("advocate_agent", "critic_agent")
        workflow.add_edge("critic_agent", "moderator_agent")
        workflow.add_edge("moderator_agent", END)
        
        return workflow.compile()
    
    async def _prepare_debate(self, state: WorkflowState) -> WorkflowState:
        """Prepare the debate by identifying players and context"""
        
        query = state["messages"][-1]["content"]
        
        # Extract players to compare using LLM
        extraction_prompt = f"""
        Extract the players being compared in this query: "{query}"
        
        Respond with a JSON object containing:
        - player1: first player name
        - player2: second player name
        - comparison_aspect: what aspect is being compared
        - sport: which sport
        """
        
        messages = [
            SystemMessage(content="You extract player comparison details from sports queries."),
            HumanMessage(content=extraction_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse response (simplified)
        state["processed_data"]["debate_setup"] = response.content
        state["step_count"] = state.get("step_count", 0) + 1
        
        return state
    
    async def _evidence_collector(self, state: WorkflowState) -> WorkflowState:
        """Collect statistical evidence for both players"""
        
        # This would use the FetchPlayerStatsTool for both players
        player_names = state.get("player_names", [])
        sport_context = SportContext(sport=state["sport"], season=state.get("season"))
        
        stats_tool = FetchPlayerStatsTool()
        evidence = {}
        
        for player in player_names:
            try:
                result = stats_tool._run(
                    player_name=player,
                    sport_context=sport_context,
                    metrics=state.get("metrics", [])
                )
                evidence[player] = result
            except Exception as e:
                state["errors"].append(f"Failed to get stats for {player}: {str(e)}")
        
        state["raw_data"]["evidence"] = evidence
        state["step_count"] += 1
        
        return state
    
    async def _advocate_agent(self, state: WorkflowState) -> WorkflowState:
        """
        Advocate Agent: Present the strongest case for player comparison
        
        This implements the "bull agent" pattern from the architectural review.
        """
        evidence = state["raw_data"].get("evidence", {})
        
        advocate_prompt = f"""
        You are an advocate presenting the strongest statistical case for player comparison.
        
        Evidence: {evidence}
        
        Present compelling arguments highlighting the strengths and achievements of each player.
        Use specific statistics and context to build your case.
        """
        
        messages = [
            SystemMessage(content="You are a passionate sports advocate who builds compelling cases using statistics."),
            HumanMessage(content=advocate_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["processed_data"]["advocate_argument"] = response.content
        state["step_count"] += 1
        
        return state
    
    async def _critic_agent(self, state: WorkflowState) -> WorkflowState:
        """
        Critic Agent: Present counterarguments and analysis
        
        This implements the "bear agent" pattern from the architectural review.
        """
        advocate_argument = state["processed_data"].get("advocate_argument", "")
        evidence = state["raw_data"].get("evidence", {})
        
        critic_prompt = f"""
        You are a critical analyst reviewing this player comparison argument:
        
        Original Argument: {advocate_argument}
        Evidence: {evidence}
        
        Provide critical analysis, counterarguments, and point out any weaknesses or missing context.
        Highlight areas where one player might have advantages over another.
        """
        
        messages = [
            SystemMessage(content="You are a critical sports analyst who provides balanced, skeptical analysis."),
            HumanMessage(content=critic_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["processed_data"]["critic_analysis"] = response.content
        state["step_count"] += 1
        
        return state
    
    async def _moderator_agent(self, state: WorkflowState) -> WorkflowState:
        """
        Moderator Agent: Synthesize arguments and provide balanced conclusion
        
        This implements the "chairman agent" pattern from the architectural review.
        """
        advocate_arg = state["processed_data"].get("advocate_argument", "")
        critic_analysis = state["processed_data"].get("critic_analysis", "")
        evidence = state["raw_data"].get("evidence", {})
        
        moderator_prompt = f"""
        You are a neutral moderator synthesizing this player comparison debate:
        
        Advocate Position: {advocate_arg}
        Critical Analysis: {critic_analysis}
        Statistical Evidence: {evidence}
        
        Provide a balanced, nuanced conclusion that acknowledges both perspectives
        and gives a fair assessment based on the available evidence.
        """
        
        messages = [
            SystemMessage(content="You are a balanced sports moderator who synthesizes different perspectives fairly."),
            HumanMessage(content=moderator_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["results"]["final_debate"] = {
            "advocate_position": advocate_arg,
            "critical_analysis": critic_analysis,
            "moderator_conclusion": response.content,
            "evidence_used": evidence
        }
        
        state["step_count"] += 1
        
        return state
    
    async def execute(self, query: str, sport: str, player_names: List[str]) -> Dict[str, Any]:
        """Execute the debate workflow"""
        
        initial_state = WorkflowState(
            messages=[{"role": "user", "content": query}],
            sport=sport,
            season=None,
            query_type="player_debate",
            player_names=player_names,
            team_names=[],
            metrics=[],
            raw_data={},
            processed_data={},
            results={},
            errors=[],
            step_count=0,
            max_steps=10
        )
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state


class WorkflowOrchestrator:
    """
    Main orchestrator for selecting and executing appropriate workflows.
    
    This provides the entry point for the hybrid LangChain/LangGraph system.
    """
    
    def __init__(self):
        self.league_leaders_workflow = LeagueLeadersWorkflow()
        self.debate_workflow = DebateWorkflow()
    
    async def execute_query(self, query: str, query_type: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the appropriate workflow based on query type
        """
        
        if query_type == "league_leaders":
            return await self.league_leaders_workflow.execute(
                query=query,
                sport=kwargs.get("sport", "NFL"),
                season=kwargs.get("season")
            )
        
        elif query_type == "player_debate" or query_type == "player_comparison":
            return await self.debate_workflow.execute(
                query=query,
                sport=kwargs.get("sport", "NFL"),
                player_names=kwargs.get("player_names", [])
            )
        
        else:
            return {
                "error": f"Unsupported query type: {query_type}",
                "supported_types": ["league_leaders", "player_debate", "player_comparison"]
            }
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow types"""
        return ["league_leaders", "player_debate", "player_comparison"] 