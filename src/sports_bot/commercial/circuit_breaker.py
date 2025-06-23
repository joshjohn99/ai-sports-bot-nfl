"""
🔌 Circuit Breaker System for Production Reliability
Implements circuit breaker patterns, retry mechanisms, and graceful degradation
"""

import asyncio
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 success_threshold: int = 3,
                 request_timeout: float = 30.0):
        self.failure_threshold = failure_threshold  # Failures before opening
        self.recovery_timeout = recovery_timeout    # Seconds before trying again
        self.success_threshold = success_threshold  # Successes to close circuit
        self.request_timeout = request_timeout      # Timeout for individual requests

class CircuitBreaker:
    """Production-grade circuit breaker with fallback support"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.request_count = 0
        self.response_times: List[float] = []
        
        # Fallback functions
        self.fallback_func: Optional[Callable] = None
        
    async def call(self, func: Callable, *args, fallback_data: Any = None, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if await self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} attempting recovery (HALF_OPEN)")
            else:
                logger.warning(f"Circuit breaker {self.name} is OPEN - using fallback")
                return await self._execute_fallback(fallback_data, *args, **kwargs)
        
        # Execute the function with timeout and error handling
        try:
            start_time = time.time()
            
            # Add timeout to prevent hanging
            result = await asyncio.wait_for(
                func(*args, **kwargs), 
                timeout=self.config.request_timeout
            )
            
            # Record success
            duration = time.time() - start_time
            await self._record_success(duration)
            
            return result
            
        except asyncio.TimeoutError:
            await self._record_failure("Request timeout")
            logger.error(f"Circuit breaker {self.name}: Request timed out after {self.config.request_timeout}s")
            return await self._execute_fallback(fallback_data, *args, **kwargs)
            
        except Exception as e:
            await self._record_failure(str(e))
            logger.error(f"Circuit breaker {self.name}: Function failed with {e}")
            return await self._execute_fallback(fallback_data, *args, **kwargs)
    
    async def _record_success(self, duration: float):
        """Record successful execution"""
        self.request_count += 1
        self.response_times.append(duration)
        
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} recovered (CLOSED)")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _record_failure(self, error: str):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(f"Circuit breaker {self.name} failed during recovery - reopening")
    
    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    async def _execute_fallback(self, fallback_data: Any, *args, **kwargs) -> Any:
        """Execute fallback function or return fallback data"""
        if self.fallback_func:
            try:
                return await self.fallback_func(fallback_data, *args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback function failed for {self.name}: {e}")
        
        # Return fallback data or default error response
        if fallback_data is not None:
            return fallback_data
        
        return {
            "type": "service_unavailable",
            "message": f"Service {self.name} is temporarily unavailable. Please try again later.",
            "fallback": True,
            "retry_after": self.config.recovery_timeout
        }
    
    def set_fallback(self, func: Callable):
        """Set fallback function"""
        self.fallback_func = func
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "request_count": self.request_count,
            "avg_response_time": avg_response_time,
            "last_failure_time": self.last_failure_time,
            "uptime_percentage": ((self.request_count - self.failure_count) / max(1, self.request_count)) * 100
        }

class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
    
    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, config or self.default_config)
        return self.breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}
    
    async def health_check(self) -> Dict[str, Any]:
        """Overall health check of all services"""
        stats = self.get_all_stats()
        
        total_services = len(stats)
        healthy_services = len([s for s in stats.values() if s["state"] == "closed"])
        degraded_services = len([s for s in stats.values() if s["state"] == "half_open"])
        failed_services = len([s for s in stats.values() if s["state"] == "open"])
        
        overall_health = "healthy"
        if failed_services > 0:
            if failed_services >= total_services * 0.5:
                overall_health = "critical"
            else:
                overall_health = "degraded"
        elif degraded_services > 0:
            overall_health = "degraded"
        
        return {
            "overall_health": overall_health,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "failed_services": failed_services,
            "services": stats
        }

# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Pre-configured circuit breakers for common services
DEBATE_CIRCUIT = circuit_manager.get_breaker("debate_arena", CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2,
    request_timeout=45.0
))

BILLING_CIRCUIT = circuit_manager.get_breaker("billing_system", CircuitBreakerConfig(
    failure_threshold=2,
    recovery_timeout=15,
    success_threshold=1,
    request_timeout=10.0
))

API_CIRCUIT = circuit_manager.get_breaker("sports_api", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=3,
    request_timeout=20.0
))

DATABASE_CIRCUIT = circuit_manager.get_breaker("database", CircuitBreakerConfig(
    failure_threshold=2,
    recovery_timeout=10,
    success_threshold=1,
    request_timeout=5.0
))

# Fallback functions
async def debate_fallback(fallback_data: Any, *args, **kwargs) -> Dict[str, Any]:
    """Fallback for debate arena failures"""
    return {
        "type": "debate_response",
        "content": "🤖 **Service Temporarily Unavailable**\\n\\n" +
                  "Our AI debate system is experiencing high demand. " +
                  "Please try again in a few moments.\\n\\n" +
                  "💡 **While you wait:**\\n" +
                  "• Check out our FAQ for common questions\\n" +
                  "• Browse recent debates from other users\\n" +
                  "• Consider upgrading for priority access",
        "fallback": True,
        "retry_suggested": True
    }

async def billing_fallback(fallback_data: Any, *args, **kwargs) -> Dict[str, Any]:
    """Fallback for billing system failures"""
    return {
        "allowed": True,  # Allow access during billing issues
        "reason": "Billing system maintenance - access granted temporarily",
        "fallback": True,
        "contact_support": True
    }

# Set up fallbacks
DEBATE_CIRCUIT.set_fallback(debate_fallback)
BILLING_CIRCUIT.set_fallback(billing_fallback) 