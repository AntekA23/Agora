"""Conversation service for multi-turn chat with agents.

This service handles the conversational flow, maintaining context
and routing to appropriate agents based on the conversation.
"""

from datetime import datetime
from typing import Any

from app.services.assistant import assistant_router, Intent


class ConversationService:
    """Service for managing multi-turn conversations with AI agents."""

    # Agent descriptions for the assistant
    AGENT_DESCRIPTIONS = {
        "instagram_specialist": "tworzenie postów na Instagram",
        "copywriter": "pisanie tekstów reklamowych i marketingowych",
        "invoice_specialist": "wystawianie faktur",
        "cashflow_analyst": "analiza przepływów finansowych",
        "hr_recruiter": "rekrutacja i ogłoszenia o pracę",
        "campaign_service": "planowanie kampanii marketingowych",
        "legal_terms": "dokumenty prawne i regulaminy",
        "support_agent": "obsługa klienta",
    }

    # Intent to agent mapping
    INTENT_AGENTS = {
        Intent.SOCIAL_MEDIA_POST: ["instagram_specialist"],
        Intent.MARKETING_COPY: ["copywriter"],
        Intent.CAMPAIGN: ["campaign_service", "instagram_specialist", "copywriter"],
        Intent.INVOICE: ["invoice_specialist"],
        Intent.CASHFLOW_ANALYSIS: ["cashflow_analyst"],
        Intent.JOB_POSTING: ["hr_recruiter"],
        Intent.INTERVIEW_QUESTIONS: ["hr_recruiter"],
        Intent.ONBOARDING: ["hr_recruiter"],
        Intent.SALES_PROPOSAL: ["copywriter"],
        Intent.LEAD_SCORING: ["copywriter"],
        Intent.FOLLOWUP_EMAIL: ["copywriter"],
        Intent.CONTRACT_REVIEW: ["legal_terms"],
        Intent.PRIVACY_POLICY: ["legal_terms"],
        Intent.TERMS_OF_SERVICE: ["legal_terms"],
        Intent.GDPR_CHECK: ["legal_terms"],
        Intent.TICKET_RESPONSE: ["support_agent"],
        Intent.FAQ: ["support_agent"],
        Intent.SENTIMENT_ANALYSIS: ["support_agent"],
    }

    async def process_message(
        self,
        message: str,
        conversation_context: dict[str, Any],
        company_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a user message and generate a response.

        Args:
            message: User's message
            conversation_context: Previous messages and extracted params
            company_context: Company info, brand, etc.

        Returns:
            Response with assistant message, actions, and any tasks to create
        """
        # First, interpret the message using existing assistant
        intent_result = await assistant_router.interpret(message)

        # Build response based on intent
        response: dict[str, Any] = {
            "content": "",
            "actions": [],
            "tasks_to_create": [],
            "follow_up_questions": [],
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "extracted_params": intent_result.extracted_params,
        }

        # Merge with conversation context params
        merged_params = {
            **conversation_context.get("extracted_params", {}),
            **intent_result.extracted_params,
        }
        response["extracted_params"] = merged_params

        # If we have enough info to auto-execute
        if intent_result.can_auto_execute:
            response = self._build_execution_response(
                intent_result, merged_params, company_context
            )
        elif intent_result.follow_up_questions:
            # Need more info
            response["content"] = self._build_follow_up_response(intent_result)
            response["follow_up_questions"] = intent_result.follow_up_questions
        else:
            # General response
            response["content"] = self._build_general_response(intent_result)

        return response

    def _build_execution_response(
        self,
        intent_result: Any,
        params: dict[str, Any],
        company_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build response for auto-executable intent.

        Note: With auto-execute enabled, tasks are created immediately
        by the endpoint, so we don't need action buttons here.
        """
        agents = self.INTENT_AGENTS.get(intent_result.intent, [])

        # Build task creation info
        tasks_to_create = []
        for agent in agents:
            task_info = self._build_task_info(agent, intent_result.intent, params)
            if task_info:
                tasks_to_create.append(task_info)

        # Content will be replaced by endpoint with params preview
        # This is just a fallback
        content = "Rozumiem! Zaczynam generowanie..."

        return {
            "content": content,
            "actions": [],  # No actions - auto-execute handles this
            "tasks_to_create": tasks_to_create,
            "follow_up_questions": [],
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "extracted_params": params,
            "can_execute": True,
        }

    def _build_follow_up_response(self, intent_result: Any) -> str:
        """Build response asking for more info."""
        if len(intent_result.follow_up_questions) == 1:
            return intent_result.follow_up_questions[0]

        content = "Potrzebuję jeszcze kilku informacji:\n\n"
        for i, question in enumerate(intent_result.follow_up_questions, 1):
            content += f"{i}. {question}\n"
        return content

    def _build_general_response(self, intent_result: Any) -> str:
        """Build general response when intent is unclear."""
        if intent_result.confidence < 0.3:
            return (
                "Nie jestem pewien czego potrzebujesz. "
                "Możesz mi powiedzieć więcej?\n\n"
                "Mogę pomóc z:\n"
                "• Postami na social media\n"
                "• Tekstami reklamowymi\n"
                "• Fakturami\n"
                "• Kampaniami marketingowymi\n"
                "• Rekrutacją\n"
                "• I wieloma innymi zadaniami!"
            )

        agents = intent_result.suggested_agents
        if agents:
            agent_names = [self.AGENT_DESCRIPTIONS.get(a, a) for a in agents]
            return (
                f"Rozumiem, że chcesz {agent_names[0]}. "
                "Opowiedz mi więcej o szczegółach."
            )

        return "Opowiedz mi więcej o tym, czego potrzebujesz."

    def _build_task_info(
        self,
        agent: str,
        intent: Intent,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Build task creation info for an agent."""
        task_configs = {
            "instagram_specialist": {
                "department": "marketing",
                "type": "create_post",
                "input_mapping": {
                    "brief": params.get("topic", params.get("brief", "")),
                    "post_type": params.get("post_type", "post"),
                    "include_hashtags": True,
                },
            },
            "copywriter": {
                "department": "marketing",
                "type": "create_copy",
                "input_mapping": {
                    "brief": params.get("topic", params.get("brief", "")),
                    "copy_type": params.get("copy_type", "ad"),
                },
            },
            "invoice_specialist": {
                "department": "finance",
                "type": "create_invoice",
                "input_mapping": {
                    "client_name": params.get("client_name", ""),
                    "items": params.get("items", []),
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

    def generate_title(self, first_message: str) -> str:
        """Generate a conversation title from the first message."""
        # Simple title generation - take first 50 chars
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title


# Global service instance
conversation_service = ConversationService()
