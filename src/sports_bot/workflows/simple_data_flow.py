"""
🧠 Simplified Data Flow (No Recursion Issues)
LangGraph-powered but with linear flow to avoid recursion
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..agents.sports_agents import QueryContext
from ..cache.shared_cache import get_cache_instance
from ..stats.universal_stat_retriever import UniversalStatRetriever

logger = logging.getLogger(__name__)


class SimpleDataFlow:
    """Simplified data flow without complex routing to avoid recursion"""

    def __init__(self):
        self.stat_retriever = UniversalStatRetriever()
        self.cache = get_cache_instance()

    async def gather_debate_data(
        self, query_context: Dict[str, Any], debate_topic: str
    ) -> Dict[str, Any]:
        """Simple linear data gathering"""

        logger.info(f"🚀 Simple data flow for: {debate_topic}")

        gathered_data = {}
        sport = query_context.get("sport", "NFL")

        # Step 1: Try cache first
        for player_name in query_context.get("player_names", []):
            cached_player = self.cache.get_player(sport, player_name)
            if cached_player:
                player_id = cached_player.get("id", cached_player.get("external_id"))
                if player_id:
                    cached_stats = self.cache.get_stats(
                        sport,
                        str(player_id),
                        "2024",
                        query_context.get("metrics_needed", []),
                    )
                    if cached_stats:
                        gathered_data[f"player_{player_name}"] = cached_stats
                        continue

            # Step 2: Try database if cache miss using real QueryContext
            real_context = QueryContext(
                question=f"Get stats for {player_name}",
                sport=sport,
                player_names=[player_name],
                metrics_needed=query_context.get("metrics_needed", []),
                season_years=query_context.get("season_years", []),
                strategy=query_context.get("strategy", ""),
            )

            player_data = self.stat_retriever.fetch_stats(real_context)
            if player_data and "error" not in player_data:
                gathered_data[f"player_{player_name}"] = player_data

                # Cache the result
                player_id = player_data.get("player_id", "")
                if player_id:
                    self.cache.set_stats(
                        sport,
                        player_id,
                        "2024",
                        query_context.get("metrics_needed", []),
                        player_data,
                    )

        # Handle league leaders
        if query_context.get("strategy") == "leaderboard_query":
            leaders_context = QueryContext(
                question=f"{debate_topic} leaderboard",
                sport=sport,
                player_names=[],
                metrics_needed=query_context.get("metrics_needed", []),
                season_years=query_context.get("season_years", []),
                strategy="leaderboard_query",
            )

            leaders_data = self.stat_retriever.fetch_league_leaders(leaders_context)
            if leaders_data and "error" not in leaders_data:
                gathered_data["league_leaders"] = leaders_data

        # Return result
        return {
            "status": "complete" if gathered_data else "failed",
            "data": gathered_data,
            "metadata": {
                "sources_used": ["cache", "database"],
                "entities_requested": len(query_context.get("player_names", [])),
                "entities_gathered": len(gathered_data),
            },
            "summary": {
                "success_rate": len(gathered_data)
                / max(1, len(query_context.get("player_names", [])))
            },
        }


class SimpleLangGraphConnector:
    """Simple connector without recursion issues"""

    def __init__(self):
        self.data_flow = SimpleDataFlow()

    async def prepare_debate_data(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare data using simple linear flow"""

        print(f"🧠 **Simple Data Flow**: Analyzing '{topic}'")
        result = await self.data_flow.gather_debate_data(context, topic)

        if result["status"] == "complete":
            print(f"✅ **Data Ready**: {len(result['data'])} data sources gathered")
        else:
            print(f"⚠️ **Partial Data**: Some data sources failed")

        return result
