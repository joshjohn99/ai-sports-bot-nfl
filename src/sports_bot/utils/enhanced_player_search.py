"""
Enhanced Player Search Module
Advanced SQL logic for finding players with fuzzy matching, name variations, and intelligent disambiguation.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import func, or_, and_
from difflib import SequenceMatcher
import re

class EnhancedPlayerSearch:
    """Advanced player search with sophisticated SQL queries and name matching."""
    
    def __init__(self, session, models, sport_config):
        self.session = session
        self.models = models
        self.sport_config = sport_config
        
        # Common name variations and nicknames
        self.name_variations = {
            # Common NFL player variations
            'cj': ['C.J.', 'CJ', 'C J'],
            'tj': ['T.J.', 'TJ', 'T J'],
            'jj': ['J.J.', 'JJ', 'J J'],
            'dj': ['D.J.', 'DJ', 'D J'],
            'aj': ['A.J.', 'AJ', 'A J'],
            'rj': ['R.J.', 'RJ', 'R J'],
            'jr': ['Jr.', 'Jr', 'Junior'],
            'sr': ['Sr.', 'Sr', 'Senior'],
            'iii': ['III', '3rd', 'Third'],
            'iv': ['IV', '4th', 'Fourth'],
            'v': ['V', '5th', 'Fifth']
        }
        
        # Position-based scoring for disambiguation
        self.position_priority = {
            'QB': 100, 'RB': 90, 'WR': 85, 'TE': 80,
            'OL': 70, 'DL': 75, 'LB': 80, 'CB': 85, 'S': 80,
            'K': 60, 'P': 55, 'LS': 50
        }
    
    def find_players_with_advanced_sql(self, player_name: str, query_context=None) -> List[Tuple[Any, float]]:
        """
        Find players using multiple advanced SQL strategies with confidence scoring.
        Returns list of (player, confidence_score) tuples.
        """
        all_matches = []
        
        # Strategy 1: Exact name match
        exact_matches = self._exact_name_search(player_name)
        all_matches.extend([(p, 1.0) for p in exact_matches])
        
        # Strategy 2: Case-insensitive exact match
        if not exact_matches:
            case_insensitive = self._case_insensitive_search(player_name)
            all_matches.extend([(p, 0.95) for p in case_insensitive])
        
        # Strategy 3: Partial name matching
        if not all_matches:
            partial_matches = self._partial_name_search(player_name)
            all_matches.extend([(p, 0.85) for p in partial_matches])
        
        # Strategy 4: Name variation matching (CJ -> C.J., etc.)
        if not all_matches:
            variation_matches = self._name_variation_search(player_name)
            all_matches.extend([(p, 0.80) for p in variation_matches])
        
        # Strategy 5: Word boundary matching
        if not all_matches:
            word_matches = self._word_boundary_search(player_name)
            all_matches.extend([(p, 0.75) for p in word_matches])
        
        # Strategy 6: Last name only matching
        if not all_matches:
            last_name_matches = self._last_name_search(player_name)
            all_matches.extend([(p, 0.60) for p in last_name_matches])
        
        # Remove duplicates while preserving highest confidence
        unique_matches = {}
        for player, confidence in all_matches:
            if player.id not in unique_matches or confidence > unique_matches[player.id][1]:
                unique_matches[player.id] = (player, confidence)
        
        return list(unique_matches.values())
    
    def _exact_name_search(self, player_name: str) -> List[Any]:
        """SQL: Exact name match."""
        return self.session.query(self.models['Player']).filter(
            self.models['Player'].name == player_name
        ).all()
    
    def _case_insensitive_search(self, player_name: str) -> List[Any]:
        """SQL: Case-insensitive exact match."""
        return self.session.query(self.models['Player']).filter(
            func.lower(self.models['Player'].name) == func.lower(player_name)
        ).all()
    
    def _partial_name_search(self, player_name: str) -> List[Any]:
        """SQL: Partial name matching with ILIKE."""
        return self.session.query(self.models['Player']).filter(
            self.models['Player'].name.ilike(f"%{player_name}%")
        ).all()
    
    def _name_variation_search(self, player_name: str) -> List[Any]:
        """SQL: Search for common name variations using OR conditions."""
        variations = self._generate_name_variations(player_name)
        if not variations:
            return []
        
        # Build OR conditions for all variations
        conditions = []
        for variation in variations:
            conditions.append(self.models['Player'].name.ilike(f"%{variation}%"))
        
        if conditions:
            return self.session.query(self.models['Player']).filter(
                or_(*conditions)
            ).all()
        
        return []
    
    def _word_boundary_search(self, player_name: str) -> List[Any]:
        """SQL: Search using word boundaries for better matching."""
        words = player_name.strip().split()
        if len(words) < 2:
            return []
        
        # Search for players where all words appear as separate words
        conditions = []
        for word in words:
            # Use REGEXP or similar for word boundaries (SQLite compatible)
            conditions.append(
                self.models['Player'].name.ilike(f"% {word} %") |
                self.models['Player'].name.ilike(f"{word} %") |
                self.models['Player'].name.ilike(f"% {word}")
            )
        
        return self.session.query(self.models['Player']).filter(
            and_(*conditions)
        ).all()
    
    def _last_name_search(self, player_name: str) -> List[Any]:
        """SQL: Search by last name only."""
        name_parts = player_name.strip().split()
        if len(name_parts) < 2:
            return []
        
        last_name = name_parts[-1]
        
        return self.session.query(self.models['Player']).filter(
            self.models['Player'].name.ilike(f"% {last_name}") |
            self.models['Player'].name.ilike(f"%{last_name}")
        ).all()
    
    def _generate_name_variations(self, player_name: str) -> List[str]:
        """Generate common variations of a player name."""
        variations = []
        name_lower = player_name.lower()
        
        # Handle common abbreviations
        for abbrev, expansions in self.name_variations.items():
            if abbrev in name_lower:
                for expansion in expansions:
                    # Replace abbreviation with expansion
                    variation = re.sub(
                        r'\b' + re.escape(abbrev) + r'\b', 
                        expansion, 
                        player_name, 
                        flags=re.IGNORECASE
                    )
                    if variation != player_name:
                        variations.append(variation)
            
            # Also try reverse (expansion to abbreviation)
            for expansion in expansions:
                if expansion.lower() in name_lower:
                    variation = re.sub(
                        r'\b' + re.escape(expansion) + r'\b', 
                        abbrev, 
                        player_name, 
                        flags=re.IGNORECASE
                    )
                    if variation != player_name:
                        variations.append(variation)
        
        # Handle punctuation variations
        if '.' in player_name:
            variations.append(player_name.replace('.', ''))
        else:
            # Add dots to potential initials
            words = player_name.split()
            if len(words) >= 2 and len(words[0]) <= 2:
                variations.append(f"{words[0]}. {' '.join(words[1:])}")
        
        return variations
    
    def get_sql_debug_info(self, player_name: str) -> Dict[str, Any]:
        """
        Get detailed SQL debugging information for troubleshooting player searches.
        """
        debug_info = {
            "search_term": player_name,
            "strategies_attempted": [],
            "results_per_strategy": {},
            "generated_variations": self._generate_name_variations(player_name),
            "total_players_in_db": self.session.query(self.models['Player']).count()
        }
        
        # Test each strategy
        strategies = [
            ("exact_match", self._exact_name_search),
            ("case_insensitive", self._case_insensitive_search),
            ("partial_match", self._partial_name_search),
            ("name_variations", self._name_variation_search),
            ("word_boundary", self._word_boundary_search),
            ("last_name", self._last_name_search)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                matches = strategy_func(player_name)
                debug_info["strategies_attempted"].append(strategy_name)
                debug_info["results_per_strategy"][strategy_name] = {
                    "count": len(matches),
                    "players": [{"name": p.name, "position": getattr(p, 'position', 'Unknown')} for p in matches[:5]]
                }
            except Exception as e:
                debug_info["results_per_strategy"][strategy_name] = {"error": str(e)}
        
        return debug_info

# Global instance will be created when needed
enhanced_player_search = None

def get_enhanced_search(session, models, sport_config):
    """Get or create enhanced player search instance."""
    global enhanced_player_search
    enhanced_player_search = EnhancedPlayerSearch(session, models, sport_config)
    return enhanced_player_search 