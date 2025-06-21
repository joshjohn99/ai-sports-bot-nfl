"""
Response Formatter Module
Handles formatting of query results into user-friendly responses.
Enhanced with LangChain for better formatting and output parsing.
"""

from typing import Dict, Any, List
from ..query.query_types import QueryType
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
import json
import re

class FormattedResponse(BaseModel):
    """Structured response model for LangChain output parsing"""
    main_content: str = Field(description="Main response content with stats and analysis")
    key_insights: List[str] = Field(description="List of key insights from the data")
    visual_elements: List[str] = Field(description="Emoji and visual formatting elements")
    conclusion: str = Field(description="Final conclusion or summary")
    confidence_score: float = Field(description="Confidence in the response accuracy (0-1)")
    
class LangChainResponseFormatter:
    """Enhanced response formatter using LangChain"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        self.response_parser = PydanticOutputParser(pydantic_object=FormattedResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.response_parser, llm=self.llm)
        self._setup_formatting_chains()
    
    def _setup_formatting_chains(self):
        """Setup specialized formatting chains for different query types"""
        
        # Player comparison chain
        self.comparison_template = """Format this player comparison into an engaging sports response:

Query Type: {query_type}
Players: {players}
Comparison Data: {comparison_data}

Create a response that:
1. Builds excitement around the matchup
2. Presents stats in an engaging way with proper context
3. Uses sports terminology and emojis appropriately
4. Provides clear insights about each player's strengths
5. Gives a fair conclusion about the comparison

{format_instructions}

Formatted Response:"""
        
        self.comparison_prompt = PromptTemplate(
            template=self.comparison_template,
            input_variables=["query_type", "players", "comparison_data"],
            partial_variables={"format_instructions": self.response_parser.get_format_instructions()}
        )
        
        self.comparison_chain = LLMChain(
            llm=self.llm,
            prompt=self.comparison_prompt,
            output_parser=self.fixing_parser
        )
        
        # League leaders chain
        self.leaders_template = """Format this league leaders response into an exciting sports narrative:

Query Type: {query_type}
Stat Category: {stat_category}
Leaders Data: {leaders_data}

Create a response that:
1. Celebrates the achievement of leading the league
2. Provides context about the statistic's importance
3. Uses engaging language with proper sports terminology
4. Ranks players with appropriate emojis (🥇🥈🥉)
5. Adds insights about what these numbers mean

{format_instructions}

Formatted Response:"""
        
        self.leaders_prompt = PromptTemplate(
            template=self.leaders_template,
            input_variables=["query_type", "stat_category", "leaders_data"],
            partial_variables={"format_instructions": self.response_parser.get_format_instructions()}
        )
        
        self.leaders_chain = LLMChain(
            llm=self.llm,
            prompt=self.leaders_prompt,
            output_parser=self.fixing_parser
        )
        
        # Single player stats chain
        self.single_player_template = """Format this single player stat response into an informative sports summary:

Query Type: {query_type}
Player: {player}
Stats Data: {stats_data}

Create a response that:
1. Highlights the player's performance
2. Provides context for the statistics
3. Uses engaging language appropriate for sports fans
4. Includes relevant emojis and formatting
5. Gives meaningful insights about the numbers

{format_instructions}

Formatted Response:"""
        
        self.single_player_prompt = PromptTemplate(
            template=self.single_player_template,
            input_variables=["query_type", "player", "stats_data"],
            partial_variables={"format_instructions": self.response_parser.get_format_instructions()}
        )
        
        self.single_player_chain = LLMChain(
            llm=self.llm,
            prompt=self.single_player_prompt,
            output_parser=self.fixing_parser
        )
    
    async def format_response_enhanced(self, query_results: Dict[str, Any]) -> str:
        """Enhanced formatting using LangChain chains"""
        query_type = query_results.get("query_type")
        
        try:
            if query_type == QueryType.PLAYER_COMPARISON.value or query_type == QueryType.MULTI_PLAYER_COMPARISON.value:
                return await self._format_comparison_enhanced(query_results)
            elif query_type == QueryType.LEAGUE_LEADERS.value:
                return await self._format_leaders_enhanced(query_results)
            elif query_type == QueryType.SINGLE_PLAYER_STAT.value:
                return await self._format_single_player_enhanced(query_results)
            else:
                # Fallback to original formatting
                return ResponseFormatter.format_response(query_results)
                
        except Exception as e:
            print(f"Enhanced formatting failed: {e}, using fallback")
            return ResponseFormatter.format_response(query_results)
    
    async def _format_comparison_enhanced(self, results: Dict[str, Any]) -> str:
        """Enhanced player comparison formatting"""
        players = results.get("players", [])
        comparison = results.get("comparison", {})
        
        try:
            result = await self.comparison_chain.ainvoke({
                "query_type": "Player Comparison",
                "players": ", ".join(players),
                "comparison_data": json.dumps(comparison, indent=2)
            })
            
            formatted_resp = result
            if isinstance(formatted_resp, dict):
                return self._build_response_from_structured(formatted_resp)
            else:
                return str(formatted_resp)
                
        except Exception as e:
            print(f"Comparison chain error: {e}")
            return ResponseFormatter._format_player_comparison(results)
    
    async def _format_leaders_enhanced(self, results: Dict[str, Any]) -> str:
        """Enhanced league leaders formatting"""
        ranked_stat = results.get("ranked_stat", "Unknown Stat")
        leaders = results.get("leaders", [])
        
        try:
            result = await self.leaders_chain.ainvoke({
                "query_type": "League Leaders",
                "stat_category": ranked_stat,
                "leaders_data": json.dumps(leaders, indent=2)
            })
            
            formatted_resp = result
            if isinstance(formatted_resp, dict):
                return self._build_response_from_structured(formatted_resp)
            else:
                return str(formatted_resp)
                
        except Exception as e:
            print(f"Leaders chain error: {e}")
            return ResponseFormatter._format_league_leaders(results)
    
    async def _format_single_player_enhanced(self, results: Dict[str, Any]) -> str:
        """Enhanced single player stats formatting"""
        player = results.get("player")
        stats = results.get("stats", {})
        
        try:
            result = await self.single_player_chain.ainvoke({
                "query_type": "Single Player Stats",
                "player": player,
                "stats_data": json.dumps(stats, indent=2)
            })
            
            formatted_resp = result
            if isinstance(formatted_resp, dict):
                return self._build_response_from_structured(formatted_resp)
            else:
                return str(formatted_resp)
                
        except Exception as e:
            print(f"Single player chain error: {e}")
            return ResponseFormatter._format_single_player_stat(results)
    
    def _build_response_from_structured(self, formatted_resp: Dict[str, Any]) -> str:
        """Build final response from structured FormattedResponse"""
        parts = []
        
        # Main content
        main_content = formatted_resp.get("main_content", "")
        if main_content:
            parts.append(main_content)
        
        # Key insights
        insights = formatted_resp.get("key_insights", [])
        if insights:
            parts.append("\n🎯 **Key Insights:**")
            for insight in insights:
                parts.append(f"• {insight}")
        
        # Conclusion
        conclusion = formatted_resp.get("conclusion", "")
        if conclusion:
            parts.append(f"\n🏆 **Bottom Line:** {conclusion}")
        
        # Confidence indicator
        confidence = formatted_resp.get("confidence_score", 0.0)
        if confidence > 0.8:
            parts.append("\n✅ *High confidence analysis*")
        elif confidence > 0.6:
            parts.append("\n🔍 *Moderate confidence analysis*")
        
        return "\n".join(parts)

class ResponseFormatter:
    """Formats query results into user-friendly responses."""
    
    @staticmethod
    def format_response(query_results: Dict[str, Any]) -> str:
        """Format query results based on query type."""
        query_type = query_results.get("query_type")
        
        if query_type == QueryType.SINGLE_PLAYER_STAT.value:
            return ResponseFormatter._format_single_player_stat(query_results)
        elif query_type == QueryType.PLAYER_COMPARISON.value:
            return ResponseFormatter._format_player_comparison(query_results)
        elif query_type == QueryType.MULTI_PLAYER_COMPARISON.value:
            return ResponseFormatter._format_multi_player_comparison(query_results)
        elif query_type == QueryType.TEAM_COMPARISON.value:
            return ResponseFormatter._format_team_comparison(query_results)
        elif query_type == QueryType.MULTI_TEAM_COMPARISON.value:
            return ResponseFormatter._format_multi_team_comparison(query_results)
        elif query_type == QueryType.SEASON_COMPARISON.value:
            return ResponseFormatter._format_season_comparison(query_results)
        elif query_type == QueryType.MULTI_SEASON_COMPARISON.value:
            return ResponseFormatter._format_multi_season_comparison(query_results)
        elif query_type == QueryType.LEAGUE_LEADERS.value:
            return ResponseFormatter._format_league_leaders(query_results)
        elif query_type == QueryType.MULTI_STAT_PLAYER.value:
            return ResponseFormatter._format_multi_stat_player(query_results)
        elif query_type == QueryType.GAME_SPECIFIC_STATS.value:
            return ResponseFormatter._format_game_specific_stats(query_results)
        elif query_type == QueryType.CONTEXTUAL_PERFORMANCE.value:
            return ResponseFormatter._format_contextual_performance(query_results)
        elif query_type == QueryType.GAME_PERFORMANCE_COMPARISON.value:
            return ResponseFormatter._format_game_performance_comparison(query_results)
        else:
            return ResponseFormatter._format_generic_response(query_results)
    
    @staticmethod
    def _format_single_player_stat(results: Dict[str, Any]) -> str:
        """Format single player stat response."""
        
        # Check if we have a pre-calculated response
        if "calculated_response" in results:
            return results["calculated_response"]
        
        player = results.get("player")
        stats = results.get("stats", {})
        
        if isinstance(stats, dict) and "error" in stats:
            return f"❌ Sorry, I couldn't get stats for {player}: {stats['error']}"
        
        if not isinstance(stats, dict) or "simple_stats" not in stats:
            return f"❌ No valid stats found for {player}"
        
        simple_stats = stats["simple_stats"]
        
        # Build response
        response_parts = [f"📊 **{player}** stats:"]
        
        for metric, value in simple_stats.items():
            if value != "Not found" and value != "Error during extraction" and value != 0:
                # Get display info if available
                if metric in stats and isinstance(stats[metric], dict):
                    display_value = stats[metric].get('displayValue', str(value))
                    display_name = stats[metric].get('displayName', metric)
                    rank = stats[metric].get('rank')
                    
                    stat_line = f"• **{display_name}**: {display_value}"
                    if rank:
                        stat_line += f" (Ranked #{rank} in NFL)"
                    response_parts.append(stat_line)
                else:
                    response_parts.append(f"• **{metric}**: {value}")
        
        if len(response_parts) == 1:
            return f"❌ No valid stats found for {player}"
        
        response_parts.append("")
        response_parts.append("🚀 *Powered by Enhanced Query Engine*")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_player_comparison(results: Dict[str, Any]) -> str:
        """Format player comparison response."""
        players = results.get("players", [])
        comparison = results.get("comparison", {})
        individual_stats = results.get("individual_stats", {})
        
        if not players or len(players) < 2:
            return "❌ Need at least 2 players for comparison"
        
        response_parts = [f"⚔️ **{' vs '.join(players)}** Comparison:"]
        response_parts.append("")
        
        winner_by_metric = comparison.get("winner_by_metric", {})
        
        for metric, metric_data in winner_by_metric.items():
            winner = metric_data.get("winner")
            all_values = metric_data.get("all_values", {})
            
            response_parts.append(f"**{metric.upper()}:**")
            for player in players:
                value = all_values.get(player, "N/A")
                if player == winner:
                    response_parts.append(f"• 🏆 **{player}**: {value}")
                else:
                    response_parts.append(f"• {player}: {value}")
            response_parts.append("")
        
        # Add summary
        winners = [data.get("winner") for data in winner_by_metric.values()]
        if winners:
            winner_counts = {player: winners.count(player) for player in set(winners)}
            overall_winner = max(winner_counts, key=winner_counts.get)
            response_parts.append(f"🎯 **Overall Leader**: {overall_winner} ({winner_counts[overall_winner]} categories)")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_multi_player_comparison(results: Dict[str, Any]) -> str:
        """Format multi-player comparison response (3+ players)."""
        players = results.get("players", [])
        comparison = results.get("comparison", {})
        errors = results.get("errors")
        
        if not players or len(players) < 3:
            return "❌ Need at least 3 players for multi-player comparison"
        
        response_parts = [f"🏆 **{len(players)}-Way Player Comparison**: {' vs '.join(players)}"]
        response_parts.append("=" * 60)
        
        # Show errors if any players failed
        if errors:
            response_parts.append(f"⚠️ **Note**: Could not fetch data for: {', '.join(errors.keys())}")
            response_parts.append("")
        
        winner_by_metric = comparison.get("winner_by_metric", {})
        rankings_by_metric = comparison.get("rankings_by_metric", {})
        
        # Show detailed rankings for each metric
        for metric, rankings in rankings_by_metric.items():
            response_parts.append(f"**{metric.upper()} RANKINGS:**")
            for ranking in rankings:
                rank = ranking["rank"]
                player = ranking["player"]
                value = ranking["value"]
                
                if rank == 1:
                    response_parts.append(f"🥇 **{rank}. {player}**: {value}")
                elif rank == 2:
                    response_parts.append(f"🥈 **{rank}. {player}**: {value}")
                elif rank == 3:
                    response_parts.append(f"🥉 **{rank}. {player}**: {value}")
                else:
                    response_parts.append(f"   **{rank}. {player}**: {value}")
            response_parts.append("")
        
        # Show overall rankings
        overall_rankings = comparison.get("overall_rankings", [])
        if overall_rankings:
            response_parts.append("🎯 **OVERALL RANKINGS** (across all metrics):")
            for ranking in overall_rankings:
                rank = ranking["rank"]
                player = ranking["player"]
                score = ranking["score"]
                
                if rank == 1:
                    response_parts.append(f"🏆 **{rank}. {player}** (Score: {score})")
                else:
                    response_parts.append(f"   **{rank}. {player}** (Score: {score})")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_team_comparison(results: Dict[str, Any]) -> str:
        """Format team comparison response."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        teams = results.get("teams", [])
        comparison = results.get("comparison", {})
        team_stats = results.get("team_stats", {})
        
        if len(teams) < 2:
            return "❌ Need at least 2 teams for comparison"
        
        response_parts = [f"🏈 **Team Comparison**: {' vs '.join(teams)}"]
        response_parts.append("=" * 50)
        
        # Show team stats comparison
        if team_stats:
            for metric, team_values in comparison.get("metrics", {}).items():
                response_parts.append(f"**{metric.upper()}:**")
                
                # Sort teams by this metric
                sorted_teams = sorted(team_values.items(), key=lambda x: x[1], reverse=True)
                
                for i, (team, value) in enumerate(sorted_teams, 1):
                    if i == 1:
                        response_parts.append(f"🏆 **{team}**: {value}")
                    else:
                        response_parts.append(f"   **{team}**: {value}")
                response_parts.append("")
        
        # Show overall winner if available
        winner = comparison.get("overall_winner")
        if winner:
            response_parts.append(f"🎯 **Overall Better Team**: {winner}")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_multi_team_comparison(results: Dict[str, Any]) -> str:
        """Format multi-team comparison response."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        teams = results.get("teams", [])
        comparison = results.get("comparison", {})
        team_stats = results.get("team_stats", {})
        
        if len(teams) < 3:
            return "❌ Need at least 3 teams for multi-team comparison"
        
        response_parts = [f"🏈 **{len(teams)}-Team Comparison**: {', '.join(teams)}"]
        response_parts.append("=" * 60)
        
        # Show rankings for each metric
        rankings_by_metric = comparison.get("rankings_by_metric", {})
        for metric, rankings in rankings_by_metric.items():
            response_parts.append(f"**{metric.upper()} RANKINGS:**")
            
            for ranking in rankings:
                rank = ranking.get("rank", 0)
                team = ranking.get("team", "Unknown")
                value = ranking.get("value", 0)
                
                if rank == 1:
                    response_parts.append(f"🥇 **{rank}. {team}**: {value}")
                elif rank == 2:
                    response_parts.append(f"🥈 **{rank}. {team}**: {value}")
                elif rank == 3:
                    response_parts.append(f"🥉 **{rank}. {team}**: {value}")
                else:
                    response_parts.append(f"   **{rank}. {team}**: {value}")
            
            response_parts.append("")
        
        # Show overall rankings
        overall_rankings = comparison.get("overall_rankings", [])
        if overall_rankings:
            response_parts.append("🎯 **OVERALL TEAM RANKINGS** (across all metrics):")
            for ranking in overall_rankings:
                rank = ranking.get("rank", 0)
                team = ranking.get("team", "Unknown")
                score = ranking.get("score", 0)
                
                if rank == 1:
                    response_parts.append(f"🏆 **{rank}. {team}** (Score: {score})")
                else:
                    response_parts.append(f"   **{rank}. {team}** (Score: {score})")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_season_comparison(results: Dict[str, Any]) -> str:
        """Format season comparison response."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        player = results.get("player")
        seasons = results.get("seasons", [])
        comparison = results.get("comparison", {})
        individual_stats = results.get("individual_stats", {})
        
        if not player or len(seasons) < 2:
            return "❌ Need player and at least 2 seasons for comparison"
        
        response_parts = [f"📅 **{player}** Season Comparison: {' vs '.join(map(str, seasons))}"]
        response_parts.append("=" * 60)
        
        best_season_by_metric = comparison.get("best_season_by_metric", {})
        trends = comparison.get("trends", {})
        
        # Show best season for each metric
        for metric, metric_data in best_season_by_metric.items():
            best_season = metric_data.get("best_season")
            best_value = metric_data.get("best_value")
            worst_season = metric_data.get("worst_season")
            worst_value = metric_data.get("worst_value")
            all_values = metric_data.get("all_values", {})
            
            response_parts.append(f"**{metric.upper()}:**")
            
            # Show values for each season
            for season in sorted(seasons, key=str):
                value = all_values.get(str(season), "N/A")
                if str(season) == best_season:
                    response_parts.append(f"• 🏆 **{season}**: {value} (Best)")
                elif str(season) == worst_season:
                    response_parts.append(f"• 📉 **{season}**: {value} (Lowest)")
                else:
                    response_parts.append(f"• **{season}**: {value}")
            
            # Show trend if available
            if metric in trends:
                trend_data = trends[metric]
                direction = trend_data.get("direction", "")
                change = trend_data.get("change", 0)
                if direction == "increasing":
                    response_parts.append(f"  📈 **Trend**: {direction.title()} (+{change})")
                elif direction == "decreasing":
                    response_parts.append(f"  📉 **Trend**: {direction.title()} ({change})")
                else:
                    response_parts.append(f"  ➡️ **Trend**: Stable")
            
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_multi_season_comparison(results: Dict[str, Any]) -> str:
        """Format multi-season comparison response."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        player = results.get("player")
        seasons = results.get("seasons", [])
        comparison = results.get("comparison", {})
        individual_stats = results.get("individual_stats", {})
        
        if not player or len(seasons) < 3:
            return "❌ Need player and at least 3 seasons for multi-season comparison"
        
        response_parts = [f"📈 **{player}** Career Analysis: {' vs '.join(map(str, seasons))}"]
        response_parts.append("=" * 70)
        
        rankings_by_metric = comparison.get("rankings_by_metric", {})
        career_progression = comparison.get("career_progression", {})
        overall_rankings = comparison.get("overall_rankings", [])
        
        # Show rankings for each metric across all seasons
        for metric, rankings in rankings_by_metric.items():
            response_parts.append(f"**{metric.upper()} RANKINGS:**")
            for ranking in rankings:
                rank = ranking["rank"]
                season = ranking["season"]
                value = ranking["value"]
                
                if rank == 1:
                    response_parts.append(f"🥇 **{rank}. {season}**: {value}")
                elif rank == 2:
                    response_parts.append(f"🥈 **{rank}. {season}**: {value}")
                elif rank == 3:
                    response_parts.append(f"🥉 **{rank}. {season}**: {value}")
                else:
                    response_parts.append(f"   **{rank}. {season}**: {value}")
            
            # Show career progression for this metric
            if metric in career_progression:
                progression = career_progression[metric]
                response_parts.append("  **Year-over-Year Changes:**")
                for change in progression:
                    from_season = change["from_season"]
                    to_season = change["to_season"]
                    change_value = change["change"]
                    trend = change["trend"]
                    
                    if trend == "improved":
                        response_parts.append(f"    📈 {from_season} → {to_season}: +{change_value}")
                    elif trend == "declined":
                        response_parts.append(f"    📉 {from_season} → {to_season}: {change_value}")
                    else:
                        response_parts.append(f"    ➡️ {from_season} → {to_season}: No change")
            
            response_parts.append("")
        
        # Show overall season rankings
        if overall_rankings:
            response_parts.append("🎯 **OVERALL SEASON RANKINGS** (across all metrics):")
            for ranking in overall_rankings:
                rank = ranking["rank"]
                season = ranking["season"]
                score = ranking["score"]
                
                if rank == 1:
                    response_parts.append(f"🏆 **{rank}. {season}** (Score: {score}) - Best Overall Season")
                elif rank == 2:
                    response_parts.append(f"🥈 **{rank}. {season}** (Score: {score})")
                elif rank == 3:
                    response_parts.append(f"🥉 **{rank}. {season}** (Score: {score})")
                else:
                    response_parts.append(f"   **{rank}. {season}** (Score: {score})")
        
        return "\n".join(response_parts)

    @staticmethod
    def _format_league_leaders(results: Dict[str, Any]) -> str:
        """Format league leaders response."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        ranked_stat = results.get("ranked_stat", "Unknown Stat")
        leaders = results.get("leaders", [])
        season = results.get("season", "Current Season")
        sport = results.get("sport", "NFL")
        
        if not leaders:
            return f"❌ No {ranked_stat} leaders found for {season}"
        
        response_parts = [f"🏆 **{sport} {ranked_stat.title()} Leaders** - {season} Season"]
        response_parts.append("=" * 50)
        
        # Show top leaders with medals for top 3
        for leader in leaders:
            rank = leader.get("rank", 0)
            player_name = leader.get("playerName", "Unknown")
            position = leader.get("position", "")
            stat_value = leader.get("statValue", "0")
            
            # Format position display
            position_display = f" ({position})" if position else ""
            
            # Add rank icons for top 3
            if rank == 1:
                rank_icon = "🥇"
            elif rank == 2:
                rank_icon = "🥈"
            elif rank == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"**{rank}.**"
            
            response_parts.append(f"{rank_icon} **{player_name}**{position_display} - {stat_value} {ranked_stat}")
        
        # Add summary info
        response_parts.append("")
        response_parts.append(f"📊 Showing top {len(leaders)} players ranked by {ranked_stat}")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_multi_stat_player(results: Dict[str, Any]) -> str:
        """Format multi-stat player response."""
        return ResponseFormatter._format_single_player_stat(results)  # Same format for now
    
    @staticmethod
    def _format_game_specific_stats(results: Dict[str, Any]) -> str:
        """Format game-specific stats response (e.g., 'Burrow vs Ravens Week 5')."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        player = results.get("player")
        filters_applied = results.get("filters_applied", {})
        matching_games = results.get("matching_games", [])
        
        if not matching_games:
            return f"❌ No games found for {player} with the specified criteria"
        
        response_parts = [f"🎮 **{player}** Game-Specific Stats:"]
        response_parts.append("=" * 50)
        
        # Show filter criteria
        if filters_applied:
            criteria_parts = []
            if "week" in filters_applied:
                criteria_parts.append(f"Week {filters_applied['week']}")
            if "opponent" in filters_applied:
                criteria_parts.append(f"vs {filters_applied['opponent']}")
            
            if criteria_parts:
                response_parts.append(f"🔍 **Criteria**: {', '.join(criteria_parts)}")
                response_parts.append("")
        
        # Show matching games
        for i, game in enumerate(matching_games, 1):
            week = game.get('week', 'N/A')
            opponent = game.get('opponent', 'Unknown')
            score = game.get('score', 'N/A')
            result = game.get('result', 'N/A')
            
            game_header = f"**Game {i}: Week {week} vs {opponent}**"
            game_info = f"Score: {score} ({result})"
            
            response_parts.append(game_header)
            response_parts.append(game_info)
            
            # Add game stats if available
            game_data = game.get('game_data', {})
            if game_data:
                response_parts.append("📊 **Performance:**")
                # This would need to be enhanced based on actual gamelog structure
                response_parts.append("   • Detailed stats available in gamelog data")
            
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_contextual_performance(results: Dict[str, Any]) -> str:
        """Format contextual performance response (e.g., 'Burrow home vs away games')."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        player = results.get("player")
        context_type = results.get("context_type", {})
        contextual_breakdown = results.get("contextual_breakdown", {})
        
        if not contextual_breakdown:
            return f"❌ No contextual data found for {player}"
        
        response_parts = [f"🏠 **{player}** Contextual Performance Analysis:"]
        response_parts.append("=" * 60)
        
        # Show breakdown by context
        for context, data in contextual_breakdown.items():
            game_count = data.get('game_count', 0)
            games = data.get('games', [])
            
            # Format context header
            if context == 'home':
                context_header = f"🏠 **HOME GAMES** ({game_count} games)"
            elif context == 'away':
                context_header = f"🛣️ **AWAY GAMES** ({game_count} games)"
            else:
                context_header = f"📋 **{context.upper()} GAMES** ({game_count} games)"
            
            response_parts.append(context_header)
            
            # Calculate basic stats from games
            wins = sum(1 for game in games if game.get('result') == 'W')
            losses = sum(1 for game in games if game.get('result') == 'L')
            
            response_parts.append(f"• **Record**: {wins}-{losses}")
            
            # Show sample of recent games
            if games:
                response_parts.append("• **Recent Games**:")
                for game in games[:3]:  # Show first 3 games
                    opponent = game.get('opponent', 'Unknown')
                    result = game.get('result', 'N/A')
                    week = game.get('week', 'N/A')
                    
                    if result == 'W':
                        response_parts.append(f"  ✅ Week {week} vs {opponent} (Win)")
                    elif result == 'L':
                        response_parts.append(f"  ❌ Week {week} vs {opponent} (Loss)")
                    else:
                        response_parts.append(f"  ➖ Week {week} vs {opponent} ({result})")
            
            response_parts.append("")
        
        # Add comparison summary if multiple contexts
        if len(contextual_breakdown) > 1:
            response_parts.append("📊 **SUMMARY COMPARISON:**")
            for context, data in contextual_breakdown.items():
                games = data.get('games', [])
                wins = sum(1 for game in games if game.get('result') == 'W')
                losses = sum(1 for game in games if game.get('result') == 'L')
                win_pct = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
                
                response_parts.append(f"• **{context.title()}**: {wins}-{losses} ({win_pct:.1f}% win rate)")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_game_performance_comparison(results: Dict[str, Any]) -> str:
        """Format game performance comparison response (e.g., 'Burrow's best games this season')."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        player = results.get("player")
        performance_criteria = results.get("performance_criteria", {})
        ranked_games = results.get("ranked_games", [])
        
        if not ranked_games:
            return f"❌ No games found to rank for {player}"
        
        sort_metric = performance_criteria.get('sort_metric', 'performance')
        sort_order = performance_criteria.get('sort_order', 'desc')
        
        # Determine header based on sort criteria
        if sort_order == 'desc':
            header = f"🏆 **{player}** Best Games by {sort_metric.replace('_', ' ').title()}:"
        else:
            header = f"📉 **{player}** Lowest Games by {sort_metric.replace('_', ' ').title()}:"
        
        response_parts = [header]
        response_parts.append("=" * 60)
        
        # Show top/bottom games
        display_count = min(10, len(ranked_games))  # Show top 10
        
        for i, game in enumerate(ranked_games[:display_count], 1):
            rank = game.get('rank', i)
            week = game.get('week', 'N/A')
            opponent = game.get('opponent', 'Unknown')
            score = game.get('score', 'N/A')
            result = game.get('result', 'N/A')
            metric_value = game.get('metric_value', 0)
            
            # Format rank with medals for top 3
            if rank == 1:
                rank_icon = "🥇"
            elif rank == 2:
                rank_icon = "🥈"
            elif rank == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"**{rank}.**"
            
            # Format result icon
            if result == 'W':
                result_icon = "✅"
            elif result == 'L':
                result_icon = "❌"
            else:
                result_icon = "➖"
            
            game_line = f"{rank_icon} **Week {week} vs {opponent}** - {metric_value} {sort_metric.replace('_', ' ')}"
            game_info = f"   {result_icon} Final: {score} ({result})"
            
            response_parts.append(game_line)
            response_parts.append(game_info)
            response_parts.append("")
        
        # Add summary stats
        if ranked_games:
            total_games = len(ranked_games)
            avg_metric = sum(game.get('metric_value', 0) for game in ranked_games) / total_games
            best_game = ranked_games[0]
            worst_game = ranked_games[-1]
            
            response_parts.append("📊 **PERFORMANCE SUMMARY:**")
            response_parts.append(f"• **Total Games Analyzed**: {total_games}")
            response_parts.append(f"• **Average {sort_metric.replace('_', ' ').title()}**: {avg_metric:.1f}")
            response_parts.append(f"• **Best Performance**: {best_game.get('metric_value')} (Week {best_game.get('week')} vs {best_game.get('opponent')})")
            response_parts.append(f"• **Lowest Performance**: {worst_game.get('metric_value')} (Week {worst_game.get('week')} vs {worst_game.get('opponent')})")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def _format_generic_response(results: Dict[str, Any]) -> str:
        """Format generic response for unknown query types."""
        if "error" in results:
            return f"❌ {results['error']}"
        
        return f"📊 Query completed:\n{str(results)}"
    
    @staticmethod
    def format_error_response(error_type: str, message: str, suggestions: List[str] = None) -> str:
        """Format error responses with helpful suggestions."""
        response_parts = [f"❌ **{error_type}**: {message}"]
        
        if suggestions:
            response_parts.append("\n💡 **Suggestions:**")
            for suggestion in suggestions:
                response_parts.append(f"• {suggestion}")
        
        return "\n".join(response_parts)
    
    @staticmethod
    def format_disambiguation_response(matching_players: List[Dict], player_name: str) -> str:
        """Format disambiguation response for multiple players with same name."""
        response_parts = [f"🤔 I found multiple players named **{player_name}**. Which one did you mean?"]
        response_parts.append("")
        
        for i, match in enumerate(matching_players, 1):
            team = match.get('team_name', 'Unknown Team')
            position = match.get('position', 'Unknown Position')
            jersey = match.get('jersey', 'N/A')
            
            response_parts.append(f"**{i}.** {team} - {position} - Jersey #{jersey}")
        
        response_parts.append("")
        response_parts.append("💬 Please specify by team name, position, or number (e.g., 'Cowboys', 'linebacker', or '1').")
        
        return "\n".join(response_parts)

class EdgeCaseHandler:
    """Handles edge cases and provides fallback responses."""
    
    @staticmethod
    def handle_no_data_found(query_context) -> str:
        """Handle cases where no data is found."""
        if query_context.player_names:
            player = query_context.player_names[0]
            suggestions = [
                f"Check if '{player}' is spelled correctly",
                "Try using the player's full name",
                "Make sure the player is currently active in the NFL",
                "Try asking about a different stat for this player"
            ]
            return ResponseFormatter.format_error_response(
                "Player Not Found", 
                f"I couldn't find stats for '{player}'",
                suggestions
            )
        
        return ResponseFormatter.format_error_response(
            "No Data", 
            "I couldn't find the requested information",
            ["Try rephrasing your question", "Check if the player/team names are correct"]
        )
    
    @staticmethod
    def handle_api_error(error_message: str) -> str:
        """Handle API errors gracefully."""
        suggestions = [
            "The sports API might be temporarily unavailable",
            "Try asking again in a few moments",
            "Try asking about a different player or statistic"
        ]
        return ResponseFormatter.format_error_response(
            "API Error",
            f"There was an issue fetching data: {error_message}",
            suggestions
        )
    
    @staticmethod
    def handle_unsupported_query(query_type: str) -> str:
        """Handle unsupported query types."""
        suggestions = [
            "Try asking about individual player statistics",
            "Ask for simple comparisons between 2 players",
            "Request basic team information",
            "Check our supported query examples"
        ]
        return ResponseFormatter.format_error_response(
            "Unsupported Query",
            f"This type of query ({query_type}) isn't supported yet",
            suggestions
        )

# Example usage and templates
RESPONSE_TEMPLATES = {
    "single_stat_success": "📊 **{player}** has **{value} {stat}** this season (Ranked #{rank} in NFL)",
    "comparison_winner": "🏆 **{winner}** leads with **{value} {stat}** vs {loser}'s **{loser_value}**",
    "multi_stat_summary": "📊 **{player}** Season Stats: {stats_summary}",
    "no_data": "❌ No data found for **{player}** - {suggestions}",
    "api_error": "⚠️ API Error: {error} - {suggestions}",
    "disambiguation": "🤔 Multiple **{name}** found: {options}"
} 