from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from ..core.stats.stat_retriever import StatRetrieverApiAgent
from ..commercial.gateway import EnhancedCommercialGateway
from ..cache.shared_cache import SharedSportsCache

router = APIRouter()

@router.get("/api/league-leaders")
async def get_league_leaders(
    sport: str = Query("NFL", description="Sport type"),
    metric: str = Query("yards", description="Stat metric to rank by"),
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    limit: int = Query(10, description="Number of results"),
    season: Optional[str] = Query(None, description="Season year")
):
    try:
        # Your existing real data systems
        stat_retriever = StatRetrieverApiAgent()
        results = await stat_retriever.get_league_leaders(
            sport=sport, metric=metric, position=position, 
            team=team, limit=limit, season=season
        )
        
        return {
            "success": True,
            "data": results,
            "metadata": {"sport": sport, "metric": metric}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/start-debate")
async def start_debate(request: dict):
    try:
        gateway = EnhancedCommercialGateway()
        
        # Extract user info and topic
        user_id = request.get("user_id", "demo_user")
        topic = request.get("topic", "")
        
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        # Stream the debate response
        responses = []
        async for response in gateway.start_commercial_debate(user_id, topic):
            responses.append(response)
        
        return {"success": True, "responses": responses}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 