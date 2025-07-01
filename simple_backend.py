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
async def get_league_leaders(sport: str = "NFL", metric: str = "yards", limit: int = 10):
    """Simple mock data for testing"""
    sample_players = [
        {
            'id': 1,
            'external_id': '1',
            'name': 'Patrick Mahomes',
            'position': 'QB',
            'sport': 'NFL',
            'current_team': {
                'id': 1,
                'name': 'Kansas City Chiefs',
                'display_name': 'Chiefs',
                'abbreviation': 'KC'
            },
            'stats': {
                'passing_yards': 4183,
                'passing_touchdowns': 27,
                'games_played': 17
            }
        },
        {
            'id': 2,
            'external_id': '2', 
            'name': 'Josh Allen',
            'position': 'QB',
            'sport': 'NFL',
            'current_team': {
                'id': 2,
                'name': 'Buffalo Bills',
                'display_name': 'Bills',
                'abbreviation': 'BUF'
            },
            'stats': {
                'passing_yards': 4306,
                'passing_touchdowns': 29,
                'games_played': 17
            }
        }
    ]
    
    return {
        'players': sample_players[:limit],
        'total': len(sample_players),
        'metadata': {
            'sport': sport,
            'metric': metric
        }
    }

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