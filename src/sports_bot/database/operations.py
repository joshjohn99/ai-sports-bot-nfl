"""
Database operations and utilities.
"""

import os
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from .models import Base, Player, Team, PlayerStats, CareerStats
from ..utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: Optional[str] = None):
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
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
    
    def safe_commit(self, session: Session):
        """Safely commit database changes."""
        try:
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database commit failed: {str(e)}")
            session.rollback()
            raise
    
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
            
            self.safe_commit(session)
            
        except Exception as e:
            logger.error(f"Failed to update career stats for player {player_id}: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get a player by name."""
        session = self.get_session()
        try:
            return session.query(Player).filter(Player.name.ilike(f"%{name}%")).first()
        finally:
            session.close()
    
    def get_player_stats(self, player_id: int, season: str) -> Optional[PlayerStats]:
        """Get player stats for a specific season."""
        session = self.get_session()
        try:
            return session.query(PlayerStats).filter_by(
                player_id=player_id,
                season=season
            ).first()
        finally:
            session.close()
    
    def get_career_stats(self, player_id: int) -> Optional[CareerStats]:
        """Get career stats for a player."""
        session = self.get_session()
        try:
            return session.query(CareerStats).filter_by(player_id=player_id).first()
        finally:
            session.close()
    
    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Get a team by name."""
        session = self.get_session()
        try:
            return session.query(Team).filter(
                (Team.name.ilike(f"%{name}%")) |
                (Team.display_name.ilike(f"%{name}%")) |
                (Team.abbreviation.ilike(f"%{name}%"))
            ).first()
        finally:
            session.close()
    
    def get_team_roster(self, team_id: int) -> List[Player]:
        """Get all players on a team's roster."""
        session = self.get_session()
        try:
            return session.query(Player).filter_by(current_team_id=team_id).all()
        finally:
            session.close()

# Create a global instance
db_manager = DatabaseManager() 