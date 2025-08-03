#!/usr/bin/env python3
"""
Simple FastAPI Server for Testing - Minimal version to get started
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Create FastAPI app
app = FastAPI(
    title="AI Sports Bot API - Simple",
    description="Simple test server",
    version="2.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Sports Bot Simple Server is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0-simple"}

@app.get("/api/league-leaders")
async def get_league_leaders(
    sport: str = "NFL", metric: str = "yards", limit: int = 10
):
    """Return league leaders from the real database."""
    try:
        from sports_bot.db.models import db_manager, Player, PlayerStats, Team

        session = db_manager.get_session()
        query = (
            session.query(Player, PlayerStats, Team)
            .join(PlayerStats, Player.id == PlayerStats.player_id)
            .join(Team, Player.current_team_id == Team.id)
            .filter(Player.sport == sport)
        )

        if metric == "yards":
            query = query.order_by(PlayerStats.passing_yards.desc())
        elif metric == "sacks":
            query = query.order_by(PlayerStats.sacks.desc())
        elif metric == "points":
            query = query.order_by(PlayerStats.points.desc())

        results = query.limit(limit).all()
        session.close()

        players = []
        for player, stats, team in results:
            players.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "sport": player.sport,
                "current_team": {
                    "name": team.name,
                    "abbreviation": team.abbreviation,
                },
                "stats": {
                    "passing_yards": stats.passing_yards or 0,
                    "passing_touchdowns": stats.passing_touchdowns or 0,
                    "sacks": float(stats.sacks) if stats.sacks else 0.0,
                    "points": stats.points or 0,
                    "games_played": stats.games_played or 0,
                },
            })

        return {
            "players": players,
            "total": len(players),
            "metadata": {"sport": sport, "metric": metric},
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
🚀 Starting Simple AI Sports Bot Server
┌─────────────────────────────────────────────┐
│  🏈 Simple Test Server v2.0.0              │
│  🌐 Server: http://localhost:{port}         │
│  📚 Docs:   http://localhost:{port}/docs    │
└─────────────────────────────────────────────┘
    """)
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 