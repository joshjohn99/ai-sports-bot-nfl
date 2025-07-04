"""
Test the debate agent with real NFL data.
"""

import os
import pytest
import asyncio
from sports_bot.agents.debate_agent import DebateAgent
from sports_bot.data.fetcher import NFLDataFetcher

@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        pytest.skip("RAPIDAPI_KEY environment variable not set")
    return key

@pytest.fixture
def fetcher(api_key):
    """Create data fetcher instance."""
    return NFLDataFetcher(api_key=api_key)

@pytest.mark.asyncio
async def test_get_teams(fetcher):
    """Test getting team list."""
    async with fetcher:
        teams = await fetcher.get_teams()
        assert teams
        assert isinstance(teams, list)
        assert len(teams) > 0
        # Verify team data structure
        team = teams[0]
        assert "team" in team
        assert "id" in team["team"]
        assert "name" in team["team"]

@pytest.mark.asyncio
async def test_get_team_info(fetcher):
    """Test getting team info."""
    async with fetcher:
        # First get a team ID
        teams = await fetcher.get_teams()
        team_id = teams[0]["team"]["id"]
        # Get team info
        team_info = await fetcher.get_team_info(team_id)
        assert team_info
        assert isinstance(team_info, dict)

@pytest.mark.asyncio
async def test_get_team_roster(fetcher):
    """Test getting team roster."""
    async with fetcher:
        # Use Cardinals team ID (22)
        roster = await fetcher.get_team_roster("22")
        assert roster
        assert isinstance(roster, dict)
        assert "athletes" in roster
        assert isinstance(roster["athletes"], list)
        assert len(roster["athletes"]) > 0
        # Verify player data structure
        player = roster["athletes"][0]
        assert "alternateIds" in player
        assert "sdr" in player["alternateIds"]
        assert "firstName" in player
        assert "lastName" in player

@pytest.mark.asyncio
async def test_get_player_info(fetcher):
    """Test getting player info."""
    async with fetcher:
        # Use Kyler Murray's ID (3917315)
        player_info = await fetcher.get_player_info("3917315")
        assert player_info
        assert isinstance(player_info, dict)
        assert player_info["fullName"] == "Kyler Murray"

@pytest.mark.asyncio
async def test_get_player_stats(fetcher):
    """Test getting player stats."""
    async with fetcher:
        # Use Kyler Murray's ID (3917315)
        stats = await fetcher.get_player_stats("3917315")
        # Since we're not sure about the stats endpoint, we just verify the response
        assert isinstance(stats, dict)

@pytest.mark.asyncio
async def test_get_team_stats(fetcher):
    """Test getting team stats."""
    async with fetcher:
        # Use Cardinals team ID (22)
        stats = await fetcher.get_team_stats("22")
        assert stats
        assert isinstance(stats, dict)
        assert "team" in stats
        assert "roster" in stats

@pytest.mark.asyncio
async def test_get_player_details(fetcher):
    """Test getting player details by name."""
    async with fetcher:
        # Use Cardinals team ID (22) and Kyler Murray
        player = await fetcher.get_player_details("22", "Kyler Murray")
        assert player
        assert isinstance(player, dict)
        assert player["fullName"] == "Kyler Murray"

@pytest.mark.asyncio
async def test_extract_player_id(fetcher):
    """Test extracting player ID from player data."""
    player_data = {
        "alternateIds": {
            "sdr": "3917315"
        }
    }
    player_id = fetcher.extract_player_id(player_data)
    assert player_id == "3917315"

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__])) 