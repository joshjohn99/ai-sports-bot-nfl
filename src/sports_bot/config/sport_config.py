"""
Sport-specific configuration system for multi-database architecture.
Each sport has its own database, schema, and stat mappings.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SupportedSport(Enum):
    """Supported sports in the system."""
    NFL = "NFL"
    NBA = "NBA"
    MLB = "MLB"
    NHL = "NHL"

@dataclass
class StatMapping:
    """Mapping configuration for a stat."""
    db_column: str
    api_field: str
    display_name: str
    category: str
    positions: List[str] = None
    aggregatable: bool = True
    user_terms: List[str] = None

@dataclass
class SportConfig:
    """Configuration for a specific sport."""
    name: str
    database_name: str
    positions: List[str]
    stat_mappings: Dict[str, StatMapping]
    season_format: str  # e.g., "2024" for NFL, "2024-25" for NBA
    api_endpoints: Dict[str, str]
    cache_ttl: int = 3600  # Cache TTL in seconds

class SportConfigManager:
    """Manages configurations for all supported sports."""
    
    def __init__(self):
        self.configs = self._initialize_configs()
    
    def _initialize_configs(self) -> Dict[str, SportConfig]:
        """Initialize all sport configurations."""
        return {
            SupportedSport.NFL.value: self._get_nfl_config(),
            SupportedSport.NBA.value: self._get_nba_config(),
            SupportedSport.MLB.value: self._get_mlb_config(),
            SupportedSport.NHL.value: self._get_nhl_config(),
        }
    
    def get_config(self, sport: str) -> Optional[SportConfig]:
        """Get configuration for a specific sport."""
        return self.configs.get(sport.upper())
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sports."""
        return list(self.configs.keys())
    
    def get_database_name(self, sport: str) -> str:
        """Get database name for a sport."""
        config = self.get_config(sport)
        return config.database_name if config else f"{sport.lower()}_stats.db"
    
    def _get_nfl_config(self) -> SportConfig:
        """Get NFL-specific configuration."""
        return SportConfig(
            name="NFL",
            database_name="nfl_stats.db",
            positions=["QB", "RB", "WR", "TE", "FB", "DE", "DT", "LB", "CB", "S", 
                      "MLB", "OLB", "ILB", "EDGE", "DL", "DB", "K", "P"],
            stat_mappings={
                "passing_yards": StatMapping(
                    db_column="passing_yards",
                    api_field="passingYards",
                    display_name="Passing Yards",
                    category="offense",
                    positions=["QB"],
                    user_terms=["passing yards", "pass yards", "yards passing"]
                ),
                "passing_touchdowns": StatMapping(
                    db_column="passing_touchdowns",
                    api_field="passingTouchdowns",
                    display_name="Passing Touchdowns",
                    category="offense",
                    positions=["QB"],
                    user_terms=["passing tds", "pass tds", "passing touchdowns"]
                ),
                "rushing_yards": StatMapping(
                    db_column="rushing_yards",
                    api_field="rushingYards",
                    display_name="Rushing Yards",
                    category="offense",
                    positions=["RB", "QB", "FB"],
                    user_terms=["rushing yards", "rush yards", "yards rushing"]
                ),
                "rushing_touchdowns": StatMapping(
                    db_column="rushing_touchdowns",
                    api_field="rushingTouchdowns",
                    display_name="Rushing Touchdowns",
                    category="offense",
                    positions=["RB", "QB", "FB"],
                    user_terms=["rushing tds", "rush tds", "rushing touchdowns"]
                ),
                "receiving_yards": StatMapping(
                    db_column="receiving_yards",
                    api_field="receivingYards",
                    display_name="Receiving Yards",
                    category="offense",
                    positions=["WR", "TE", "RB"],
                    user_terms=["receiving yards", "rec yards", "yards receiving"]
                ),
                "receiving_touchdowns": StatMapping(
                    db_column="receiving_touchdowns",
                    api_field="receivingTouchdowns",
                    display_name="Receiving Touchdowns",
                    category="offense",
                    positions=["WR", "TE", "RB"],
                    user_terms=["receiving tds", "rec tds", "receiving touchdowns"]
                ),
                "receptions": StatMapping(
                    db_column="receptions",
                    api_field="receptions",
                    display_name="Receptions",
                    category="offense",
                    positions=["WR", "TE", "RB"],
                    user_terms=["receptions", "catches", "rec"]
                ),
                "sacks": StatMapping(
                    db_column="sacks",
                    api_field="sacks",
                    display_name="Sacks",
                    category="defense",
                    positions=["DE", "DT", "LB", "OLB", "ILB", "MLB", "EDGE", "DL"],
                    user_terms=["sacks", "sck"]
                ),
                "tackles": StatMapping(
                    db_column="tackles",
                    api_field="tackles",
                    display_name="Tackles",
                    category="defense",
                    positions=["LB", "DE", "DT", "S", "CB", "MLB", "OLB", "ILB", "DL", "DB"],
                    user_terms=["tackles", "tkl"]
                ),
                "interceptions": StatMapping(
                    db_column="interceptions",
                    api_field="interceptions",
                    display_name="Interceptions",
                    category="defense",
                    positions=["CB", "S", "LB", "DB"],
                    user_terms=["interceptions", "int", "picks"]
                ),
                "field_goals_made": StatMapping(
                    db_column="field_goals_made",
                    api_field="fieldGoalsMade",
                    display_name="Field Goals Made",
                    category="special_teams",
                    positions=["K"],
                    user_terms=["field goals", "fg made", "field goals made"]
                ),
            },
            season_format="YYYY",
            api_endpoints={
                "player_stats": "/nfl-player-stats/v1/data",
                "team_roster": "/nfl-player-listing/v1/data",
                "league_leaders": "/nfl-league-leaders/v1/data",
            }
        )
    
    def _get_nba_config(self) -> SportConfig:
        """Get NBA-specific configuration."""
        return SportConfig(
            name="NBA",
            database_name="nba_stats.db",
            positions=["PG", "SG", "SF", "PF", "C", "G", "F"],
            stat_mappings={
                "points": StatMapping(
                    db_column="points",
                    api_field="points",
                    display_name="Points",
                    category="offense",
                    positions=["PG", "SG", "SF", "PF", "C"],
                    user_terms=["points", "pts", "scoring"]
                ),
                "rebounds": StatMapping(
                    db_column="rebounds",
                    api_field="rebounds",
                    display_name="Rebounds",
                    category="general",
                    positions=["PF", "C", "SF"],
                    user_terms=["rebounds", "reb", "boards"]
                ),
                "assists": StatMapping(
                    db_column="assists",
                    api_field="assists",
                    display_name="Assists",
                    category="offense",
                    positions=["PG", "SG"],
                    user_terms=["assists", "ast", "dimes"]
                ),
                "steals": StatMapping(
                    db_column="steals",
                    api_field="steals",
                    display_name="Steals",
                    category="defense",
                    positions=["PG", "SG", "SF"],
                    user_terms=["steals", "stl"]
                ),
                "blocks": StatMapping(
                    db_column="blocks",
                    api_field="blocks",
                    display_name="Blocks",
                    category="defense",
                    positions=["C", "PF"],
                    user_terms=["blocks", "blk", "swats"]
                ),
                "three_pointers_made": StatMapping(
                    db_column="three_pointers_made",
                    api_field="threePointersMade",
                    display_name="Three Pointers Made",
                    category="offense",
                    positions=["PG", "SG", "SF"],
                    user_terms=["three pointers", "3pm", "threes", "3 pointers made"]
                ),
                "field_goals_made": StatMapping(
                    db_column="field_goals_made_basketball",
                    api_field="fieldGoalsMade",
                    display_name="Field Goals Made",
                    category="offense",
                    positions=["PG", "SG", "SF", "PF", "C"],
                    user_terms=["field goals", "fg made", "shots made"]
                ),
                "free_throws_made": StatMapping(
                    db_column="free_throws_made",
                    api_field="freeThrowsMade",
                    display_name="Free Throws Made",
                    category="offense",
                    positions=["PG", "SG", "SF", "PF", "C"],
                    user_terms=["free throws", "ft made", "free throws made"]
                ),
                "minutes": StatMapping(
                    db_column="minutes_played",
                    api_field="minutesPlayed",
                    display_name="Minutes Played",
                    category="general",
                    positions=["PG", "SG", "SF", "PF", "C"],
                    user_terms=["minutes", "min", "minutes played"]
                ),
            },
            season_format="YYYY-YY",
            api_endpoints={
                "player_stats": "/nba-player-stats/v1/data",
                "team_roster": "/nba-player-listing/v1/data",
                "league_leaders": "/nba-league-leaders/v1/data",
            }
        )
    
    def _get_mlb_config(self) -> SportConfig:
        """Get MLB-specific configuration."""
        return SportConfig(
            name="MLB",
            database_name="mlb_stats.db",
            positions=["P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"],
            stat_mappings={
                "batting_average": StatMapping(
                    db_column="batting_average",
                    api_field="battingAverage",
                    display_name="Batting Average",
                    category="batting",
                    positions=["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"],
                    user_terms=["batting average", "avg", "ba"]
                ),
                "home_runs": StatMapping(
                    db_column="home_runs",
                    api_field="homeRuns",
                    display_name="Home Runs",
                    category="batting",
                    positions=["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"],
                    user_terms=["home runs", "hr", "homers"]
                ),
                "rbi": StatMapping(
                    db_column="runs_batted_in",
                    api_field="runsBattedIn",
                    display_name="RBIs",
                    category="batting",
                    positions=["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"],
                    user_terms=["rbi", "rbis", "runs batted in"]
                ),
                "era": StatMapping(
                    db_column="earned_run_average",
                    api_field="earnedRunAverage",
                    display_name="ERA",
                    category="pitching",
                    positions=["P"],
                    user_terms=["era", "earned run average"]
                ),
                "wins": StatMapping(
                    db_column="wins",
                    api_field="wins",
                    display_name="Wins",
                    category="pitching",
                    positions=["P"],
                    user_terms=["wins", "w"]
                ),
                "strikeouts": StatMapping(
                    db_column="strikeouts",
                    api_field="strikeouts",
                    display_name="Strikeouts",
                    category="pitching",
                    positions=["P"],
                    user_terms=["strikeouts", "k", "so"]
                ),
            },
            season_format="YYYY",
            api_endpoints={
                "player_stats": "/mlb-player-stats/v1/data",
                "team_roster": "/mlb-player-listing/v1/data",
                "league_leaders": "/mlb-league-leaders/v1/data",
            }
        )
    
    def _get_nhl_config(self) -> SportConfig:
        """Get NHL-specific configuration."""
        return SportConfig(
            name="NHL",
            database_name="nhl_stats.db",
            positions=["C", "LW", "RW", "D", "G"],
            stat_mappings={
                "goals": StatMapping(
                    db_column="goals",
                    api_field="goals",
                    display_name="Goals",
                    category="offense",
                    positions=["C", "LW", "RW", "D"],
                    user_terms=["goals", "g"]
                ),
                "assists": StatMapping(
                    db_column="assists_hockey",
                    api_field="assists",
                    display_name="Assists",
                    category="offense",
                    positions=["C", "LW", "RW", "D"],
                    user_terms=["assists", "a"]
                ),
                "points": StatMapping(
                    db_column="points_hockey",
                    api_field="points",
                    display_name="Points",
                    category="offense",
                    positions=["C", "LW", "RW", "D"],
                    user_terms=["points", "pts"]
                ),
                "penalty_minutes": StatMapping(
                    db_column="penalty_minutes",
                    api_field="penaltyMinutes",
                    display_name="Penalty Minutes",
                    category="general",
                    positions=["C", "LW", "RW", "D"],
                    user_terms=["penalty minutes", "pim", "penalties"]
                ),
                "plus_minus": StatMapping(
                    db_column="plus_minus",
                    api_field="plusMinus",
                    display_name="Plus/Minus",
                    category="general",
                    positions=["C", "LW", "RW", "D"],
                    user_terms=["plus minus", "+/-", "plus/minus"]
                ),
            },
            season_format="YYYY-YY",
            api_endpoints={
                "player_stats": "/nhl-player-stats/v1/data",
                "team_roster": "/nhl-player-listing/v1/data",
                "league_leaders": "/nhl-league-leaders/v1/data",
            }
        )

# Global instance
sport_config_manager = SportConfigManager() 