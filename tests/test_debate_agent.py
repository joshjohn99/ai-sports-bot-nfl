"""
Test the NFL debate agent.
"""

import os
import pytest
import asyncio
from sports_bot.agents.debate_agent import DebateAgent, DebateContext

@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        pytest.skip("RAPIDAPI_KEY environment variable not set")
    return key

@pytest.fixture
def agent(api_key):
    """Create debate agent instance."""
    return DebateAgent(api_key=api_key)

@pytest.mark.asyncio
async def test_stats_lookup(agent):
    """Test looking up player statistics."""
    async with agent:
        # Test with Kyler Murray
        stats = await agent.stats_lookup("Kyler Murray")
        assert stats
        assert "error" not in stats
        assert stats["name"] == "Kyler Murray"
        assert stats["team"]["name"] == "Cardinals"

@pytest.mark.asyncio
async def test_player_compare(agent):
    """Test player comparison."""
    async with agent:
        comparison = await agent.player_compare(
            "Kyler Murray",
            "Josh Allen",
            metrics=["completions", "passingYards"]
        )
        assert comparison
        assert "error" not in comparison
        assert comparison["player1"]["name"] == "Kyler Murray"
        assert comparison["player2"]["name"] == "Josh Allen"
        assert "metrics" in comparison

@pytest.mark.asyncio
async def test_context_search(agent):
    """Test context search."""
    async with agent:
        results = await agent.context_search("Cardinals")
        assert results
        assert len(results["teams"]) > 0

@pytest.mark.asyncio
async def test_generate_debate(agent):
    """Test debate generation."""
    async with agent:
        context = DebateContext(
            query="Compare Kyler Murray and Josh Allen's passing performance",
            player_names=["Kyler Murray", "Josh Allen"],
            metrics=["completions", "passingYards", "passingTouchdowns"]
        )
        debate = await agent.generate_debate(context)
        assert debate
        assert len(debate["players"]) > 0
        assert len(debate["comparisons"]) > 0

@pytest.mark.asyncio
async def test_player_not_found(agent):
    """Test handling of non-existent player."""
    async with agent:
        stats = await agent.stats_lookup("NonExistent Player")
        assert stats
        assert "error" in stats

@pytest.mark.asyncio
async def test_team_search(agent):
    """Test team search."""
    async with agent:
        results = await agent.context_search("Arizona")
        assert results
        assert len(results["teams"]) > 0
        assert any("Arizona" in team["fullName"] for team in results["teams"])

@pytest.mark.asyncio
async def test_multi_player_debate(agent):
    """Test debate generation with multiple players."""
    async with agent:
        context = DebateContext(
            query="Compare the Cardinals' quarterbacks",
            player_names=["Kyler Murray", "Jacoby Brissett"],
            team_names=["Arizona Cardinals"],
            metrics=["completions", "passingYards"]
        )
        debate = await agent.generate_debate(context)
        assert debate
        assert len(debate["players"]) > 0
        assert len(debate["teams"]) > 0
        assert len(debate["comparisons"]) > 0

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__])) 