from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, Database
from app.services.cache import get_cache_service, CacheService

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# SCHEMAS
# ============================================================================


class AgentPerformance(BaseModel):
    """Performance metrics for an agent."""
    agent: str
    department: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_rating: float | None
    feedback_count: int
    usage_rate: float | None  # % of outputs used by client


class TrendData(BaseModel):
    """Trend comparison data."""
    current_period: int
    previous_period: int
    change_percent: float
    trend: str  # "up", "down", "stable"


class AdvancedAnalytics(BaseModel):
    """Advanced analytics response."""
    period: str
    summary: dict[str, Any]
    trends: dict[str, TrendData]
    agent_performance: list[AgentPerformance]
    hourly_distribution: list[dict[str, Any]]
    content_types: dict[str, int]
    estimated_value: dict[str, Any]


@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Get dashboard analytics for current user's company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id

    # Try to get from cache first
    cache = await get_cache_service()
    cache_key = CacheService.analytics_key(company_id)
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Total tasks
    total_tasks = await db.tasks.count_documents({"company_id": company_id})

    # Tasks today
    tasks_today = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": today_start}
    })

    # Tasks this week
    tasks_week = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": week_start}
    })

    # Tasks by status
    status_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = await db.tasks.aggregate(status_pipeline).to_list(None)
    tasks_by_status = {item["_id"]: item["count"] for item in status_results}

    # Tasks by department
    dept_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    dept_results = await db.tasks.aggregate(dept_pipeline).to_list(None)
    tasks_by_department = {item["_id"]: item["count"] for item in dept_results}

    # Tasks by agent
    agent_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$agent", "count": {"$sum": 1}}}
    ]
    agent_results = await db.tasks.aggregate(agent_pipeline).to_list(None)
    tasks_by_agent = {item["_id"]: item["count"] for item in agent_results}

    # Completion rate
    completed = tasks_by_status.get("completed", 0)
    failed = tasks_by_status.get("failed", 0)
    total_finished = completed + failed
    completion_rate = (completed / total_finished * 100) if total_finished > 0 else 0

    # Recent activity (last 7 days)
    activity_pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "created_at": {"$gte": week_start}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    activity_results = await db.tasks.aggregate(activity_pipeline).to_list(None)
    daily_activity = {item["_id"]: item["count"] for item in activity_results}

    # Fill in missing days
    activity_data = []
    for i in range(7):
        date = (today_start - timedelta(days=6-i)).strftime("%Y-%m-%d")
        activity_data.append({
            "date": date,
            "count": daily_activity.get(date, 0)
        })

    result = {
        "summary": {
            "total_tasks": total_tasks,
            "tasks_today": tasks_today,
            "tasks_week": tasks_week,
            "completion_rate": round(completion_rate, 1),
        },
        "tasks_by_status": tasks_by_status,
        "tasks_by_department": tasks_by_department,
        "tasks_by_agent": tasks_by_agent,
        "daily_activity": activity_data,
    }

    # Cache for 5 minutes
    await cache.set(cache_key, result, ttl=300)

    return result


# ============================================================================
# ADVANCED ANALYTICS
# ============================================================================


@router.get("/advanced", response_model=AdvancedAnalytics)
async def get_advanced_analytics(
    current_user: CurrentUser,
    db: Database,
    period: str = Query("week", description="Period: day, week, month"),
) -> AdvancedAnalytics:
    """Get advanced analytics with trends and agent performance."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id
    now = datetime.utcnow()

    # Define periods
    period_days = {"day": 1, "week": 7, "month": 30}.get(period, 7)
    current_start = now - timedelta(days=period_days)
    previous_start = current_start - timedelta(days=period_days)

    # Get current period tasks
    current_tasks = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": current_start},
    })

    # Get previous period tasks
    previous_tasks = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": previous_start, "$lt": current_start},
    })

    # Get current completed
    current_completed = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": current_start},
        "status": "completed",
    })

    previous_completed = await db.tasks.count_documents({
        "company_id": company_id,
        "created_at": {"$gte": previous_start, "$lt": current_start},
        "status": "completed",
    })

    # Calculate trends
    def calc_trend(current: int, previous: int) -> TrendData:
        if previous == 0:
            change = 100.0 if current > 0 else 0.0
        else:
            change = ((current - previous) / previous) * 100

        if change > 5:
            trend = "up"
        elif change < -5:
            trend = "down"
        else:
            trend = "stable"

        return TrendData(
            current_period=current,
            previous_period=previous,
            change_percent=round(change, 1),
            trend=trend,
        )

    trends = {
        "tasks": calc_trend(current_tasks, previous_tasks),
        "completed": calc_trend(current_completed, previous_completed),
    }

    # Agent Performance
    agent_pipeline = [
        {"$match": {"company_id": company_id}},
        {
            "$group": {
                "_id": {"agent": "$agent", "department": "$department"},
                "total": {"$sum": 1},
                "completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
                "failed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                },
            }
        },
    ]
    agent_stats = await db.tasks.aggregate(agent_pipeline).to_list(None)

    # Get feedback data per agent
    feedback_pipeline = [
        {"$match": {"company_id": company_id}},
        {
            "$group": {
                "_id": "$agent",
                "count": {"$sum": 1},
                "sum_rating": {"$sum": "$rating"},
                "used_count": {"$sum": {"$cond": ["$used", 1, 0]}},
            }
        },
    ]
    feedback_stats = {
        item["_id"]: item
        async for item in db.feedbacks.aggregate(feedback_pipeline)
    }

    agent_performance = []
    for stat in agent_stats:
        agent = stat["_id"]["agent"]
        dept = stat["_id"]["department"]
        total = stat["total"]
        completed = stat["completed"]
        failed = stat["failed"]

        fb = feedback_stats.get(agent, {})
        fb_count = fb.get("count", 0)
        avg_rating = fb.get("sum_rating", 0) / fb_count if fb_count > 0 else None
        usage_rate = fb.get("used_count", 0) / fb_count * 100 if fb_count > 0 else None

        agent_performance.append(AgentPerformance(
            agent=agent,
            department=dept,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            success_rate=round(completed / total * 100, 1) if total > 0 else 0,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            feedback_count=fb_count,
            usage_rate=round(usage_rate, 1) if usage_rate else None,
        ))

    # Sort by total tasks
    agent_performance.sort(key=lambda x: x.total_tasks, reverse=True)

    # Hourly distribution
    hourly_pipeline = [
        {"$match": {"company_id": company_id, "created_at": {"$gte": current_start}}},
        {
            "$group": {
                "_id": {"$hour": "$created_at"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    hourly_results = await db.tasks.aggregate(hourly_pipeline).to_list(None)
    hourly_distribution = [
        {"hour": item["_id"], "count": item["count"]}
        for item in hourly_results
    ]

    # Content types distribution
    type_pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    type_results = await db.tasks.aggregate(type_pipeline).to_list(None)
    content_types = {item["_id"]: item["count"] for item in type_results}

    # Estimated value calculation
    # Assuming each task saves ~30 min of human work at ~100 PLN/hour
    hourly_rate = 100
    time_per_task_minutes = 30
    total_all_tasks = await db.tasks.count_documents({"company_id": company_id, "status": "completed"})

    estimated_hours_saved = (total_all_tasks * time_per_task_minutes) / 60
    estimated_value_pln = estimated_hours_saved * hourly_rate

    estimated_value = {
        "hours_saved": round(estimated_hours_saved, 1),
        "estimated_value_pln": round(estimated_value_pln, 0),
        "avg_task_value_pln": round(time_per_task_minutes / 60 * hourly_rate, 0),
    }

    return AdvancedAnalytics(
        period=period,
        summary={
            "total_tasks": current_tasks,
            "completed_tasks": current_completed,
            "success_rate": round(current_completed / current_tasks * 100, 1) if current_tasks > 0 else 0,
            "agents_active": len(agent_performance),
        },
        trends=trends,
        agent_performance=agent_performance,
        hourly_distribution=hourly_distribution,
        content_types=content_types,
        estimated_value=estimated_value,
    )


@router.get("/agent/{agent_name}")
async def get_agent_analytics(
    agent_name: str,
    current_user: CurrentUser,
    db: Database,
    period: str = Query("month", description="Period: week, month, quarter"),
) -> dict[str, Any]:
    """Get detailed analytics for a specific agent."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id
    now = datetime.utcnow()

    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    start_date = now - timedelta(days=period_days)

    # Basic stats
    total = await db.tasks.count_documents({
        "company_id": company_id,
        "agent": agent_name,
        "created_at": {"$gte": start_date},
    })

    completed = await db.tasks.count_documents({
        "company_id": company_id,
        "agent": agent_name,
        "status": "completed",
        "created_at": {"$gte": start_date},
    })

    failed = await db.tasks.count_documents({
        "company_id": company_id,
        "agent": agent_name,
        "status": "failed",
        "created_at": {"$gte": start_date},
    })

    # Daily trend
    daily_pipeline = [
        {
            "$match": {
                "company_id": company_id,
                "agent": agent_name,
                "created_at": {"$gte": start_date},
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    daily_stats = await db.tasks.aggregate(daily_pipeline).to_list(None)

    # Feedback stats
    feedback_pipeline = [
        {"$match": {"company_id": company_id, "agent": agent_name}},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "sum_rating": {"$sum": "$rating"},
                "used_count": {"$sum": {"$cond": ["$used", 1, 0]}},
                "edited_count": {"$sum": {"$cond": ["$edited", 1, 0]}},
                "ratings": {"$push": "$rating"},
            }
        },
    ]
    feedback_results = await db.feedbacks.aggregate(feedback_pipeline).to_list(1)
    feedback = feedback_results[0] if feedback_results else {}

    # Rating distribution
    rating_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in feedback.get("ratings", []):
        rating_dist[str(r)] = rating_dist.get(str(r), 0) + 1

    fb_count = feedback.get("count", 0)

    return {
        "agent": agent_name,
        "period": period,
        "period_days": period_days,
        "summary": {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
        },
        "feedback": {
            "total_feedbacks": fb_count,
            "average_rating": round(feedback.get("sum_rating", 0) / fb_count, 2) if fb_count > 0 else None,
            "usage_rate": round(feedback.get("used_count", 0) / fb_count * 100, 1) if fb_count > 0 else 0,
            "edit_rate": round(feedback.get("edited_count", 0) / fb_count * 100, 1) if fb_count > 0 else 0,
            "rating_distribution": rating_dist,
        },
        "daily_trend": [
            {
                "date": item["_id"],
                "total": item["total"],
                "completed": item["completed"],
            }
            for item in daily_stats
        ],
    }


@router.get("/export")
async def export_analytics(
    current_user: CurrentUser,
    db: Database,
    format: str = Query("json", description="Export format: json, csv"),
    period: str = Query("month", description="Period: week, month, quarter"),
) -> dict[str, Any]:
    """Export analytics data."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company_id = current_user.company_id
    now = datetime.utcnow()

    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
    start_date = now - timedelta(days=period_days)

    # Get all tasks in period
    tasks = []
    async for task in db.tasks.find({
        "company_id": company_id,
        "created_at": {"$gte": start_date},
    }).sort("created_at", -1):
        tasks.append({
            "id": str(task["_id"]),
            "agent": task["agent"],
            "department": task["department"],
            "type": task["type"],
            "status": task["status"],
            "created_at": task["created_at"].isoformat(),
            "completed_at": task.get("completed_at", "").isoformat() if task.get("completed_at") else None,
        })

    if format == "csv":
        # Return CSV-ready structure
        headers = ["id", "agent", "department", "type", "status", "created_at", "completed_at"]
        rows = [[task.get(h, "") for h in headers] for task in tasks]
        return {
            "format": "csv",
            "headers": headers,
            "rows": rows,
            "total_rows": len(rows),
        }

    return {
        "format": "json",
        "period": period,
        "period_days": period_days,
        "exported_at": now.isoformat(),
        "total_records": len(tasks),
        "data": tasks,
    }
