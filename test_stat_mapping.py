#!/usr/bin/env python3
"""
Quick test to verify the stat mapping fix for passing yards
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sports_bot.core.stat_retriever import NFLStatsSchema

def test_stat_mapping():
    """Test that our new stat mappings work correctly."""
    
    print("🧪 Testing NFL Stats Schema Mapping")
    print("=" * 50)
    
    # Test cases that should now work
    test_queries = [
        "passing yards",
        "pass yards", 
        "passing yardage",
        "completions",
        "passing attempts",
        "passer rating",
        "interceptions",
        "rushing yards",
        "receiving yards",
        "touchdowns"
    ]
    
    print("📊 Testing user query mapping:")
    
    for query in test_queries:
        schema_stat = NFLStatsSchema.find_stat_by_user_term(query)
        if schema_stat:
            stat_info = NFLStatsSchema.get_stat_info(schema_stat)
            print(f"✅ '{query}' → '{schema_stat}' ({stat_info.get('display_name', 'N/A')})")
        else:
            print(f"❌ '{query}' → NOT FOUND")
    
    # Test the specific issue: "passing yards"
    print(f"\n🎯 Specific Test - 'passing yards':")
    result = NFLStatsSchema.find_stat_by_user_term("passing yards")
    if result:
        print(f"✅ SUCCESS: 'passing yards' maps to '{result}'")
        info = NFLStatsSchema.get_stat_info(result)
        print(f"   Display name: {info.get('display_name')}")
        print(f"   Description: {info.get('description')}")
        print(f"   User terms: {info.get('user_terms')}")
    else:
        print(f"❌ FAILED: 'passing yards' still not found")
    
    # Show stats count
    print(f"\n📈 Schema Statistics:")
    print(f"   Total stats mapped: {len(NFLStatsSchema.STATS_MAPPING)}")
    print(f"   Categories: {list(NFLStatsSchema.CATEGORIES.keys())}")
    
    # Show passing stats specifically
    passing_stats = NFLStatsSchema.get_stats_by_category('passing')
    print(f"   Passing stats: {len(passing_stats)} → {passing_stats}")

if __name__ == "__main__":
    test_stat_mapping() 