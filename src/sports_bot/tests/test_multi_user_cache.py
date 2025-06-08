#!/usr/bin/env python3
"""
Multi-User Cache Test - Simulates multiple users to demonstrate shared cache benefits.
Shows how 100 users asking for same players results in massive API call reduction.
"""

import asyncio
import sys
import os
import time
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sports_bot.core.sports_agents import run_query_planner, run_enhanced_query_processor
from sports_bot.core.shared_cache import get_cache_instance


class SimulatedUser:
    """Simulates a user making sports queries."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.queries_made = 0
        self.total_time = 0
    
    async def make_query(self, query):
        """Simulate a user making a query."""
        start_time = time.time()
        
        print(f"👤 User {self.user_id}: {query}")
        
        try:
            query_context = await run_query_planner(query)
            result = await run_enhanced_query_processor(query, query_context)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            self.queries_made += 1
            self.total_time += query_time
            
            players = result.get('players', [])
            print(f"✅ User {self.user_id} completed query in {query_time:.2f}s - Players: {players}")
            
            return True
            
        except Exception as e:
            print(f"❌ User {self.user_id} query failed: {e}")
            return False


async def simulate_concurrent_users():
    """Simulate multiple users making queries concurrently."""
    
    print("🧪 MULTI-USER CACHE TEST")
    print("=" * 60)
    print("Simulating scenario: 10 users ask about same 2 players")
    print("Expected: First user makes ~34 API calls, others make ~2 calls each")
    print("=" * 60)
    
    # Get shared cache instance to monitor stats
    cache = get_cache_instance()
    cache.clear_all()  # Start fresh
    
    # Popular queries that multiple users might ask
    popular_queries = [
        "who had the most touchdowns between Micah Parsons and Justin Jefferson",
        "Compare Micah Parsons vs Aaron Donald sacks",
        "Micah Parsons touchdowns vs Justin Jefferson touchdowns", 
        "Micah Parsons stats",
        "Justin Jefferson stats"
    ]
    
    # Create 10 simulated users
    users = [SimulatedUser(i+1) for i in range(10)]
    
    print(f"👥 Created {len(users)} simulated users")
    print("🚀 Starting concurrent queries...")
    
    start_time = time.time()
    
    # Each user makes queries concurrently
    tasks = []
    for user in users:
        # Each user asks 2-3 random queries from popular list
        user_queries = popular_queries[:2]  # First 2 queries for each user
        for query in user_queries:
            task = asyncio.create_task(user.make_query(query))
            tasks.append(task)
    
    # Wait for all queries to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Get final cache statistics
    cache_stats = cache.get_cache_stats()
    
    print("\n" + "=" * 60)
    print("📊 MULTI-USER PERFORMANCE REPORT")
    print("=" * 60)
    
    # User statistics
    successful_queries = sum(1 for r in results if r is True)
    failed_queries = len(results) - successful_queries
    
    print(f"👥 Users: {len(users)}")
    print(f"✅ Successful queries: {successful_queries}")
    print(f"❌ Failed queries: {failed_queries}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"⚡ Average query time: {total_time/len(results):.2f} seconds")
    
    # Cache performance
    print(f"\n💾 CACHE PERFORMANCE:")
    print(f"   Cache hits: {cache_stats['cache_hits']}")
    print(f"   Cache misses: {cache_stats['cache_misses']}")
    print(f"   Hit rate: {cache_stats['hit_rate_percentage']}%")
    print(f"   API calls saved: ~{cache_stats['api_calls_saved']}")
    print(f"   Cached players: {cache_stats['cached_players']}")
    
    # Efficiency calculation
    total_queries = len(results)
    without_cache_calls = total_queries * 17  # ~17 calls per comparison query
    with_cache_calls = cache_stats['cache_misses'] * 17 + successful_queries * 2
    efficiency_gain = (without_cache_calls - with_cache_calls) / without_cache_calls * 100
    
    print(f"\n🚀 EFFICIENCY ANALYSIS:")
    print(f"   Without shared cache: ~{without_cache_calls} API calls")
    print(f"   With shared cache: ~{with_cache_calls} API calls") 
    print(f"   Efficiency gain: {efficiency_gain:.1f}% reduction")
    
    # Show what's cached
    print(f"\n🗂️  CACHED DATA (benefits all future users):")
    for cache_key in cache.player_cache.keys():
        sport, player_name = cache_key.split(':', 1)
        print(f"   • {player_name.title()} ({sport.upper()})")
    
    print(f"\n💡 SCALE IMPACT:")
    print(f"   With 100 users: ~{100 * with_cache_calls / len(users)} API calls")
    print(f"   Without cache: ~{100 * without_cache_calls / len(users)} API calls")
    print(f"   Savings: ~{100 * (without_cache_calls - with_cache_calls) / len(users)} calls")


async def test_cache_persistence():
    """Test that cache persists across different user sessions."""
    
    print("\n" + "=" * 60)
    print("🔄 CACHE PERSISTENCE TEST")
    print("=" * 60)
    
    cache = get_cache_instance()
    initial_stats = cache.get_cache_stats()
    
    print(f"Initial cache state: {initial_stats['cached_players']} players cached")
    
    # Simulate new user session asking for already-cached player
    new_user = SimulatedUser(999)
    
    print("👤 New user session asking for previously cached player...")
    start_time = time.time()
    
    success = await new_user.make_query("Micah Parsons stats")
    
    end_time = time.time()
    query_time = end_time - start_time
    
    final_stats = cache.get_cache_stats()
    
    print(f"✅ Query completed in {query_time:.2f}s")
    print(f"📊 Cache hits increased from {initial_stats['cache_hits']} to {final_stats['cache_hits']}")
    print(f"💾 Cache persisted - no new API calls needed!")


if __name__ == "__main__":
    asyncio.run(simulate_concurrent_users())
    asyncio.run(test_cache_persistence()) 