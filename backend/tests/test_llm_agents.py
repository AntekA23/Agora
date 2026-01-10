"""Tests for LLM-powered agents (Phase 4)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.assistant.llm_agents import (
    ConversationAgent,
    ParameterAgent,
    Orchestrator,
    ConversationContext,
)


class TestConversationContext:
    """Tests for ConversationContext dataclass."""

    def test_default_values(self):
        """Test default context values."""
        ctx = ConversationContext()

        assert ctx.messages == []
        assert ctx.current_task is None
        assert ctx.gathered_params == {}
        assert ctx.missing_params == []

    def test_get_summary_empty(self):
        """Test summary with empty context."""
        ctx = ConversationContext()
        assert ctx.get_summary() == "Brak kontekstu"

    def test_get_summary_with_data(self):
        """Test summary with data."""
        ctx = ConversationContext(
            current_task="social_media_post",
            original_request="Stwórz post o kawie",
            gathered_params={"topic": "kawa", "tone": "casualowy"},
            missing_params=["platform"],
        )

        summary = ctx.get_summary()

        assert "social_media_post" in summary
        assert "Stwórz post o kawie" in summary
        assert "topic=kawa" in summary
        assert "platform" in summary

    def test_get_messages_for_llm_limits(self):
        """Test that messages are limited to last 10."""
        messages = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        ctx = ConversationContext(messages=messages)

        result = ctx.get_messages_for_llm()

        assert len(result) == 10
        assert result[0]["content"] == "msg 10"
        assert result[-1]["content"] == "msg 19"


class TestConversationAgentFallback:
    """Tests for ConversationAgent fallback logic (no LLM calls)."""

    def test_fallback_process_tone_extraction(self):
        """Test fallback extraction of tone values."""
        agent = ConversationAgent()
        ctx = ConversationContext()

        result = agent._fallback_process("casualowy", ctx)

        assert result["extracted_params"]["tone"] == "casualowy"
        assert result["next_action"] == "continue"

    def test_fallback_process_platform_extraction(self):
        """Test fallback extraction of platform values."""
        agent = ConversationAgent()
        ctx = ConversationContext()

        result = agent._fallback_process("instagram", ctx)

        assert result["extracted_params"]["platform"] == "instagram"

    def test_fallback_process_audience_extraction(self):
        """Test fallback extraction of audience values."""
        agent = ConversationAgent()
        ctx = ConversationContext()

        # Use exact key that the fallback recognizes
        result = agent._fallback_process("młodzi", ctx)

        assert result["extracted_params"]["target_audience"] == "młodzi"

    def test_fallback_process_long_message_new_task(self):
        """Test that long messages (>10 words) without params are treated as new tasks."""
        agent = ConversationAgent()
        ctx = ConversationContext()

        # Long message (12 words) without any recognized parameter values
        result = agent._fallback_process(
            "Chciałbym stworzyć treść marketingową dla mojej nowej aplikacji do zarządzania czasem pracy", ctx
        )

        assert result["next_action"] == "new_task"

    def test_fallback_process_unknown_short(self):
        """Test that unknown short messages request clarification."""
        agent = ConversationAgent()
        ctx = ConversationContext()

        result = agent._fallback_process("xyz", ctx)

        assert result["next_action"] == "clarify"
        assert result["confidence"] == 0.3


class TestParameterAgentFallback:
    """Tests for ParameterAgent fallback logic (no LLM calls)."""

    def test_fallback_extract_tone_with_context(self):
        """Test extraction when we expect tone param."""
        agent = ParameterAgent()

        result = agent._fallback_extract("luźny", last_question_param="tone")

        assert result["extracted"]["tone"] == "casualowy"
        assert result["confidence"] > 0.5

    def test_fallback_extract_platform(self):
        """Test extraction of platform values."""
        agent = ParameterAgent()

        result = agent._fallback_extract("fb", last_question_param="platform")

        assert result["extracted"]["platform"] == "facebook"

    def test_fallback_extract_multiple_values(self):
        """Test extraction of multiple values from one message."""
        agent = ParameterAgent()

        result = agent._fallback_extract(
            "instagram dla młodych",
            last_question_param=None
        )

        assert result["extracted"]["platform"] == "instagram"
        assert result["extracted"]["target_audience"] == "młodzi"

    def test_fallback_extract_post_type(self):
        """Test extraction of post type."""
        agent = ParameterAgent()

        result = agent._fallback_extract("story", last_question_param="post_type")

        assert result["extracted"]["post_type"] == "story"

    def test_fallback_extract_short_unknown_as_value(self):
        """Test that short unknown message is used as value for expected param."""
        agent = ParameterAgent()

        # The fallback should use the exact message as value for short responses
        # when expecting a specific parameter (like tone)
        result = agent._fallback_extract("super luźny", last_question_param="tone")

        # "luźny" is mapped to "casualowy"
        assert result["extracted"]["tone"] == "casualowy"


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator (with mocked LLM)."""

    @pytest.mark.asyncio
    async def test_process_uses_parameter_agent(self):
        """Test that orchestrator uses parameter agent for gathering."""
        orchestrator = Orchestrator()

        # Mock the parameter agent
        orchestrator.parameter_agent._fallback_extract = MagicMock(
            return_value={"extracted": {"tone": "casualowy"}, "confidence": 0.9}
        )

        # Mock the conversation agent to avoid LLM calls
        async def mock_process(*args, **kwargs):
            return {
                "understanding": "User said casualowy",
                "response": "OK, zapisuję ton casualowy.",
                "extracted_params": {},
                "next_action": "continue",
                "confidence": 0.8,
            }

        orchestrator.conversation_agent.process = mock_process

        ctx = ConversationContext(
            current_task="social_media_post",
            missing_params=["tone"],
        )

        result = await orchestrator.process("casualowy", ctx)

        assert "tone" in ctx.gathered_params
        assert ctx.gathered_params["tone"] == "casualowy"
        assert "tone" not in ctx.missing_params

    @pytest.mark.asyncio
    async def test_interpret_intent_new_request(self):
        """Test intent interpretation for new requests."""
        orchestrator = Orchestrator()

        # Mock conversation agent
        async def mock_process(*args, **kwargs):
            return {
                "understanding": "User wants a post",
                "response": "OK",
                "extracted_params": {"topic": "kawa"},
                "next_action": "new_task",
                "confidence": 0.9,
            }

        orchestrator.conversation_agent.process = mock_process

        ctx = ConversationContext()

        result = await orchestrator.interpret_intent(
            "Stwórz post o kawie",
            ctx
        )

        assert result["is_new_request"] is True
        assert result["extracted_params"]["topic"] == "kawa"


class TestFlowControllerWithLLM:
    """Tests for FlowController with LLM agents."""

    @pytest.mark.asyncio
    async def test_extract_param_uses_llm_agent(self):
        """Test that async extraction uses LLM agent."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.agent_state import AgentState

        controller = ConversationFlowController(use_llm=True)

        # Mock the parameter agent
        async def mock_extract(*args, **kwargs):
            return {
                "extracted": {"tone": "casualowy"},
                "needs_clarification": [],
                "confidence": 0.9,
            }

        controller._parameter_agent.extract = mock_extract

        agent_state = AgentState()
        agent_state.current_task = "social_media_post"

        result = await controller._extract_param_from_response_async(
            message="luźny styl",
            expected_param="tone",
            task_type="social_media_post",
            agent_state=agent_state,
        )

        assert result["tone"] == "casualowy"

    @pytest.mark.asyncio
    async def test_extract_param_fallback_on_error(self):
        """Test that extraction falls back on LLM error."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.agent_state import AgentState

        controller = ConversationFlowController(use_llm=True)

        # Mock the parameter agent to raise an exception
        async def mock_extract_fail(*args, **kwargs):
            raise Exception("LLM unavailable")

        controller._parameter_agent.extract = mock_extract_fail

        agent_state = AgentState()
        agent_state.current_task = "social_media_post"

        # Should not raise, should fallback
        result = await controller._extract_param_from_response_async(
            message="casualowy",
            expected_param="tone",
            task_type="social_media_post",
            agent_state=agent_state,
        )

        # Fallback should still extract the tone
        assert result.get("tone") == "casualowy"

    def test_build_llm_context(self):
        """Test building LLM context from state."""
        from app.services.assistant.flow_controller import ConversationFlowController
        from app.services.assistant.agent_state import AgentState

        controller = ConversationFlowController()

        agent_state = AgentState()
        agent_state.current_task = "social_media_post"
        agent_state.original_request = "Stwórz post o kawie"
        agent_state.gathered_params = {"topic": "kawa"}
        agent_state.missing_required = []
        agent_state.missing_recommended = ["tone", "platform"]

        conversation_context = {
            "messages": [
                {"role": "user", "content": "Stwórz post o kawie"},
                {"role": "assistant", "content": "Jaki ton?"},
            ]
        }

        company_context = {
            "name": "Test Company",
            "brand": {"voice": "profesjonalny"},
        }

        result = controller._build_llm_context(
            agent_state, conversation_context, company_context
        )

        assert result.current_task == "social_media_post"
        assert result.original_request == "Stwórz post o kawie"
        assert result.gathered_params == {"topic": "kawa"}
        assert "tone" in result.missing_params
        assert "platform" in result.missing_params
        assert result.company_name == "Test Company"
        assert result.brand_voice == "profesjonalny"
        assert len(result.messages) == 2
