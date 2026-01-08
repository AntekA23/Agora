"""Publication worker for automatically publishing scheduled content."""

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.models.platform_credentials import (
    PlatformCredentials,
    ConnectionStatus,
    PLATFORM_CREDENTIALS_COLLECTION,
)
from app.models.scheduled_content import ContentStatus
from app.services.publishers import get_publisher
from app.services.notification_service import NotificationService


class PublicationWorker:
    """Worker that processes and publishes scheduled content."""

    def __init__(self, db):
        self.db = db
        self.notification_service = NotificationService(db)

    async def process_scheduled_publications(self) -> dict[str, Any]:
        """
        Process all content scheduled for publication.

        This should be called periodically (e.g., every minute).

        Returns:
            Statistics about processed content
        """
        now = datetime.utcnow()
        window_end = now + timedelta(minutes=2)

        results = {
            "processed": 0,
            "published": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        # Find content scheduled for publication in the next 2 minutes
        cursor = self.db.scheduled_content.find({
            "status": ContentStatus.SCHEDULED.value,
            "scheduled_for": {"$lte": window_end},
        })

        async for content in cursor:
            content_id = str(content["_id"])
            results["processed"] += 1

            try:
                # Get platform credentials
                credentials = await self._get_credentials(
                    company_id=content["company_id"],
                    platform=content["platform"],
                )

                if not credentials:
                    # No credentials - mark as failed
                    await self._mark_failed(
                        content_id=content_id,
                        error="No platform credentials configured",
                    )
                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": content_id,
                        "error": "No credentials",
                    })
                    continue

                if credentials.get("status") != ConnectionStatus.CONNECTED.value:
                    # Credentials not connected
                    await self._mark_failed(
                        content_id=content_id,
                        error="Platform not connected",
                    )
                    results["failed"] += 1
                    continue

                # Get the appropriate publisher
                try:
                    publisher = get_publisher(content["platform"])
                except ValueError:
                    await self._mark_failed(
                        content_id=content_id,
                        error=f"No publisher for platform: {content['platform']}",
                    )
                    results["failed"] += 1
                    continue

                # Update status to publishing
                await self.db.scheduled_content.update_one(
                    {"_id": content["_id"]},
                    {"$set": {"status": ContentStatus.PUBLISHING.value, "updated_at": now}},
                )

                # Build credentials object
                creds = PlatformCredentials(
                    company_id=content["company_id"],
                    platform=credentials["platform"],
                    status=ConnectionStatus(credentials["status"]),
                    access_token=credentials.get("access_token"),
                    refresh_token=credentials.get("refresh_token"),
                    platform_user_id=credentials.get("platform_user_id"),
                    platform_page_id=credentials.get("platform_page_id"),
                )

                # Publish the content
                result = await publisher.publish(
                    content=content.get("content", {}),
                    credentials=creds,
                    media_urls=content.get("media_urls", []),
                )

                if result.success:
                    # Update content as published
                    await self.db.scheduled_content.update_one(
                        {"_id": content["_id"]},
                        {
                            "$set": {
                                "status": ContentStatus.PUBLISHED.value,
                                "published_at": result.published_at or now,
                                "platform_post_id": result.post_id,
                                "platform_post_url": result.post_url,
                                "error_message": None,
                                "updated_at": now,
                            }
                        },
                    )

                    # Update credentials usage stats
                    await self.db[PLATFORM_CREDENTIALS_COLLECTION].update_one(
                        {"company_id": content["company_id"], "platform": content["platform"]},
                        {
                            "$set": {"last_used_at": now, "last_error": None},
                            "$inc": {"total_posts_published": 1},
                        },
                    )

                    # Send success notification
                    await self.notification_service.notify_content_published(
                        company_id=content["company_id"],
                        user_id=content["created_by"],
                        content_id=content_id,
                        content_title=content.get("title", "Treść"),
                        platform=content["platform"],
                    )

                    results["published"] += 1

                else:
                    # Publication failed
                    retry_count = content.get("retry_count", 0) + 1
                    max_retries = content.get("max_retries", 3)

                    if retry_count < max_retries:
                        # Schedule for retry
                        new_status = ContentStatus.SCHEDULED.value
                        new_scheduled_for = now + timedelta(minutes=5 * retry_count)
                    else:
                        # Max retries reached
                        new_status = ContentStatus.FAILED.value
                        new_scheduled_for = content.get("scheduled_for")

                    await self.db.scheduled_content.update_one(
                        {"_id": content["_id"]},
                        {
                            "$set": {
                                "status": new_status,
                                "scheduled_for": new_scheduled_for,
                                "error_message": result.error_message,
                                "retry_count": retry_count,
                                "updated_at": now,
                            }
                        },
                    )

                    # Update credentials with error
                    await self.db[PLATFORM_CREDENTIALS_COLLECTION].update_one(
                        {"company_id": content["company_id"], "platform": content["platform"]},
                        {"$set": {"last_error": result.error_message}},
                    )

                    if new_status == ContentStatus.FAILED.value:
                        # Send failure notification
                        await self.notification_service.notify_content_failed(
                            company_id=content["company_id"],
                            user_id=content["created_by"],
                            content_id=content_id,
                            content_title=content.get("title", "Treść"),
                            error_message=result.error_message or "Unknown error",
                        )

                    results["failed"] += 1
                    results["errors"].append({
                        "content_id": content_id,
                        "error": result.error_message,
                    })

            except Exception as e:
                await self._mark_failed(content_id=content_id, error=str(e))
                results["failed"] += 1
                results["errors"].append({
                    "content_id": content_id,
                    "error": str(e),
                })

        return results

    async def _get_credentials(self, company_id: str, platform: str) -> dict | None:
        """Get platform credentials for a company."""
        return await self.db[PLATFORM_CREDENTIALS_COLLECTION].find_one({
            "company_id": company_id,
            "platform": platform,
        })

    async def _mark_failed(self, content_id: str, error: str) -> None:
        """Mark content as failed."""
        await self.db.scheduled_content.update_one(
            {"_id": ObjectId(content_id)},
            {
                "$set": {
                    "status": ContentStatus.FAILED.value,
                    "error_message": error,
                    "updated_at": datetime.utcnow(),
                }
            },
        )


async def process_publications(ctx: dict) -> dict:
    """ARQ task for processing scheduled publications."""
    from app.services.task_queue import get_mongodb

    db = await get_mongodb()
    worker = PublicationWorker(db)
    return await worker.process_scheduled_publications()
