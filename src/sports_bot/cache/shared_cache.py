"""
Shared Sports Cache - Singleton pattern for multi-user efficiency
Prevents API explosion by sharing cache across all user sessions.
"""

import time
import threading
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class SharedSportsCache:
    """
    Singleton cache shared across ALL users and sessions.
    Prevents API explosion when multiple users query same players.
    
    Benefits:
    - 100 users asking for "Micah Parsons" = 1 API call total (instead of 100)
    - Memory efficient: Single cache instance
    - Thread-safe: Multiple users can access concurrently
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize cache data structures."""
        self.player_cache = {}       # "sport:player_name" -> player_info
        self.stats_cache = {}        # "sport:player_id:year:metrics" -> stats_data
        self.team_list_cache = {}    # "sport" -> teams_data
        self.roster_cache = {}       # "sport:team_id" -> roster_data
        
        # TTL tracking
        self.cache_timestamps = {}   # cache_key -> timestamp
        self.ttl_config = {
            'player_ids': 24 * 3600,     # 24 hours (players don't change teams often)
            'team_rosters': 6 * 3600,    # 6 hours (roster changes during season)
            'player_stats': 1 * 3600,    # 1 hour (stats update during games)
            'team_lists': 24 * 3600,     # 24 hours (rarely changes)
        }
        
        # Stats tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls_saved = 0
        
        print("[SHARED CACHE] Initialized global sports cache - all users will benefit!")
    
    def _is_expired(self, cache_key: str, cache_type: str) -> bool:
        """Check if cache entry is expired based on TTL."""
        if cache_key not in self.cache_timestamps:
            return True
        
        timestamp = self.cache_timestamps[cache_key]
        ttl = self.ttl_config.get(cache_type, 3600)  # Default 1 hour
        
        return (time.time() - timestamp) > ttl
    
    def _set_timestamp(self, cache_key: str):
        """Record timestamp for TTL tracking."""
        self.cache_timestamps[cache_key] = time.time()
    
    # Player ID Cache Methods
    def get_player(self, sport: str, player_name: str) -> Optional[Dict[str, Any]]:
        """Get cached player information."""
        cache_key = f"{sport}:{player_name.lower()}"
        
        if cache_key in self.player_cache and not self._is_expired(cache_key, 'player_ids'):
            self.cache_hits += 1
            self.api_calls_saved += 16  # Estimated: saves ~16 team roster calls
            print(f"[CACHE HIT] Player '{player_name}' found - saved ~16 API calls!")
            return self.player_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def set_player(self, sport: str, player_name: str, player_data: Dict[str, Any]):
        """Cache player information."""
        cache_key = f"{sport}:{player_name.lower()}"
        self.player_cache[cache_key] = player_data
        self._set_timestamp(cache_key)
        print(f"[CACHE STORE] Cached player '{player_name}' - future users will benefit!")
    
    # Stats Cache Methods  
    def get_stats(self, sport: str, player_id: str, year: str, metrics: list) -> Optional[Dict[str, Any]]:
        """Get cached player stats."""
        metrics_key = ":".join(sorted(metrics)) if metrics else "all"
        cache_key = f"{sport}:stats:{player_id}:{year}:{metrics_key}"
        
        if cache_key in self.stats_cache and not self._is_expired(cache_key, 'player_stats'):
            self.cache_hits += 1
            self.api_calls_saved += 1
            print(f"[CACHE HIT] Stats for player {player_id} found - saved 1 API call!")
            return self.stats_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def set_stats(self, sport: str, player_id: str, year: str, metrics: list, stats_data: Dict[str, Any]):
        """Cache player stats."""
        metrics_key = ":".join(sorted(metrics)) if metrics else "all"
        cache_key = f"{sport}:stats:{player_id}:{year}:{metrics_key}"
        self.stats_cache[cache_key] = stats_data
        self._set_timestamp(cache_key)
        print(f"[CACHE STORE] Cached stats for player {player_id}")
    
    # Team Cache Methods
    def get_team_list(self, sport: str) -> Optional[list]:
        """Get cached team list."""
        cache_key = f"{sport}:teams"
        
        if cache_key in self.team_list_cache and not self._is_expired(cache_key, 'team_lists'):
            self.cache_hits += 1
            self.api_calls_saved += 1
            print(f"[CACHE HIT] Teams list for {sport} found - saved 1 API call!")
            return self.team_list_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def set_team_list(self, sport: str, teams_data: list):
        """Cache team list."""
        cache_key = f"{sport}:teams"
        self.team_list_cache[cache_key] = teams_data
        self._set_timestamp(cache_key)
        print(f"[CACHE STORE] Cached teams list for {sport}")
    
    def get_roster(self, sport: str, team_id: str) -> Optional[Dict[str, Any]]:
        """Get cached team roster."""
        cache_key = f"{sport}:roster:{team_id}"
        
        if cache_key in self.roster_cache and not self._is_expired(cache_key, 'team_rosters'):
            self.cache_hits += 1
            self.api_calls_saved += 1
            print(f"[CACHE HIT] Roster for team {team_id} found - saved 1 API call!")
            return self.roster_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def set_roster(self, sport: str, team_id: str, roster_data: Dict[str, Any]):
        """Cache team roster."""
        cache_key = f"{sport}:roster:{team_id}"
        self.roster_cache[cache_key] = roster_data
        self._set_timestamp(cache_key)
        print(f"[CACHE STORE] Cached roster for team {team_id}")
    
    # Cache Management
    def clear_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, timestamp in self.cache_timestamps.items():
            # Determine cache type from key pattern
            if ':stats:' in cache_key:
                cache_type = 'player_stats'
            elif ':roster:' in cache_key:
                cache_type = 'team_rosters'
            elif ':teams' in cache_key:
                cache_type = 'team_lists'
            else:
                cache_type = 'player_ids'
            
            ttl = self.ttl_config.get(cache_type, 3600)
            if (current_time - timestamp) > ttl:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        if expired_keys:
            print(f"[CACHE CLEANUP] Removed {len(expired_keys)} expired entries")
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry from appropriate cache."""
        if cache_key in self.cache_timestamps:
            del self.cache_timestamps[cache_key]
        
        if cache_key in self.player_cache:
            del self.player_cache[cache_key]
        elif cache_key in self.stats_cache:
            del self.stats_cache[cache_key]
        elif cache_key in self.team_list_cache:
            del self.team_list_cache[cache_key]
        elif cache_key in self.roster_cache:
            del self.roster_cache[cache_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percentage': round(hit_rate, 1),
            'api_calls_saved': self.api_calls_saved,
            'cached_players': len(self.player_cache),
            'cached_stats': len(self.stats_cache),
            'cached_teams': len(self.team_list_cache),
            'cached_rosters': len(self.roster_cache)
        }
    
    def reset_stats(self):
        """Reset cache statistics."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls_saved = 0
        print("[CACHE] Statistics reset")
    
    def clear_all(self):
        """Clear entire cache (useful for testing)."""
        self.player_cache.clear()
        self.stats_cache.clear()
        self.team_list_cache.clear()
        self.roster_cache.clear()
        self.cache_timestamps.clear()
        self.reset_stats()
        print("[CACHE] All cache data cleared")


# Global cache instance - singleton ensures all users share the same cache
sports_cache = SharedSportsCache()


def get_cache_instance() -> SharedSportsCache:
    """Get the global shared cache instance."""
    return sports_cache 