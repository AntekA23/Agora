from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.services.cache import get_cache_service, CacheService

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
