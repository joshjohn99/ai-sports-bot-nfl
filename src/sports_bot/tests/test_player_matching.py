#!/usr/bin/env python3
"""
Test script to demonstrate intelligent player matching functionality.
"""

import sys
import os
sys.path.insert(0, 'src')

from sports_bot.core.stats.stat_retriever import StatRetrieverApiAgent
from sports_bot.db.models import db_manager
from config.api_config import api_config

def test_player_matching():
    """Test the intelligent player matching system."""
    print("🧪 Testing Intelligent Player Matching System")
    print("=" * 50)
    
    # Initialize the stat agent
    stat_agent = StatRetrieverApiAgent(api_config)
    
    # Test 1: Lamar Jackson (should prioritize QB)
    print("\n🏈 Test 1: Finding 'Lamar Jackson'")
    player, confidence, alternatives = stat_agent.find_best_matching_player('Lamar Jackson')
    if player:
        print(f"✅ Selected: {player.name} ({player.position}) - Confidence: {confidence:.2f}")
        print(f"   Team ID: {player.current_team_id}")
        if alternatives:
            print(f"   Found {len(alternatives)} other players with similar names")
    else:
        print("❌ No player found")
    
    # Test 2: Joe Burrow (should be easy to find)
    print("\n🏈 Test 2: Finding 'Joe Burrow'")
    player, confidence, alternatives = stat_agent.find_best_matching_player('Joe Burrow')
    if player:
        print(f"✅ Selected: {player.name} ({player.position}) - Confidence: {confidence:.2f}")
        print(f"   Team ID: {player.current_team_id}")
    else:
        print("❌ No player found")
    
    # Test 3: Mike Williams (common name, should show alternatives)
    print("\n🏈 Test 3: Finding 'Mike Williams'")
    player, confidence, alternatives = stat_agent.find_best_matching_player('Mike Williams')
    if player:
        print(f"✅ Selected: {player.name} ({player.position}) - Confidence: {confidence:.2f}")
        print(f"   Team ID: {player.current_team_id}")
        if alternatives:
            print(f"   Found {len(alternatives)} other Mike Williams:")
            for i, alt in enumerate(alternatives[:3], 1):
                print(f"     {i}. {alt.name} ({alt.position}) - Team: {alt.current_team_id}")
    else:
        print("❌ No player found")
    
    # Test 4: Partial name match
    print("\n🏈 Test 4: Finding 'Patrick Mahomes' (testing partial match)")
    player, confidence, alternatives = stat_agent.find_best_matching_player('Mahomes')
    if player:
        print(f"✅ Selected: {player.name} ({player.position}) - Confidence: {confidence:.2f}")
        print(f"   Team ID: {player.current_team_id}")
    else:
        print("❌ No player found")
    
    print("\n🎯 Player Matching Test Complete!")

if __name__ == "__main__":
    test_player_matching() 