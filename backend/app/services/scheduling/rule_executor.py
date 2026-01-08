"""Rule executor service for generating content from schedule rules."""

from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from app.models.schedule_rule import (
    ApprovalMode,
    ContentCategory,
    DEFAULT_PROMPTS,
)
from app.models.scheduled_content import ContentStatus


class RuleExecutor:
    """Executes schedule rules to generate content."""

    def __init__(self, db):
        self.db = db

    async def execute_rule(
        self,
        rule: dict,
        schedule_for: datetime | None = None,
    ) -> str:
        """
        Execute a schedule rule to generate content.

        Args:
            rule: The schedule rule document
            schedule_for: Optional specific time to schedule the content

        Returns:
            The ID of the created scheduled content
        """
        rule_id = str(rule["_id"])
        company_id = rule["company_id"]
        created_by = rule["created_by"]

        # Get company info for prompt
        company = await self.db.companies.find_one({"_id": ObjectId(company_id)})
        company_name = company.get("name", "Firma") if company else "Firma"
        industry = company.get("industry", "ogólna") if company else "ogólna"

        # Get brand settings for additional context
        brand_settings = company.get("brand_settings", {}) if company else {}

        # Build prompt
        template = rule.get("content_template", {})
        prompt = self._build_prompt(template, company_name, industry, brand_settings)

        # Generate content using AI agent
        generated_content = await self._generate_content(
            prompt=prompt,
            content_type=rule["content_type"],
            platform=rule["platform"],
            template=template,
            company_id=company_id,
        )

        # Determine status based on approval mode
        approval_mode = rule.get("approval_mode", ApprovalMode.REQUIRE_APPROVAL.value)
        if approval_mode == ApprovalMode.AUTO_PUBLISH.value:
            status = ContentStatus.SCHEDULED.value
        elif approval_mode == ApprovalMode.REQUIRE_APPROVAL.value:
            status = ContentStatus.PENDING_APPROVAL.value
        else:  # DRAFT_ONLY
            status = ContentStatus.DRAFT.value

        # Calculate scheduled time
        if schedule_for:
            scheduled_for = schedule_for
        elif approval_mode != ApprovalMode.DRAFT_ONLY.value:
            # Use schedule config to determine time
            schedule = rule.get("schedule", {})
            scheduled_for = self._calculate_publish_time(schedule)
        else:
            scheduled_for = None

        # Create scheduled content
        now = datetime.utcnow()
        content_doc = {
            "company_id": company_id,
            "created_by": created_by,
            "title": self._generate_title(generated_content, rule["name"]),
            "content_type": rule["content_type"],
            "platform": rule["platform"],
            "content": generated_content,
            "media_urls": [],  # TODO: Image generation in future
            "status": status,
            "scheduled_for": scheduled_for,
            "timezone": rule.get("schedule", {}).get("timezone", "Europe/Warsaw"),
            "published_at": None,
            "source_task_id": None,
            "source_conversation_id": None,
            "source_rule_id": rule_id,
            "platform_post_id": None,
            "platform_post_url": None,
            "engagement_stats": None,
            "error_message": None,
            "retry_count": 0,
            "max_retries": 3,
            "requires_approval": approval_mode == ApprovalMode.REQUIRE_APPROVAL.value,
            "approved_by": None,
            "approved_at": None,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.db.scheduled_content.insert_one(content_doc)
        content_id = str(result.inserted_id)

        # Update rule statistics
        await self.db.schedule_rules.update_one(
            {"_id": rule["_id"]},
            {
                "$set": {
                    "last_executed": now,
                    "last_error": None,
                    "updated_at": now,
                },
                "$inc": {"total_generated": 1},
            },
        )

        return content_id

    def _build_prompt(
        self,
        template: dict,
        company_name: str,
        industry: str,
        brand_settings: dict,
    ) -> str:
        """Build the prompt for content generation."""
        category = template.get("category", ContentCategory.CUSTOM.value)
        style = template.get("style", "profesjonalny")
        additional = template.get("additional_instructions", "")
        custom_prompt = template.get("prompt_template", "")

        # Get base prompt template
        base_prompt = DEFAULT_PROMPTS.get(
            ContentCategory(category),
            DEFAULT_PROMPTS[ContentCategory.CUSTOM]
        )

        # Format prompt with placeholders
        prompt = base_prompt.format(
            company_name=company_name,
            industry=industry,
            style=style,
            additional_instructions=additional,
            prompt_template=custom_prompt,
        )

        # Add brand context if available
        if brand_settings:
            brand_context = self._build_brand_context(brand_settings)
            if brand_context:
                prompt = f"{prompt}\n\nKontekst marki:\n{brand_context}"

        # Add hashtag/emoji instructions
        include_hashtags = template.get("include_hashtags", True)
        include_emoji = template.get("include_emoji", True)

        if include_hashtags:
            prompt += "\n\nDodaj odpowiednie hashtagi."
        if include_emoji:
            prompt += "\nUżyj emoji dla lepszego zaangażowania."

        return prompt

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
        if brand_settings.get("unique_selling_points"):
            usp = brand_settings["unique_selling_points"]
            if isinstance(usp, list):
                parts.append(f"Wyróżniki: {', '.join(usp)}")
            else:
                parts.append(f"Wyróżniki: {usp}")

        return "\n".join(parts)

    async def _generate_content(
        self,
        prompt: str,
        content_type: str,
        platform: str,
        template: dict,
        company_id: str,
    ) -> dict[str, Any]:
        """Generate content using AI agent."""
        # For now, we'll create a simple structure
        # In production, this would call the actual AI agent

        try:
            # Import the appropriate agent based on platform/content type
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
                # Generic content generation
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
            # Fallback: return placeholder content
            # In production, we'd handle this more gracefully
            return {
                "text": f"[Automatycznie wygenerowana treść]\n\n{prompt[:200]}...",
                "caption": f"[Automatycznie wygenerowana treść]",
                "error": str(e),
            }

    def _calculate_publish_time(self, schedule: dict) -> datetime:
        """Calculate the publish time from schedule config."""
        time_str = schedule.get("time", "08:00")
        hour, minute = map(int, time_str.split(":"))

        # Set to next occurrence based on schedule
        now = datetime.utcnow()
        publish_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has passed today, schedule for tomorrow
        if publish_time <= now:
            publish_time += timedelta(days=1)

        return publish_time

    def _generate_title(self, content: dict, rule_name: str) -> str:
        """Generate a title for the scheduled content."""
        text = content.get("text", content.get("caption", ""))

        if text:
            # Take first line or first 50 chars
            first_line = text.split("\n")[0]
            if len(first_line) > 50:
                return first_line[:50] + "..."
            return first_line

        # Fallback to rule name + date
        return f"{rule_name} - {datetime.utcnow().strftime('%d.%m.%Y')}"
