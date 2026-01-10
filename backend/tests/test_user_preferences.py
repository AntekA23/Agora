"""Tests for UserPreferences model and service."""

import pytest
from datetime import datetime, timezone

from app.services.assistant.user_preferences import UserPreferences, PreferencesService


class TestUserPreferences:
    """Unit tests for UserPreferences model."""

    def test_default_values(self):
        """Test that default preferences are set correctly."""
        prefs = UserPreferences()

        assert prefs.preferred_tone == "profesjonalny"
        assert prefs.preferred_platform == "instagram"
        assert prefs.preferred_audience == "ogólna"
        assert prefs.skip_recommendations is False
        assert prefs.auto_approve is False
        assert prefs.total_tasks == 0

    def test_record_choice_tone(self):
        """Test recording tone choices updates history and preference."""
        prefs = UserPreferences()

        prefs.record_choice("tone", "casualowy")
        prefs.record_choice("tone", "casualowy")
        prefs.record_choice("tone", "profesjonalny")

        assert prefs.tone_history == {"casualowy": 2, "profesjonalny": 1}
        assert prefs.preferred_tone == "casualowy"  # Most frequent
        assert prefs.updated_at is not None

    def test_record_choice_platform(self):
        """Test recording platform choices."""
        prefs = UserPreferences()

        prefs.record_choice("platform", "facebook")
        prefs.record_choice("platform", "facebook")
        prefs.record_choice("platform", "instagram")

        assert prefs.platform_history == {"facebook": 2, "instagram": 1}
        assert prefs.preferred_platform == "facebook"

    def test_record_choice_audience(self):
        """Test recording audience choices with both param names."""
        prefs = UserPreferences()

        prefs.record_choice("target_audience", "młodzi")
        prefs.record_choice("audience", "młodzi")  # Alias
        prefs.record_choice("target_audience", "dorośli")

        assert prefs.audience_history == {"młodzi": 2, "dorośli": 1}
        assert prefs.preferred_audience == "młodzi"

    def test_record_choice_empty_value(self):
        """Test that empty values are ignored."""
        prefs = UserPreferences()

        prefs.record_choice("tone", "")
        prefs.record_choice("tone", None)

        assert prefs.tone_history == {}
        assert prefs.preferred_tone == "profesjonalny"  # Default unchanged

    def test_record_task_completion(self):
        """Test recording a completed task updates all relevant params."""
        prefs = UserPreferences()

        prefs.record_task_completion({
            "tone": "zabawny",
            "platform": "linkedin",
            "target_audience": "firmy",
            "irrelevant_param": "ignored",
        })

        assert prefs.total_tasks == 1
        assert prefs.tone_history == {"zabawny": 1}
        assert prefs.platform_history == {"linkedin": 1}
        assert prefs.audience_history == {"firmy": 1}
        assert prefs.preferred_tone == "zabawny"
        assert prefs.preferred_platform == "linkedin"
        assert prefs.preferred_audience == "firmy"

    def test_get_smart_defaults(self):
        """Test smart defaults returns learned preferences."""
        prefs = UserPreferences()

        # Record some choices to learn preferences
        prefs.record_choice("tone", "casualowy")
        prefs.record_choice("platform", "facebook")
        prefs.record_choice("target_audience", "młodzi")

        defaults = prefs.get_smart_defaults()

        assert defaults == {
            "tone": "casualowy",
            "platform": "facebook",
            "target_audience": "młodzi",
        }

    def test_should_skip_recommendations_explicit(self):
        """Test explicit skip_recommendations setting."""
        prefs = UserPreferences()
        prefs.skip_recommendations = True

        assert prefs.should_skip_recommendations() is True

    def test_should_skip_recommendations_default(self):
        """Test default skip behavior (don't skip)."""
        prefs = UserPreferences()

        assert prefs.should_skip_recommendations() is False

    def test_should_skip_recommendations_experienced_user(self):
        """Test that experienced users still don't skip by default."""
        prefs = UserPreferences()
        prefs.total_tasks = 15
        # Without consistent preferences, shouldn't skip
        prefs.tone_history = {"casualowy": 5, "profesjonalny": 5, "zabawny": 5}

        assert prefs.should_skip_recommendations() is False

    def test_get_preference_summary(self):
        """Test generating preference summary."""
        prefs = UserPreferences()
        prefs.record_choice("tone", "casualowy")
        prefs.record_task_completion({"platform": "instagram"})

        summary = prefs.get_preference_summary()

        assert "Preferowany ton: casualowy" in summary
        assert "Preferowana platforma: instagram" in summary
        assert "Wykonanych zadań: 1" in summary

    def test_get_preference_summary_empty(self):
        """Test preference summary when empty."""
        prefs = UserPreferences()

        assert prefs.get_preference_summary() == "Brak zapisanych preferencji"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        prefs = UserPreferences()
        prefs.record_choice("tone", "casualowy")
        prefs.skip_recommendations = True

        data = prefs.to_dict()

        assert data["preferred_tone"] == "casualowy"
        assert data["tone_history"] == {"casualowy": 1}
        assert data["skip_recommendations"] is True
        assert data["total_tasks"] == 0
        assert data["updated_at"] is not None

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "preferred_tone": "zabawny",
            "preferred_platform": "linkedin",
            "preferred_audience": "firmy",
            "tone_history": {"zabawny": 5, "profesjonalny": 2},
            "platform_history": {"linkedin": 3},
            "audience_history": {},
            "skip_recommendations": True,
            "auto_approve": False,
            "updated_at": datetime.now(timezone.utc),
            "total_tasks": 7,
        }

        prefs = UserPreferences.from_dict(data)

        assert prefs.preferred_tone == "zabawny"
        assert prefs.preferred_platform == "linkedin"
        assert prefs.tone_history == {"zabawny": 5, "profesjonalny": 2}
        assert prefs.skip_recommendations is True
        assert prefs.total_tasks == 7

    def test_from_dict_none(self):
        """Test deserialization from None returns defaults."""
        prefs = UserPreferences.from_dict(None)

        assert prefs.preferred_tone == "profesjonalny"
        assert prefs.total_tasks == 0

    def test_from_dict_empty(self):
        """Test deserialization from empty dict uses defaults."""
        prefs = UserPreferences.from_dict({})

        assert prefs.preferred_tone == "profesjonalny"
        assert prefs.preferred_platform == "instagram"

    def test_repr(self):
        """Test string representation."""
        prefs = UserPreferences()
        prefs.preferred_tone = "casualowy"
        prefs.total_tasks = 5
        prefs.skip_recommendations = True

        repr_str = repr(prefs)

        assert "tone=casualowy" in repr_str
        assert "tasks=5" in repr_str
        assert "skip=True" in repr_str


class TestPreferencesService:
    """Integration tests for PreferencesService."""

    @pytest.mark.asyncio
    async def test_get_preferences_new_company(self, db):
        """Test getting preferences for company with no saved prefs."""
        # Create a test company
        from bson import ObjectId
        company_id = ObjectId()
        await db.companies.insert_one({
            "_id": company_id,
            "name": "Test Company",
        })

        service = PreferencesService(db)
        prefs = await service.get_preferences(str(company_id))

        # Should return default preferences
        assert prefs.preferred_tone == "profesjonalny"
        assert prefs.total_tasks == 0

        # Cleanup
        await db.companies.delete_one({"_id": company_id})

    @pytest.mark.asyncio
    async def test_save_and_get_preferences(self, db):
        """Test saving and retrieving preferences."""
        from bson import ObjectId
        company_id = ObjectId()
        await db.companies.insert_one({
            "_id": company_id,
            "name": "Test Company",
        })

        service = PreferencesService(db)

        # Create and save preferences
        prefs = UserPreferences()
        prefs.record_choice("tone", "casualowy")
        prefs.skip_recommendations = True

        await service.save_preferences(str(company_id), prefs)

        # Retrieve and verify
        loaded = await service.get_preferences(str(company_id))

        assert loaded.preferred_tone == "casualowy"
        assert loaded.tone_history == {"casualowy": 1}
        assert loaded.skip_recommendations is True

        # Cleanup
        await db.companies.delete_one({"_id": company_id})

    @pytest.mark.asyncio
    async def test_record_task_completion(self, db):
        """Test recording task completion updates preferences."""
        from bson import ObjectId
        company_id = ObjectId()
        await db.companies.insert_one({
            "_id": company_id,
            "name": "Test Company",
        })

        service = PreferencesService(db)

        # Record first task
        prefs = await service.record_task_completion(
            str(company_id),
            {"tone": "zabawny", "platform": "facebook"}
        )

        assert prefs.total_tasks == 1
        assert prefs.preferred_tone == "zabawny"
        assert prefs.preferred_platform == "facebook"

        # Record second task with different choices
        prefs = await service.record_task_completion(
            str(company_id),
            {"tone": "zabawny", "platform": "instagram"}
        )

        assert prefs.total_tasks == 2
        assert prefs.tone_history == {"zabawny": 2}
        assert prefs.platform_history == {"facebook": 1, "instagram": 1}

        # Cleanup
        await db.companies.delete_one({"_id": company_id})

    @pytest.mark.asyncio
    async def test_update_setting(self, db):
        """Test updating explicit settings."""
        from bson import ObjectId
        company_id = ObjectId()
        await db.companies.insert_one({
            "_id": company_id,
            "name": "Test Company",
        })

        service = PreferencesService(db)

        # Update skip_recommendations
        prefs = await service.update_setting(
            str(company_id),
            "skip_recommendations",
            True
        )

        assert prefs.skip_recommendations is True

        # Verify it persisted
        loaded = await service.get_preferences(str(company_id))
        assert loaded.skip_recommendations is True

        # Cleanup
        await db.companies.delete_one({"_id": company_id})
