"""
Enhanced response formatter that includes per-game, season, and career calculations.
"""

from .dynamic_stats_calculator import enhance_stat_response_with_calculations

def format_enhanced_stat_response(query_results: dict, sport_db_manager) -> str:
    """
    Enhanced formatting that includes comprehensive stat calculations.
    """
    
    # Extract player info
    if isinstance(query_results.get("stats"), dict):
        stats_data = query_results["stats"]
        player_name = stats_data.get("player_fullName", "Unknown Player")
        sport = query_results.get("sport", stats_data.get("sport", "Unknown"))
        
        # Use enhanced calculations
        enhanced_response = enhance_stat_response_with_calculations(
            player_name, sport, stats_data, sport_db_manager
        )
        
        return enhanced_response
    
    else:
        # Fallback to simple formatting
        return str(query_results) 