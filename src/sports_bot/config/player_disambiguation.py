"""
Scalable player disambiguation system for multi-sport applications.
Handles name conflicts across all sports with position and context awareness.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

@dataclass
class PlayerCandidate:
    """Represents a potential player match with disambiguation metadata."""
    id: str
    name: str
    position: str
    sport: str
    team: Optional[str] = None
    active: bool = True
    score: float = 0.0
    disambiguation_factors: List[str] = None

class UniversalPlayerDisambiguator:
    """
    Universal player disambiguation system that scales across all sports.
    Uses multiple factors: position context, stat context, team context, and popularity.
    """
    
    # Sport-agnostic stat-to-position mappings
    UNIVERSAL_STAT_MAPPINGS = {
        # Passing stats (primarily QB in football, not applicable in other sports)
        'passing_yards': {'NFL': ['QB'], 'CFL': ['QB']},
        'passing_touchdowns': {'NFL': ['QB'], 'CFL': ['QB']},
        'completions': {'NFL': ['QB'], 'CFL': ['QB']},
        'pass_attempts': {'NFL': ['QB'], 'CFL': ['QB']},
        'quarterback_rating': {'NFL': ['QB'], 'CFL': ['QB']},
        
        # Rushing stats (multiple positions across sports)
        'rushing_yards': {
            'NFL': ['RB', 'QB', 'FB', 'WR'], 
            'CFL': ['RB', 'QB', 'FB', 'WR']
        },
        'rushing_touchdowns': {
            'NFL': ['RB', 'QB', 'FB', 'WR'], 
            'CFL': ['RB', 'QB', 'FB', 'WR']
        },
        'carries': {
            'NFL': ['RB', 'QB', 'FB'], 
            'CFL': ['RB', 'QB', 'FB']
        },
        
        # Receiving stats
        'receiving_yards': {
            'NFL': ['WR', 'TE', 'RB', 'FB'], 
            'CFL': ['WR', 'TE', 'RB', 'FB']
        },
        'receptions': {
            'NFL': ['WR', 'TE', 'RB', 'FB'], 
            'CFL': ['WR', 'TE', 'RB', 'FB']
        },
        'receiving_touchdowns': {
            'NFL': ['WR', 'TE', 'RB', 'FB'], 
            'CFL': ['WR', 'TE', 'RB', 'FB']
        },
        'targets': {
            'NFL': ['WR', 'TE', 'RB'], 
            'CFL': ['WR', 'TE', 'RB']
        },
        
        # Defensive stats
        'sacks': {
            'NFL': ['DE', 'DT', 'LB', 'OLB', 'ILB', 'MLB', 'EDGE', 'DL'], 
            'CFL': ['DE', 'DT', 'LB']
        },
        'tackles': {
            'NFL': ['LB', 'DE', 'DT', 'S', 'CB', 'MLB', 'OLB', 'ILB', 'DL', 'DB'], 
            'CFL': ['LB', 'DE', 'DT', 'S', 'CB', 'DB']
        },
        'interceptions': {
            'NFL': ['CB', 'S', 'LB', 'DB'], 
            'CFL': ['CB', 'S', 'LB', 'DB']
        },
        'forced_fumbles': {
            'NFL': ['LB', 'DE', 'DT', 'CB', 'S', 'DB'], 
            'CFL': ['LB', 'DE', 'DT', 'CB', 'S', 'DB']
        },
        'fumble_recoveries': {
            'NFL': ['LB', 'DE', 'DT', 'CB', 'S', 'DB'], 
            'CFL': ['LB', 'DE', 'DT', 'CB', 'S', 'DB']
        },
        'pass_deflections': {
            'NFL': ['CB', 'S', 'LB', 'DB'], 
            'CFL': ['CB', 'S', 'LB', 'DB']
        },
        
        # Special teams
        'field_goals_made': {
            'NFL': ['K'], 'CFL': ['K']
        },
        'field_goals_attempted': {
            'NFL': ['K'], 'CFL': ['K']
        },
        'extra_points_made': {
            'NFL': ['K'], 'CFL': ['K']
        },
        'punting_yards': {
            'NFL': ['P'], 'CFL': ['P']
        },
        'punt_average': {
            'NFL': ['P'], 'CFL': ['P']
        },
        
        # Basketball stats
        'points': {
            'NBA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F'],
            'WNBA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F'],
            'NCAA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F']
        },
        'rebounds': {
            'NBA': ['PF', 'C', 'SF', 'PG', 'SG', 'F', 'G'],
            'WNBA': ['PF', 'C', 'SF', 'PG', 'SG', 'F', 'G'],
            'NCAA': ['PF', 'C', 'SF', 'PG', 'SG', 'F', 'G']
        },
        'assists': {
            'NBA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F'],
            'WNBA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F'],
            'NCAA': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F']
        },
        'steals': {
            'NBA': ['PG', 'SG', 'SF', 'G', 'F'],
            'WNBA': ['PG', 'SG', 'SF', 'G', 'F'],
            'NCAA': ['PG', 'SG', 'SF', 'G', 'F']
        },
        'blocks': {
            'NBA': ['C', 'PF', 'SF', 'F'],
            'WNBA': ['C', 'PF', 'SF', 'F'],
            'NCAA': ['C', 'PF', 'SF', 'F']
        },
        
        # Baseball stats
        'batting_average': {
            'MLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF'],
            'MiLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF']
        },
        'home_runs': {
            'MLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF'],
            'MiLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF']
        },
        'rbis': {
            'MLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF'],
            'MiLB': ['1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'C', 'DH', 'OF', 'IF']
        },
        'earned_run_average': {
            'MLB': ['SP', 'RP', 'CP', 'P'],
            'MiLB': ['SP', 'RP', 'CP', 'P']
        },
        'strikeouts': {
            'MLB': ['SP', 'RP', 'CP', 'P'],
            'MiLB': ['SP', 'RP', 'CP', 'P']
        },
        'wins': {
            'MLB': ['SP', 'RP', 'P'],
            'MiLB': ['SP', 'RP', 'P']
        },
        'saves': {
            'MLB': ['CP', 'RP', 'P'],
            'MiLB': ['CP', 'RP', 'P']
        },
        
        # Hockey stats
        'goals': {
            'NHL': ['C', 'LW', 'RW', 'F', 'D'],
            'NWHL': ['C', 'LW', 'RW', 'F', 'D']
        },
        'assists': {
            'NHL': ['C', 'LW', 'RW', 'F', 'D'],
            'NWHL': ['C', 'LW', 'RW', 'F', 'D']
        },
        'plus_minus': {
            'NHL': ['C', 'LW', 'RW', 'F', 'D'],
            'NWHL': ['C', 'LW', 'RW', 'F', 'D']
        },
        'penalty_minutes': {
            'NHL': ['C', 'LW', 'RW', 'F', 'D'],
            'NWHL': ['C', 'LW', 'RW', 'F', 'D']
        },
        'shots_on_goal': {
            'NHL': ['C', 'LW', 'RW', 'F', 'D'],
            'NWHL': ['C', 'LW', 'RW', 'F', 'D']
        },
        'save_percentage': {
            'NHL': ['G'],
            'NWHL': ['G']
        },
        'goals_against_average': {
            'NHL': ['G'],
            'NWHL': ['G']
        }
    }
    
    # Position popularity/priority by sport (higher = more likely to be searched)
    POSITION_PRIORITY = {
        'NFL': {
            'QB': 100, 'RB': 90, 'WR': 85, 'TE': 80, 'K': 75,
            'DE': 70, 'LB': 65, 'CB': 60, 'S': 55, 'DT': 50,
            'FB': 45, 'P': 40, 'OL': 30, 'LS': 20
        },
        'NBA': {
            'PG': 100, 'SG': 95, 'SF': 90, 'PF': 85, 'C': 80,
            'G': 75, 'F': 70
        },
        'MLB': {
            'SP': 100, '1B': 95, 'SS': 90, 'CF': 85, '3B': 80,
            'C': 75, 'LF': 70, 'RF': 70, '2B': 65, 'CP': 60,
            'RP': 55, 'DH': 50, 'OF': 45, 'IF': 40, 'P': 35
        },
        'NHL': {
            'C': 100, 'LW': 95, 'RW': 90, 'D': 85, 'G': 80,
            'F': 75
        }
    }
    
    # Common name patterns and aliases
    NICKNAME_PATTERNS = {
        # Common nickname patterns
        r'^([A-Z])\.?[A-Z]\.?\s+(.+)$': r'\2',  # "L.J. Smith" -> "Smith"
        r'^([A-Z][a-z]+)\s+([A-Z])\.?\s+(.+)$': r'\1 \3',  # "Lamar J. Jackson" -> "Lamar Jackson"
        
        # Known aliases (can be expanded)
        'LJ': ['Lamar Jackson', 'LeBron James'],
        'MJ': ['Michael Jordan', 'Michael Jackson'],
        'TB': ['Tom Brady'],
        'AD': ['Anthony Davis'],
        'KD': ['Kevin Durant'],
        'CP3': ['Chris Paul'],
        'PG13': ['Paul George']
    }
    
    def __init__(self):
        self.sport_apis = {}  # Can be populated with different sport API handlers
    
    def disambiguate_players(self, 
                           candidates: List[Dict[str, Any]], 
                           sport: str,
                           stat_context: List[str] = None,
                           team_context: str = None,
                           season_context: str = None) -> Optional[Dict[str, Any]]:
        """
        Disambiguate between multiple player candidates using multiple factors.
        
        Args:
            candidates: List of player dictionaries from API
            sport: Sport code (NFL, NBA, MLB, NHL, etc.)
            stat_context: List of stats being requested
            team_context: Team name/abbreviation if mentioned
            season_context: Season if specified
            
        Returns:
            Best matching player or None
        """
        if not candidates:
            return None
            
        if len(candidates) == 1:
            return candidates[0]
        
        # Convert to PlayerCandidate objects for easier scoring
        player_candidates = []
        for candidate in candidates:
            pc = PlayerCandidate(
                id=str(candidate.get('id', '')),
                name=candidate.get('name', candidate.get('fullName', '')),
                position=candidate.get('position', {}).get('abbreviation', '') if isinstance(candidate.get('position'), dict) else candidate.get('position', ''),
                sport=sport,
                team=candidate.get('team', {}).get('abbreviation', '') if isinstance(candidate.get('team'), dict) else candidate.get('team', ''),
                active=candidate.get('active', True),
                disambiguation_factors=[]
            )
            player_candidates.append(pc)
        
        # Score each candidate
        for candidate in player_candidates:
            candidate.score = self._calculate_disambiguation_score(
                candidate, sport, stat_context, team_context, season_context
            )
        
        # Return highest scoring candidate
        best_candidate = max(player_candidates, key=lambda x: x.score)
        
        # Convert back to dictionary format
        return next(c for c in candidates if str(c.get('id')) == best_candidate.id)
    
    def _calculate_disambiguation_score(self,
                                     candidate: PlayerCandidate,
                                     sport: str,
                                     stat_context: List[str] = None,
                                     team_context: str = None,
                                     season_context: str = None) -> float:
        """Calculate disambiguation score for a player candidate."""
        score = 0.0
        factors = []
        
        # 1. Position-based scoring from stat context
        if stat_context and candidate.position:
            position_score = self._score_position_for_stats(candidate.position, sport, stat_context)
            score += position_score
            if position_score > 0:
                factors.append(f"position_match({position_score})")
        
        # 2. Position popularity/priority
        if candidate.position and sport in self.POSITION_PRIORITY:
            priority_score = self.POSITION_PRIORITY[sport].get(candidate.position.upper(), 0) / 10
            score += priority_score
            factors.append(f"position_priority({priority_score})")
        
        # 3. Team context matching
        if team_context and candidate.team:
            if self._teams_match(team_context, candidate.team):
                score += 50
                factors.append("team_match(50)")
        
        # 4. Active player bonus
        if candidate.active:
            score += 10
            factors.append("active(10)")
        
        # 5. Sport-specific bonuses
        sport_bonus = self._get_sport_specific_bonus(candidate, sport)
        if sport_bonus > 0:
            score += sport_bonus
            factors.append(f"sport_bonus({sport_bonus})")
        
        candidate.disambiguation_factors = factors
        return score
    
    def _score_position_for_stats(self, position: str, sport: str, stats: List[str]) -> float:
        """Score how well a position matches the requested stats."""
        if not stats or not position:
            return 0.0
        
        total_score = 0.0
        position_upper = position.upper()
        
        for stat in stats:
            stat_lower = stat.lower().replace(' ', '_')
            if stat_lower in self.UNIVERSAL_STAT_MAPPINGS:
                sport_positions = self.UNIVERSAL_STAT_MAPPINGS[stat_lower].get(sport.upper(), [])
                if position_upper in sport_positions:
                    # Primary position for this stat
                    total_score += 20
                elif self._is_secondary_position(position_upper, sport_positions, sport):
                    # Secondary position (e.g., QB can have rushing stats)
                    total_score += 5
        
        return total_score
    
    def _is_secondary_position(self, position: str, primary_positions: List[str], sport: str) -> bool:
        """Check if position can reasonably have stats from primary positions."""
        secondary_mappings = {
            'NFL': {
                'QB': ['RB', 'WR'],  # QB can rush and occasionally receive
                'RB': ['WR'],        # RB can receive
                'WR': ['RB'],        # WR can occasionally rush
                'TE': ['WR', 'RB'],  # TE can receive and block
                'FB': ['RB', 'TE']   # FB can rush and receive
            }
        }
        
        if sport in secondary_mappings and position in secondary_mappings[sport]:
            return any(pos in primary_positions for pos in secondary_mappings[sport][position])
        
        return False
    
    def _teams_match(self, context_team: str, player_team: str) -> bool:
        """Check if team contexts match (handles abbreviations and full names)."""
        if not context_team or not player_team:
            return False
        
        # Normalize both team names
        context_norm = context_team.upper().strip()
        player_norm = player_team.upper().strip()
        
        # Direct match
        if context_norm == player_norm:
            return True
        
        # Check if one is contained in the other (for abbreviations)
        if len(context_norm) <= 3 and context_norm in player_norm:
            return True
        if len(player_norm) <= 3 and player_norm in context_norm:
            return True
        
        return False
    
    def _get_sport_specific_bonus(self, candidate: PlayerCandidate, sport: str) -> float:
        """Apply sport-specific disambiguation bonuses."""
        bonus = 0.0
        
        # NFL specific
        if sport.upper() == 'NFL':
            # Prefer skill positions for common names
            if candidate.position.upper() in ['QB', 'RB', 'WR', 'TE']:
                bonus += 5
        
        # NBA specific
        elif sport.upper() == 'NBA':
            # Prefer guards and forwards for common names
            if candidate.position.upper() in ['PG', 'SG', 'SF']:
                bonus += 5
        
        return bonus
    
    def expand_name_variations(self, name: str) -> List[str]:
        """Generate possible name variations and nicknames."""
        variations = [name]
        
        # Check nickname patterns
        for pattern, replacement in self.NICKNAME_PATTERNS.items():
            if isinstance(replacement, str):
                match = re.match(pattern, name)
                if match:
                    variations.append(re.sub(pattern, replacement, name))
            elif isinstance(replacement, list):
                # Direct nickname lookup
                if name.upper() in [n.upper() for n in replacement]:
                    variations.extend(replacement)
        
        # Add common variations
        variations.extend(self._generate_common_variations(name))
        
        return list(set(variations))  # Remove duplicates
    
    def _generate_common_variations(self, name: str) -> List[str]:
        """Generate common name variations (Jr/Sr, initials, etc.)."""
        variations = []
        
        # Remove suffixes
        suffixes = [' Jr.', ' Jr', ' Sr.', ' Sr', ' III', ' II', ' IV']
        for suffix in suffixes:
            if name.endswith(suffix):
                variations.append(name.replace(suffix, ''))
        
        # Add initials
        parts = name.split()
        if len(parts) >= 2:
            # First initial + last name
            variations.append(f"{parts[0][0]}. {' '.join(parts[1:])}")
            # First name + last initial
            variations.append(f"{parts[0]} {parts[-1][0]}.")
        
        return variations

# Global instance
disambiguator = UniversalPlayerDisambiguator() 