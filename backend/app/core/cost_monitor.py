"""
Cost monitoring and optimization for free tiers
Track usage and alert when approaching limits
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict
import httpx


class CostMonitor:
    """Monitor free tier usage across all services"""

    def __init__(self):
        self.alerts = []
        self.usage = {
            "gemini": {"daily_limit": 1500, "used_today": 0},
            "groq": {"rpm_limit": 20, "current_rpm": 0},
            "resend": {"monthly_limit": 3000, "used_this_month": 0},
            "supabase": {
                "db_limit_mb": 500,
                "used_mb": 0,
                "bandwidth_limit_gb": 2,
                "used_gb": 0
            }
        }

    async def check_all_services(self) -> Dict:
        """Check usage across all services"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "alerts": [],
            "estimated_monthly_cost": 0
        }

        # Check Gemini
        gemini_usage = await self._check_gemini()
        results["services"]["gemini"] = gemini_usage
        if gemini_usage["percentage"] > 80:
            results["alerts"].append({
                "service": "gemini",
                "level": "warning",
                "message": f"Gemini usage at {gemini_usage['percentage']}%"
            })

        # Check Supabase
        supabase_usage = await self._check_supabase()
        results["services"]["supabase"] = supabase_usage
        if supabase_usage["db_percentage"] > 80:
            results["alerts"].append({
                "service": "supabase",
                "level": "critical",
                "message": f"Database at {supabase_usage['db_percentage']}%"
            })

        # Check Resend (requires manual tracking)
        resend_usage = self._check_resend()
        results["services"]["resend"] = resend_usage

        # Calculate estimated cost
        results["estimated_monthly_cost"] = self._estimate_cost(results["services"])

        return results

    async def _check_gemini(self) -> Dict:
        """Check Gemini API usage"""
        # Gemini doesn't have a usage API, so we track manually
        # This would be stored in Redis/database in production
        return {
            "service": "Gemini Flash",
            "daily_limit": 1500,
            "used_today": 0,  # Would be fetched from tracking DB
            "remaining": 1500,
            "percentage": 0,
            "reset_time": "24:00 UTC",
            "cost_if_paid": "$0 (free tier)"
        }

    async def _check_supabase(self) -> Dict:
        """Check Supabase usage"""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")

            if not url or not key:
                return {"error": "Supabase credentials not configured"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{url}/rest/v1/",
                    headers={"apikey": key}
                )

            # Estimate DB size (this is simplified)
            return {
                "service": "Supabase",
                "db_limit_mb": 500,
                "used_mb": 50,  # Placeholder
                "db_percentage": 10,
                "bandwidth_limit_gb": 2,
                "used_gb": 0.5,  # Placeholder
                "bandwidth_percentage": 25,
                "cost_if_paid": "$25/month"
            }
        except Exception as e:
            return {"error": str(e)}

    def _check_resend(self) -> Dict:
        """Check Resend email usage"""
        # Requires tracking sends in application
        return {
            "service": "Resend",
            "monthly_limit": 3000,
            "used_this_month": 0,  # Would be fetched from tracking DB
            "remaining": 3000,
            "percentage": 0,
            "cost_if_paid": "$20/month"
        }

    def _estimate_cost(self, services: Dict) -> float:
        """Estimate monthly cost if exceeding free tiers"""
        cost = 0

        # Gemini - if exceeding, need paid plan
        if services.get("gemini", {}).get("percentage", 0) > 100:
            cost += 20  # Paid API access

        # Supabase - if exceeding
        supabase = services.get("supabase", {})
        if supabase.get("db_percentage", 0) > 100:
            cost += 25  # Pro tier

        # Resend - if exceeding
        if services.get("resend", {}).get("percentage", 0) > 100:
            cost += 20  # Paid tier

        return cost

    def get_optimization_suggestions(self) -> list:
        """Get suggestions to reduce costs"""
        suggestions = []

        suggestions.append({
            "priority": "high",
            "action": "Enable response caching",
            "savings": "$10-20/month",
            "description": "Cache AI responses for similar prompts"
        })

        suggestions.append({
            "priority": "medium",
            "action": "Compress images in storage",
            "savings": "$5-10/month",
            "description": "Reduce storage and bandwidth usage"
        })

        suggestions.append({
            "priority": "medium",
            "action": "Batch email sends",
            "savings": "Free tier longer",
            "description": "Group emails to stay under limits"
        })

        suggestions.append({
            "priority": "low",
            "action": "Archive old leads",
            "savings": "Database space",
            "description": "Move old data to cheaper storage"
        })

        return suggestions


# Usage tracker for application integration
class UsageTracker:
    """Track API usage across the application"""

    def __init__(self):
        self.daily_stats = {
            "ai_calls": 0,
            "emails_sent": 0,
            "db_queries": 0,
            "api_requests": 0
        }

    def track_ai_call(self, provider: str = "gemini"):
        """Track AI API call"""
        self.daily_stats["ai_calls"] += 1
        # In production, save to Redis/DB

    def track_email_sent(self):
        """Track email send"""
        self.daily_stats["emails_sent"] += 1

    def track_db_query(self):
        """Track database query"""
        self.daily_stats["db_queries"] += 1

    def get_daily_report(self) -> Dict:
        """Get daily usage report"""
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            **self.daily_stats,
            "projected_monthly_ai": self.daily_stats["ai_calls"] * 30,
            "projected_monthly_emails": self.daily_stats["emails_sent"] * 30,
            "within_free_tier": self._check_within_limits()
        }

    def _check_within_limits(self) -> bool:
        """Check if usage is within free tier limits"""
        return (
            self.daily_stats["ai_calls"] <= 1500 and  # Gemini limit
            self.daily_stats["emails_sent"] <= 100  # Resend daily avg
        )


# Global instances
cost_monitor = CostMonitor()
usage_tracker = UsageTracker()
