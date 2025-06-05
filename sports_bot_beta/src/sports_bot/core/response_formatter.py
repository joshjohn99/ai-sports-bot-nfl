"""
Response Formatter Module
Handles formatting of query results into user-friendly responses.
"""

from typing import Dict, Any, List
from .query_types import QueryType

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
        else:
            return ResponseFormatter._format_generic_response(query_results)
    
    @staticmethod
    def _format_single_player_stat(results: Dict[str, Any]) -> str:
        """Format single player stat response."""
        player = results.get("player")
        stats = results.get("stats", {})
        
        if isinstance(stats, dict) and "error" in stats:
            return f"❌ Sorry, I couldn't get stats for {player}: {stats['error']}"
        
        if not isinstance(stats, dict) or "simple_stats" not in stats:
            return f"❌ No stats found for {player}"
        
        simple_stats = stats["simple_stats"]
        
        # Build response
        response_parts = [f"📊 **{player}** stats:"]
        
        for metric, value in simple_stats.items():
            if value != "Not found" and value != "Error during extraction":
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
        return "🏈 Team comparison functionality coming soon!"
    
    @staticmethod
    def _format_multi_team_comparison(results: Dict[str, Any]) -> str:
        """Format multi-team comparison response."""
        if "error" in results:
            return f"❌ {results['error']}"
        return "🏈 Multi-team comparison functionality coming soon!"
    
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
        return "🏆 League leaders functionality coming soon! This requires additional API endpoints."
    
    @staticmethod
    def _format_multi_stat_player(results: Dict[str, Any]) -> str:
        """Format multi-stat player response."""
        return ResponseFormatter._format_single_player_stat(results)  # Same format for now
    
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