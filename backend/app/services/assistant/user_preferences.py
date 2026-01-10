"""User Preferences - Long-term memory for agent personalization.

Tracks user preferences learned from conversation history to:
1. Provide smarter defaults
2. Skip unnecessary questions
3. Personalize agent responses

Stored in MongoDB as part of company settings.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from collections import Counter


@dataclass
class UserPreferences:
    """Learned and explicit user preferences for agent interactions.

    Attributes:
        # Learned from history (most frequently chosen values)
        preferred_tone: Most commonly selected tone
        preferred_platform: Most commonly selected platform
        preferred_audience: Most commonly selected target audience

        # Frequency counts for learning
        tone_history: Counter of tone selections
        platform_history: Counter of platform selections
        audience_history: Counter of audience selections

        # Explicit settings
        skip_recommendations: If True, use defaults without asking
        auto_approve: If True, skip confirmation step

        # Metadata
        updated_at: Last update timestamp
        total_tasks: Total number of completed tasks
    """

    # Learned preferences (derived from history)
    preferred_tone: str = "profesjonalny"
    preferred_platform: str = "instagram"
    preferred_audience: str = "ogólna"

    # History counters for learning
    tone_history: dict[str, int] = field(default_factory=dict)
    platform_history: dict[str, int] = field(default_factory=dict)
    audience_history: dict[str, int] = field(default_factory=dict)

    # Explicit user settings
    skip_recommendations: bool = False
    auto_approve: bool = False

    # Metadata
    updated_at: datetime | None = None
    total_tasks: int = 0

    def record_choice(self, param: str, value: str) -> None:
        """Record a user's choice to learn preferences.

        Args:
            param: Parameter name (tone, platform, target_audience)
            value: The value chosen by the user
        """
        if not value:
            return

        if param == "tone":
            self.tone_history[value] = self.tone_history.get(value, 0) + 1
            self._update_preferred("tone")
        elif param == "platform":
            self.platform_history[value] = self.platform_history.get(value, 0) + 1
            self._update_preferred("platform")
        elif param in ("target_audience", "audience"):
            self.audience_history[value] = self.audience_history.get(value, 0) + 1
            self._update_preferred("audience")

        self.updated_at = datetime.now(timezone.utc)

    def record_task_completion(self, params: dict[str, Any]) -> None:
        """Record a completed task to learn from all its parameters.

        Args:
            params: All parameters used for the task
        """
        self.total_tasks += 1

        # Record each relevant parameter
        if "tone" in params:
            self.record_choice("tone", params["tone"])
        if "platform" in params:
            self.record_choice("platform", params["platform"])
        if "target_audience" in params:
            self.record_choice("target_audience", params["target_audience"])

        self.updated_at = datetime.now(timezone.utc)

    def _update_preferred(self, category: str) -> None:
        """Update the preferred value for a category based on history.

        Args:
            category: One of 'tone', 'platform', 'audience'
        """
        if category == "tone" and self.tone_history:
            self.preferred_tone = max(self.tone_history, key=self.tone_history.get)
        elif category == "platform" and self.platform_history:
            self.preferred_platform = max(self.platform_history, key=self.platform_history.get)
        elif category == "audience" and self.audience_history:
            self.preferred_audience = max(self.audience_history, key=self.audience_history.get)

    def get_smart_defaults(self) -> dict[str, str]:
        """Get personalized default values based on learned preferences.

        Returns:
            Dictionary of default parameter values
        """
        return {
            "tone": self.preferred_tone,
            "platform": self.preferred_platform,
            "target_audience": self.preferred_audience,
        }

    def should_skip_recommendations(self) -> bool:
        """Check if we should skip asking for recommendations.

        Returns True if:
        1. User explicitly set skip_recommendations
        2. User has completed many tasks (experienced user)

        Returns:
            True if recommendations should be skipped
        """
        if self.skip_recommendations:
            return True

        # Experienced users (10+ tasks) might want faster flow
        # But only if they have consistent preferences
        if self.total_tasks >= 10:
            # Check if preferences are consistent (one choice > 70%)
            for history in [self.tone_history, self.platform_history]:
                if history:
                    total = sum(history.values())
                    max_count = max(history.values())
                    if max_count / total < 0.7:
                        return False  # Preferences vary, keep asking
            # Consistent preferences, could skip
            # But let's keep asking by default for now
            pass

        return False

    def get_preference_summary(self) -> str:
        """Get a human-readable summary of preferences.

        Returns:
            Summary string in Polish
        """
        parts = []

        if self.tone_history:
            parts.append(f"Preferowany ton: {self.preferred_tone}")
        if self.platform_history:
            parts.append(f"Preferowana platforma: {self.preferred_platform}")
        if self.audience_history:
            parts.append(f"Typowa grupa docelowa: {self.preferred_audience}")

        if self.total_tasks > 0:
            parts.append(f"Wykonanych zadań: {self.total_tasks}")

        return "\n".join(parts) if parts else "Brak zapisanych preferencji"

    def to_dict(self) -> dict[str, Any]:
        """Convert preferences to dictionary for MongoDB storage.

        Returns:
            Dictionary representation
        """
        return {
            "preferred_tone": self.preferred_tone,
            "preferred_platform": self.preferred_platform,
            "preferred_audience": self.preferred_audience,
            "tone_history": self.tone_history,
            "platform_history": self.platform_history,
            "audience_history": self.audience_history,
            "skip_recommendations": self.skip_recommendations,
            "auto_approve": self.auto_approve,
            "updated_at": self.updated_at,
            "total_tasks": self.total_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "UserPreferences":
        """Create UserPreferences from dictionary (MongoDB document).

        Args:
            data: Dictionary from MongoDB or None

        Returns:
            UserPreferences instance
        """
        if not data:
            return cls()

        return cls(
            preferred_tone=data.get("preferred_tone", "profesjonalny"),
            preferred_platform=data.get("preferred_platform", "instagram"),
            preferred_audience=data.get("preferred_audience", "ogólna"),
            tone_history=data.get("tone_history", {}),
            platform_history=data.get("platform_history", {}),
            audience_history=data.get("audience_history", {}),
            skip_recommendations=data.get("skip_recommendations", False),
            auto_approve=data.get("auto_approve", False),
            updated_at=data.get("updated_at"),
            total_tasks=data.get("total_tasks", 0),
        )

    def __repr__(self) -> str:
        return (
            f"UserPreferences(tone={self.preferred_tone}, "
            f"platform={self.preferred_platform}, "
            f"tasks={self.total_tasks}, "
            f"skip={self.skip_recommendations})"
        )


class PreferencesService:
    """Service for loading and saving user preferences from MongoDB."""

    def __init__(self, db):
        """Initialize with database connection.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def get_preferences(self, company_id: str) -> UserPreferences:
        """Load preferences for a company.

        Args:
            company_id: Company ID

        Returns:
            UserPreferences for the company
        """
        from bson import ObjectId

        company = await self.db.companies.find_one(
            {"_id": ObjectId(company_id)},
            {"user_preferences": 1}
        )

        if company and "user_preferences" in company:
            return UserPreferences.from_dict(company["user_preferences"])

        return UserPreferences()

    async def save_preferences(
        self,
        company_id: str,
        preferences: UserPreferences,
    ) -> None:
        """Save preferences for a company.

        Args:
            company_id: Company ID
            preferences: Preferences to save
        """
        from bson import ObjectId

        await self.db.companies.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": {"user_preferences": preferences.to_dict()}}
        )

    async def record_task_completion(
        self,
        company_id: str,
        params: dict[str, Any],
    ) -> UserPreferences:
        """Record a completed task and update preferences.

        Args:
            company_id: Company ID
            params: Parameters used for the task

        Returns:
            Updated preferences
        """
        preferences = await self.get_preferences(company_id)
        preferences.record_task_completion(params)
        await self.save_preferences(company_id, preferences)
        return preferences

    async def update_setting(
        self,
        company_id: str,
        setting: str,
        value: bool,
    ) -> UserPreferences:
        """Update an explicit preference setting.

        Args:
            company_id: Company ID
            setting: Setting name ('skip_recommendations' or 'auto_approve')
            value: New value

        Returns:
            Updated preferences
        """
        preferences = await self.get_preferences(company_id)

        if setting == "skip_recommendations":
            preferences.skip_recommendations = value
        elif setting == "auto_approve":
            preferences.auto_approve = value

        preferences.updated_at = datetime.utcnow()
        await self.save_preferences(company_id, preferences)
        return preferences

    async def learn_from_history(self, company_id: str) -> UserPreferences:
        """Analyze conversation history to learn preferences.

        Scans completed tasks in conversations to build preference profile.

        Args:
            company_id: Company ID

        Returns:
            Updated preferences based on history
        """
        from bson import ObjectId

        preferences = await self.get_preferences(company_id)

        # Find all conversations with completed tasks
        cursor = self.db.conversations.find(
            {
                "company_id": company_id,
                "context.extracted_params": {"$exists": True},
            },
            {"context.extracted_params": 1, "agent_state.gathered_params": 1}
        )

        async for conv in cursor:
            # Check both old and new param storage
            params = conv.get("context", {}).get("extracted_params", {})
            if not params:
                params = conv.get("agent_state", {}).get("gathered_params", {})

            if params:
                # Record without incrementing total_tasks (historical data)
                if "tone" in params:
                    preferences.tone_history[params["tone"]] = (
                        preferences.tone_history.get(params["tone"], 0) + 1
                    )
                if "platform" in params:
                    preferences.platform_history[params["platform"]] = (
                        preferences.platform_history.get(params["platform"], 0) + 1
                    )
                if "target_audience" in params:
                    preferences.audience_history[params["target_audience"]] = (
                        preferences.audience_history.get(params["target_audience"], 0) + 1
                    )

        # Update preferred values based on history
        preferences._update_preferred("tone")
        preferences._update_preferred("platform")
        preferences._update_preferred("audience")

        await self.save_preferences(company_id, preferences)
        return preferences
