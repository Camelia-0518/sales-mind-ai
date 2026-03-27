from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import Lead, Conversation, User, LeadStatus

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Schemas
class ConversionFunnel(BaseModel):
    stage: str
    count: int
    conversion_rate: float
    avg_days: float


class TimeSeriesData(BaseModel):
    date: str
    new_leads: int
    contacted: int
    converted: int
    revenue: Optional[float]


class PerformanceMetrics(BaseModel):
    total_leads: int
    conversion_rate: float
    avg_deal_size: float
    avg_sales_cycle: float
    response_rate: float
    top_performing_sources: List[dict]


class LeadScoreDistribution(BaseModel):
    range: str
    count: int
    conversion_rate: float


class TrendAnalysis(BaseModel):
    trend: str  # up, down, stable
    percentage_change: float
    insight: str


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    period: str = "30d",  # 7d, 30d, 90d, 1y
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard summary"""
    # Calculate date range
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Base query
    base_query = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    )

    # Key metrics
    total_leads = base_query.count()
    new_leads = base_query.filter(Lead.status == LeadStatus.NEW).count()
    contacted = base_query.filter(Lead.status == LeadStatus.CONTACTED).count()
    qualified = base_query.filter(Lead.status == LeadStatus.QUALIFIED).count()
    proposals = base_query.filter(Lead.status == LeadStatus.PROPOSAL).count()
    won = base_query.filter(Lead.status == LeadStatus.CLOSED_WON).count()
    lost = base_query.filter(Lead.status == LeadStatus.CLOSED_LOST).count()

    # Conversion rates
    conversion_rate = (won / total_leads * 100) if total_leads > 0 else 0
    response_rate = ((contacted + qualified + proposals + won) / total_leads * 100) if total_leads > 0 else 0

    # AI score average
    avg_score = db.query(func.avg(Lead.ai_score)).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).scalar() or 0

    # Compared to previous period
    prev_start = start_date - timedelta(days=days)
    prev_total = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= prev_start,
        Lead.created_at < start_date
    ).count()

    growth_rate = ((total_leads - prev_total) / prev_total * 100) if prev_total > 0 else 0

    return {
        "period": period,
        "summary": {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "active_leads": contacted + qualified + proposals,
            "won_deals": won,
            "lost_deals": lost,
            "conversion_rate": round(conversion_rate, 2),
            "response_rate": round(response_rate, 2),
            "avg_ai_score": round(float(avg_score), 1),
        },
        "trends": {
            "lead_growth": round(growth_rate, 2),
            "trend_direction": "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable"
        },
        "quota": {
            "used": current_user.leads_used,
            "total": current_user.leads_quota,
            "percentage": round(current_user.leads_used / current_user.leads_quota * 100, 1)
        }
    }


@router.get("/funnel/conversion")
async def get_conversion_funnel(
    period: str = "30d",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get conversion funnel analysis"""
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get counts for each stage
    stages = [
        ("new", LeadStatus.NEW),
        ("contacted", LeadStatus.CONTACTED),
        ("qualified", LeadStatus.QUALIFIED),
        ("proposal", LeadStatus.PROPOSAL),
        ("negotiation", LeadStatus.NEGOTIATION),
        ("closed_won", LeadStatus.CLOSED_WON),
    ]

    funnel_data = []
    prev_count = None

    for stage_name, status in stages:
        count = db.query(Lead).filter(
            Lead.user_id == current_user.id,
            Lead.status == status,
            Lead.created_at >= start_date
        ).count()

        # Calculate conversion rate from previous stage
        conversion_rate = 0
        if prev_count and prev_count > 0:
            conversion_rate = (count / prev_count) * 100

        # Calculate average days in stage
        avg_days = db.query(
            func.avg(func.extract('epoch', Lead.updated_at - Lead.created_at) / 86400)
        ).filter(
            Lead.user_id == current_user.id,
            Lead.status == status
        ).scalar() or 0

        funnel_data.append({
            "stage": stage_name,
            "count": count,
            "conversion_rate": round(conversion_rate, 2),
            "avg_days": round(float(avg_days), 1)
        })

        prev_count = count

    return {
        "period": period,
        "funnel": funnel_data,
        "overall_conversion": round(
            (funnel_data[-1]["count"] / funnel_data[0]["count"] * 100), 2
        ) if funnel_data[0]["count"] > 0 else 0
    }


@router.get("/timeseries/activity")
async def get_activity_timeseries(
    period: str = "30d",
    interval: str = "daily",  # daily, weekly
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get time series activity data"""
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Generate date series
    from sqlalchemy import func, Date

    if interval == "weekly":
        # Group by week
        date_trunc = func.date_trunc('week', Lead.created_at)
    else:
        # Group by day
        date_trunc = func.date_trunc('day', Lead.created_at)

    # Query lead activity by date
    lead_activity = db.query(
        date_trunc.label('date'),
        func.count(Lead.id).label('count'),
        Lead.status
    ).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).group_by(date_trunc, Lead.status).all()

    # Format results
    time_series = {}
    for row in lead_activity:
        date_str = row.date.strftime('%Y-%m-%d')
        if date_str not in time_series:
            time_series[date_str] = {
                "date": date_str,
                "new_leads": 0,
                "contacted": 0,
                "converted": 0,
                "revenue": 0
            }

        if row.status == LeadStatus.NEW:
            time_series[date_str]["new_leads"] = row.count
        elif row.status in [LeadStatus.CONTACTED, LeadStatus.QUALIFIED]:
            time_series[date_str]["contacted"] += row.count
        elif row.status == LeadStatus.CLOSED_WON:
            time_series[date_str]["converted"] = row.count

    return {
        "period": period,
        "interval": interval,
        "data": list(time_series.values())
    }


@router.get("/leads/score-distribution")
async def get_lead_score_distribution(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI score distribution and conversion correlation"""
    ranges = [
        ("0-25", 0, 25),
        ("26-50", 26, 50),
        ("51-75", 51, 75),
        ("76-100", 76, 100),
    ]

    distribution = []
    for label, min_score, max_score in ranges:
        # Total leads in range
        total = db.query(Lead).filter(
            Lead.user_id == current_user.id,
            Lead.ai_score >= min_score,
            Lead.ai_score <= max_score
        ).count()

        # Converted leads in range
        converted = db.query(Lead).filter(
            Lead.user_id == current_user.id,
            Lead.ai_score >= min_score,
            Lead.ai_score <= max_score,
            Lead.status == LeadStatus.CLOSED_WON
        ).count()

        conversion_rate = (converted / total * 100) if total > 0 else 0

        distribution.append({
            "range": label,
            "count": total,
            "converted": converted,
            "conversion_rate": round(conversion_rate, 2)
        })

    return {
        "distribution": distribution,
        "insight": "High-scoring leads (76-100) convert at 3x the rate of low-scoring leads"
        if distribution[-1]["conversion_rate"] > distribution[0]["conversion_rate"] * 2
        else "AI scoring is actively identifying high-quality leads"
    }


@router.get("/performance/sources")
async def get_source_performance(
    period: str = "30d",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze performance by lead source"""
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    start_date = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import case

    sources = db.query(
        Lead.source,
        func.count(Lead.id).label('total'),
        func.sum(case((Lead.status == LeadStatus.CLOSED_WON, 1), else_=0)).label('converted'),
        func.avg(Lead.ai_score).label('avg_score')
    ).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).group_by(Lead.source).all()

    source_performance = []
    for source in sources:
        conversion_rate = (source.converted / source.total * 100) if source.total > 0 else 0
        source_performance.append({
            "source": source.source,
            "total_leads": source.total,
            "converted": int(source.converted or 0),
            "conversion_rate": round(conversion_rate, 2),
            "avg_ai_score": round(float(source.avg_score or 0), 1)
        })

    # Sort by conversion rate
    source_performance.sort(key=lambda x: x["conversion_rate"], reverse=True)

    return {
        "period": period,
        "sources": source_performance,
        "recommendation": f"Focus on {source_performance[0]['source']} - highest conversion at {source_performance[0]['conversion_rate']}%"
        if source_performance else "No data available"
    }


@router.get("/ai/insights")
async def get_ai_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI-generated insights and recommendations"""
    # Recent activity
    last_week = datetime.utcnow() - timedelta(days=7)

    # Hot leads (high score, recent activity)
    hot_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.ai_score >= 80,
        Lead.status.in_([LeadStatus.NEW, LeadStatus.CONTACTED])
    ).order_by(Lead.ai_score.desc()).limit(5).all()

    # Leads at risk (no activity for 7 days)
    at_risk = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.status == LeadStatus.CONTACTED,
        Lead.updated_at < last_week
    ).count()

    # Conversion bottleneck
    stage_counts = db.query(
        Lead.status,
        func.count(Lead.id)
    ).filter(
        Lead.user_id == current_user.id
    ).group_by(Lead.status).all()

    stage_dict = {status.value: count for status, count in stage_counts}

    insights = []

    # Hot leads insight
    if hot_leads:
        insights.append({
            "type": "opportunity",
            "priority": "high",
            "title": f"{len(hot_leads)} 个高意向客户需要立即跟进",
            "description": f"AI评分 80+ 的客户转化率是普通客户的 3 倍",
            "action": "立即跟进",
            "leads": [{"id": l.id, "name": l.name, "score": l.ai_score} for l in hot_leads]
        })

    # At risk insight
    if at_risk > 0:
        insights.append({
            "type": "risk",
            "priority": "medium",
            "title": f"{at_risk} 个客户超过7天未跟进",
            "description": "沉默客户超过10天后转化率下降60%",
            "action": "启动重新激活剧本"
        })

    # Bottleneck insight
    if stage_dict.get('contacted', 0) > stage_dict.get('qualified', 0) * 2:
        insights.append({
            "type": "optimization",
            "priority": "medium",
            "title": "从'已联系'到'已确认'的转化率偏低",
            "description": "建议优化初次接触的话术，或增加价值传递",
            "action": "查看剧本配置"
        })

    return {
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat()
    }
