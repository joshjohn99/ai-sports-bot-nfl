"""
💳 Commercial Billing and User Tier Management
Production-grade billing system for AI Sports Debate Arena
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from decimal import Decimal

class UserTier(Enum):
    """Commercial user tiers with different feature access"""
    FREE = "free"
    BASIC = "basic"  
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class TierLimits:
    """Limits and features for each tier"""
    tier: UserTier
    monthly_debates: int
    concurrent_debates: int
    max_players_per_debate: int
    historical_data_months: int
    advanced_analytics: bool
    api_access: bool
    real_time_streaming: bool
    custom_agents: bool
    export_features: bool
    priority_support: bool
    monthly_price_usd: Decimal
    
    # API usage limits
    api_calls_per_hour: int
    compute_seconds_per_month: int

class TierConfiguration:
    """Production tier configurations for monetization"""
    
    TIER_CONFIGS = {
        UserTier.FREE: TierLimits(
            tier=UserTier.FREE,
            monthly_debates=5,
            concurrent_debates=1,
            max_players_per_debate=2,
            historical_data_months=1,
            advanced_analytics=False,
            api_access=False,
            real_time_streaming=False,
            custom_agents=False,
            export_features=False,
            priority_support=False,
            monthly_price_usd=Decimal('0.00'),
            api_calls_per_hour=10,
            compute_seconds_per_month=60
        ),
        
        UserTier.BASIC: TierLimits(
            tier=UserTier.BASIC,
            monthly_debates=50,
            concurrent_debates=2,
            max_players_per_debate=4,
            historical_data_months=12,
            advanced_analytics=True,
            api_access=True,
            real_time_streaming=True,
            custom_agents=False,
            export_features=True,
            priority_support=False,
            monthly_price_usd=Decimal('29.99'),
            api_calls_per_hour=100,
            compute_seconds_per_month=3600
        ),
        
        UserTier.PREMIUM: TierLimits(
            tier=UserTier.PREMIUM,
            monthly_debates=500,
            concurrent_debates=5,
            max_players_per_debate=8,
            historical_data_months=60,
            advanced_analytics=True,
            api_access=True,
            real_time_streaming=True,
            custom_agents=True,
            export_features=True,
            priority_support=True,
            monthly_price_usd=Decimal('99.99'),
            api_calls_per_hour=1000,
            compute_seconds_per_month=18000
        ),
        
        UserTier.ENTERPRISE: TierLimits(
            tier=UserTier.ENTERPRISE,
            monthly_debates=-1,  # Unlimited
            concurrent_debates=20,
            max_players_per_debate=20,
            historical_data_months=-1,  # Unlimited
            advanced_analytics=True,
            api_access=True,
            real_time_streaming=True,
            custom_agents=True,
            export_features=True,
            priority_support=True,
            monthly_price_usd=Decimal('499.99'),
            api_calls_per_hour=10000,
            compute_seconds_per_month=-1  # Unlimited
        )
    }
    
    @classmethod
    def get_limits(cls, tier: UserTier) -> TierLimits:
        return cls.TIER_CONFIGS[tier]

@dataclass
class UsageRecord:
    """Track user usage for billing"""
    user_id: str
    timestamp: datetime
    feature: str
    resource_type: str  # 'debate', 'api_call', 'compute_time'
    quantity: int
    cost_usd: Decimal
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserAccount:
    """Commercial user account with billing info"""
    user_id: str
    email: str
    tier: UserTier
    created_at: datetime
    subscription_start: datetime
    subscription_end: Optional[datetime]
    is_active: bool
    
    # Usage tracking
    current_month_debates: int = 0
    current_month_api_calls: int = 0
    current_month_compute_seconds: int = 0
    
    # Billing
    payment_method_id: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    tax_rate: Decimal = Decimal('0.00')
    
    # Feature flags
    beta_features_enabled: bool = False
    custom_rate_limits: Optional[Dict[str, int]] = None

class BillingManager:
    """
    Production billing system for AI Sports Debate Arena
    Handles subscriptions, usage tracking, and revenue optimization
    """
    
    def __init__(self):
        self.users: Dict[str, UserAccount] = {}
        self.usage_records: List[UsageRecord] = []
        self.tier_config = TierConfiguration()
        
    async def create_user_account(self, email: str, tier: UserTier = UserTier.FREE) -> UserAccount:
        """Create new commercial user account"""
        user_id = str(uuid.uuid4())
        
        account = UserAccount(
            user_id=user_id,
            email=email,
            tier=tier,
            created_at=datetime.utcnow(),
            subscription_start=datetime.utcnow(),
            subscription_end=self._calculate_subscription_end(tier),
            is_active=True
        )
        
        self.users[user_id] = account
        return account
    
    async def check_feature_access(self, user_id: str, feature: str) -> Dict[str, Any]:
        """Check if user has access to specific feature"""
        user = self.users.get(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}
        
        if not user.is_active:
            return {"allowed": False, "reason": "Account inactive"}
        
        limits = self.tier_config.get_limits(user.tier)
        
        # Check specific features
        if feature == "advanced_debate":
            if not limits.advanced_analytics:
                return {
                    "allowed": False, 
                    "reason": "Advanced debates require Basic tier or higher",
                    "upgrade_url": f"/upgrade?from={user.tier.value}&feature=advanced_debate"
                }
        
        elif feature == "real_time_streaming":
            if not limits.real_time_streaming:
                return {
                    "allowed": False,
                    "reason": "Real-time streaming requires Basic tier or higher",
                    "upgrade_url": f"/upgrade?from={user.tier.value}&feature=streaming"
                }
        
        elif feature == "custom_agents":
            if not limits.custom_agents:
                return {
                    "allowed": False,
                    "reason": "Custom agents require Premium tier or higher", 
                    "upgrade_url": f"/upgrade?from={user.tier.value}&feature=custom_agents"
                }
        
        return {"allowed": True, "tier": user.tier.value, "limits": limits}
    
    async def check_usage_quota(self, user_id: str, resource_type: str, quantity: int = 1) -> Dict[str, Any]:
        """Check if user has quota for resource usage"""
        user = self.users.get(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}
        
        limits = self.tier_config.get_limits(user.tier)
        
        if resource_type == "debate":
            if limits.monthly_debates != -1 and user.current_month_debates >= limits.monthly_debates:
                return {
                    "allowed": False,
                    "reason": f"Monthly debate limit reached ({limits.monthly_debates})",
                    "current_usage": user.current_month_debates,
                    "limit": limits.monthly_debates,
                    "upgrade_tier": self._suggest_upgrade_tier(user.tier)
                }
        
        elif resource_type == "api_call":
            # Check hourly rate limit
            hourly_calls = await self._get_hourly_api_calls(user_id)
            if hourly_calls >= limits.api_calls_per_hour:
                return {
                    "allowed": False,
                    "reason": f"Hourly API limit reached ({limits.api_calls_per_hour})",
                    "reset_time": self._get_next_hour_reset()
                }
        
        elif resource_type == "compute_time":
            if limits.compute_seconds_per_month != -1 and user.current_month_compute_seconds >= limits.compute_seconds_per_month:
                return {
                    "allowed": False,
                    "reason": f"Monthly compute time limit reached ({limits.compute_seconds_per_month}s)",
                    "current_usage": user.current_month_compute_seconds,
                    "limit": limits.compute_seconds_per_month
                }
        
        return {"allowed": True, "remaining": self._calculate_remaining_quota(user, resource_type)}
    
    async def record_usage(self, user_id: str, feature: str, resource_type: str, 
                          quantity: int, metadata: Dict[str, Any] = None) -> UsageRecord:
        """Record billable usage for analytics and billing"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate cost based on tier and usage
        cost = self._calculate_usage_cost(user.tier, resource_type, quantity)
        
        record = UsageRecord(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            feature=feature,
            resource_type=resource_type,
            quantity=quantity,
            cost_usd=cost,
            metadata=metadata or {}
        )
        
        # Update user usage counters
        if resource_type == "debate":
            user.current_month_debates += quantity
        elif resource_type == "api_call":
            user.current_month_api_calls += quantity
        elif resource_type == "compute_time":
            user.current_month_compute_seconds += quantity
        
        self.usage_records.append(record)
        return record
    
    async def upgrade_user_tier(self, user_id: str, new_tier: UserTier, payment_method_id: str) -> Dict[str, Any]:
        """Upgrade user to higher tier with payment processing"""
        user = self.users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        if new_tier.value <= user.tier.value:
            return {"success": False, "error": "Cannot downgrade or same tier"}
        
        # In production, integrate with Stripe/payment processor here
        old_tier = user.tier
        user.tier = new_tier
        user.payment_method_id = payment_method_id
        user.subscription_start = datetime.utcnow()
        user.subscription_end = self._calculate_subscription_end(new_tier)
        
        # Reset usage counters for new tier
        user.current_month_debates = 0
        user.current_month_api_calls = 0
        user.current_month_compute_seconds = 0
        
        return {
            "success": True,
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "new_limits": self.tier_config.get_limits(new_tier).__dict__,
            "billing_cycle_start": user.subscription_start.isoformat()
        }
    
    def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get revenue analytics for business intelligence"""
        total_revenue = sum(record.cost_usd for record in self.usage_records)
        
        revenue_by_tier = {}
        users_by_tier = {}
        
        for tier in UserTier:
            tier_users = [u for u in self.users.values() if u.tier == tier and u.is_active]
            users_by_tier[tier.value] = len(tier_users)
            
            tier_revenue = sum(
                record.cost_usd for record in self.usage_records 
                if record.user_id in [u.user_id for u in tier_users]
            )
            revenue_by_tier[tier.value] = float(tier_revenue)
        
        return {
            "total_revenue_usd": float(total_revenue),
            "total_active_users": len([u for u in self.users.values() if u.is_active]),
            "revenue_by_tier": revenue_by_tier,
            "users_by_tier": users_by_tier,
            "avg_revenue_per_user": float(total_revenue / len(self.users)) if self.users else 0,
            "conversion_funnel": self._calculate_conversion_funnel()
        }
    
    def _calculate_subscription_end(self, tier: UserTier) -> Optional[datetime]:
        """Calculate subscription end date"""
        if tier == UserTier.FREE:
            return None  # No expiration for free tier
        return datetime.utcnow() + timedelta(days=30)  # Monthly billing
    
    def _suggest_upgrade_tier(self, current_tier: UserTier) -> Optional[UserTier]:
        """Suggest next tier for upgrade"""
        tier_order = [UserTier.FREE, UserTier.BASIC, UserTier.PREMIUM, UserTier.ENTERPRISE]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def _calculate_usage_cost(self, tier: UserTier, resource_type: str, quantity: int) -> Decimal:
        """Calculate cost for usage (for usage-based billing features)"""
        # Free tier users don't get charged for basic usage
        if tier == UserTier.FREE:
            return Decimal('0.00')
        
        # Usage-based pricing for overage
        overage_rates = {
            "debate": Decimal('0.50'),  # $0.50 per extra debate
            "api_call": Decimal('0.01'),  # $0.01 per extra API call
            "compute_time": Decimal('0.10')  # $0.10 per extra compute minute
        }
        
        return overage_rates.get(resource_type, Decimal('0.00')) * quantity
    
    async def _get_hourly_api_calls(self, user_id: str) -> int:
        """Get API calls in current hour"""
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        return sum(
            record.quantity for record in self.usage_records
            if (record.user_id == user_id and 
                record.resource_type == "api_call" and
                record.timestamp >= current_hour)
        )
    
    def _get_next_hour_reset(self) -> datetime:
        """Get timestamp for next hour reset"""
        return (datetime.utcnow() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    
    def _calculate_remaining_quota(self, user: UserAccount, resource_type: str) -> int:
        """Calculate remaining quota for resource"""
        limits = self.tier_config.get_limits(user.tier)
        
        if resource_type == "debate":
            if limits.monthly_debates == -1:
                return -1  # Unlimited
            return max(0, limits.monthly_debates - user.current_month_debates)
        
        elif resource_type == "compute_time":
            if limits.compute_seconds_per_month == -1:
                return -1  # Unlimited
            return max(0, limits.compute_seconds_per_month - user.current_month_compute_seconds)
        
        return 0
    
    def _calculate_conversion_funnel(self) -> Dict[str, Any]:
        """Calculate conversion rates between tiers"""
        total_users = len(self.users)
        if total_users == 0:
            return {}
        
        tier_counts = {}
        for tier in UserTier:
            count = len([u for u in self.users.values() if u.tier == tier])
            tier_counts[tier.value] = {
                "count": count,
                "percentage": (count / total_users) * 100
            }
        
        return tier_counts

# Global billing manager instance
billing_manager = BillingManager() 