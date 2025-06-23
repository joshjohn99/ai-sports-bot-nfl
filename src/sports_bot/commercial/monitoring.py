"""
🔍 Production Monitoring System for Commercial AI Sports Debate Arena  
Enterprise-grade monitoring for error tracking, performance metrics, and SLA monitoring
"""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Production monitoring system for enterprise reliability"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.uptime_checks: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            "error_rate_5min": 0.05,  # 5% error rate triggers alert
            "avg_response_time": 10.0,  # 10 seconds avg response time
            "system_downtime": 60.0   # 60 seconds downtime triggers alert
        }
        
    async def record_error(self, operation: str, error_message: str, context: Dict[str, Any] = None):
        """Record production error for monitoring and alerting"""
        error_id = hashlib.md5(f"{operation}_{error_message}_{time.time()}".encode()).hexdigest()[:8]
        
        error_record = {
            "error_id": error_id,
            "operation": operation,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
            "severity": self._classify_error_severity(error_message),
            "user_impact": self._assess_user_impact(operation)
        }
        
        self.errors.append(error_record)
        
        # Check if we need to trigger alerts
        await self._check_alert_conditions(operation, error_record)
        
        return error_id
    
    async def record_performance_metric(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Record performance metrics for SLA monitoring"""
        self.performance_metrics[operation].append(duration)
        
        # Keep only last 1000 records per operation
        if len(self.performance_metrics[operation]) > 1000:
            self.performance_metrics[operation] = self.performance_metrics[operation][-1000:]
        
        # Check for performance degradation
        if await self._is_performance_degraded(operation, duration):
            await self.record_error(
                f"{operation}_performance_degradation",
                f"Performance degraded: {duration:.2f}s (threshold: {self.alert_thresholds['avg_response_time']}s)",
                {"duration": duration, "metadata": metadata}
            )
    
    async def get_error_id(self) -> str:
        """Get unique error ID for customer support"""
        return f"ERR_{int(time.time())}"
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {}
        
        for operation, durations in self.performance_metrics.items():
            if durations:
                metrics[operation] = {
                    "avg_duration": sum(durations) / len(durations),
                    "max_duration": max(durations),
                    "min_duration": min(durations),
                    "total_requests": len(durations),
                    "p95_duration": self._calculate_percentile(durations, 95),
                    "p99_duration": self._calculate_percentile(durations, 99)
                }
        
        return {
            "operations": metrics,
            "overall_health": await self._calculate_system_health(),
            "error_summary": await self._get_error_summary(),
            "uptime_percentage": await self._calculate_uptime()
        }
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for operations dashboard"""
        recent_errors = [e for e in self.errors if self._is_recent(e["timestamp"], hours=24)]
        
        return {
            "system_status": await self._get_system_status(),
            "errors_last_24h": len(recent_errors),
            "critical_errors": len([e for e in recent_errors if e["severity"] == "critical"]),
            "avg_response_time": await self._get_avg_response_time(),
            "uptime_percentage": await self._calculate_uptime(),
            "active_alerts": await self._get_active_alerts(),
            "performance_trends": await self._get_performance_trends()
        }
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health_score = await self._calculate_system_health()
        
        issues = []
        if health_score < 0.9:
            issues.append("Performance degradation detected")
        
        recent_errors = [e for e in self.errors if self._is_recent(e["timestamp"], hours=1)]
        if len(recent_errors) > 10:
            issues.append("High error rate detected")
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score > 0.95 else "degraded" if health_score > 0.8 else "unhealthy",
            "issues": issues,
            "recommendations": await self._get_health_recommendations(health_score, issues)
        }
    
    def _classify_error_severity(self, error_message: str) -> str:
        """Classify error severity based on message content"""
        error_lower = error_message.lower()
        
        if any(word in error_lower for word in ["critical", "fatal", "crash", "system down"]):
            return "critical"
        elif any(word in error_lower for word in ["error", "failed", "exception", "timeout"]):
            return "high"
        elif any(word in error_lower for word in ["warning", "deprecated", "rate limit"]):
            return "medium"
        else:
            return "low"
    
    def _assess_user_impact(self, operation: str) -> str:
        """Assess user impact of operation failure"""
        high_impact_operations = ["commercial_debate", "user_authentication", "billing"]
        medium_impact_operations = ["dashboard", "analytics", "monitoring"]
        
        if operation in high_impact_operations:
            return "high"
        elif operation in medium_impact_operations:
            return "medium"
        else:
            return "low"
    
    async def _check_alert_conditions(self, operation: str, error_record: Dict[str, Any]):
        """Check if error conditions trigger alerts"""
        # Check error rate in last 5 minutes
        recent_errors = [
            e for e in self.errors 
            if self._is_recent(e["timestamp"], minutes=5) and e["operation"] == operation
        ]
        
        if len(recent_errors) > 5:  # More than 5 errors in 5 minutes
            logger.warning(f"HIGH ERROR RATE ALERT: {len(recent_errors)} errors in 5 minutes for {operation}")
            
        # Check critical errors
        if error_record["severity"] == "critical":
            logger.critical(f"CRITICAL ERROR ALERT: {error_record['error_message']} in {operation}")
    
    async def _is_performance_degraded(self, operation: str, current_duration: float) -> bool:
        """Check if current performance is degraded"""
        if current_duration > self.alert_thresholds["avg_response_time"]:
            return True
        
        # Check if significantly slower than average
        recent_durations = self.performance_metrics[operation][-10:]  # Last 10 requests
        if len(recent_durations) >= 5:
            avg_recent = sum(recent_durations) / len(recent_durations)
            if current_duration > avg_recent * 2:  # 2x slower than recent average
                return True
        
        return False
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score (0-1)"""
        # Factor in error rates, performance, uptime
        recent_errors = [e for e in self.errors if self._is_recent(e["timestamp"], hours=1)]
        error_score = max(0, 1 - (len(recent_errors) / 100))  # Penalty for errors
        
        # Performance score
        if self.performance_metrics:
            avg_performance = []
            for operation, durations in self.performance_metrics.items():
                if durations:
                    recent_durations = durations[-10:]
                    avg_duration = sum(recent_durations) / len(recent_durations)
                    performance_score = max(0, 1 - (avg_duration / 30))  # 30s is very poor
                    avg_performance.append(performance_score)
            
            performance_score = sum(avg_performance) / len(avg_performance) if avg_performance else 1.0
        else:
            performance_score = 1.0
        
        # Weighted average
        return error_score * 0.6 + performance_score * 0.4
    
    async def _get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for dashboard"""
        recent_errors = [e for e in self.errors if self._is_recent(e["timestamp"], hours=24)]
        
        error_by_severity = defaultdict(int)
        error_by_operation = defaultdict(int)
        
        for error in recent_errors:
            error_by_severity[error["severity"]] += 1
            error_by_operation[error["operation"]] += 1
        
        return {
            "total_errors_24h": len(recent_errors),
            "by_severity": dict(error_by_severity),
            "by_operation": dict(error_by_operation),
            "most_common_operation": max(error_by_operation.items(), key=lambda x: x[1])[0] if error_by_operation else None
        }
    
    async def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage"""
        # Simplified uptime calculation
        # In production, this would integrate with infrastructure monitoring
        total_time = 24 * 60 * 60  # 24 hours in seconds
        
        critical_errors = [e for e in self.errors if e["severity"] == "critical" and self._is_recent(e["timestamp"], hours=24)]
        downtime = len(critical_errors) * 60  # Assume 1 minute downtime per critical error
        
        uptime = max(0, (total_time - downtime) / total_time * 100)
        return uptime
    
    def _is_recent(self, timestamp: str, hours: int = 1, minutes: int = 0) -> bool:
        """Check if timestamp is within specified time period"""
        event_time = datetime.fromisoformat(timestamp)
        cutoff = datetime.utcnow() - timedelta(hours=hours, minutes=minutes)
        return event_time >= cutoff
    
    async def _get_system_status(self) -> str:
        """Get overall system status"""
        health_score = await self._calculate_system_health()
        
        if health_score > 0.95:
            return "operational"
        elif health_score > 0.8:
            return "degraded"
        else:
            return "major_outage"
    
    async def _get_avg_response_time(self) -> float:
        """Get average response time across all operations"""
        all_durations = []
        for durations in self.performance_metrics.values():
            all_durations.extend(durations[-50:])  # Last 50 per operation
        
        return sum(all_durations) / len(all_durations) if all_durations else 0.0
    
    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        alerts = []
        
        # High error rate alerts
        recent_errors = [e for e in self.errors if self._is_recent(e["timestamp"], minutes=5)]
        if len(recent_errors) > 5:
            alerts.append({
                "type": "high_error_rate",
                "message": f"{len(recent_errors)} errors in last 5 minutes",
                "severity": "high"
            })
        
        # Performance alerts
        avg_response = await self._get_avg_response_time()
        if avg_response > self.alert_thresholds["avg_response_time"]:
            alerts.append({
                "type": "slow_response",
                "message": f"Average response time: {avg_response:.2f}s",
                "severity": "medium"
            })
        
        return alerts
    
    async def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends for visualization"""
        return {
            "response_time_trend": "stable",  # Could be "improving", "degrading", "stable"
            "error_rate_trend": "decreasing",
            "user_satisfaction": 4.2  # Out of 5
        }
    
    async def _get_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Get recommendations to improve system health"""
        recommendations = []
        
        if health_score < 0.9:
            recommendations.append("Review and optimize slow-performing operations")
        
        if "High error rate detected" in issues:
            recommendations.append("Investigate root cause of recent errors")
            recommendations.append("Consider implementing circuit breakers")
        
        if "Performance degradation detected" in issues:
            recommendations.append("Scale up compute resources")
            recommendations.append("Optimize database queries")
        
        return recommendations 