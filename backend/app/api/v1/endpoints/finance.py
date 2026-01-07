from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, Database
from app.schemas.finance import InvoiceTaskInput, CashflowTaskInput
from app.schemas.task import TaskResponse
from app.services.task_queue import get_task_queue

router = APIRouter(prefix="/agents/finance", tags=["finance"])


@router.post("/invoice", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_task(
    data: InvoiceTaskInput,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Create invoice generation task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Enable finance for all companies for now
    enabled_agents = company.get("enabled_agents", [])
    if "finance" not in enabled_agents:
        await db.companies.update_one(
            {"_id": ObjectId(current_user.company_id)},
            {"$addToSet": {"enabled_agents": "finance"}}
        )

    now = datetime.utcnow()
    task_input = {
        "client_name": data.client_name,
        "client_address": data.client_address,
        "items": [item.model_dump() for item in data.items],
        "notes": data.notes,
    }

    task_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "department": "finance",
        "agent": "invoice_worker",
        "type": "create_invoice",
        "input": task_input,
        "output": None,
        "status": "pending",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    result = await db.tasks.insert_one(task_doc)
    task_id = str(result.inserted_id)

    try:
        pool = await get_task_queue()
        await pool.enqueue_job("process_invoice_task", task_id, task_input)
    except Exception as e:
        await db.tasks.update_one(
            {"_id": result.inserted_id},
            {"$set": {"error": f"Queue error: {str(e)}", "status": "pending"}}
        )

    return TaskResponse(
        id=task_id,
        company_id=current_user.company_id,
        user_id=current_user.id or "",
        department="finance",
        agent="invoice_worker",
        type="create_invoice",
        input=task_input,
        output=None,
        status="pending",
        error=None,
        created_at=now,
        completed_at=None,
    )


@router.post("/cashflow", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_cashflow_task(
    data: CashflowTaskInput,
    current_user: CurrentUser,
    db: Database,
) -> TaskResponse:
    """Create cashflow analysis task."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    enabled_agents = company.get("enabled_agents", [])
    if "finance" not in enabled_agents:
        await db.companies.update_one(
            {"_id": ObjectId(current_user.company_id)},
            {"$addToSet": {"enabled_agents": "finance"}}
        )

    now = datetime.utcnow()
    task_input = {
        "income": [item.model_dump() for item in data.income],
        "expenses": [item.model_dump() for item in data.expenses],
        "period": data.period,
    }

    task_doc = {
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "department": "finance",
        "agent": "cashflow_analyst",
        "type": "analyze_cashflow",
        "input": task_input,
        "output": None,
        "status": "pending",
        "error": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }

    result = await db.tasks.insert_one(task_doc)
    task_id = str(result.inserted_id)

    try:
        pool = await get_task_queue()
        await pool.enqueue_job("process_cashflow_task", task_id, task_input)
    except Exception as e:
        await db.tasks.update_one(
            {"_id": result.inserted_id},
            {"$set": {"error": f"Queue error: {str(e)}", "status": "pending"}}
        )

    return TaskResponse(
        id=task_id,
        company_id=current_user.company_id,
        user_id=current_user.id or "",
        department="finance",
        agent="cashflow_analyst",
        type="analyze_cashflow",
        input=task_input,
        output=None,
        status="pending",
        error=None,
        created_at=now,
        completed_at=None,
    )
