#!/usr/bin/env python3
"""
FastAPI Server for AI Sports Bot
Serves the frontend bridge endpoints and connects to existing backend systems
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import your existing systems - FIXED IMPORT
from sports_bot.api.frontend_bridge import router as frontend_router
from sports_bot.commercial.gateway import EnhancedCommercialGateway
from sports_bot.commercial.circuit_breaker import CircuitBreakerManager
from sports_bot.cache.shared_cache import SharedSportsCache  # ✅ FIXED
from sports_bot.db.models import db_manager

# Global variables for system components
circuit_breaker_manager = None
commercial_gateway = None
shared_cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global circuit_breaker_manager, commercial_gateway, shared_cache
    
    print("🚀 Starting AI Sports Bot FastAPI Server...")
    
    # Initialize system components
    try:
        # Initialize database
        db_manager.init_db()
        print("✅ Database initialized")
        
        # Initialize cache
        shared_cache = SharedSportsCache()  # ✅ FIXED
        print("✅ Cache system initialized")
        
        # Initialize circuit breakers
        circuit_breaker_manager = CircuitBreakerManager()
        print("✅ Circuit breaker system initialized")
        
        # Initialize commercial gateway
        commercial_gateway = EnhancedCommercialGateway()
        print("✅ Enhanced commercial gateway initialized")
        
        print("🎉 All systems initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing systems: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # Cleanup
    print("🔄 Shutting down AI Sports Bot FastAPI Server...")
    print("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI Sports Bot API",
    description="Production-ready AI Sports Bot with multi-sport support, commercial features, and real-time data",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative Next.js port
        "https://your-domain.com",  # Production domain
        "https://vercel.app",  # Vercel deployment
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include the frontend bridge router
app.include_router(frontend_router, tags=["Frontend API"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        # Check circuit breaker status
        health_status = await circuit_breaker_manager.health_check() if circuit_breaker_manager else {"overall_health": "unknown"}
        
        # Check database connection
        try:
            session = db_manager.get_session()
            session.close()
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        
        # Check cache
        cache_status = "healthy" if shared_cache else "unavailable"
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "systems": {
                "database": db_status,
                "cache": cache_status,
                "circuit_breakers": health_status["overall_health"],
                "services": health_status.get("services", {})
            },
            "features": {
                "multi_sport_support": True,
                "commercial_features": True,
                "real_time_data": True,
                "caching": True,
                "circuit_breakers": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# System stats endpoint
@app.get("/api/system/stats")
async def get_system_stats():
    """Get system performance statistics"""
    try:
        stats = {}
        
        # Circuit breaker stats
        if circuit_breaker_manager:
            stats["circuit_breakers"] = circuit_breaker_manager.get_all_stats()
        
        # Cache stats (if available)
        if shared_cache:
            stats["cache"] = {
                "status": "active",
                "type": "SharedCache"
            }
        
        # Database stats
        try:
            session = db_manager.get_session()
            from sports_bot.db.models import Player, Team, PlayerStats
            
            stats["database"] = {
                "players": session.query(Player).count(),
                "teams": session.query(Team).count(),
                "player_stats": session.query(PlayerStats).count(),
            }
            session.close()
        except Exception as e:
            stats["database"] = {"error": str(e)}
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

# Commercial gateway endpoints
@app.get("/api/commercial/usage")
async def get_usage_stats():
    """Get commercial usage statistics"""
    try:
        if not commercial_gateway:
            raise HTTPException(status_code=503, detail="Commercial gateway not available")
        
        # This would integrate with your existing commercial system
        return {
            "message": "Commercial features active",
            "features": ["billing", "rate_limiting", "analytics", "monitoring"],
            "status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting usage stats: {str(e)}")

# Root endpoint with API info
@app.get("/")
async def root():
    """API root endpoint with information"""
    return {
        "message": "AI Sports Bot API v2.0.0",
        "description": "Production-ready AI Sports Bot with multi-sport support",
        "features": [
            "Multi-sport data (NFL, NBA, MLB, NHL)",
            "Real-time player statistics", 
            "Enhanced commercial system",
            "Circuit breaker reliability",
            "Shared caching system"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "league_leaders": "/api/league-leaders",
            "system_stats": "/api/system/stats",
            "commercial_usage": "/api/commercial/usage"
        },
        "frontend_integration": {
            "next_js_api": "pages/api/sports/leaders.ts",
            "react_components": "src/sports_bot/components/carousel/SportsCarousel.tsx"
        }
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"""
🚀 Starting AI Sports Bot FastAPI Server
┌─────────────────────────────────────────────┐
│  🏈 Multi-Sport AI Bot API Server v2.0.0   │
│                                             │
│  🌐 Server: http://{host}:{port}             │
│  📚 Docs:   http://{host}:{port}/docs        │
│  🔥 Health: http://{host}:{port}/health      │
│                                             │
│  Features:                                  │
│  ✅ Multi-sport support (NFL/NBA/MLB/NHL)   │
│  ✅ Enhanced commercial system              │
│  ✅ Circuit breaker reliability            │
│  ✅ Real-time caching                      │
│  ✅ Frontend bridge API                    │
│  ✅ Performance monitoring                 │
└─────────────────────────────────────────────┘
    """)
    
    uvicorn.run(
        "fastapi_server:app",
        host=host,
        port=port,
        reload=True,  # Enable hot reload for development
        log_level="info"
    ) 