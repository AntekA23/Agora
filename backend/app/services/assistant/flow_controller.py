"""Conversation Flow Controller for managing multi-turn agent interactions.

Orchestrates the conversation flow based on AgentState, handling:
- New task requests
- Parameter gathering
- Confirmation before execution
- Task execution and results

Now with LLM-powered agents (Phase 4) for better context understanding
and natural parameter extraction.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.assistant.agent_state import AgentState
from app.services.assistant.router import (
    assistant_router,
    Intent,
    PARAM_QUESTIONS,
    RECOMMENDED_PARAM_QUESTIONS,
    INTENT_TO_AGENTS,
)
from app.services.assistant.user_preferences import UserPreferences
from app.services.assistant.llm_agents import (
    ConversationContext,
    parameter_agent,
    conversation_agent,
)
from app.services.assistant.ux_messages import (
    ux_helper,
    ProgressStage,
    ErrorType,
    FeedbackCollector,
)

logger = logging.getLogger(__name__)


@dataclass
class FlowResponse:
    """Response from the flow controller."""

    # Message content for the user
    content: str

    # Action buttons to show
    actions: list[dict[str, str]] = field(default_factory=list)

    # Tasks to create (when executing)
    tasks_to_create: list[dict[str, Any]] = field(default_factory=list)

    # Updated agent state
    agent_state: AgentState | None = None

    # Whether execution should happen
    should_execute: bool = False

    # Intent for tracking
    intent: str = "unknown"

    # Confidence score
    confidence: float = 0.0

    # All extracted/gathered params
    extracted_params: dict[str, Any] = field(default_factory=dict)

    # Progress tracking (Phase 5: UX improvements)
    progress: dict[str, Any] | None = None

    # Error info if any
    error: dict[str, Any] | None = None

    # Whether to show feedback prompt
    show_feedback: bool = False


class ConversationFlowController:
    """Controller for managing conversation flow with state machine.

    Handles different stages of conversation:
    - idle: Waiting for new request
    - gathering: Collecting required and recommended parameters
    - confirming: Showing summary before execution
    - executing: Task is running
    - completed: Task finished, ready for new requests

    Now supports LLM-powered agents (Phase 4) for better understanding.
    """

    def __init__(self, use_llm: bool = True):
        """Initialize the flow controller.

        Args:
            use_llm: If True, use LLM agents for smarter extraction.
                    Falls back to rule-based if LLM fails.
        """
        self._router = assistant_router
        self._use_llm = use_llm
        self._parameter_agent = parameter_agent
        self._conversation_agent = conversation_agent

    def _build_llm_context(
        self,
        agent_state: AgentState,
        conversation_context: dict[str, Any],
        company_context: dict[str, Any],
    ) -> ConversationContext:
        """Build context object for LLM agents.

        Args:
            agent_state: Current agent state
            conversation_context: Conversation history and params
            company_context: Company information

        Returns:
            ConversationContext for LLM agents
        """
        # Extract messages from context
        messages = []
        for msg in conversation_context.get("messages", [])[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        return ConversationContext(
            messages=messages,
            current_task=agent_state.current_task,
            gathered_params=agent_state.gathered_params.copy(),
            missing_params=(
                agent_state.missing_required + agent_state.missing_recommended
            ),
            original_request=agent_state.original_request,
            company_name=company_context.get("name"),
            brand_voice=company_context.get("brand", {}).get("voice"),
        )

    async def process(
        self,
        message: str,
        agent_state: AgentState,
        conversation_context: dict[str, Any],
        company_context: dict[str, Any],
        user_preferences: UserPreferences | None = None,
    ) -> FlowResponse:
        """Process a message based on current agent state.

        Args:
            message: User's message
            agent_state: Current state of the agent
            conversation_context: Previous messages, params, etc.
            company_context: Company info for personalization
            user_preferences: Learned user preferences for smart defaults

        Returns:
            FlowResponse with content, actions, and updated state
        """
        stage = agent_state.conversation_stage
        prefs = user_preferences or UserPreferences()

        if stage == "idle":
            return await self._handle_idle(message, agent_state, conversation_context, prefs)

        elif stage == "gathering":
            return await self._handle_gathering(message, agent_state, conversation_context, prefs)

        elif stage == "confirming":
            return await self._handle_confirming(message, agent_state, company_context, prefs)

        elif stage == "executing":
            return await self._handle_executing(message, agent_state)

        elif stage == "completed":
            return await self._handle_completed(message, agent_state, conversation_context, prefs)

        else:
            # Unknown state, reset to idle
            agent_state.reset()
            return await self._handle_idle(message, agent_state, conversation_context, prefs)

    async def _handle_idle(
        self,
        message: str,
        agent_state: AgentState,
        context: dict[str, Any],
        prefs: UserPreferences,
    ) -> FlowResponse:
        """Handle message when in idle state (new request)."""
        # Interpret the new request
        intent_result = await self._router.interpret(message, conversation_context=context)

        # Handle conversational intents using LLM (no task execution needed)
        if intent_result.intent in (Intent.GREETING, Intent.HELP, Intent.CAPABILITIES, Intent.UNKNOWN):
            # Use LLM for intelligent, contextual response
            response_content = await self._generate_conversational_response(
                message=message,
                intent=intent_result.intent,
                context=context,
            )
            return FlowResponse(
                content=response_content,
                agent_state=agent_state,
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
            )

        # Legacy fallback for UNKNOWN if LLM fails (should not reach here normally)
        if intent_result.intent == Intent.UNKNOWN:
            return FlowResponse(
                content=self._build_unknown_response(),
                agent_state=agent_state,
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
            )

        # Apply smart defaults from user preferences
        initial_params = intent_result.extracted_params.copy()
        smart_defaults = prefs.get_smart_defaults()

        # Only apply defaults for params not already extracted
        for key, value in smart_defaults.items():
            if key not in initial_params:
                initial_params[key] = value

        # Update recommended_missing based on what we already have from preferences
        missing_recommended = [
            p for p in intent_result.recommended_missing
            if p not in initial_params
        ]

        # Start a new task
        agent_state.start_task(
            task_type=intent_result.intent.value,
            original_request=message,
            initial_params=initial_params,
            missing_required=intent_result.missing_info,
            missing_recommended=missing_recommended,
        )

        # Check what we need to do next
        if agent_state.missing_required:
            # Need required params first
            return self._ask_for_param(
                agent_state,
                agent_state.missing_required[0],
                is_required=True,
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
            )

        elif agent_state.missing_recommended:
            # Check if user prefers to skip recommendations
            if prefs.should_skip_recommendations():
                # Apply defaults and go directly to confirming/executing
                return self._apply_defaults_and_confirm(agent_state, prefs)

            # Have required, ask for recommended
            return self._ask_for_recommendations(
                agent_state,
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
                prefs=prefs,
            )

        else:
            # All params present, check auto_approve
            if prefs.auto_approve:
                # Skip confirmation, go directly to execution
                agent_state.transition("quick_execute")
                agent_state.transition("confirmed")
                return self._build_execution_response(agent_state, {})
            else:
                # Go to confirming
                agent_state.transition("quick_execute")
                return self._build_confirmation(
                    agent_state,
                    intent=intent_result.intent.value,
                    confidence=intent_result.confidence,
                )

    async def _handle_gathering(
        self,
        message: str,
        agent_state: AgentState,
        context: dict[str, Any],
        prefs: UserPreferences,
    ) -> FlowResponse:
        """Handle message when gathering parameters."""
        message_lower = message.lower().strip()

        # Check for special commands (support both Polish and ASCII variants)
        use_defaults_commands = [
            "[użyj domyślnych]", "użyj domyślnych", "domyślne",
            "[uzyj domyslnych]", "uzyj domyslnych", "domyslne",
            "defaults", "use defaults",
        ]
        if message_lower in use_defaults_commands:
            return self._apply_defaults_and_confirm(agent_state, prefs)

        # Check for "don't ask again" command
        skip_commands = [
            "nie pytaj więcej", "nie pytaj wiecej", "zapamiętaj",
            "skip always", "always defaults",
        ]
        if message_lower in skip_commands:
            # This would need to be saved via PreferencesService
            # For now, just apply defaults
            return self._apply_defaults_and_confirm(agent_state, prefs)

        if message_lower in ["anuluj", "cancel", "stop"]:
            agent_state.transition("cancel")
            agent_state.reset()
            return FlowResponse(
                content="Anulowano. Jak mogę Ci pomóc?",
                agent_state=agent_state,
                intent="unknown",
            )

        # Extract parameter value from the response (using LLM when available)
        extracted = await self._extract_param_from_response_async(
            message,
            agent_state.last_question_param,
            agent_state.current_task,
            agent_state,
        )

        # Update gathered params
        for key, value in extracted.items():
            agent_state.add_param(key, value)

        # Check if we need more params
        if agent_state.missing_required:
            return self._ask_for_param(
                agent_state,
                agent_state.missing_required[0],
                is_required=True,
                intent=agent_state.current_task or "unknown",
            )

        elif agent_state.missing_recommended:
            return self._ask_for_recommendations(
                agent_state,
                intent=agent_state.current_task or "unknown",
                prefs=prefs,
            )

        else:
            # All done gathering, move to confirming
            agent_state.transition("params_complete")

            # Check auto_approve preference
            if prefs.auto_approve:
                agent_state.transition("confirmed")
                return self._build_execution_response(agent_state, {})

            return self._build_confirmation(
                agent_state,
                intent=agent_state.current_task or "unknown",
            )

    async def _handle_confirming(
        self,
        message: str,
        agent_state: AgentState,
        company_context: dict[str, Any],
        prefs: UserPreferences,
    ) -> FlowResponse:
        """Handle message when confirming parameters."""
        message_lower = message.lower().strip()

        # Check for confirmation
        if message_lower in ["tak", "ok", "dobrze", "zatwierdź", "wykonaj", "start", "generuj"]:
            agent_state.transition("confirmed")
            return self._build_execution_response(agent_state, company_context)

        # Check for undo request (Phase 5: UX)
        if message_lower in ["cofnij", "undo", "wróć", "poprzedni"]:
            if agent_state.undo_last_change():
                return FlowResponse(
                    content="↩️ Cofnięto ostatnią zmianę.\n\n" + self._format_params_preview(agent_state.gathered_params),
                    actions=[
                        {"id": "confirm", "label": "✅ Wykonaj", "type": "primary"},
                        {"id": "modify", "label": "✏️ Zmień", "type": "secondary"},
                        {"id": "undo", "label": "↩️ Cofnij", "type": "ghost"} if agent_state.can_undo() else {"id": "cancel", "label": "❌ Anuluj", "type": "ghost"},
                    ],
                    agent_state=agent_state,
                    intent=agent_state.current_task or "unknown",
                    extracted_params=agent_state.gathered_params,
                )
            else:
                return FlowResponse(
                    content="Nie ma czego cofać. Brak historii zmian.",
                    agent_state=agent_state,
                    intent=agent_state.current_task or "unknown",
                    extracted_params=agent_state.gathered_params,
                )

        # Check for modification request
        if message_lower in ["nie", "zmień", "popraw", "edytuj", "modyfikuj"]:
            agent_state.transition("modify")
            # Save current state for undo
            agent_state.save_params_snapshot()
            # Ask what to change
            return FlowResponse(
                content="✏️ Co chcesz zmienić? Możesz podać nowe wartości dla parametrów.\n\n💡 Wpisz **cofnij** aby przywrócić poprzednie wartości.",
                agent_state=agent_state,
                intent=agent_state.current_task or "unknown",
                extracted_params=agent_state.gathered_params,
            )

        # Check for cancel
        if message_lower in ["anuluj", "cancel", "stop"]:
            agent_state.transition("cancel")
            agent_state.reset()
            error_info = ux_helper.get_error_response(ErrorType.CANCELLED)
            return FlowResponse(
                content=f"{error_info['message']} Jak mogę Ci pomóc?",
                agent_state=agent_state,
                intent="unknown",
            )

        # Try to extract changes from the message (using LLM when available)
        extracted = await self._extract_param_from_response_async(
            message,
            None,  # No specific param expected
            agent_state.current_task,
            agent_state,
        )

        if extracted:
            # User provided new values, update and re-confirm
            for key, value in extracted.items():
                agent_state.gathered_params[key] = value

            return self._build_confirmation(
                agent_state,
                intent=agent_state.current_task or "unknown",
            )

        # Unclear response, ask for clarification
        return FlowResponse(
            content=(
                "Nie rozumiem. Powiedz:\n"
                "• **tak** - aby wykonać zadanie\n"
                "• **zmień** - aby zmodyfikować parametry\n"
                "• **anuluj** - aby anulować"
            ),
            agent_state=agent_state,
            intent=agent_state.current_task or "unknown",
            extracted_params=agent_state.gathered_params,
        )

    async def _handle_executing(
        self,
        message: str,
        agent_state: AgentState,
    ) -> FlowResponse:
        """Handle message when task is executing."""
        # Task is running, user can check status or wait
        return FlowResponse(
            content="Zadanie jest w trakcie wykonywania. Proszę czekać...",
            agent_state=agent_state,
            intent=agent_state.current_task or "unknown",
            extracted_params=agent_state.gathered_params,
        )

    async def _handle_completed(
        self,
        message: str,
        agent_state: AgentState,
        context: dict[str, Any],
        prefs: UserPreferences,
    ) -> FlowResponse:
        """Handle message after task completion."""
        # Check if user wants to start something new
        agent_state.transition("reset")
        agent_state.reset()

        # Process as new request
        return await self._handle_idle(message, agent_state, context, prefs)

    def _ask_for_param(
        self,
        agent_state: AgentState,
        param: str,
        is_required: bool,
        intent: str,
        confidence: float = 1.0,
    ) -> FlowResponse:
        """Build response asking for a specific parameter."""
        if is_required:
            question = PARAM_QUESTIONS.get(param, f"Podaj {param}:")
        else:
            question = RECOMMENDED_PARAM_QUESTIONS.get(param, f"Podaj {param}:")

        agent_state.set_question(question, param)

        return FlowResponse(
            content=question,
            agent_state=agent_state,
            intent=intent,
            confidence=confidence,
            extracted_params=agent_state.gathered_params,
        )

    def _ask_for_recommendations(
        self,
        agent_state: AgentState,
        intent: str,
        confidence: float = 1.0,
        prefs: UserPreferences | None = None,
    ) -> FlowResponse:
        """Ask for all recommended parameters at once."""
        questions = []
        for param in agent_state.missing_recommended:
            q = RECOMMENDED_PARAM_QUESTIONS.get(param, f"Podaj {param}")
            questions.append(f"• {q}")

        content = "Chcę stworzyć najlepszy wynik! Doprecyzuj:\n\n"
        content += "\n".join(questions)
        content += "\n\nMożesz też użyć domyślnych ustawień."

        # Show learned preferences hint if available
        if prefs and prefs.total_tasks > 0:
            smart_defaults = prefs.get_smart_defaults()
            hints = []
            for param in agent_state.missing_recommended:
                if param in smart_defaults:
                    hints.append(f"{param}: {smart_defaults[param]}")
            if hints:
                content += f"\n\n💡 Twoje typowe ustawienia: {', '.join(hints)}"

        # Track that we asked about recommendations
        agent_state.set_question(content, "recommendations")

        actions = [
            {"id": "use_defaults", "label": "Użyj domyślnych", "type": "secondary"},
        ]

        # Add "don't ask again" option for experienced users
        if prefs and prefs.total_tasks >= 3:
            actions.append({
                "id": "skip_always",
                "label": "Nie pytaj więcej",
                "type": "ghost",
            })

        return FlowResponse(
            content=content,
            actions=actions,
            agent_state=agent_state,
            intent=intent,
            confidence=confidence,
            extracted_params=agent_state.gathered_params,
        )

    def _apply_defaults_and_confirm(
        self,
        agent_state: AgentState,
        prefs: UserPreferences | None = None,
    ) -> FlowResponse:
        """Apply default values for recommended params and move to confirm."""
        # First try user's learned preferences
        if prefs:
            smart_defaults = prefs.get_smart_defaults()
            for param in list(agent_state.missing_recommended):
                if param in smart_defaults:
                    agent_state.add_param(param, smart_defaults[param])

        # Then fill remaining with system defaults
        try:
            intent_enum = Intent(agent_state.current_task)
            defaults = self._router.get_default_params(intent_enum)

            for param in list(agent_state.missing_recommended):
                if param in defaults:
                    agent_state.add_param(param, defaults[param])
        except (ValueError, KeyError):
            pass

        agent_state.transition("use_defaults")
        return self._build_confirmation(
            agent_state,
            intent=agent_state.current_task or "unknown",
        )

    def _build_confirmation(
        self,
        agent_state: AgentState,
        intent: str,
        confidence: float = 1.0,
    ) -> FlowResponse:
        """Build confirmation message showing all parameters."""
        params = agent_state.gathered_params

        # Use UX helper for better formatting
        content = ux_helper.format_confirmation_message(intent, params)

        # Add progress indicator
        progress = ux_helper.get_progress_update(
            ProgressStage.CONFIRMING,
            task_type=intent,
        )

        return FlowResponse(
            content=content,
            actions=[
                {"id": "confirm", "label": "✅ Wykonaj", "type": "primary"},
                {"id": "modify", "label": "✏️ Zmień", "type": "secondary"},
                {"id": "cancel", "label": "❌ Anuluj", "type": "ghost"},
            ],
            agent_state=agent_state,
            intent=intent,
            confidence=confidence,
            extracted_params=params,
            progress={
                "stage": progress.stage.value,
                "message": progress.message,
                "percentage": progress.percentage,
            },
        )

    def _build_execution_response(
        self,
        agent_state: AgentState,
        company_context: dict[str, Any],
    ) -> FlowResponse:
        """Build response for starting execution."""
        params = agent_state.gathered_params
        intent = agent_state.current_task or "unknown"

        # Build tasks to create
        tasks_to_create = self._build_tasks(intent, params)

        # Get progress indicator
        progress = ux_helper.get_progress_update(
            ProgressStage.EXECUTING,
            task_type=intent,
        )

        content = f"{progress.message}\n\n"
        content += self._format_params_preview(params)

        return FlowResponse(
            content=content,
            tasks_to_create=tasks_to_create,
            agent_state=agent_state,
            should_execute=True,
            intent=intent,
            confidence=1.0,
            extracted_params=params,
            progress={
                "stage": progress.stage.value,
                "message": progress.message,
                "percentage": progress.percentage,
            },
            show_feedback=True,  # Show feedback after completion
        )

    def _build_tasks(self, intent: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Build task creation info based on intent and params."""
        try:
            intent_enum = Intent(intent)
            agents = INTENT_TO_AGENTS.get(intent_enum, [])
        except ValueError:
            return []

        tasks = []
        for agent in agents:
            task_info = self._build_task_info(agent, intent, params)
            if task_info:
                tasks.append(task_info)

        return tasks

    def _build_task_info(
        self,
        agent: str,
        intent: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Build task creation info for a specific agent."""
        task_configs = {
            "instagram_specialist": {
                "department": "marketing",
                "type": "create_post",
                "input_mapping": {
                    "brief": params.get("topic", params.get("brief", "")),
                    "post_type": params.get("post_type", "post"),
                    "include_hashtags": True,
                    "platform": params.get("platform", "instagram"),
                    "tone": params.get("tone", "profesjonalny"),
                    "target_audience": params.get("target_audience", "ogólna"),
                },
            },
            "copywriter": {
                "department": "marketing",
                "type": "create_copy",
                "input_mapping": {
                    "brief": params.get("topic", params.get("brief", "")),
                    "copy_type": params.get("copy_type", "ad"),
                    "tone": params.get("tone", "profesjonalny"),
                    "target_audience": params.get("target_audience", "ogólna"),
                },
            },
            "invoice_specialist": {
                "department": "finance",
                "type": "create_invoice",
                "input_mapping": {
                    "client_name": params.get("client_name", ""),
                    "items": params.get("items", []),
                    "due_date": params.get("due_date", "14 dni"),
                    "payment_terms": params.get("payment_terms", "przelew"),
                },
            },
        }

        config = task_configs.get(agent)
        if not config:
            return None

        return {
            "agent": agent,
            "department": config["department"],
            "type": config["type"],
            "input": config["input_mapping"],
        }

    async def _extract_param_from_response_async(
        self,
        message: str,
        expected_param: str | None,
        task_type: str | None,
        agent_state: AgentState,
    ) -> dict[str, Any]:
        """Extract parameter values from user's response using LLM agent.

        Args:
            message: User's message
            expected_param: The parameter we asked about
            task_type: Current task type
            agent_state: Current agent state with context

        Returns:
            Dictionary of extracted parameters
        """
        if self._use_llm:
            try:
                # Use LLM parameter agent for smarter extraction
                result = await self._parameter_agent.extract(
                    message=message,
                    task_type=task_type,
                    existing_params=agent_state.gathered_params,
                    missing_params=agent_state.missing_required + agent_state.missing_recommended,
                    last_question_param=expected_param,
                )

                extracted = result.get("extracted", {})
                if extracted:
                    logger.debug(f"LLM extracted params: {extracted}")
                    return extracted

            except Exception as e:
                logger.warning(f"LLM parameter extraction failed: {e}")

        # Fallback to rule-based extraction
        return self._extract_param_from_response(message, expected_param, task_type)

    def _extract_param_from_response(
        self,
        message: str,
        expected_param: str | None,
        task_type: str | None,
    ) -> dict[str, Any]:
        """Extract parameter values from user's response (rule-based fallback)."""
        try:
            if task_type:
                intent = Intent(task_type)
            else:
                intent = Intent.UNKNOWN
        except ValueError:
            intent = Intent.UNKNOWN

        # Use the router's extraction
        extracted = self._router.extract_params_from_message(
            message, intent, is_followup=True
        )

        return extracted

    def _format_params_preview(self, params: dict[str, Any]) -> str:
        """Format parameters for display."""
        labels = {
            "topic": "Temat",
            "brief": "Temat",
            "post_type": "Typ",
            "platform": "Platforma",
            "copy_type": "Rodzaj tekstu",
            "client_name": "Klient",
            "tone": "Ton",
            "target_audience": "Grupa docelowa",
            "campaign_goal": "Cel kampanii",
            "salary_range": "Wynagrodzenie",
            "location": "Lokalizacja",
            "remote_option": "Praca zdalna",
            "due_date": "Termin płatności",
            "payment_terms": "Warunki płatności",
        }

        value_labels = {
            "post": "post",
            "story": "story",
            "reel": "reel",
            "instagram": "Instagram",
            "facebook": "Facebook",
            "linkedin": "LinkedIn",
            "profesjonalny": "profesjonalny",
            "casualowy": "casualowy",
            "zabawny": "zabawny",
            "ogólna": "ogólna",
        }

        lines = ["📋 **Parametry:**"]
        for key, value in params.items():
            if value and key in labels:
                display_value = value_labels.get(value, value) if isinstance(value, str) else value
                # Truncate long values
                if isinstance(display_value, str) and len(display_value) > 50:
                    display_value = display_value[:50] + "..."
                lines.append(f"• {labels[key]}: {display_value}")

        return "\n".join(lines) if len(lines) > 1 else ""

    async def _generate_conversational_response(
        self,
        message: str,
        intent: Intent,
        context: dict[str, Any],
    ) -> str:
        """Generate intelligent conversational response using LLM.

        Args:
            message: User's message
            intent: Detected intent type
            context: Conversation context

        Returns:
            AI-generated response string
        """
        try:
            # Build context for the conversation agent
            conv_context = ConversationContext(
                messages=context.get("messages", []),
                current_task=None,
                gathered_params={},
                missing_params=[],
            )

            # Create a specialized prompt for general conversation
            system_prompt = self._build_conversational_system_prompt(intent)

            # Use the conversation agent's LLM
            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=message),
            ]

            response = await conversation_agent.llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.warning(f"LLM conversation failed: {e}, using fallback")
            # Fallback to hardcoded responses
            if intent == Intent.GREETING:
                return self._build_greeting_response()
            elif intent == Intent.HELP:
                return self._build_help_response()
            elif intent == Intent.CAPABILITIES:
                domain = self._detect_domain_from_message(message)
                return self._build_capabilities_response(domain)
            else:
                return self._build_unknown_response()

    def _build_conversational_system_prompt(self, intent: Intent) -> str:
        """Build system prompt for conversational responses."""
        base_info = """Jesteś Agora - inteligentnym asystentem AI dla firm. Twoje możliwości:

**MARKETING:**
- Tworzenie postów na social media (Instagram, Facebook, LinkedIn)
- Pisanie tekstów reklamowych, sloganów, opisów produktów
- Planowanie kampanii marketingowych
- Generowanie grafik do postów

**FINANSE:**
- Generowanie profesjonalnych faktur VAT
- Analiza przepływów finansowych (cashflow)
- Planowanie budżetu

**HR:**
- Tworzenie ogłoszeń o pracę
- Przygotowanie pytań rekrutacyjnych
- Materiały onboardingowe dla nowych pracowników

**PRAWO:**
- Analiza umów i kontraktów
- Tworzenie polityki prywatności
- Regulaminy i warunki usług
- Weryfikacja zgodności z RODO/GDPR

**SPRZEDAŻ:**
- Przygotowanie ofert handlowych
- Lead scoring - ocena potencjalnych klientów
- Emaile follow-up do klientów

**OBSŁUGA KLIENTA:**
- Odpowiedzi na zgłoszenia i reklamacje
- Tworzenie bazy FAQ
- Analiza sentymentu opinii klientów"""

        if intent == Intent.GREETING:
            return f"""{base_info}

Użytkownik się wita. Odpowiedz przyjaźnie, krótko przedstaw się i zapytaj jak możesz pomóc.
Bądź naturalny, nie wymieniaj wszystkich funkcji - po prostu przywitaj się ciepło.
Odpowiadaj po polsku."""

        elif intent == Intent.HELP:
            return f"""{base_info}

Użytkownik prosi o pomoc lub instrukcje. Wyjaśnij jak korzystać z asystenta:
- Wystarczy opisać czego potrzebuje naturalnym językiem
- Możesz podać 2-3 przykłady użycia
- Bądź pomocny i zachęcający
Odpowiadaj po polsku."""

        elif intent == Intent.CAPABILITIES:
            return f"""{base_info}

Użytkownik pyta o Twoje możliwości. Odpowiedz na konkretne pytanie:
- Jeśli pyta ogólnie - daj przegląd głównych obszarów
- Jeśli pyta o konkretny obszar (np. finanse) - opisz szczegółowo ten obszar
- Podaj 1-2 przykłady użycia dla danego obszaru
Odpowiadaj po polsku, używaj emoji dla lepszej czytelności."""

        else:  # UNKNOWN
            return f"""{base_info}

Nie rozpoznano konkretnego zadania w wiadomości użytkownika.
Spróbuj zrozumieć co użytkownik chce osiągnąć i:
1. Jeśli to pytanie - odpowiedz na nie
2. Jeśli to prośba niejasna - dopytaj o szczegóły
3. Jeśli to rozmowa - prowadź ją naturalnie

NIE mów "nie rozumiem" - zawsze staraj się pomóc.
Jeśli naprawdę nie wiesz o co chodzi, zaproponuj przykłady tego co możesz zrobić.
Odpowiadaj po polsku, bądź pomocny i naturalny."""

    def _build_greeting_response(self) -> str:
        """Build friendly greeting response (fallback)."""
        return (
            "Cześć! 👋 Jestem **Agora** - Twój asystent biznesowy.\n\n"
            "Mogę pomóc Ci z:\n"
            "• 📱 **Marketing** - posty, teksty reklamowe, kampanie\n"
            "• 💰 **Finanse** - faktury, analizy cashflow\n"
            "• 👥 **HR** - ogłoszenia o pracę, onboarding\n"
            "• ⚖️ **Prawo** - umowy, regulaminy, RODO\n"
            "• 🎯 **Sprzedaż** - oferty, follow-upy, lead scoring\n\n"
            "Po prostu powiedz mi czego potrzebujesz!"
        )

    def _build_help_response(self) -> str:
        """Build help response with usage instructions."""
        return (
            "**Jak mogę Ci pomóc?** 🤝\n\n"
            "Po prostu napisz czego potrzebujesz, np.:\n"
            "• *\"Stwórz post na Instagram o nowej kawie\"*\n"
            "• *\"Wygeneruj fakturę dla klienta ABC\"*\n"
            "• *\"Napisz ogłoszenie o pracę na stanowisko programisty\"*\n\n"
            "Zadam Ci kilka pytań, żeby doprecyzować szczegóły, "
            "a potem wykonam zadanie.\n\n"
            "💡 **Wskazówka**: Możesz też zapytać *\"co możesz zrobić w kwestii finansów?\"* "
            "żeby poznać moje możliwości w danym obszarze."
        )

    def _detect_domain_from_message(self, message: str) -> str | None:
        """Detect which domain the user is asking about."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["finans", "faktur", "cashflow", "pieniądz", "budżet"]):
            return "finance"
        if any(word in message_lower for word in ["market", "reklam", "post", "social", "instagram"]):
            return "marketing"
        if any(word in message_lower for word in ["hr", "rekrutac", "pracownik", "zatrudn", "onboard"]):
            return "hr"
        if any(word in message_lower for word in ["praw", "umow", "regulamin", "rodo", "gdpr"]):
            return "legal"
        if any(word in message_lower for word in ["sprzedaż", "ofert", "klient", "lead", "handl"]):
            return "sales"
        if any(word in message_lower for word in ["support", "obsług", "ticket", "zgłoszeni"]):
            return "support"

        return None

    def _build_capabilities_response(self, domain: str | None = None) -> str:
        """Build response describing capabilities, optionally for specific domain."""

        capabilities = {
            "marketing": (
                "**📱 Marketing - moje możliwości:**\n\n"
                "• **Posty social media** - Instagram, Facebook, LinkedIn z hashtagami i grafiką\n"
                "• **Teksty reklamowe** - copy, slogany, opisy produktów\n"
                "• **Kampanie** - pełne pakiety materiałów marketingowych\n"
                "• **Newsletter** - treści emailowe\n\n"
                "Przykład: *\"Stwórz post na Instagram o promocji -20%\"*"
            ),
            "finance": (
                "**💰 Finanse - moje możliwości:**\n\n"
                "• **Faktury** - generowanie profesjonalnych faktur z VAT\n"
                "• **Analiza cashflow** - przegląd przepływów finansowych\n"
                "• **Budżetowanie** - planowanie wydatków\n\n"
                "Przykład: *\"Wygeneruj fakturę dla firmy ABC na 5000 zł\"*"
            ),
            "hr": (
                "**👥 HR - moje możliwości:**\n\n"
                "• **Ogłoszenia o pracę** - profesjonalne oferty zatrudnienia\n"
                "• **Pytania rekrutacyjne** - zestawy na rozmowy kwalifikacyjne\n"
                "• **Onboarding** - materiały powitalne dla nowych pracowników\n\n"
                "Przykład: *\"Napisz ogłoszenie o pracę dla programisty Python\"*"
            ),
            "legal": (
                "**⚖️ Prawo - moje możliwości:**\n\n"
                "• **Analiza umów** - przegląd i uwagi do kontraktów\n"
                "• **Polityka prywatności** - dokumenty RODO/GDPR\n"
                "• **Regulaminy** - warunki korzystania z usług\n"
                "• **Weryfikacja RODO** - sprawdzenie zgodności\n\n"
                "Przykład: *\"Sprawdź zgodność mojej strony z RODO\"*"
            ),
            "sales": (
                "**🎯 Sprzedaż - moje możliwości:**\n\n"
                "• **Oferty handlowe** - propozycje i wyceny\n"
                "• **Lead scoring** - ocena potencjalnych klientów\n"
                "• **Follow-up** - emaile przypominające do klientów\n\n"
                "Przykład: *\"Przygotuj ofertę handlową dla klienta XYZ\"*"
            ),
            "support": (
                "**🎧 Obsługa klienta - moje możliwości:**\n\n"
                "• **Odpowiedzi na zgłoszenia** - profesjonalne odpowiedzi\n"
                "• **FAQ** - baza najczęściej zadawanych pytań\n"
                "• **Analiza sentymentu** - ocena opinii klientów\n\n"
                "Przykład: *\"Napisz odpowiedź na reklamację klienta\"*"
            ),
        }

        if domain and domain in capabilities:
            return capabilities[domain]

        # General overview
        return (
            "**Oto co mogę dla Ciebie zrobić:** 🚀\n\n"
            "📱 **Marketing**\n"
            "Posty social media, teksty reklamowe, kampanie\n\n"
            "💰 **Finanse**\n"
            "Faktury, analizy cashflow, budżetowanie\n\n"
            "👥 **HR**\n"
            "Ogłoszenia o pracę, rekrutacja, onboarding\n\n"
            "⚖️ **Prawo**\n"
            "Umowy, regulaminy, RODO\n\n"
            "🎯 **Sprzedaż**\n"
            "Oferty, lead scoring, follow-upy\n\n"
            "🎧 **Obsługa klienta**\n"
            "Odpowiedzi na zgłoszenia, FAQ\n\n"
            "💡 Zapytaj np. *\"co możesz zrobić w kwestii marketingu?\"* "
            "żeby poznać szczegóły danego obszaru."
        )

    def _build_unknown_response(self) -> str:
        """Build response for unknown intent."""
        # Use UX helper for consistent error messaging
        error_info = ux_helper.get_error_response(ErrorType.UNKNOWN_INTENT)

        content = f"**{error_info['title']}**\n\n{error_info['message']}\n\n"

        if error_info.get('suggestions'):
            content += "Spróbuj na przykład:\n"
            for suggestion in error_info['suggestions'][:4]:
                content += f"• {suggestion}\n"

        return content


# Singleton instance
flow_controller = ConversationFlowController()
