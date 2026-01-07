import asyncio
from datetime import datetime
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.services.agents.marketing.instagram import generate_instagram_post
from app.services.agents.marketing.copywriter import generate_marketing_copy
from app.services.agents.finance.invoice import generate_invoice_draft, analyze_cashflow


async def get_mongodb():
    """Get MongoDB client for worker."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB_NAME]


async def process_instagram_task(ctx: dict, task_id: str, task_input: dict[str, Any]) -> dict:
    """Process Instagram content generation task."""
    db = await get_mongodb()

    try:
        # Update status to processing
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )

        # Get company settings
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        company = await db.companies.find_one({"_id": ObjectId(task["company_id"])})

        company_settings = company.get("settings", {}) if company else {}

        # Generate content with memory
        result = await generate_instagram_post(
            brief=task_input.get("brief", ""),
            brand_voice=company_settings.get("brand_voice", "profesjonalny"),
            target_audience=company_settings.get("target_audience", ""),
            language=company_settings.get("language", "pl"),
            include_hashtags=task_input.get("include_hashtags", True),
            post_type=task_input.get("post_type", "post"),
            company_id=task["company_id"],
        )

        # Update task with result
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "completed",
                    "output": result,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result

    except Exception as e:
        # Update task with error
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        raise


async def process_copywriter_task(ctx: dict, task_id: str, task_input: dict[str, Any]) -> dict:
    """Process copywriting task."""
    db = await get_mongodb()

    try:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        company = await db.companies.find_one({"_id": ObjectId(task["company_id"])})

        company_settings = company.get("settings", {}) if company else {}

        result = await generate_marketing_copy(
            brief=task_input.get("brief", ""),
            copy_type=task_input.get("copy_type", "ad"),
            brand_voice=company_settings.get("brand_voice", "profesjonalny"),
            target_audience=company_settings.get("target_audience", ""),
            language=company_settings.get("language", "pl"),
            max_length=task_input.get("max_length"),
            company_id=task["company_id"],
        )

        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "completed",
                    "output": result,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result

    except Exception as e:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        raise


async def process_invoice_task(ctx: dict, task_id: str, task_input: dict[str, Any]) -> dict:
    """Process invoice generation task."""
    db = await get_mongodb()

    try:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        company = await db.companies.find_one({"_id": ObjectId(task["company_id"])})
        company_settings = company.get("settings", {}) if company else {}

        result = await generate_invoice_draft(
            client_name=task_input.get("client_name", ""),
            client_address=task_input.get("client_address", ""),
            items=task_input.get("items", []),
            notes=task_input.get("notes", ""),
            language=company_settings.get("language", "pl"),
        )

        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "completed",
                    "output": result,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result

    except Exception as e:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        raise


async def process_cashflow_task(ctx: dict, task_id: str, task_input: dict[str, Any]) -> dict:
    """Process cashflow analysis task."""
    db = await get_mongodb()

    try:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
        )

        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        company = await db.companies.find_one({"_id": ObjectId(task["company_id"])})
        company_settings = company.get("settings", {}) if company else {}

        result = await analyze_cashflow(
            income=task_input.get("income", []),
            expenses=task_input.get("expenses", []),
            period=task_input.get("period", "miesiac"),
            language=company_settings.get("language", "pl"),
        )

        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "completed",
                    "output": result,
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        return result

    except Exception as e:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        raise


class WorkerSettings:
    """ARQ Worker settings."""

    functions = [
        process_instagram_task,
        process_copywriter_task,
        process_invoice_task,
        process_cashflow_task,
    ]

    @staticmethod
    def redis_settings() -> RedisSettings:
        # Parse Redis URL
        url = settings.REDIS_URL
        if url.startswith("redis://"):
            url = url[8:]
        host, port = url.split(":") if ":" in url else (url, "6379")
        return RedisSettings(host=host, port=int(port))


async def get_task_queue() -> ArqRedis:
    """Get ARQ Redis pool for enqueueing tasks."""
    return await create_pool(WorkerSettings.redis_settings())
