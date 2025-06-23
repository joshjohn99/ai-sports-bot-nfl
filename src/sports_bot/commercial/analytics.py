"""
📊 Analytics System for Commercial AI Sports Debate Arena
Production-grade analytics for business intelligence and user behavior tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json

class DebateAnalytics:
    """Production analytics system for business intelligence"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.user_sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    async def record_debate_start(self, user_id: str, debate_id: str, topic: str):
        """Record debate start event"""
        event = {
            "event_type": "debate_start",
            "user_id": user_id,
            "debate_id": debate_id,
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "topic_category": self._categorize_topic(topic),
                "topic_length": len(topic.split())
            }
        }
        
        self.events.append(event)
        self.user_sessions[user_id].append(event)
    
    async def record_debate_completion(self, user_id: str, debate_id: str, compute_time: float):
        """Record debate completion event"""
        event = {
            "event_type": "debate_completion",
            "user_id": user_id,
            "debate_id": debate_id,
            "timestamp": datetime.utcnow().isoformat(),
            "compute_time": compute_time,
            "metadata": {
                "session_duration": compute_time,
                "performance_tier": self._categorize_performance(compute_time)
            }
        }
        
        self.events.append(event)
        self.user_sessions[user_id].append(event)
    
    async def record_tier_upgrade(self, user_id: str, old_tier: str, new_tier: str):
        """Record tier upgrade event"""
        event = {
            "event_type": "tier_upgrade",
            "user_id": user_id,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "upgrade_path": f"{old_tier}->{new_tier}",
                "revenue_impact": self._calculate_revenue_impact(old_tier, new_tier)
            }
        }
        
        self.events.append(event)
        self.user_sessions[user_id].append(event)
    
    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        total_debates = len([e for e in self.events if e["event_type"] == "debate_start"])
        completed_debates = len([e for e in self.events if e["event_type"] == "debate_completion"])
        
        # Topic analytics
        topic_categories = defaultdict(int)
        for event in self.events:
            if event["event_type"] == "debate_start":
                category = event["metadata"]["topic_category"]
                topic_categories[category] += 1
        
        # Performance analytics
        compute_times = [e["compute_time"] for e in self.events if e["event_type"] == "debate_completion"]
        avg_compute_time = sum(compute_times) / len(compute_times) if compute_times else 0
        
        return {
            "total_debates_started": total_debates,
            "total_debates_completed": completed_debates,
            "completion_rate": (completed_debates / total_debates * 100) if total_debates > 0 else 0,
            "avg_compute_time_seconds": avg_compute_time,
            "popular_topic_categories": dict(topic_categories),
            "active_users_last_7_days": self._get_active_users(7),
            "active_users_last_30_days": self._get_active_users(30)
        }
    
    async def get_user_behavior_insights(self) -> Dict[str, Any]:
        """Get user behavior insights for product optimization"""
        user_patterns = {}
        
        for user_id, sessions in self.user_sessions.items():
            debate_count = len([s for s in sessions if s["event_type"] == "debate_start"])
            completion_count = len([s for s in sessions if s["event_type"] == "debate_completion"])
            
            user_patterns[user_id] = {
                "total_debates": debate_count,
                "completion_rate": (completion_count / debate_count * 100) if debate_count > 0 else 0,
                "avg_session_length": self._calculate_avg_session_length(sessions),
                "engagement_score": self._calculate_engagement_score(sessions)
            }
        
        return {
            "user_patterns": user_patterns,
            "high_engagement_users": [
                uid for uid, pattern in user_patterns.items() 
                if pattern["engagement_score"] > 0.8
            ],
            "at_risk_users": [
                uid for uid, pattern in user_patterns.items()
                if pattern["completion_rate"] < 50 and pattern["total_debates"] > 2
            ]
        }
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize debate topic"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["nfl", "football", "quarterback", "touchdown"]):
            return "NFL"
        elif any(word in topic_lower for word in ["nba", "basketball", "dunk", "three-pointer"]):
            return "NBA"
        elif any(word in topic_lower for word in ["mlb", "baseball", "home run", "pitcher"]):
            return "MLB"
        elif any(word in topic_lower for word in ["comparison", "vs", "versus", "better"]):
            return "Player Comparison"
        else:
            return "General Sports"
    
    def _categorize_performance(self, compute_time: float) -> str:
        """Categorize performance based on compute time"""
        if compute_time < 5:
            return "fast"
        elif compute_time < 15:
            return "medium"
        else:
            return "slow"
    
    def _calculate_revenue_impact(self, old_tier: str, new_tier: str) -> float:
        """Calculate revenue impact of tier upgrade"""
        tier_prices = {
            "free": 0.00,
            "basic": 29.99,
            "premium": 99.99,
            "enterprise": 499.99
        }
        
        old_price = tier_prices.get(old_tier, 0)
        new_price = tier_prices.get(new_tier, 0)
        
        return new_price - old_price
    
    def _get_active_users(self, days: int) -> int:
        """Get count of active users in last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        active_users = set()
        for event in self.events:
            event_date = datetime.fromisoformat(event["timestamp"])
            if event_date >= cutoff_date:
                active_users.add(event["user_id"])
        
        return len(active_users)
    
    def _calculate_avg_session_length(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate average session length for user"""
        completion_events = [s for s in sessions if s["event_type"] == "debate_completion"]
        if not completion_events:
            return 0.0
        
        total_time = sum(e["compute_time"] for e in completion_events)
        return total_time / len(completion_events)
    
    def _calculate_engagement_score(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate user engagement score (0-1)"""
        if not sessions:
            return 0.0
        
        # Factors: frequency, completion rate, session length
        debate_count = len([s for s in sessions if s["event_type"] == "debate_start"])
        completion_count = len([s for s in sessions if s["event_type"] == "debate_completion"])
        
        if debate_count == 0:
            return 0.0
        
        completion_rate = completion_count / debate_count
        frequency_score = min(debate_count / 10, 1.0)  # Normalize to 0-1
        
        return (completion_rate * 0.6 + frequency_score * 0.4) 