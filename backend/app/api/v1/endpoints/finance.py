from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, Database
from app.schemas.finance import InvoiceTaskInput, CashflowTaskInput
from app.schemas.task import TaskResponse
from app.services.task_queue import get_task_queue
from app.services.agents.tools.pdf_generator import pdf_generator

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


# ============================================================================
# PDF GENERATION ENDPOINTS
# ============================================================================


@router.get("/tasks/{task_id}/pdf")
async def get_invoice_pdf(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> Response:
    """Generate PDF for a completed invoice task."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    # Get task
    try:
        task = await db.tasks.find_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
            "agent": "invoice_worker",
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed yet")

    # Get company data for seller info
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Get knowledge base for company details
    knowledge = company.get("knowledge", {})

    # Prepare invoice data
    task_input = task["input"]
    task_output = task.get("output", {})

    # Generate invoice number
    invoice_count = await db.tasks.count_documents({
        "company_id": current_user.company_id,
        "agent": "invoice_worker",
        "status": "completed",
    })
    invoice_number = f"FV/{datetime.now().year}/{invoice_count:04d}"

    # Generate PDF
    pdf_bytes = pdf_generator.generate_invoice_pdf(
        invoice_number=invoice_number,
        seller_name=company["name"],
        seller_address=knowledge.get("company_description", ""),
        seller_nip=knowledge.get("custom_facts", [""])[0] if knowledge.get("custom_facts") else "",
        seller_email=knowledge.get("social_media", {}).get("email", ""),
        client_name=task_input.get("client_name", ""),
        client_address=task_input.get("client_address", ""),
        items=task_input.get("items", []),
        notes=task_input.get("notes", ""),
        bank_account=knowledge.get("custom_facts", ["", ""])[1] if len(knowledge.get("custom_facts", [])) > 1 else "",
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{invoice_number.replace("/", "-")}.pdf"'
        }
    )


@router.get("/tasks/{task_id}/report-pdf")
async def get_cashflow_report_pdf(
    task_id: str,
    current_user: CurrentUser,
    db: Database,
) -> Response:
    """Generate PDF report for a completed cashflow analysis task."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    try:
        task = await db.tasks.find_one({
            "_id": ObjectId(task_id),
            "company_id": current_user.company_id,
            "agent": "cashflow_analyst",
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task not completed yet")

    task_output = task.get("output", {})
    task_input = task["input"]

    # Generate PDF
    pdf_bytes = pdf_generator.generate_report_pdf(
        title="Analiza Cashflow",
        subtitle=f"Okres: {task_input.get('period', 'nieznany')}",
        content=task_output.get("content", "Brak danych"),
        total_income=task_output.get("total_income", 0),
        total_expenses=task_output.get("total_expenses", 0),
        balance=task_output.get("balance", 0),
        show_summary=True,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cashflow-report-{task_id[:8]}.pdf"'
        }
    )
