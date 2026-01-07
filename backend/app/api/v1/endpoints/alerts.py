"""Alerts and Monitoring API endpoints."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.monitoring import (
    AlertService,
    AlertType,
    AlertPriority,
    CashflowMonitor,
    InvoiceMonitor,
    ContentMonitor,
    TrendMonitor,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============================================================================
# SCHEMAS
# ============================================================================


class AlertResponse(BaseModel):
    """Alert response schema."""
    id: str
    type: str
    priority: str
    title: str
    message: str
    data: dict = {}
    action_url: str | None = None
    action_label: str | None = None
    suggested_actions: list[str] = []
    read: bool
    created_at: datetime


class AlertCountResponse(BaseModel):
    """Alert count response."""
    total: int
    urgent: int
    high: int
    medium: int
    low: int


class CashflowCheckRequest(BaseModel):
    """Request for cashflow check."""
    current_balance: float
    monthly_expenses: float
    low_balance_threshold: float | None = None
    recent_transactions: list[dict] | None = None


class InvoiceCheckRequest(BaseModel):
    """Request for invoice check."""
    invoices: list[dict] = Field(..., min_length=1)
    reminder_days_before: int = 3


class ContentCheckRequest(BaseModel):
    """Request for content check."""
    scheduled_posts: list[dict] = []
    days_to_check: int = 7
    min_posts_per_week: int = 3


class TrendScanRequest(BaseModel):
    """Request for trend scan."""
    industry: str = Field(..., min_length=2)
    keywords: list[str] | None = None
    competitors: list[str] | None = None


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================


@router.get("", response_model=list[AlertResponse])
async def get_alerts(
    current_user: CurrentUser,
    db: Database,
    unread_only: bool = Query(False),
    priority: str | None = Query(None),
    alert_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> list[AlertResponse]:
    """Get alerts for the company."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    alert_service = AlertService(db)

    priority_enum = AlertPriority(priority) if priority else None
    type_enum = AlertType(alert_type) if alert_type else None

    alerts = await alert_service.get_alerts(
        company_id=current_user.company_id,
        unread_only=unread_only,
        priority=priority_enum,
        alert_type=type_enum,
        limit=limit,
    )

    return [
        AlertResponse(
            id=a.id,
            type=a.type.value,
            priority=a.priority.value,
            title=a.title,
            message=a.message,
            data=a.data,
            action_url=a.action_url,
            action_label=a.action_label,
            suggested_actions=a.suggested_actions,
            read=a.read,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.get("/count", response_model=AlertCountResponse)
async def get_alert_count(
    current_user: CurrentUser,
    db: Database,
) -> AlertCountResponse:
    """Get count of unread alerts."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    alert_service = AlertService(db)
    counts = await alert_service.get_unread_count(current_user.company_id)

    return AlertCountResponse(**counts)


@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Mark an alert as read."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    alert_service = AlertService(db)
    success = await alert_service.mark_as_read(alert_id, current_user.company_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return {"status": "read", "alert_id": alert_id}


@router.post("/read-all")
async def mark_all_alerts_read(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Mark all alerts as read."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    alert_service = AlertService(db)
    count = await alert_service.mark_all_as_read(current_user.company_id)

    return {"status": "all_read", "count": count}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Dismiss an alert."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    alert_service = AlertService(db)
    success = await alert_service.dismiss_alert(alert_id, current_user.company_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return {"status": "dismissed", "alert_id": alert_id}


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================


@router.post("/monitor/cashflow")
async def run_cashflow_monitor(
    data: CashflowCheckRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Run cashflow monitor and generate alerts."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    monitor = CashflowMonitor(db)
    alerts = await monitor.check_company(
        company_id=current_user.company_id,
        current_balance=data.current_balance,
        monthly_expenses=data.monthly_expenses,
        low_balance_threshold=data.low_balance_threshold,
        recent_transactions=data.recent_transactions,
    )

    return {
        "success": True,
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@router.post("/monitor/invoices")
async def run_invoice_monitor(
    data: InvoiceCheckRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Run invoice monitor and generate alerts."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    monitor = InvoiceMonitor(db)
    alerts = await monitor.check_invoices(
        company_id=current_user.company_id,
        invoices=data.invoices,
        reminder_days_before=data.reminder_days_before,
    )

    return {
        "success": True,
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@router.post("/monitor/content")
async def run_content_monitor(
    data: ContentCheckRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Run content calendar monitor and generate alerts."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    monitor = ContentMonitor(db)
    alerts = await monitor.check_content_calendar(
        company_id=current_user.company_id,
        scheduled_posts=data.scheduled_posts,
        days_to_check=data.days_to_check,
        min_posts_per_week=data.min_posts_per_week,
    )

    return {
        "success": True,
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@router.post("/monitor/trends")
async def run_trend_monitor(
    data: TrendScanRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Scan for industry trends and generate alerts."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    monitor = TrendMonitor(db)
    alerts = await monitor.scan_industry_trends(
        company_id=current_user.company_id,
        industry=data.industry,
        keywords=data.keywords,
        competitors=data.competitors,
    )

    return {
        "success": True,
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@router.get("/monitor/trends/report")
async def get_trend_report(
    current_user: CurrentUser,
    db: Database,
    industry: str = Query(...),
    period: str = Query("weekly"),
) -> dict[str, Any]:
    """Get a comprehensive trend report."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    monitor = TrendMonitor(db)
    report = await monitor.get_trend_report(
        company_id=current_user.company_id,
        industry=industry,
        period=period,
    )

    return report
