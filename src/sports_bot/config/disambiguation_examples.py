"""
Real-world examples of player disambiguation scenarios that the system can handle.
"""

from .player_disambiguation import disambiguator

# Example disambiguation scenarios
DISAMBIGUATION_EXAMPLES = {
    "lamar_jackson_example": {
        "description": "Multiple Lamar Jacksons - QB vs CB",
        "candidates": [
            {
                "id": "3043078",
                "name": "Lamar Jackson",
                "position": {"abbreviation": "QB"},
                "team": {"abbreviation": "BAL"},
                "active": True
            },
            {
                "id": "9876543",
                "name": "Lamar Jackson",
                "position": {"abbreviation": "CB"},
                "team": {"abbreviation": "NYJ"},
                "active": True
            }
        ],
        "test_cases": [
            {
                "query": "Lamar Jackson passing yards",
                "stat_context": ["passing yards"],
                "expected_position": "QB",
                "reasoning": "Passing yards is QB-specific stat"
            },
            {
                "query": "Lamar Jackson interceptions",
                "stat_context": ["interceptions"],
                "expected_position": "QB",  # Still QB due to position priority
                "reasoning": "Both can have interceptions, but QB is higher priority"
            },
            {
                "query": "Ravens Lamar Jackson",
                "team_context": "BAL",
                "expected_position": "QB",
                "reasoning": "Team context disambiguation"
            }
        ]
    },
    
    "michael_jordan_example": {
        "description": "Michael Jordan - Basketball vs Baseball",
        "candidates": [
            {
                "id": "jordan_nba",
                "name": "Michael Jordan",
                "position": {"abbreviation": "SG"},
                "team": {"abbreviation": "CHI"},
                "sport": "NBA",
                "active": False
            },
            {
                "id": "jordan_mlb",
                "name": "Michael Jordan",
                "position": {"abbreviation": "OF"},
                "team": {"abbreviation": "BIR"},
                "sport": "MLB",
                "active": False
            }
        ],
        "test_cases": [
            {
                "query": "Michael Jordan points",
                "stat_context": ["points"],
                "sport": "NBA",
                "expected_sport": "NBA",
                "reasoning": "Points stat in NBA context"
            },
            {
                "query": "Michael Jordan batting average",
                "stat_context": ["batting_average"],
                "sport": "MLB",
                "expected_sport": "MLB",
                "reasoning": "Baseball-specific stat"
            }
        ]
    },
    
    "common_names_example": {
        "description": "Very common names with multiple players",
        "candidates": [
            {
                "id": "smith_qb",
                "name": "John Smith",
                "position": {"abbreviation": "QB"},
                "team": {"abbreviation": "KC"},
                "active": True
            },
            {
                "id": "smith_lb",
                "name": "John Smith",
                "position": {"abbreviation": "LB"},
                "team": {"abbreviation": "DEN"},
                "active": True
            },
            {
                "id": "smith_wr",
                "name": "John Smith",
                "position": {"abbreviation": "WR"},
                "team": {"abbreviation": "LAC"},
                "active": False
            }
        ],
        "test_cases": [
            {
                "query": "John Smith touchdowns",
                "stat_context": ["touchdowns"],
                "expected_position": "QB",
                "reasoning": "QB has highest priority for touchdown stats"
            },
            {
                "query": "John Smith tackles",
                "stat_context": ["tackles"],
                "expected_position": "LB",
                "reasoning": "LB is primary position for tackles"
            },
            {
                "query": "Active John Smith",
                "active_filter": True,
                "expected_candidates": 2,
                "reasoning": "Filters out inactive players"
            }
        ]
    },
    
    "nickname_example": {
        "description": "Nickname and alias handling",
        "test_cases": [
            {
                "input": "LJ",
                "possible_expansions": ["Lamar Jackson", "LeBron James"],
                "reasoning": "Common nickname expansion"
            },
            {
                "input": "TB12",
                "possible_expansions": ["Tom Brady"],
                "reasoning": "Number-based nickname"
            },
            {
                "input": "CP3",
                "possible_expansions": ["Chris Paul"],
                "reasoning": "Alphanumeric nickname"
            }
        ]
    }
}

def test_disambiguation_system():
    """Test the disambiguation system with real-world scenarios."""
    print("🧪 Testing Universal Player Disambiguation System\n")
    
    # Test Lamar Jackson scenario
    lamar_example = DISAMBIGUATION_EXAMPLES["lamar_jackson_example"]
    print(f"📝 {lamar_example['description']}")
    
    for test_case in lamar_example["test_cases"]:
        result = disambiguator.disambiguate_players(
            candidates=lamar_example["candidates"],
            sport="NFL",
            stat_context=test_case.get("stat_context"),
            team_context=test_case.get("team_context")
        )
        
        if result:
            actual_position = result["position"]["abbreviation"]
            expected_position = test_case.get("expected_position")
            status = "✅ PASS" if actual_position == expected_position else "❌ FAIL"
            print(f"  {status} Query: '{test_case.get('query', 'N/A')}' → {actual_position} ({test_case['reasoning']})")
        else:
            print(f"  ❌ FAIL Query: '{test_case.get('query', 'N/A')}' → No result")
    
    print("\n" + "="*60)
    
    # Test nickname expansion
    nickname_example = DISAMBIGUATION_EXAMPLES["nickname_example"]
    print(f"📝 {nickname_example['description']}")
    
    for test_case in nickname_example["test_cases"]:
        variations = disambiguator.expand_name_variations(test_case["input"])
        expected = test_case["possible_expansions"]
        
        # Check if any expected expansion is in variations
        found_expected = any(exp in variations for exp in expected)
        status = "✅ PASS" if found_expected else "❌ FAIL"
        print(f"  {status} '{test_case['input']}' → {variations} (Expected: {expected})")
    
    print(f"\n🎯 System supports {len(disambiguator.UNIVERSAL_STAT_MAPPINGS)} different stats")
    print(f"🏟️  System supports {len(disambiguator.POSITION_PRIORITY)} different sports")
    print(f"🔄 System handles {len(disambiguator.NICKNAME_PATTERNS)} nickname patterns")

if __name__ == "__main__":
    test_disambiguation_system() 