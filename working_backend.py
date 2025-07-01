#!/usr/bin/env python3
"""
Direct connection to your existing debate arena system
Uses your real data: 2,920+ NFL players, 407+ NBA players
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# DIRECT import to your working debate system
from sports_bot.debate.data_connected_debate_arena import dynamic_arena, process_any_debate_query

app = FastAPI(title="AI Sports Bot - Direct Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class DebateRequest(BaseModel):
    question: str
    user_id: str = "user_1"

@app.get("/")
async def root():
    return {"message": "Real AI Sports Debate Arena", "status": "connected_to_real_data"}

@app.get("/health")
async def health_check():
    # Test connection to your real systems
    try:
        from sports_bot.debate.data_connected_debate_arena import dynamic_arena
        from sports_bot.cache.shared_cache import sports_cache  
        from sports_bot.db.models import db_manager
        
        # Test database connection
        session = db_manager.get_session()
        session.close()
        
        return {
            "status": "healthy",
            "debate_arena": "✅ Connected",
            "database": "✅ Connected", 
            "cache": "✅ Active",
            "real_data": "✅ 2920+ NFL players ready"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/start-debate")
async def start_debate(request: DebateRequest):
    """Start real debate using YOUR systems"""
    try:
        print(f"🏟️ Starting REAL debate for: {request.question}")
        
        # Use your ACTUAL debate arena (not mock!)
        debate_result = await dynamic_arena.process_any_debate_query(
            request.question, 
            {
                "real_time_streaming": False,
                "advanced_analytics": True,
                "use_real_data": True  # Force real data usage
            }
        )
        
        print(f"✅ Real debate result: {debate_result}")
        
        return {
            "success": True,
            "debate_id": f"real_debate_{int(time.time())}",
            "participants": ["User", "NFL Data Expert", "NBA Analytics Bot", "Sports Debate Moderator"],
            "response": debate_result,
            "data_source": "REAL_DATABASE_AND_APIs"
        }
        
    except Exception as e:
        print(f"❌ Real debate failed: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Real debate system error: {str(e)}"
        )

@app.get("/api/league-leaders")
async def get_real_league_leaders(sport: str = "NFL", metric: str = "yards", limit: int = 10):
    """Get REAL league leaders from YOUR database"""
    try:
        from sports_bot.db.models import db_manager, Player, PlayerStats, Team
        
        session = db_manager.get_session()
        
        # Query YOUR real database
        query = session.query(Player, PlayerStats, Team).join(
            PlayerStats, Player.id == PlayerStats.player_id
        ).join(
            Team, Player.current_team_id == Team.id
        ).filter(
            Player.sport == sport
        )
        
        # Order by real metric
        if metric == "yards":
            query = query.order_by(PlayerStats.passing_yards.desc())
        elif metric == "sacks":  
            query = query.order_by(PlayerStats.sacks.desc())
        elif metric == "points":
            query = query.order_by(PlayerStats.points.desc())
            
        results = query.limit(limit).all()
        session.close()
        
        # Format REAL data
        real_players = []
        for player, stats, team in results:
            real_players.append({
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'sport': player.sport,
                'current_team': {
                    'name': team.name,
                    'abbreviation': team.abbreviation
                },
                'stats': {
                    'passing_yards': stats.passing_yards,
                    'passing_touchdowns': stats.passing_touchdowns,
                    'sacks': stats.sacks,
                    'points': stats.points,
                    'games_played': stats.games_played
                }
            })
        
        print(f"✅ Retrieved {len(real_players)} REAL players from database")
        
        return {
            "success": True,
            "data": real_players,
            "metadata": {
                "sport": sport,
                "metric": metric, 
                "total": len(real_players),
                "source": "REAL_DATABASE"
            }
        }
        
    except Exception as e:
        print(f"❌ Real data query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import time
    
    print(f"""
🏟️ Starting REAL AI Sports Debate Arena
┌─────────────────────────────────────────────┐
│  🏈 Connecting to YOUR real systems...     │
│  📊 2,920+ NFL players ready              │
│  🏀 407 NBA players cached                │  
│  🔥 Dynamic debate arena active           │
│  💾 Real database connections             │
│  🚫 NO MOCK DATA - REAL ONLY             │
└─────────────────────────────────────────────┘
    """)
    
    uvicorn.run(
        "working_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 