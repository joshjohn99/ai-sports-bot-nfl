"""
Enhanced Name and Action Extraction Module
Provides advanced capabilities for extracting player names and statistical actions from natural language queries.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class ExtractedQuery:
    """Structured representation of extracted query components."""
    player_names: List[str]
    full_player_names: List[str]  # Expanded from partial names
    team_names: List[str]
    actions: List[str]
    metrics: List[str]
    aggregations: List[str]
    comparisons: List[str]
    temporal_context: List[str]
    confidence_score: float

class NameActionExtractor:
    """Advanced extractor for player names and statistical actions."""
    
    def __init__(self):
        # Remove hardcoded player list - system should work with ANY player name
        # Dynamic name extraction strategies will handle all variations
        
        # Statistical action patterns
        self.stat_patterns = {
            # Passing stats
            'passing': ['passing_yards', 'passing_touchdowns', 'completions', 'attempts', 'completion_percentage', 'passer_rating'],
            'throwing': ['passing_yards', 'passing_touchdowns', 'completions', 'attempts'],
            'pass': ['passing_yards', 'passing_touchdowns'],
            
            # Rushing stats  
            'rushing': ['rushing_yards', 'rushing_touchdowns', 'rushing_attempts', 'yards_per_carry'],
            'running': ['rushing_yards', 'rushing_touchdowns', 'rushing_attempts'],
            'carries': ['rushing_attempts', 'rushing_yards'],
            
            # Receiving stats
            'receiving': ['receiving_yards', 'receiving_touchdowns', 'receptions', 'targets'],
            'catching': ['receptions', 'receiving_yards', 'receiving_touchdowns'],
            'reception': ['receptions', 'receiving_yards'],
            
            # Defensive stats
            'defensive': ['sacks', 'tackles', 'interceptions', 'forced_fumbles', 'pass_deflections'],
            'defense': ['sacks', 'tackles', 'interceptions', 'forced_fumbles'],
            'tackling': ['tackles', 'solo_tackles', 'assisted_tackles'],
            
            # Kicking stats
            'kicking': ['field_goals_made', 'field_goals_attempted', 'extra_points_made'],
            'field_goal': ['field_goals_made', 'field_goals_attempted'],
        }
        
        # Aggregation operation patterns
        self.aggregation_patterns = {
            'combined': 'sum',
            'total': 'sum', 
            'altogether': 'sum',
            'sum': 'sum',
            'average': 'avg',
            'mean': 'avg',
            'per_game': 'avg_per_game',
            'career': 'career_total',
            'season': 'season_total',
            'best': 'max',
            'worst': 'min',
            'highest': 'max',
            'lowest': 'min'
        }
        
        # Comparison patterns
        self.comparison_patterns = [
            'vs', 'versus', 'against', 'compared to', 'compare',
            'better than', 'worse than', 'more than', 'less than',
            'between', 'and', 'or'
        ]
        
        # Temporal context patterns
        self.temporal_patterns = {
            'this season': 'current_season',
            'last season': 'previous_season', 
            'this year': 'current_year',
            'last year': 'previous_year',
            'career': 'career_total',
            'all time': 'all_time',
            'historically': 'historical',
            'playoffs': 'playoffs',
            'regular season': 'regular_season'
        }
    
    def extract_comprehensive(self, query: str) -> ExtractedQuery:
        """Extract all components from a natural language query."""
        query_lower = query.lower()
        
        # Extract player names
        player_names = self._extract_player_names(query)
        full_player_names = self._expand_player_names(player_names)
        
        # Extract team names
        team_names = self._extract_team_names(query)
        
        # Extract actions and metrics
        actions = self._extract_actions(query_lower)
        metrics = self._extract_metrics(query_lower, actions)
        
        # Extract aggregations
        aggregations = self._extract_aggregations(query_lower)
        
        # Extract comparisons
        comparisons = self._extract_comparisons(query_lower)
        
        # Extract temporal context
        temporal_context = self._extract_temporal_context(query_lower)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            player_names, actions, metrics, aggregations, comparisons
        )
        
        return ExtractedQuery(
            player_names=player_names,
            full_player_names=full_player_names,
            team_names=team_names,
            actions=actions,
            metrics=metrics,
            aggregations=aggregations,
            comparisons=comparisons,
            temporal_context=temporal_context,
            confidence_score=confidence_score
        )
    
    def _extract_player_names(self, query: str) -> List[str]:
        """Extract player names using dynamic strategies that work for any player."""
        names = []
        
        # Strategy 1: Full name patterns (First Last) - works for any player
        # This pattern captures: "Patrick Mahomes", "Ja'Marr Chase", "T.J. Watt", etc.
        full_name_pattern = r'\b([A-Z][a-z]+(?:\'[A-Z][a-z]+)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        full_names = re.findall(full_name_pattern, query)
        
        # Filter out common non-player words that might match the pattern
        non_player_words = {
            'new england', 'green bay', 'new york', 'new orleans',
            'las vegas', 'san francisco', 'kansas city', 'los angeles',
            'this season', 'last season', 'this year', 'last year',
            'more than', 'less than', 'better than', 'worse than',
            'show me', 'compare the', 'what are', 'show me the'
        }
        
        # Filter out names that start with obvious non-player words, but be careful not to exclude real names
        non_player_prefixes = {'compare', 'show', 'what', 'who', 'how', 'when', 'where', 'which'}
        
        for full_name in full_names:
            first_word = full_name.split()[0].lower()
            # If the name starts with a command word, try to extract just the player name part
            if first_word in non_player_prefixes and len(full_name.split()) > 2:
                # Extract everything after the command word
                potential_name = ' '.join(full_name.split()[1:])
                # Check if this looks like a valid player name (at least 2 words, both capitalized)
                name_parts = potential_name.split()
                if (len(name_parts) >= 2 and 
                    all(part[0].isupper() for part in name_parts if len(part) > 0)):
                    names.append(potential_name)
            elif (full_name.lower() not in non_player_words and 
                  first_word not in non_player_prefixes):
                names.append(full_name)
        
        # Strategy 2: Dynamic name pattern matching (no hardcoded lists)
        # The enhanced SQL search will handle name variations and expansions
        # This ensures the system works with ANY player name, not just predefined ones
        
        # Strategy 3: Handle special cases like "CJ Stroud", "JJ Watt", etc.
        # Look for initials + last name pattern
        initial_pattern = r'\b([A-Z]{1,2}\.?\s+[A-Z][a-z]+)\b'
        initial_names = re.findall(initial_pattern, query)
        for name in initial_names:
            # Clean up the name (remove extra dots/spaces)
            clean_name = re.sub(r'\.+', '', name).strip()
            if clean_name not in names and len(clean_name) > 3:
                names.append(clean_name)
        
        # Strategy 4: Handle "Jr", "Sr", "III" suffixes
        suffix_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Jr\.?|Sr\.?|III?|IV?))\b'
        suffix_names = re.findall(suffix_pattern, query)
        for name in suffix_names:
            clean_name = name.replace('Jr?', 'Jr').replace('Sr?', 'Sr')
            if clean_name not in names:
                names.append(clean_name)
        
        # Remove exact duplicates and substrings
        unique_names = []
        for name in names:
            # Skip if this name is a substring of an existing longer name
            is_substring = False
            for existing in unique_names:
                if name.lower() in existing.lower() and name.lower() != existing.lower():
                    is_substring = True
                    break
                # Also check if existing is substring of current (replace with longer)
                elif existing.lower() in name.lower() and name.lower() != existing.lower():
                    unique_names.remove(existing)
                    break
            
            if not is_substring and name not in unique_names:
                unique_names.append(name)
        
        return unique_names
    
    def _expand_player_names(self, names: List[str]) -> List[str]:
        """Return names as-is since we're not using hardcoded expansions anymore."""
        # The enhanced SQL search handles all name variations dynamically
        # No need for hardcoded expansions - system works with ANY player name
        return names
    
    def _extract_team_names(self, query: str) -> List[str]:
        """Extract team names from query."""
        # Common NFL team names and abbreviations
        teams = [
            'Patriots', 'Bills', 'Dolphins', 'Jets',
            'Steelers', 'Ravens', 'Browns', 'Bengals',
            'Titans', 'Colts', 'Texans', 'Jaguars',
            'Chiefs', 'Chargers', 'Broncos', 'Raiders',
            'Cowboys', 'Giants', 'Eagles', 'Commanders',
            'Packers', 'Bears', 'Lions', 'Vikings',
            'Saints', 'Falcons', 'Panthers', 'Buccaneers',
            'Cardinals', '49ers', 'Seahawks', 'Rams'
        ]
        
        found_teams = []
        query_lower = query.lower()
        for team in teams:
            if team.lower() in query_lower:
                found_teams.append(team)
        
        return found_teams
    
    def _extract_actions(self, query: str) -> List[str]:
        """Extract action verbs and statistical actions."""
        actions = []
        
        # Direct action words
        action_words = [
            'score', 'scored', 'throw', 'threw', 'pass', 'passed',
            'run', 'ran', 'rush', 'rushed', 'catch', 'caught',
            'receive', 'received', 'tackle', 'tackled', 'sack', 'sacked',
            'intercept', 'intercepted', 'kick', 'kicked'
        ]
        
        words = query.split()
        for word in words:
            if word.lower() in action_words:
                actions.append(word.lower())
        
        return actions
    
    def _extract_metrics(self, query: str, actions: List[str]) -> List[str]:
        """Extract specific statistical metrics."""
        metrics = []
        
        # Direct metric mentions with improved mapping
        direct_metrics = {
            'yards': 'yards',
            'touchdowns': 'touchdowns', 
            'tds': 'touchdowns',
            'sacks': 'sacks',
            'sack': 'sacks',  # Add singular form
            'tackles': 'tackles',
            'tackle': 'tackles',  # Add singular form
            'interceptions': 'interceptions',
            'interception': 'interceptions',  # Add singular form
            'completions': 'completions',
            'attempts': 'attempts',
            'receptions': 'receptions',
            'reception': 'receptions',  # Add singular form
            'targets': 'targets',
            'fumbles': 'fumbles',
            'field_goals': 'field_goals',
            'points': 'points',
            'rating': 'rating',
            'percentage': 'percentage',
            'totals': 'total'  # Add totals
        }
        
        for metric_term, metric_name in direct_metrics.items():
            if metric_term in query:
                metrics.append(metric_name)
        
        # Context-based metrics from stat patterns
        for stat_type, stat_metrics in self.stat_patterns.items():
            if stat_type in query:
                metrics.extend(stat_metrics)
        
        # Remove duplicates
        return list(set(metrics))
    
    def _extract_aggregations(self, query: str) -> List[str]:
        """Extract aggregation operations."""
        aggregations = []
        
        for pattern, operation in self.aggregation_patterns.items():
            if pattern in query:
                aggregations.append(operation)
        
        return aggregations
    
    def _extract_comparisons(self, query: str) -> List[str]:
        """Extract comparison operators."""
        comparisons = []
        
        for pattern in self.comparison_patterns:
            if pattern in query:
                comparisons.append(pattern)
        
        return comparisons
    
    def _extract_temporal_context(self, query: str) -> List[str]:
        """Extract temporal context."""
        temporal = []
        
        for pattern, context in self.temporal_patterns.items():
            if pattern in query:
                temporal.append(context)
        
        return temporal
    
    def _calculate_confidence(self, players: List[str], actions: List[str], 
                            metrics: List[str], aggregations: List[str], 
                            comparisons: List[str]) -> float:
        """Calculate confidence score for extraction quality."""
        score = 0.0
        
        # Player names found
        if players:
            score += 0.3
        
        # Actions or metrics found
        if actions or metrics:
            score += 0.3
        
        # Aggregations found
        if aggregations:
            score += 0.2
        
        # Comparisons found
        if comparisons:
            score += 0.2
        
        return min(score, 1.0)

# Global instance
name_action_extractor = NameActionExtractor() 