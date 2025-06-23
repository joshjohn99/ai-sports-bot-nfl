"""
⚡ Rate Limiting System for Commercial AI Sports Debate Arena
Production-grade rate limiting to prevent abuse and ensure fair usage
"""

import time
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Production rate limiting system"""
    
    def __init__(self):
        self.request_counts: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    async def check_rate_limit(self, user_id: str, operation: str) -> Dict[str, Any]:
        """Check if user is within rate limits for operation"""
        current_time = time.time()
        
        # Different limits for different operations
        limits = {
            "debate_start": {"requests": 10, "window": 3600},  # 10 debates per hour
            "api_call": {"requests": 100, "window": 3600},     # 100 API calls per hour
            "dashboard": {"requests": 60, "window": 3600}      # 60 dashboard loads per hour
        }
        
        if operation not in limits:
            return {"allowed": True}
        
        limit_config = limits[operation]
        window_start = current_time - limit_config["window"]
        
        # Clean old requests
        user_requests = self.request_counts[user_id].get(operation, [])
        user_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        # Check if within limits
        if len(user_requests) >= limit_config["requests"]:
            reset_time = datetime.fromtimestamp(user_requests[0] + limit_config["window"])
            return {
                "allowed": False,
                "message": f"Rate limit exceeded for {operation}",
                "reset_time": reset_time.isoformat(),
                "requests_remaining": 0
            }
        
        # Record this request
        user_requests.append(current_time)
        self.request_counts[user_id][operation] = user_requests
        
        return {
            "allowed": True,
            "requests_remaining": limit_config["requests"] - len(user_requests)
        } 