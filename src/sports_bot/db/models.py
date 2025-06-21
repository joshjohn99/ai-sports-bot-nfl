"""
SQLAlchemy models for the sports database.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

from sports_bot.config.db_config import get_db_url, DATABASE_PATH

# Create base class for declarative models
Base = declarative_base()

class Player(Base):
    """Player model storing basic player information."""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)  # ID from external API
    name = Column(String, index=True)
    position = Column(String, index=True)
    sport = Column(String, index=True, default='NFL')  # Added sport column
    current_team_id = Column(Integer, ForeignKey('teams.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_team = relationship("Team", back_populates="players")
    stats = relationship("PlayerStats", back_populates="player")
    career_stats = relationship("CareerStats", back_populates="player")

class Team(Base):
    """Team model storing team information."""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)  # ID from external API
    name = Column(String, index=True)
    display_name = Column(String)
    abbreviation = Column(String)
    sport = Column(String, index=True, default='NFL')  # Added sport column
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    players = relationship("Player", back_populates="current_team")

class PlayerStats(Base):
    """Player statistics for a specific season - sport-agnostic."""
    __tablename__ = 'player_stats'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), index=True)
    season = Column(String, index=True)
    
    # Common stats across all sports
    games_played = Column(Integer)
    games_started = Column(Integer)
    
    # NFL-specific offensive stats
    passing_yards = Column(Integer)
    passing_touchdowns = Column(Integer)
    rushing_yards = Column(Integer)
    rushing_touchdowns = Column(Integer)
    receiving_yards = Column(Integer)
    receptions = Column(Integer)
    receiving_touchdowns = Column(Integer)
    
    # NFL-specific defensive stats
    sacks = Column(Float)
    tackles = Column(Integer)
    interceptions = Column(Integer)
    forced_fumbles = Column(Integer)
    
    # NFL-specific special teams
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    extra_points_made = Column(Integer)
    
    # NBA-specific stats
    points = Column(Integer)
    rebounds = Column(Integer)
    assists = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    turnovers = Column(Integer)
    field_goals_made_basketball = Column(Integer)  # Different from NFL field goals
    field_goals_attempted_basketball = Column(Integer)
    three_pointers_made = Column(Integer)
    three_pointers_attempted = Column(Integer)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    minutes_played = Column(Float)
    personal_fouls = Column(Integer)
    
    # MLB-specific stats (for future expansion)
    batting_average = Column(Float)
    home_runs = Column(Integer)
    runs_batted_in = Column(Integer)
    stolen_bases = Column(Integer)
    earned_run_average = Column(Float)
    wins = Column(Integer)
    losses = Column(Integer)
    saves = Column(Integer)
    strikeouts = Column(Integer)
    
    # NHL-specific stats (for future expansion)
    goals = Column(Integer)
    assists_hockey = Column(Integer)  # Different from basketball assists
    penalty_minutes = Column(Integer)
    plus_minus = Column(Integer)
    shots_on_goal = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="stats")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_player_season', 'player_id', 'season'),
        Index('idx_player_sport', 'player_id'),  # Added for sport queries
    )

class CareerStats(Base):
    """Aggregated career statistics for a player - sport-agnostic."""
    __tablename__ = 'career_stats'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), unique=True, index=True)
    
    # Career totals
    total_games = Column(Integer)
    total_starts = Column(Integer)
    seasons_played = Column(Integer)
    
    # NFL career totals
    career_passing_yards = Column(Integer)
    career_passing_touchdowns = Column(Integer)
    career_rushing_yards = Column(Integer)
    career_rushing_touchdowns = Column(Integer)
    career_receiving_yards = Column(Integer)
    career_receptions = Column(Integer)
    career_receiving_touchdowns = Column(Integer)
    career_sacks = Column(Float)
    career_tackles = Column(Integer)
    career_interceptions = Column(Integer)
    career_forced_fumbles = Column(Integer)
    career_field_goals_made = Column(Integer)
    career_field_goals_attempted = Column(Integer)
    career_extra_points_made = Column(Integer)
    
    # NBA career totals
    career_points = Column(Integer)
    career_rebounds = Column(Integer)
    career_assists = Column(Integer)
    career_steals = Column(Integer)
    career_blocks = Column(Integer)
    career_turnovers = Column(Integer)
    career_three_pointers_made = Column(Integer)
    career_three_pointers_attempted = Column(Integer)
    career_free_throws_made = Column(Integer)
    career_free_throws_attempted = Column(Integer)
    career_minutes_played = Column(Float)
    career_personal_fouls = Column(Integer)
    
    # MLB career totals (for future)
    career_home_runs = Column(Integer)
    career_runs_batted_in = Column(Integer)
    career_stolen_bases = Column(Integer)
    career_wins = Column(Integer)
    career_losses = Column(Integer)
    career_saves = Column(Integer)
    career_strikeouts = Column(Integer)
    
    # NHL career totals (for future)
    career_goals = Column(Integer)
    career_assists_hockey = Column(Integer)
    career_penalty_minutes = Column(Integer)
    career_shots_on_goal = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="career_stats")

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path=None):
        if not db_path:
            # Use the centrally configured database path
            db_path = DATABASE_PATH
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine and session factory
        self.engine = create_engine(get_db_url())
        self.Session = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Initialize the database schema."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def update_career_stats(self, player_id: int):
        """Update career stats for a player by aggregating season stats."""
        session = self.get_session()
        try:
            # Get player to determine sport
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                return
                
            sport = getattr(player, 'sport', 'NFL')  # Default to NFL for existing data
            
            # Get all season stats for the player
            season_stats = session.query(PlayerStats).filter_by(player_id=player_id).all()
            
            if not season_stats:
                return
            
            # Calculate career totals based on sport
            if sport == 'NFL':
                career_totals = self._calculate_nfl_career_totals(season_stats)
            elif sport == 'NBA':
                career_totals = self._calculate_nba_career_totals(season_stats)
            elif sport == 'MLB':
                career_totals = self._calculate_mlb_career_totals(season_stats)
            elif sport == 'NHL':
                career_totals = self._calculate_nhl_career_totals(season_stats)
            else:
                # Default to NFL calculation
                career_totals = self._calculate_nfl_career_totals(season_stats)
            
            # Add common totals
            career_totals.update({
                'total_games': sum(s.games_played or 0 for s in season_stats),
                'total_starts': sum(s.games_started or 0 for s in season_stats),
                'seasons_played': len(set(s.season for s in season_stats)),
            })
            
            # Update or create career stats
            career_stats = session.query(CareerStats).filter_by(player_id=player_id).first()
            if career_stats:
                for key, value in career_totals.items():
                    setattr(career_stats, key, value)
            else:
                career_stats = CareerStats(player_id=player_id, **career_totals)
                session.add(career_stats)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _calculate_nfl_career_totals(self, season_stats):
        """Calculate NFL-specific career totals."""
        return {
            'career_passing_yards': sum(s.passing_yards or 0 for s in season_stats),
            'career_passing_touchdowns': sum(s.passing_touchdowns or 0 for s in season_stats),
            'career_rushing_yards': sum(s.rushing_yards or 0 for s in season_stats),
            'career_rushing_touchdowns': sum(s.rushing_touchdowns or 0 for s in season_stats),
            'career_receiving_yards': sum(s.receiving_yards or 0 for s in season_stats),
            'career_receptions': sum(s.receptions or 0 for s in season_stats),
            'career_receiving_touchdowns': sum(s.receiving_touchdowns or 0 for s in season_stats),
            'career_sacks': sum(s.sacks or 0 for s in season_stats),
            'career_tackles': sum(s.tackles or 0 for s in season_stats),
            'career_interceptions': sum(s.interceptions or 0 for s in season_stats),
            'career_forced_fumbles': sum(s.forced_fumbles or 0 for s in season_stats),
            'career_field_goals_made': sum(s.field_goals_made or 0 for s in season_stats),
            'career_field_goals_attempted': sum(s.field_goals_attempted or 0 for s in season_stats),
            'career_extra_points_made': sum(s.extra_points_made or 0 for s in season_stats),
        }
    
    def _calculate_nba_career_totals(self, season_stats):
        """Calculate NBA-specific career totals."""
        return {
            'career_points': sum(s.points or 0 for s in season_stats),
            'career_rebounds': sum(s.rebounds or 0 for s in season_stats),
            'career_assists': sum(s.assists or 0 for s in season_stats),
            'career_steals': sum(s.steals or 0 for s in season_stats),
            'career_blocks': sum(s.blocks or 0 for s in season_stats),
            'career_turnovers': sum(s.turnovers or 0 for s in season_stats),
            'career_three_pointers_made': sum(s.three_pointers_made or 0 for s in season_stats),
            'career_three_pointers_attempted': sum(s.three_pointers_attempted or 0 for s in season_stats),
            'career_free_throws_made': sum(s.free_throws_made or 0 for s in season_stats),
            'career_free_throws_attempted': sum(s.free_throws_attempted or 0 for s in season_stats),
            'career_minutes_played': sum(s.minutes_played or 0 for s in season_stats),
            'career_personal_fouls': sum(s.personal_fouls or 0 for s in season_stats),
        }
    
    def _calculate_mlb_career_totals(self, season_stats):
        """Calculate MLB-specific career totals."""
        return {
            'career_home_runs': sum(s.home_runs or 0 for s in season_stats),
            'career_runs_batted_in': sum(s.runs_batted_in or 0 for s in season_stats),
            'career_stolen_bases': sum(s.stolen_bases or 0 for s in season_stats),
            'career_wins': sum(s.wins or 0 for s in season_stats),
            'career_losses': sum(s.losses or 0 for s in season_stats),
            'career_saves': sum(s.saves or 0 for s in season_stats),
            'career_strikeouts': sum(s.strikeouts or 0 for s in season_stats),
        }
    
    def _calculate_nhl_career_totals(self, season_stats):
        """Calculate NHL-specific career totals."""
        return {
            'career_goals': sum(s.goals or 0 for s in season_stats),
            'career_assists_hockey': sum(s.assists_hockey or 0 for s in season_stats),
            'career_penalty_minutes': sum(s.penalty_minutes or 0 for s in season_stats),
            'career_shots_on_goal': sum(s.shots_on_goal or 0 for s in season_stats),
        }

# Create a global instance
db_manager = DatabaseManager() 