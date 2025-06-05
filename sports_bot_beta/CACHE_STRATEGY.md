# Scalable Cache Strategy for Multi-User Sports Bot

## 🚨 Current Problem
- **Per-user caching**: Each user gets own StatRetrieverApiAgent instance
- **Memory explosion**: 100 users = 100x memory usage
- **Redundant API calls**: Same player data fetched multiple times
- **No persistence**: Server restart = lost cache

## 🎯 Solution: Shared Global Cache

### Architecture: 3-Tier Caching Strategy

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   L1: Memory    │    │   L2: Redis     │    │   L3: Database  │
│   (Ultra Fast)  │───▶│   (Fast+Shared) │───▶│   (Persistent)  │
│   TTL: 5 min    │    │   TTL: 1 hour   │    │   TTL: 24 hours │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Phase 1: Shared Memory Cache (Quick Win)
```python
# Global shared cache - all users benefit
class GlobalSportsCache:
    _instance = None
    _cache = {}
    _timestamps = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Phase 2: Redis Cache (Production Ready)
```python
# Distributed cache for multiple servers
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

# Cache keys with namespacing
player_key = f"nfl:player:{player_name.lower()}"
stats_key = f"nfl:stats:{player_id}:{year}"
```

### Phase 3: Database Cache (Enterprise)
```sql
-- Persistent cache with metadata
CREATE TABLE player_cache (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(10),
    player_name VARCHAR(100),
    player_id VARCHAR(20),
    team_name VARCHAR(50),
    cached_at TIMESTAMP,
    ttl_expires_at TIMESTAMP,
    data JSONB
);

CREATE INDEX idx_player_cache_lookup ON player_cache(sport, player_name);
```

## 🚀 Implementation Plan

### Immediate: Singleton Pattern Cache
```python
class SharedSportsCache:
    """Shared cache across all user sessions - prevents API explosion"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.player_cache = {}
            cls._instance.stats_cache = {}
            cls._instance.team_cache = None
        return cls._instance
    
    def get_player(self, sport, player_name):
        key = f"{sport}:{player_name.lower()}"
        return self.player_cache.get(key)
    
    def set_player(self, sport, player_name, data):
        key = f"{sport}:{player_name.lower()}"
        self.player_cache[key] = data
```

### Production: Redis with TTL
```python
import redis
import json
from datetime import timedelta

class RedisSportsCache:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def get_player(self, sport, player_name):
        key = f"sports:{sport}:player:{player_name.lower()}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def set_player(self, sport, player_name, data, ttl_hours=24):
        key = f"sports:{sport}:player:{player_name.lower()}"
        self.redis.setex(key, timedelta(hours=ttl_hours), json.dumps(data))
```

## 📊 Expected Performance Improvements

| Scenario | Without Cache | With Global Cache | Improvement |
|----------|---------------|-------------------|-------------|
| **1 User, 2 Players** | 34 calls | 34 calls | 0% (first time) |
| **1 User, 2 Players (repeat)** | 34 calls | 2 calls | **94% reduction** |
| **100 Users, Same 2 Players** | 3,400 calls | 34 calls | **99% reduction** |
| **100 Users, 10 Unique Players** | 17,000 calls | 340 calls | **98% reduction** |

## 🛡️ Cache Invalidation Strategy

### TTL (Time-To-Live) Policies:
- **Player IDs**: 24 hours (players don't change teams often)
- **Team Rosters**: 6 hours (roster changes during season)
- **Player Stats**: 1 hour (stats update frequently during games)
- **All Teams List**: 24 hours (rarely changes)

### Smart Invalidation:
```python
# Invalidate cache during NFL trade deadline, free agency
INVALIDATION_PERIODS = {
    'nfl': [
        ('2024-03-11', '2024-03-20'),  # Free agency
        ('2024-08-27', '2024-11-05'),  # Trade deadline
    ]
}
```

## 🔧 Implementation Steps

### Step 1: Quick Fix (30 minutes)
1. ✅ Create singleton cache class
2. ✅ Replace per-instance cache with shared cache
3. ✅ Test with multiple "users" (concurrent requests)

### Step 2: Production Ready (2 hours)
1. 🔄 Add Redis dependency
2. 🔄 Implement Redis cache layer
3. 🔄 Add TTL and invalidation logic
4. 🔄 Monitor cache hit/miss rates

### Step 3: Enterprise (1 day)
1. 🔄 Database cache layer
2. 🔄 Cache warming strategies
3. 🔄 Monitoring and analytics
4. 🔄 Cache cluster for high availability

## 💡 Additional Optimizations

### Batch API Calls
```python
# Instead of 2 separate calls for 2 players:
GET /player/4361423/stats
GET /player/4262921/stats

# Use batch endpoint (if available):
POST /players/stats
{"player_ids": ["4361423", "4262921"], "year": 2024}
```

### Predictive Caching
```python
# When user asks about "Micah Parsons", also cache:
# - His teammates (likely next questions)
# - Popular comparison players (T.J. Watt, Aaron Donald)
# - His historical stats (2021, 2022, 2023)
```

### Cache Warming
```python
# Pre-populate cache with popular players
POPULAR_PLAYERS = [
    "Patrick Mahomes", "Josh Allen", "Lamar Jackson",
    "Micah Parsons", "T.J. Watt", "Aaron Donald",
    "Justin Jefferson", "Tyreek Hill", "Davante Adams"
]
```

## 🎯 Immediate Next Steps
1. Implement shared singleton cache (quick win)
2. Add TTL to prevent stale data
3. Test with concurrent users
4. Monitor API call reduction
5. Plan Redis deployment 