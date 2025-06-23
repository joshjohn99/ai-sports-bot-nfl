"""
Sport-specific database models for multi-database architecture.
Each sport gets its own optimized database schema.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from typing import Dict, Optional

from ..config.db_config import DATABASE_PATH
from ..config.sport_config import sport_config_manager

# Create base classes for each sport
def create_sport_base():
    """Create a new base class for sport-specific models."""
    return declarative_base()

class SportDatabaseManager:
    """Manages multiple sport-specific databases."""
    
    def __init__(self):
        self.engines = {}
        self.sessions = {}
        self.bases = {}
        self.models = {}
        self._initialize_sport_databases()
    
    def _initialize_sport_databases(self):
        """Initialize databases for all supported sports."""
        supported_sports = sport_config_manager.get_supported_sports()
        
        for sport in supported_sports:
            self._create_sport_database(sport)
    
    def _create_sport_database(self, sport: str):
        """Create database models and engine for a specific sport."""
        config = sport_config_manager.get_config(sport)
        if not config:
            return
        
        # Create sport-specific database path
        db_name = config.database_name
        db_path = os.path.join(os.path.dirname(DATABASE_PATH), db_name)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        self.engines[sport] = engine
        
        # Create base and models
        base = create_sport_base()
        self.bases[sport] = base
        
        # Create sport-specific models
        models = self._create_sport_models(sport, base, config)
        self.models[sport] = models
        
        # Create tables
        base.metadata.create_all(engine)
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        self.sessions[sport] = Session
    
    def _create_sport_models(self, sport: str, base, config):
        """Create SQLAlchemy models for a specific sport."""
        
        class Player(base):
            """Player model for specific sport."""
            __tablename__ = f'{sport.lower()}_players'
            
            id = Column(Integer, primary_key=True)
            external_id = Column(String, unique=True, index=True)
            name = Column(String, index=True)
            position = Column(String, index=True)
            current_team_id = Column(Integer, ForeignKey(f'{sport.lower()}_teams.id'))
            active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships - using string references to avoid circular imports
            # current_team = relationship("Team", back_populates="players")
            # stats = relationship("PlayerStats", back_populates="player")
            # career_stats = relationship("CareerStats", back_populates="player", uselist=False)
        
        class Team(base):
            """Team model for specific sport."""
            __tablename__ = f'{sport.lower()}_teams'
            
            id = Column(Integer, primary_key=True)
            external_id = Column(String, unique=True, index=True)
            name = Column(String, index=True)
            display_name = Column(String)
            abbreviation = Column(String, index=True)
            city = Column(String)
            conference = Column(String, index=True)
            division = Column(String, index=True)
            active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships - using string references to avoid circular imports
            # players = relationship("Player", back_populates="current_team")
        
        # Create sport-specific stats model
        if sport == "NFL":
            PlayerStats = self._create_nfl_stats_model(base)
            CareerStats = self._create_nfl_career_model(base)
        elif sport == "NBA":
            PlayerStats = self._create_nba_stats_model(base)
            CareerStats = self._create_nba_career_model(base)
        elif sport == "MLB":
            PlayerStats = self._create_mlb_stats_model(base)
            CareerStats = self._create_mlb_career_model(base)
        elif sport == "NHL":
            PlayerStats = self._create_nhl_stats_model(base)
            CareerStats = self._create_nhl_career_model(base)
        else:
            # Generic stats model
            PlayerStats = self._create_generic_stats_model(base, sport)
            CareerStats = self._create_generic_career_model(base, sport)
        
        return {
            'Player': Player,
            'Team': Team,
            'PlayerStats': PlayerStats,
            'CareerStats': CareerStats
        }
    
    def _create_nfl_stats_model(self, base):
        """Create NFL-specific stats model."""
        class NFLPlayerStats(base):
            __tablename__ = 'nfl_player_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nfl_players.id'), index=True)
            season = Column(String, index=True)
            week = Column(Integer, index=True)
            
            # Common stats
            games_played = Column(Integer)
            games_started = Column(Integer)
            
            # Offensive stats
            passing_yards = Column(Integer)
            passing_touchdowns = Column(Integer)
            passing_attempts = Column(Integer)
            passing_completions = Column(Integer)
            passing_interceptions = Column(Integer)
            passer_rating = Column(Float)
            
            rushing_yards = Column(Integer)
            rushing_touchdowns = Column(Integer)
            rushing_attempts = Column(Integer)
            rushing_fumbles = Column(Integer)
            
            receiving_yards = Column(Integer)
            receiving_touchdowns = Column(Integer)
            receptions = Column(Integer)
            receiving_targets = Column(Integer)
            receiving_fumbles = Column(Integer)
            
            # Defensive stats
            sacks = Column(Float)
            tackles = Column(Integer)
            solo_tackles = Column(Integer)
            assisted_tackles = Column(Integer)
            interceptions = Column(Integer)
            interception_yards = Column(Integer)
            interception_touchdowns = Column(Integer)
            forced_fumbles = Column(Integer)
            fumble_recoveries = Column(Integer)
            pass_deflections = Column(Integer)
            
            # Special teams
            field_goals_made = Column(Integer)
            field_goals_attempted = Column(Integer)
            extra_points_made = Column(Integer)
            extra_points_attempted = Column(Integer)
            punts = Column(Integer)
            punt_yards = Column(Integer)
            punt_average = Column(Float)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships - commented out to avoid circular imports
            # # player = relationship("Player", back_populates="stats")
            
            # Indexes
            __table_args__ = (
                Index('idx_nfl_player_season', 'player_id', 'season'),
                Index('idx_nfl_season_week', 'season', 'week'),
            )
        
        return NFLPlayerStats
    
    def _create_nfl_career_model(self, base):
        """Create NFL-specific career stats model."""
        class NFLCareerStats(base):
            __tablename__ = 'nfl_career_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nfl_players.id'), unique=True, index=True)
            
            # Career totals
            total_games = Column(Integer)
            total_starts = Column(Integer)
            seasons_played = Column(Integer)
            
            # Career offensive totals
            career_passing_yards = Column(Integer)
            career_passing_touchdowns = Column(Integer)
            career_passing_attempts = Column(Integer)
            career_passing_completions = Column(Integer)
            career_passing_interceptions = Column(Integer)
            
            career_rushing_yards = Column(Integer)
            career_rushing_touchdowns = Column(Integer)
            career_rushing_attempts = Column(Integer)
            
            career_receiving_yards = Column(Integer)
            career_receiving_touchdowns = Column(Integer)
            career_receptions = Column(Integer)
            
            # Career defensive totals
            career_sacks = Column(Float)
            career_tackles = Column(Integer)
            career_interceptions = Column(Integer)
            career_forced_fumbles = Column(Integer)
            
            # Career special teams totals
            career_field_goals_made = Column(Integer)
            career_field_goals_attempted = Column(Integer)
            career_extra_points_made = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="career_stats")
        
        return NFLCareerStats
    
    def _create_nba_stats_model(self, base):
        """Create NBA-specific stats model."""
        class NBAPlayerStats(base):
            __tablename__ = 'nba_player_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nba_players.id'), index=True)
            season = Column(String, index=True)
            game_date = Column(String, index=True)
            
            # Common stats
            games_played = Column(Integer)
            games_started = Column(Integer)
            minutes_played = Column(Float)
            
            # Scoring stats
            points = Column(Integer)
            field_goals_made = Column(Integer)
            field_goals_attempted = Column(Integer)
            field_goal_percentage = Column(Float)
            three_pointers_made = Column(Integer)
            three_pointers_attempted = Column(Integer)
            three_point_percentage = Column(Float)
            free_throws_made = Column(Integer)
            free_throws_attempted = Column(Integer)
            free_throw_percentage = Column(Float)
            
            # Other stats
            rebounds = Column(Integer)
            offensive_rebounds = Column(Integer)
            defensive_rebounds = Column(Integer)
            assists = Column(Integer)
            steals = Column(Integer)
            blocks = Column(Integer)
            turnovers = Column(Integer)
            personal_fouls = Column(Integer)
            
            # Advanced stats
            plus_minus = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="stats")
            
            # Indexes
            __table_args__ = (
                Index('idx_nba_player_season', 'player_id', 'season'),
                Index('idx_nba_season_date', 'season', 'game_date'),
            )
        
        return NBAPlayerStats
    
    def _create_nba_career_model(self, base):
        """Create NBA-specific career stats model."""
        class NBACareerStats(base):
            __tablename__ = 'nba_career_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nba_players.id'), unique=True, index=True)
            
            # Career totals
            total_games = Column(Integer)
            total_starts = Column(Integer)
            seasons_played = Column(Integer)
            career_minutes = Column(Float)
            
            # Career scoring totals
            career_points = Column(Integer)
            career_field_goals_made = Column(Integer)
            career_field_goals_attempted = Column(Integer)
            career_three_pointers_made = Column(Integer)
            career_three_pointers_attempted = Column(Integer)
            career_free_throws_made = Column(Integer)
            career_free_throws_attempted = Column(Integer)
            
            # Career other stats
            career_rebounds = Column(Integer)
            career_assists = Column(Integer)
            career_steals = Column(Integer)
            career_blocks = Column(Integer)
            career_turnovers = Column(Integer)
            career_personal_fouls = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="career_stats")
        
        return NBACareerStats
    
    def _create_mlb_stats_model(self, base):
        """Create MLB-specific stats model."""
        class MLBPlayerStats(base):
            __tablename__ = 'mlb_player_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('mlb_players.id'), index=True)
            season = Column(String, index=True)
            game_date = Column(String, index=True)
            
            # Common stats
            games_played = Column(Integer)
            games_started = Column(Integer)
            
            # Batting stats
            at_bats = Column(Integer)
            hits = Column(Integer)
            doubles = Column(Integer)
            triples = Column(Integer)
            home_runs = Column(Integer)
            runs_batted_in = Column(Integer)
            runs_scored = Column(Integer)
            stolen_bases = Column(Integer)
            walks = Column(Integer)
            strikeouts_batting = Column(Integer)
            batting_average = Column(Float)
            on_base_percentage = Column(Float)
            slugging_percentage = Column(Float)
            
            # Pitching stats
            innings_pitched = Column(Float)
            wins = Column(Integer)
            losses = Column(Integer)
            saves = Column(Integer)
            earned_runs = Column(Integer)
            earned_run_average = Column(Float)
            strikeouts_pitching = Column(Integer)
            walks_allowed = Column(Integer)
            hits_allowed = Column(Integer)
            home_runs_allowed = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="stats")
            
            # Indexes
            __table_args__ = (
                Index('idx_mlb_player_season', 'player_id', 'season'),
                Index('idx_mlb_season_date', 'season', 'game_date'),
            )
        
        return MLBPlayerStats
    
    def _create_mlb_career_model(self, base):
        """Create MLB-specific career stats model."""
        class MLBCareerStats(base):
            __tablename__ = 'mlb_career_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('mlb_players.id'), unique=True, index=True)
            
            # Career totals
            total_games = Column(Integer)
            seasons_played = Column(Integer)
            
            # Career batting totals
            career_at_bats = Column(Integer)
            career_hits = Column(Integer)
            career_home_runs = Column(Integer)
            career_runs_batted_in = Column(Integer)
            career_runs_scored = Column(Integer)
            career_stolen_bases = Column(Integer)
            
            # Career pitching totals
            career_innings_pitched = Column(Float)
            career_wins = Column(Integer)
            career_losses = Column(Integer)
            career_saves = Column(Integer)
            career_strikeouts = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="career_stats")
        
        return MLBCareerStats
    
    def _create_nhl_stats_model(self, base):
        """Create NHL-specific stats model."""
        class NHLPlayerStats(base):
            __tablename__ = 'nhl_player_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nhl_players.id'), index=True)
            season = Column(String, index=True)
            game_date = Column(String, index=True)
            
            # Common stats
            games_played = Column(Integer)
            
            # Scoring stats
            goals = Column(Integer)
            assists = Column(Integer)
            points = Column(Integer)
            plus_minus = Column(Integer)
            penalty_minutes = Column(Integer)
            
            # Shooting stats
            shots_on_goal = Column(Integer)
            shooting_percentage = Column(Float)
            
            # Time stats
            time_on_ice = Column(String)
            power_play_time = Column(String)
            short_handed_time = Column(String)
            
            # Goalie stats (for goalies)
            saves = Column(Integer)
            goals_against = Column(Integer)
            save_percentage = Column(Float)
            goals_against_average = Column(Float)
            shutouts = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="stats")
            
            # Indexes
            __table_args__ = (
                Index('idx_nhl_player_season', 'player_id', 'season'),
                Index('idx_nhl_season_date', 'season', 'game_date'),
            )
        
        return NHLPlayerStats
    
    def _create_nhl_career_model(self, base):
        """Create NHL-specific career stats model."""
        class NHLCareerStats(base):
            __tablename__ = 'nhl_career_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey('nhl_players.id'), unique=True, index=True)
            
            # Career totals
            total_games = Column(Integer)
            seasons_played = Column(Integer)
            
            # Career scoring totals
            career_goals = Column(Integer)
            career_assists = Column(Integer)
            career_points = Column(Integer)
            career_penalty_minutes = Column(Integer)
            career_shots_on_goal = Column(Integer)
            
            # Career goalie totals
            career_saves = Column(Integer)
            career_goals_against = Column(Integer)
            career_shutouts = Column(Integer)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="career_stats")
        
        return NHLCareerStats
    
    def _create_generic_stats_model(self, base, sport):
        """Create generic stats model for new sports."""
        class GenericPlayerStats(base):
            __tablename__ = f'{sport.lower()}_player_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey(f'{sport.lower()}_players.id'), index=True)
            season = Column(String, index=True)
            
            # Basic stats that most sports have
            games_played = Column(Integer)
            games_started = Column(Integer)
            
            # Generic stat columns (can be used flexibly)
            stat_1 = Column(Integer)  # Main scoring stat
            stat_2 = Column(Integer)  # Secondary stat
            stat_3 = Column(Integer)  # Third stat
            stat_4 = Column(Float)    # Percentage/ratio stat
            stat_5 = Column(Float)    # Another percentage/ratio stat
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="stats")
            
            # Indexes
            __table_args__ = (
                Index(f'idx_{sport.lower()}_player_season', 'player_id', 'season'),
            )
        
        return GenericPlayerStats
    
    def _create_generic_career_model(self, base, sport):
        """Create generic career stats model for new sports."""
        class GenericCareerStats(base):
            __tablename__ = f'{sport.lower()}_career_stats'
            
            id = Column(Integer, primary_key=True)
            player_id = Column(Integer, ForeignKey(f'{sport.lower()}_players.id'), unique=True, index=True)
            
            # Career totals
            total_games = Column(Integer)
            seasons_played = Column(Integer)
            
            # Generic career stat columns
            career_stat_1 = Column(Integer)
            career_stat_2 = Column(Integer)
            career_stat_3 = Column(Integer)
            career_stat_4 = Column(Float)
            career_stat_5 = Column(Float)
            
            created_at = Column(DateTime, default=datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            
            # Relationships
            # player = relationship("Player", back_populates="career_stats")
        
        return GenericCareerStats
    
    def get_session(self, sport: str):
        """Get database session for a specific sport."""
        Session = self.sessions.get(sport.upper())
        return Session() if Session else None
    
    def get_models(self, sport: str):
        """Get models for a specific sport."""
        return self.models.get(sport.upper())
    
    def get_engine(self, sport: str):
        """Get database engine for a specific sport."""
        return self.engines.get(sport.upper())
    
    def get_available_sports(self):
        """Get list of available sports with database connections."""
        return list(self.engines.keys())
    
    def update_career_stats(self, sport: str, player_id: int):
        """Update career stats for a player in a specific sport."""
        session = self.get_session(sport)
        models = self.get_models(sport)
        
        if not session or not models:
            return
        
        try:
            # Get all season stats for the player
            season_stats = session.query(models['PlayerStats']).filter_by(player_id=player_id).all()
            
            if not season_stats:
                return
            
            # Calculate career totals based on sport
            config = sport_config_manager.get_config(sport)
            career_totals = self._calculate_career_totals(season_stats, config)
            
            # Add common totals
            career_totals.update({
                'total_games': sum(getattr(s, 'games_played', 0) or 0 for s in season_stats),
                'seasons_played': len(set(getattr(s, 'season', '') for s in season_stats)),
            })
            
            # Update or create career stats
            career_stats = session.query(models['CareerStats']).filter_by(player_id=player_id).first()
            if career_stats:
                for key, value in career_totals.items():
                    if hasattr(career_stats, key):
                        setattr(career_stats, key, value)
            else:
                career_stats = models['CareerStats'](player_id=player_id, **career_totals)
                session.add(career_stats)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _calculate_career_totals(self, season_stats, config):
        """Calculate career totals based on sport configuration."""
        career_totals = {}
        
        if not config or not config.stat_mappings:
            return career_totals
        
        # Sum up all the stats based on the sport's configuration
        for stat_name, stat_mapping in config.stat_mappings.items():
            if stat_mapping.aggregatable:
                db_column = stat_mapping.db_column
                career_column = f"career_{db_column}"
                
                total = sum(getattr(s, db_column, 0) or 0 for s in season_stats)
                career_totals[career_column] = total
        
        return career_totals

# Global instance
sport_db_manager = SportDatabaseManager() 