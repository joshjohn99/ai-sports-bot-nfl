"""
Dynamic stats calculator that converts between per-game, season totals, and career totals.
Works with any player and any stat automatically.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math

@dataclass
class StatCalculation:
    """Container for different stat calculations."""
    stat_name: str
    per_game: float
    season_total: float
    career_total: float
    games_played_season: int
    total_games_career: int
    seasons_played: int
    context: str

class DynamicStatsCalculator:
    """
    Calculates per-game, season totals, and career totals for any player and any stat.
    """
    
    def __init__(self, sport_db_manager):
        self.sport_db_manager = sport_db_manager
        
        # Define which stats should be calculated as totals vs averages
        self.summable_stats = {
            # NBA Stats that can be summed
            'points', 'assists', 'rebounds', 'steals', 'blocks', 'turnovers',
            'field_goals_made', 'field_goals_attempted', 'three_pointers_made', 
            'three_pointers_attempted', 'free_throws_made', 'free_throws_attempted',
            'minutes_played',
            
            # NFL Stats that can be summed
            'passing_yards', 'rushing_yards', 'receiving_yards', 'passing_touchdowns',
            'rushing_touchdowns', 'receiving_touchdowns', 'sacks', 'tackles',
            'interceptions', 'forced_fumbles', 'receptions'
        }
        
        # Stats that should remain as averages/percentages
        self.percentage_stats = {
            'field_goal_percentage', 'three_point_percentage', 'free_throw_percentage',
            'completion_percentage', 'passer_rating'
        }
    
    def calculate_comprehensive_stats(self, player_name: str, sport: str, 
                                    requested_stats: List[str]) -> Dict[str, StatCalculation]:
        """
        Calculate comprehensive stats (per-game, season, career) for any player.
        
        Args:
            player_name: Name of the player
            sport: Sport (NBA, NFL, etc.)
            requested_stats: List of stats to calculate
            
        Returns:
            Dictionary of stat_name -> StatCalculation
        """
        
        # Get all player data from database
        player_data = self._get_comprehensive_player_data(player_name, sport)
        if not player_data:
            return {}
        
        results = {}
        
        for stat_name in requested_stats:
            if stat_name in self.summable_stats:
                calculation = self._calculate_summable_stat(player_data, stat_name)
                if calculation:
                    results[stat_name] = calculation
            elif stat_name in self.percentage_stats:
                calculation = self._calculate_percentage_stat(player_data, stat_name)
                if calculation:
                    results[stat_name] = calculation
            else:
                # Try as summable stat by default
                calculation = self._calculate_summable_stat(player_data, stat_name)
                if calculation:
                    results[stat_name] = calculation
        
        return results
    
    def _get_comprehensive_player_data(self, player_name: str, sport: str) -> Optional[Dict[str, Any]]:
        """Get all seasons of data for a player."""
        try:
            session = self.sport_db_manager.get_session(sport)
            models = self.sport_db_manager.get_models(sport)
            
            if not session or not models:
                return None
            
            Player = models['Player']
            PlayerStats = models['PlayerStats']
            
            # Find player
            player = session.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).first()
            
            if not player:
                return None
            
            # Get ALL seasons for this player
            all_seasons = session.query(PlayerStats).filter_by(player_id=player.id).all()
            
            # Get current season (most recent)
            current_season = None
            if all_seasons:
                current_season = max(all_seasons, key=lambda x: x.season)
            
            player_data = {
                "player": player,
                "all_seasons": all_seasons,
                "current_season": current_season,
                "sport": sport
            }
            
            session.close()
            return player_data
            
        except Exception as e:
            print(f"Error getting player data: {e}")
            return None
    
    def _calculate_summable_stat(self, player_data: Dict[str, Any], stat_name: str) -> Optional[StatCalculation]:
        """Calculate summable stat (points, assists, etc.) across all contexts."""
        try:
            all_seasons = player_data["all_seasons"]
            current_season = player_data["current_season"]
            player = player_data["player"]
            
            if not current_season:
                return None
            
            # Current season calculations
            current_stat_value = getattr(current_season, stat_name, 0) or 0
            current_games = getattr(current_season, 'games_played', 0) or 0
            
            if current_games == 0:
                return None
            
            # Per-game calculation for current season
            per_game = current_stat_value / current_games if current_games > 0 else 0
            
            # Season total (this might already be a total, or might be per-game)
            # We need to determine if the stored value is per-game or total
            season_total = self._determine_season_total(current_stat_value, current_games, stat_name)
            
            # Career calculations
            career_total = 0
            total_career_games = 0
            
            for season in all_seasons:
                season_value = getattr(season, stat_name, 0) or 0
                season_games = getattr(season, 'games_played', 0) or 0
                
                # Add to career total
                season_contribution = self._determine_season_total(season_value, season_games, stat_name)
                career_total += season_contribution
                total_career_games += season_games
            
            return StatCalculation(
                stat_name=stat_name,
                per_game=round(per_game, 1),
                season_total=round(season_total, 1),
                career_total=round(career_total, 1),
                games_played_season=current_games,
                total_games_career=total_career_games,
                seasons_played=len(all_seasons),
                context=f"{current_season.season} season"
            )
            
        except Exception as e:
            print(f"Error calculating summable stat {stat_name}: {e}")
            return None
    
    def _determine_season_total(self, stored_value: float, games_played: int, stat_name: str) -> float:
        """
        Determine if stored value is per-game or season total, and return season total.
        
        This is the key function that handles the conversion logic.
        """
        
        # Heuristics to determine if value is per-game or total
        if games_played == 0:
            return stored_value
        
        # If the value is very large relative to games, it's likely a season total
        if stored_value > games_played * 50:  # e.g., 1000+ points in 50 games
            return stored_value  # Already a season total
        
        # If the value is reasonable for per-game, treat as per-game
        if stat_name in ['points', 'assists', 'rebounds']:
            if stored_value <= 50:  # Reasonable per-game values
                return stored_value * games_played  # Convert to season total
        
        if stat_name in ['passing_yards', 'rushing_yards']:
            if stored_value <= 500:  # Reasonable per-game values
                return stored_value * games_played  # Convert to season total
        
        # For other stats, use a general heuristic
        avg_per_game = stored_value / games_played if games_played > 0 else 0
        
        # If average is reasonable, stored value is likely a total
        if avg_per_game > 0.1 and avg_per_game < 100:
            return stored_value  # Already a season total
        else:
            return stored_value * games_played  # Convert to season total
    
    def _calculate_percentage_stat(self, player_data: Dict[str, Any], stat_name: str) -> Optional[StatCalculation]:
        """Calculate percentage stats (field goal %, etc.)."""
        # For percentages, we typically want to show the percentage itself
        # rather than summing across seasons
        current_season = player_data["current_season"]
        if not current_season:
            return None
        
        stat_value = getattr(current_season, stat_name, 0) or 0
        
        return StatCalculation(
            stat_name=stat_name,
            per_game=stat_value,  # Percentage stays the same
            season_total=stat_value,  # Percentage for the season
            career_total=stat_value,  # Would need weighted average for true career %
            games_played_season=getattr(current_season, 'games_played', 0),
            total_games_career=getattr(current_season, 'games_played', 0),
            seasons_played=1,
            context=f"{current_season.season} season percentage"
        )

def format_comprehensive_stats(stat_calculations: Dict[str, StatCalculation], 
                             player_name: str, sport: str) -> str:
    """
    Format comprehensive stats for display with per-game, season, and career totals.
    """
    if not stat_calculations:
        return f"❌ No stats available for {player_name}"
    
    response_parts = [f"📊 **{player_name}** ({sport}) Comprehensive Stats:"]
    
    for stat_name, calc in stat_calculations.items():
        stat_display = stat_name.replace('_', ' ').title()
        
        response_parts.append(f"\n**{stat_display}:**")
        response_parts.append(f"  • **Per Game**: {calc.per_game}")
        response_parts.append(f"  • **Season Total**: {calc.season_total:,} ({calc.context})")
        response_parts.append(f"  • **Career Total**: {calc.career_total:,} ({calc.seasons_played} seasons)")
        
        if calc.stat_name in ['points', 'assists', 'rebounds']:
            # Add some context for major stats
            response_parts.append(f"    _{calc.games_played_season} games this season, {calc.total_games_career} career games_")
    
    return "\n".join(response_parts)

# Integration function for existing system
def enhance_stat_response_with_calculations(player_name: str, sport: str, 
                                          original_stats: Dict[str, Any],
                                          sport_db_manager) -> str:
    """
    Enhance the existing stat response with comprehensive calculations.
    """
    
    # Extract stat names from original response
    if isinstance(original_stats, dict) and "simple_stats" in original_stats:
        stat_names = list(original_stats["simple_stats"].keys())
    else:
        stat_names = ["points"]  # Default fallback
    
    # Calculate comprehensive stats
    calculator = DynamicStatsCalculator(sport_db_manager)
    calculations = calculator.calculate_comprehensive_stats(player_name, sport, stat_names)
    
    if calculations:
        return format_comprehensive_stats(calculations, player_name, sport)
    else:
        # Fallback to original formatting
        return f"📊 **{player_name}** ({sport}) Stats: {original_stats}" 