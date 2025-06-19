"""
Database models and configuration for the sports bot.
Uses SQLAlchemy for ORM and SQLite for storage.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Index, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# Create base class for declarative models
Base = declarative_base()

class Player(Base):
    """Player model storing basic player information."""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)  # ID from external API
    name = Column(String, index=True)
    position = Column(String, index=True)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    players = relationship("Player", back_populates="current_team")

class PlayerStats(Base):
    """Player statistics for a specific season."""
    __tablename__ = 'player_stats'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), index=True)
    season = Column(String, index=True)
    
    # Common stats (add more as needed)
    games_played = Column(Integer)
    games_started = Column(Integer)
    
    # Offensive stats
    passing_yards = Column(Integer)
    passing_touchdowns = Column(Integer)
    rushing_yards = Column(Integer)
    rushing_touchdowns = Column(Integer)
    receiving_yards = Column(Integer)
    receptions = Column(Integer)
    receiving_touchdowns = Column(Integer)
    
    # Defensive stats
    sacks = Column(Float)
    tackles = Column(Integer)
    interceptions = Column(Integer)
    forced_fumbles = Column(Integer)
    
    # Special teams
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    extra_points_made = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="stats")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_player_season', 'player_id', 'season'),
    )

class CareerStats(Base):
    """Aggregated career statistics for a player."""
    __tablename__ = 'career_stats'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), unique=True, index=True)
    
    # Career totals
    total_games = Column(Integer)
    total_starts = Column(Integer)
    seasons_played = Column(Integer)
    
    # Offensive career totals
    career_passing_yards = Column(Integer)
    career_passing_touchdowns = Column(Integer)
    career_rushing_yards = Column(Integer)
    career_rushing_touchdowns = Column(Integer)
    career_receiving_yards = Column(Integer)
    career_receptions = Column(Integer)
    career_receiving_touchdowns = Column(Integer)
    
    # Defensive career totals
    career_sacks = Column(Float)
    career_tackles = Column(Integer)
    career_interceptions = Column(Integer)
    career_forced_fumbles = Column(Integer)
    
    # Special teams career totals
    career_field_goals_made = Column(Integer)
    career_field_goals_attempted = Column(Integer)
    career_extra_points_made = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="career_stats")

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path=None):
        if not db_path:
            # Default to a SQLite database in the project's data directory
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'sports_stats.db')
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine and session factory
        self.engine = create_engine(f'sqlite:///{db_path}')
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
            # Get all season stats for the player
            season_stats = session.query(PlayerStats).filter_by(player_id=player_id).all()
            
            if not season_stats:
                return
            
            # Calculate career totals
            career_totals = {
                'total_games': sum(s.games_played or 0 for s in season_stats),
                'total_starts': sum(s.games_started or 0 for s in season_stats),
                'seasons_played': len(set(s.season for s in season_stats)),
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

# Create a global instance
db_manager = DatabaseManager() 