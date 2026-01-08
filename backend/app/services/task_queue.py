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
from app.services.agents.brand_context import build_brand_context, get_fallback_context


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

        # Get company settings and knowledge
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
        company = await db.companies.find_one({"_id": ObjectId(task["company_id"])})

        company_settings = company.get("settings", {}) if company else {}
        company_knowledge = company.get("knowledge", {}) if company else {}

        # Build rich brand context
        brand_context = build_brand_context(
            knowledge=company_knowledge,
            settings=company_settings,
            agent_type="instagram",
        )

        # Fallback values for backward compatibility
        brand_voice, target_audience = get_fallback_context(company_settings)

        # Generate content with memory and brand context
        result = await generate_instagram_post(
            brief=task_input.get("brief", ""),
            brand_voice=brand_voice,
            target_audience=target_audience,
            language=company_settings.get("language", "pl"),
            include_hashtags=task_input.get("include_hashtags", True),
            post_type=task_input.get("post_type", "post"),
            company_id=task["company_id"],
            brand_context=brand_context,
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
        company_knowledge = company.get("knowledge", {}) if company else {}

        # Build rich brand context for copywriter
        brand_context = build_brand_context(
            knowledge=company_knowledge,
            settings=company_settings,
            agent_type="copywriter",
        )

        # Fallback values for backward compatibility
        brand_voice, target_audience = get_fallback_context(company_settings)

        result = await generate_marketing_copy(
            brief=task_input.get("brief", ""),
            copy_type=task_input.get("copy_type", "ad"),
            brand_voice=brand_voice,
            target_audience=target_audience,
            language=company_settings.get("language", "pl"),
            max_length=task_input.get("max_length"),
            company_id=task["company_id"],
            brand_context=brand_context,
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


async def process_schedule_rules(ctx: dict) -> dict:
    """
    Process schedule rules - check for rules that need execution.

    This should be run periodically (e.g., every hour via cron).
    """
    from datetime import timedelta

    db = await get_mongodb()
    now = datetime.utcnow()
    results = {"processed": 0, "errors": 0, "skipped": 0}

    # Find active rules that are due for execution
    cursor = db.schedule_rules.find({
        "is_active": True,
        "next_execution": {"$lte": now},
    })

    async for rule in cursor:
        rule_id = str(rule["_id"])

        try:
            # Check queue size
            queue_count = await db.scheduled_content.count_documents({
                "source_rule_id": rule_id,
                "status": {"$in": ["draft", "queued", "scheduled", "pending_approval"]},
            })

            if queue_count >= rule.get("max_queue_size", 4):
                results["skipped"] += 1
                # Still update next_execution to prevent repeated checks
                await _update_next_execution(db, rule)
                continue

            # Execute the rule
            from app.services.scheduling.rule_executor import RuleExecutor

            executor = RuleExecutor(db)
            await executor.execute_rule(rule)

            # Update next_execution
            await _update_next_execution(db, rule)

            results["processed"] += 1

        except Exception as e:
            # Log error and update rule
            await db.schedule_rules.update_one(
                {"_id": rule["_id"]},
                {
                    "$set": {
                        "last_error": str(e),
                        "updated_at": now,
                    }
                },
            )
            results["errors"] += 1

    return results


async def _update_next_execution(db, rule: dict) -> None:
    """Update the next_execution time for a rule."""
    from app.api.v1.endpoints.schedule_rules import _calculate_next_execution

    schedule = rule.get("schedule", {})
    next_exec = _calculate_next_execution(schedule)

    await db.schedule_rules.update_one(
        {"_id": rule["_id"]},
        {
            "$set": {
                "next_execution": next_exec,
                "updated_at": datetime.utcnow(),
            }
        },
    )


class WorkerSettings:
    """ARQ Worker settings."""

    functions = [
        process_instagram_task,
        process_copywriter_task,
        process_invoice_task,
        process_cashflow_task,
        process_schedule_rules,
    ]

    # Cron jobs for periodic tasks
    cron_jobs = [
        # Run schedule rules processor every hour
        {
            "coroutine": process_schedule_rules,
            "hour": {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},
            "minute": 0,
        },
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
