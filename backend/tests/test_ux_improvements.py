"""Tests for UX improvements (Phase 5)."""

import pytest
from datetime import datetime, timezone

from app.services.assistant.ux_messages import (
    UXHelper,
    ErrorType,
    ProgressStage,
    ProgressUpdate,
    FeedbackEntry,
    FeedbackCollector,
    ux_helper,
)
from app.services.assistant.agent_state import AgentState


class TestUXHelper:
    """Tests for UXHelper class."""

    def test_get_error_response_unknown_intent(self):
        """Test error response for unknown intent."""
        result = ux_helper.get_error_response(ErrorType.UNKNOWN_INTENT)

        assert result["type"] == "error"
        assert result["error_type"] == "unknown_intent"
        assert "Nie rozumiem" in result["title"]
        assert len(result["suggestions"]) > 0
        assert result["recoverable"] is True

    def test_get_error_response_missing_required_with_param(self):
        """Test error response with specific param name."""
        result = ux_helper.get_error_response(
            ErrorType.MISSING_REQUIRED,
            param_name="client_name"
        )

        assert "client_name" in result["message"]

    def test_get_error_response_with_details(self):
        """Test error response with additional details."""
        result = ux_helper.get_error_response(
            ErrorType.EXECUTION_FAILED,
            details="Connection timeout"
        )

        assert "Connection timeout" in result["message"]

    def test_get_error_response_non_recoverable(self):
        """Test that rate limited errors are non-recoverable."""
        result = ux_helper.get_error_response(ErrorType.RATE_LIMITED)

        assert result["recoverable"] is False

    def test_get_progress_update_basic(self):
        """Test basic progress update."""
        progress = ux_helper.get_progress_update(ProgressStage.EXECUTING)

        assert isinstance(progress, ProgressUpdate)
        assert progress.stage == ProgressStage.EXECUTING
        assert progress.percentage > 0
        assert "🤖" in progress.message

    def test_get_progress_update_task_specific(self):
        """Test task-specific progress message."""
        progress = ux_helper.get_progress_update(
            ProgressStage.GENERATING,
            task_type="social_media_post"
        )

        assert "hashtagi" in progress.message.lower() or "treść" in progress.message.lower()

    def test_get_progress_update_custom_message(self):
        """Test custom progress message."""
        progress = ux_helper.get_progress_update(
            ProgressStage.EXECUTING,
            custom_message="Niestandardowa wiadomość"
        )

        assert "Niestandardowa wiadomość" in progress.message

    def test_get_help_message(self):
        """Test help message content."""
        help_text = ux_helper.get_help_message()

        assert "Marketing" in help_text
        assert "Finanse" in help_text
        assert "HR" in help_text
        assert "Prawne" in help_text
        assert "Instagram" in help_text

    def test_format_confirmation_message(self):
        """Test confirmation message formatting."""
        params = {
            "topic": "Kawa speciality",
            "platform": "instagram",
            "tone": "casualowy",
        }

        result = ux_helper.format_confirmation_message("social_media_post", params)

        assert "Post na social media" in result
        assert "Temat: Kawa speciality" in result
        assert "Platforma: instagram" in result
        assert "Ton: casualowy" in result
        assert "Wykonaj" in result
        assert "Zmień" in result
        assert "Anuluj" in result

    def test_format_confirmation_truncates_long_values(self):
        """Test that long values are truncated."""
        params = {
            "topic": "A" * 100,  # Very long topic
        }

        result = ux_helper.format_confirmation_message("social_media_post", params)

        # Should be truncated with ellipsis
        assert "..." in result

    def test_get_success_message(self):
        """Test success message for different task types."""
        assert "Post" in ux_helper.get_success_message("social_media_post")
        assert "Faktura" in ux_helper.get_success_message("invoice")
        assert "Tekst" in ux_helper.get_success_message("marketing_copy")

    def test_get_success_message_unknown_task(self):
        """Test success message for unknown task type."""
        result = ux_helper.get_success_message("unknown_task_type")

        assert "Zadanie zostało wykonane" in result


class TestProgressStages:
    """Tests for progress stage consistency."""

    def test_all_stages_have_messages(self):
        """Test that all stages have defined messages."""
        from app.services.assistant.ux_messages import PROGRESS_MESSAGES

        for stage in ProgressStage:
            assert stage in PROGRESS_MESSAGES
            assert "message" in PROGRESS_MESSAGES[stage]
            assert "percentage" in PROGRESS_MESSAGES[stage]

    def test_progress_percentages_are_ordered(self):
        """Test that progress percentages increase with stages."""
        from app.services.assistant.ux_messages import PROGRESS_MESSAGES

        stages_order = [
            ProgressStage.UNDERSTANDING,
            ProgressStage.GATHERING,
            ProgressStage.CONFIRMING,
            ProgressStage.PREPARING,
            ProgressStage.EXECUTING,
            ProgressStage.GENERATING,
            ProgressStage.FINALIZING,
            ProgressStage.COMPLETED,
        ]

        prev_percentage = 0
        for stage in stages_order:
            current = PROGRESS_MESSAGES[stage]["percentage"]
            assert current >= prev_percentage, f"{stage} should have higher percentage than previous"
            prev_percentage = current


class TestAgentStateUndo:
    """Tests for AgentState undo functionality."""

    def test_save_params_snapshot(self):
        """Test saving params to history."""
        state = AgentState()
        state.gathered_params = {"topic": "kawa"}
        state.save_params_snapshot()

        assert len(state.params_history) == 1
        assert state.params_history[0] == {"topic": "kawa"}

    def test_undo_last_change(self):
        """Test undoing the last change."""
        state = AgentState()

        # First state
        state.gathered_params = {"topic": "kawa"}
        state.save_params_snapshot()

        # Second state
        state.gathered_params = {"topic": "kawa", "tone": "casualowy"}

        # Undo should restore first state
        result = state.undo_last_change()

        assert result is True
        assert state.gathered_params == {"topic": "kawa"}

    def test_undo_empty_history(self):
        """Test undo when no history."""
        state = AgentState()

        result = state.undo_last_change()

        assert result is False

    def test_can_undo(self):
        """Test can_undo check."""
        state = AgentState()

        assert state.can_undo() is False

        state.gathered_params = {"topic": "test"}
        state.save_params_snapshot()

        assert state.can_undo() is True

    def test_max_history_limit(self):
        """Test that history is limited to MAX_HISTORY entries."""
        state = AgentState()

        # Add more than MAX_HISTORY entries
        for i in range(state.MAX_HISTORY + 5):
            state.gathered_params = {"count": i}
            state.save_params_snapshot()

        assert len(state.params_history) == state.MAX_HISTORY

    def test_to_dict_includes_history(self):
        """Test that to_dict includes params_history."""
        state = AgentState()
        state.gathered_params = {"topic": "kawa"}
        state.save_params_snapshot()

        data = state.to_dict()

        assert "params_history" in data
        assert data["params_history"] == [{"topic": "kawa"}]

    def test_from_dict_restores_history(self):
        """Test that from_dict restores params_history."""
        data = {
            "current_task": "social_media_post",
            "gathered_params": {"topic": "kawa"},
            "params_history": [{"topic": "herbata"}],
        }

        state = AgentState.from_dict(data)

        assert state.params_history == [{"topic": "herbata"}]
        assert state.can_undo() is True


class TestFeedbackEntry:
    """Tests for FeedbackEntry dataclass."""

    def test_create_feedback_entry(self):
        """Test creating a feedback entry."""
        entry = FeedbackEntry(
            task_id="task123",
            task_type="social_media_post",
            rating=5,
            comment="Świetny post!",
            params_used={"topic": "kawa"},
        )

        assert entry.task_id == "task123"
        assert entry.rating == 5
        assert entry.comment == "Świetny post!"

    def test_feedback_entry_to_dict(self):
        """Test serialization to dictionary."""
        entry = FeedbackEntry(
            task_id="task123",
            task_type="social_media_post",
            rating=4,
        )

        data = entry.to_dict()

        assert data["task_id"] == "task123"
        assert data["rating"] == 4
        assert "created_at" in data

    def test_feedback_entry_default_timestamp(self):
        """Test that created_at is set by default."""
        entry = FeedbackEntry(
            task_id="task123",
            task_type="social_media_post",
            rating=3,
        )

        assert entry.created_at is not None
        assert isinstance(entry.created_at, datetime)


class TestFeedbackCollector:
    """Tests for FeedbackCollector class."""

    def test_get_task_feedback_prompt(self):
        """Test getting feedback prompt structure."""
        import asyncio

        collector = FeedbackCollector()

        prompt = asyncio.get_event_loop().run_until_complete(
            collector.get_task_feedback_prompt()
        )

        assert prompt["type"] == "feedback_request"
        assert len(prompt["options"]) == 5  # 5 rating options
        assert prompt["allow_comment"] is True

    def test_submit_feedback_no_db(self):
        """Test feedback submission without database."""
        import asyncio

        collector = FeedbackCollector(db=None)

        result = asyncio.get_event_loop().run_until_complete(
            collector.submit_feedback(
                company_id="comp123",
                task_id="task123",
                task_type="social_media_post",
                rating=5,
            )
        )

        assert result is False  # No db, should fail gracefully


class TestFlowControllerUX:
    """Tests for FlowController UX improvements."""

    @pytest.mark.asyncio
    async def test_undo_command_in_confirming(self):
        """Test undo command during confirmation."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.user_preferences import UserPreferences

        controller = ConversationFlowController(use_llm=False)

        # Setup state with history
        state = AgentState()
        state.current_task = "social_media_post"
        state.conversation_stage = "confirming"
        state.gathered_params = {"topic": "kawa", "tone": "casualowy"}
        state.params_history = [{"topic": "kawa"}]

        prefs = UserPreferences()

        response = await controller._handle_confirming(
            message="cofnij",
            agent_state=state,
            company_context={},
            prefs=prefs,
        )

        assert "Cofnięto" in response.content
        assert state.gathered_params == {"topic": "kawa"}

    @pytest.mark.asyncio
    async def test_modify_saves_snapshot(self):
        """Test that modify command saves snapshot for undo."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.user_preferences import UserPreferences

        controller = ConversationFlowController(use_llm=False)

        state = AgentState()
        state.current_task = "social_media_post"
        state.conversation_stage = "confirming"
        state.gathered_params = {"topic": "kawa"}

        prefs = UserPreferences()

        await controller._handle_confirming(
            message="zmień",
            agent_state=state,
            company_context={},
            prefs=prefs,
        )

        # Should have saved snapshot
        assert len(state.params_history) == 1
        assert state.params_history[0] == {"topic": "kawa"}

    @pytest.mark.asyncio
    async def test_cancel_uses_ux_helper(self):
        """Test that cancel uses UX helper for message."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.user_preferences import UserPreferences

        controller = ConversationFlowController(use_llm=False)

        state = AgentState()
        state.current_task = "social_media_post"
        state.conversation_stage = "confirming"
        state.gathered_params = {"topic": "kawa"}

        prefs = UserPreferences()

        response = await controller._handle_confirming(
            message="anuluj",
            agent_state=state,
            company_context={},
            prefs=prefs,
        )

        assert "anulowane" in response.content.lower()

    def test_build_confirmation_has_progress(self):
        """Test that confirmation includes progress info."""
        from app.services.assistant.flow_controller import ConversationFlowController

        controller = ConversationFlowController(use_llm=False)

        state = AgentState()
        state.current_task = "social_media_post"
        state.gathered_params = {"topic": "kawa"}

        response = controller._build_confirmation(state, "social_media_post")

        assert response.progress is not None
        assert response.progress["stage"] == "confirming"
        assert response.progress["percentage"] > 0

    def test_build_execution_response_has_progress_and_feedback(self):
        """Test that execution response includes progress and feedback flag."""
        from app.services.assistant.flow_controller import ConversationFlowController

        controller = ConversationFlowController(use_llm=False)

        state = AgentState()
        state.current_task = "social_media_post"
        state.gathered_params = {"topic": "kawa"}

        response = controller._build_execution_response(state, {})

        assert response.progress is not None
        assert response.progress["stage"] == "executing"
        assert response.show_feedback is True

    def test_build_unknown_response_uses_ux_helper(self):
        """Test that unknown response uses UX helper."""
        from app.services.assistant.flow_controller import ConversationFlowController

        controller = ConversationFlowController(use_llm=False)

        response = controller._build_unknown_response()

        assert "Nie rozumiem" in response
        assert "Spróbuj" in response
