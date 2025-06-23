#!/usr/bin/env python3
"""
Quick fix to add season calculation functionality to the response formatter.
This patches the existing system to handle "for season" queries correctly.
"""

import sys
import os
sys.path.append('src')

# Import the existing response formatter
from sports_bot.core.stats.response_formatter import ResponseFormatter

# Save the original method
original_format_single_player_stat = ResponseFormatter._format_single_player_stat

@staticmethod
def enhanced_format_single_player_stat(results):
    """Enhanced version that handles season calculations."""
    player = results.get("player")
    stats = results.get("stats", {})
    
    # Try to get the original query
    query = ""
    if hasattr(results, 'get'):
        query = results.get("original_query", results.get("query", ""))
    
    if isinstance(stats, dict) and "error" in stats:
        return f"❌ Sorry, I couldn't get stats for {player}: {stats['error']}"
    
    if not isinstance(stats, dict) or "simple_stats" not in stats:
        return f"❌ No stats found for {player}"
    
    simple_stats = stats["simple_stats"]
    query_lower = query.lower() if query else ""
    
    # Check if user asked for season totals
    if "for season" in query_lower or "season total" in query_lower:
        return format_season_totals(player, simple_stats, query, stats)
    
    # Fall back to original method
    return original_format_single_player_stat(results)

def format_season_totals(player, simple_stats, query, full_stats):
    """Calculate and format season totals."""
    query_lower = query.lower()
    response_parts = [f"🏀 **{player}** Season Totals:"]
    
    games_played = simple_stats.get("games_played", 0)
    sport = full_stats.get("sport", "NBA")
    season = full_stats.get("season", "2024-25")
    
    if games_played == 0:
        return f"❌ Cannot calculate season totals - no games played data for {player}"
    
    calculations_made = False
    
    # Points calculation
    if "points" in query_lower:
        points_ppg = simple_stats.get("points", 0)
        if points_ppg:
            season_total = points_ppg * games_played
            response_parts.append(f"• **Season Total Points**: {season_total:,.0f} points")
            response_parts.append(f"• **Points Per Game**: {points_ppg} PPG")
            response_parts.append(f"• **Games Played**: {games_played} games")
            response_parts.append(f"• **Season**: {season}")
            response_parts.append("")
            response_parts.append(f"📊 **Calculation**: {points_ppg} PPG × {games_played} games = {season_total:,.0f} total points")
            
            # Add validation notes
            if season_total > 3000:
                response_parts.append("⚠️ **Note**: This is an exceptionally high season total")
            elif season_total < 100 and games_played > 10:
                response_parts.append("⚠️ **Note**: This seems low for the number of games played")
            
            calculations_made = True
    
    # Rebounds calculation
    if "rebounds" in query_lower:
        rebounds_rpg = simple_stats.get("rebounds", 0)
        if rebounds_rpg:
            season_total = rebounds_rpg * games_played
            response_parts.append(f"• **Season Total Rebounds**: {season_total:,.0f} rebounds")
            response_parts.append(f"• **Rebounds Per Game**: {rebounds_rpg} RPG")
            response_parts.append(f"• **Games Played**: {games_played} games")
            response_parts.append(f"• **Season**: {season}")
            response_parts.append("")
            response_parts.append(f"📊 **Calculation**: {rebounds_rpg} RPG × {games_played} games = {season_total:,.0f} total rebounds")
            calculations_made = True
    
    # Assists calculation
    if "assists" in query_lower:
        assists_apg = simple_stats.get("assists", 0)
        if assists_apg:
            season_total = assists_apg * games_played
            response_parts.append(f"• **Season Total Assists**: {season_total:,.0f} assists")
            response_parts.append(f"• **Assists Per Game**: {assists_apg} APG")
            response_parts.append(f"• **Games Played**: {games_played} games")
            response_parts.append(f"• **Season**: {season}")
            response_parts.append("")
            response_parts.append(f"📊 **Calculation**: {assists_apg} APG × {games_played} games = {season_total:,.0f} total assists")
            calculations_made = True
    
    if not calculations_made:
        # Default to points if no specific stat mentioned but "for season" was requested
        points_ppg = simple_stats.get("points", 0)
        if points_ppg:
            season_total = points_ppg * games_played
            response_parts.append(f"• **Season Total Points**: {season_total:,.0f} points")
            response_parts.append(f"• **Points Per Game**: {points_ppg} PPG")
            response_parts.append(f"• **Games Played**: {games_played} games")
            response_parts.append(f"• **Season**: {season}")
            response_parts.append("")
            response_parts.append(f"📊 **Calculation**: {points_ppg} PPG × {games_played} games = {season_total:,.0f} total points")
    
    response_parts.append("")
    response_parts.append("✅ **Season totals calculated from per-game averages**")
    response_parts.append("🚀 *Powered by Enhanced Query Engine*")
    
    return "\n".join(response_parts)

# Apply the patch
ResponseFormatter._format_single_player_stat = enhanced_format_single_player_stat

print("✅ Season calculation patch applied!")
print("Now 'Ja Morant points for season' will calculate: 25.1 PPG × 57 games = 1,431 total points") 