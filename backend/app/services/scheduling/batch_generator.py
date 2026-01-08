"""Batch content generator service for generating multiple pieces of content at once."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.models.scheduled_content import ContentStatus
from app.services.scheduling.intelligence import SchedulingIntelligence


class BatchGenerator:
    """Generates multiple pieces of content at once."""

    def __init__(self, db):
        self.db = db
        self.scheduling_intelligence = SchedulingIntelligence(db)

    async def generate_batch(
        self,
        company_id: str,
        user_id: str,
        content_type: str,
        platform: str,
        count: int,
        theme: str,
        variety: str = "medium",
        date_range: dict | None = None,
        auto_schedule: bool = True,
        require_approval: bool = False,
    ) -> dict[str, Any]:
        """
        Generate a batch of content.

        Args:
            company_id: Company ID
            user_id: User who initiated the batch
            content_type: Type of content (e.g., "instagram_post")
            platform: Target platform
            count: Number of pieces to generate (1-30)
            theme: Main theme/topic for the batch
            variety: Content variety level ("low", "medium", "high")
            date_range: Optional date range for scheduling
            auto_schedule: Whether to auto-schedule content
            require_approval: Whether content requires approval

        Returns:
            Dict with generated content and scheduling info
        """
        # Validate count
        count = max(1, min(30, count))

        # Get company context
        company = await self.db.companies.find_one({"_id": ObjectId(company_id)})
        company_name = company.get("name", "Firma") if company else "Firma"
        industry = company.get("industry", "ogólna") if company else "ogólna"
        brand_settings = company.get("brand_settings", {}) if company else {}

        # Generate varied prompts based on theme
        prompts = self._generate_varied_prompts(
            theme=theme,
            count=count,
            variety=variety,
            company_name=company_name,
            industry=industry,
            brand_settings=brand_settings,
            platform=platform,
        )

        # Generate content for each prompt
        generated_items = []
        for i, prompt in enumerate(prompts):
            try:
                content = await self._generate_single_content(
                    prompt=prompt,
                    content_type=content_type,
                    platform=platform,
                    company_id=company_id,
                )
                generated_items.append({
                    "index": i,
                    "prompt": prompt,
                    "content": content,
                    "status": "success",
                })
            except Exception as e:
                generated_items.append({
                    "index": i,
                    "prompt": prompt,
                    "content": None,
                    "status": "failed",
                    "error": str(e),
                })

        # Schedule content if requested
        scheduled_items = []
        if auto_schedule:
            successful_items = [item for item in generated_items if item["status"] == "success"]
            scheduled_items = await self._schedule_batch(
                items=successful_items,
                company_id=company_id,
                user_id=user_id,
                content_type=content_type,
                platform=platform,
                theme=theme,
                date_range=date_range,
                require_approval=require_approval,
            )

        return {
            "total_requested": count,
            "total_generated": len([i for i in generated_items if i["status"] == "success"]),
            "total_failed": len([i for i in generated_items if i["status"] == "failed"]),
            "total_scheduled": len(scheduled_items),
            "generated_items": generated_items,
            "scheduled_items": scheduled_items,
        }

    def _generate_varied_prompts(
        self,
        theme: str,
        count: int,
        variety: str,
        company_name: str,
        industry: str,
        brand_settings: dict,
        platform: str,
    ) -> list[str]:
        """Generate varied prompts for batch content."""
        prompts = []

        # Variety modifiers
        variety_angles = {
            "low": [
                "profesjonalnie",
            ],
            "medium": [
                "profesjonalnie",
                "inspirująco",
                "edukacyjnie",
                "zabawnie",
            ],
            "high": [
                "profesjonalnie",
                "inspirująco",
                "edukacyjnie",
                "zabawnie",
                "emocjonalnie",
                "storytellingowo",
                "za kulisami",
                "z perspektywy klienta",
            ],
        }

        angles = variety_angles.get(variety, variety_angles["medium"])

        # Content types for variety
        content_hooks = [
            "Zacznij od pytania do odbiorców",
            "Zacznij od ciekawostki",
            "Zacznij od osobistej historii",
            "Zacznij od statystyki",
            "Zacznij od cytatu",
            "Zacznij od wyzwania",
            "Zacznij od porady dnia",
            "Zacznij od behind-the-scenes",
        ]

        # Build brand context
        brand_context = self._build_brand_context(brand_settings)

        for i in range(count):
            angle = angles[i % len(angles)]
            hook = content_hooks[i % len(content_hooks)]

            prompt = f"""Stwórz post na {platform} dla firmy {company_name} (branża: {industry}).

Temat główny: {theme}

Styl: {angle}
{hook}

{brand_context}

Dodaj odpowiednie hashtagi i emoji.
Post powinien być unikalny i angażujący.
Post nr {i + 1} z {count} - zadbaj o różnorodność!"""

            prompts.append(prompt)

        return prompts

    def _build_brand_context(self, brand_settings: dict) -> str:
        """Build brand context string from settings."""
        parts = []

        if brand_settings.get("tone"):
            parts.append(f"Ton komunikacji: {brand_settings['tone']}")
        if brand_settings.get("target_audience"):
            parts.append(f"Grupa docelowa: {brand_settings['target_audience']}")
        if brand_settings.get("brand_values"):
            values = brand_settings["brand_values"]
            if isinstance(values, list):
                parts.append(f"Wartości marki: {', '.join(values)}")
            else:
                parts.append(f"Wartości marki: {values}")

        if parts:
            return "Kontekst marki:\n" + "\n".join(parts)
        return ""

    async def _generate_single_content(
        self,
        prompt: str,
        content_type: str,
        platform: str,
        company_id: str,
    ) -> dict[str, Any]:
        """Generate a single piece of content."""
        try:
            if platform == "instagram" or content_type.startswith("instagram"):
                from app.services.agents.marketing.instagram import InstagramSpecialist

                agent = InstagramSpecialist()
                result = await agent.generate_post(
                    prompt=prompt,
                    company_id=company_id,
                )
                return {
                    "text": result.get("post_text", result.get("caption", "")),
                    "caption": result.get("caption", result.get("post_text", "")),
                    "hashtags": result.get("hashtags", []),
                }
            else:
                from app.services.agents.marketing.copywriter import Copywriter

                agent = Copywriter()
                result = await agent.generate_content(
                    prompt=prompt,
                    company_id=company_id,
                )
                return {
                    "text": result.get("content", result.get("text", "")),
                    "caption": result.get("content", result.get("text", "")),
                }

        except Exception as e:
            # Return placeholder on error
            return {
                "text": f"[Treść do uzupełnienia]\n\nTemat: {prompt[:100]}...",
                "caption": "[Treść do uzupełnienia]",
                "error": str(e),
            }

    async def _schedule_batch(
        self,
        items: list[dict],
        company_id: str,
        user_id: str,
        content_type: str,
        platform: str,
        theme: str,
        date_range: dict | None,
        require_approval: bool,
    ) -> list[dict]:
        """Schedule generated batch content."""
        if not items:
            return []

        # Calculate time slots
        time_slots = await self._calculate_batch_slots(
            company_id=company_id,
            platform=platform,
            count=len(items),
            date_range=date_range,
        )

        scheduled = []
        now = datetime.utcnow()

        for i, (item, slot) in enumerate(zip(items, time_slots)):
            content = item["content"]
            if not content:
                continue

            # Determine status
            if require_approval:
                status = ContentStatus.PENDING_APPROVAL.value
            else:
                status = ContentStatus.SCHEDULED.value

            # Generate title
            text = content.get("text", content.get("caption", ""))
            title = self._generate_title(text, theme, i + 1)

            # Create scheduled content document
            doc = {
                "company_id": company_id,
                "created_by": user_id,
                "title": title,
                "content_type": content_type,
                "platform": platform,
                "content": content,
                "media_urls": [],
                "status": status,
                "scheduled_for": slot,
                "timezone": "Europe/Warsaw",
                "published_at": None,
                "source_task_id": None,
                "source_conversation_id": None,
                "source_rule_id": None,
                "source_batch_id": None,  # Could add batch tracking
                "platform_post_id": None,
                "platform_post_url": None,
                "engagement_stats": None,
                "error_message": None,
                "retry_count": 0,
                "max_retries": 3,
                "requires_approval": require_approval,
                "approved_by": None,
                "approved_at": None,
                "created_at": now,
                "updated_at": now,
            }

            result = await self.db.scheduled_content.insert_one(doc)

            scheduled.append({
                "id": str(result.inserted_id),
                "title": title,
                "scheduled_for": slot.isoformat() if slot else None,
                "status": status,
            })

        return scheduled

    async def _calculate_batch_slots(
        self,
        company_id: str,
        platform: str,
        count: int,
        date_range: dict | None,
    ) -> list[datetime]:
        """Calculate optimal time slots for batch content."""
        now = datetime.utcnow()

        # Determine date range
        if date_range:
            start_date = datetime.fromisoformat(date_range.get("start", now.isoformat()))
            end_date = datetime.fromisoformat(date_range.get("end", (now + timedelta(days=7)).isoformat()))
        else:
            start_date = now + timedelta(hours=1)  # Start at least 1 hour from now
            end_date = now + timedelta(days=7)  # Default to 1 week

        # Get optimal times for platform
        optimal_hours = self._get_platform_optimal_hours(platform)

        # Get existing scheduled content to avoid collisions
        existing = await self.db.scheduled_content.find({
            "company_id": company_id,
            "platform": platform,
            "status": {"$in": ["scheduled", "pending_approval", "queued"]},
            "scheduled_for": {"$gte": start_date, "$lte": end_date},
        }).to_list(length=100)

        existing_times = {doc["scheduled_for"] for doc in existing if doc.get("scheduled_for")}

        # Generate slots
        slots = []
        current_date = start_date

        while len(slots) < count and current_date <= end_date:
            # Try each optimal hour
            for hour in optimal_hours:
                if len(slots) >= count:
                    break

                slot = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)

                # Skip if in the past
                if slot <= now:
                    continue

                # Skip if too close to existing content (within 2 hours)
                too_close = any(
                    abs((slot - existing).total_seconds()) < 7200
                    for existing in existing_times
                )
                if too_close:
                    continue

                slots.append(slot)
                existing_times.add(slot)  # Mark as used

            current_date += timedelta(days=1)

        # If we still don't have enough slots, fill remaining with any available times
        while len(slots) < count:
            last_slot = slots[-1] if slots else start_date
            next_slot = last_slot + timedelta(hours=6)
            if next_slot > end_date:
                next_slot = end_date
            slots.append(next_slot)

        return slots[:count]

    def _get_platform_optimal_hours(self, platform: str) -> list[int]:
        """Get optimal posting hours for platform."""
        optimal_hours = {
            "instagram": [8, 12, 18, 21],
            "facebook": [9, 13, 16, 19],
            "linkedin": [7, 12, 17],
            "twitter": [8, 12, 17, 21],
            "email": [9, 14],
        }
        return optimal_hours.get(platform, [9, 12, 18])

    def _generate_title(self, text: str, theme: str, index: int) -> str:
        """Generate a title for scheduled content."""
        if text:
            first_line = text.split("\n")[0]
            # Remove emojis and hashtags for cleaner title
            clean_line = "".join(c for c in first_line if not c.startswith("#"))
            if len(clean_line) > 50:
                return clean_line[:50].strip() + "..."
            if clean_line.strip():
                return clean_line.strip()

        return f"{theme} #{index}"
