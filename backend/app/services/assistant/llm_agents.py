"""LLM-powered agents for intelligent conversation handling.

This module implements the multi-agent architecture for Phase 4:
1. ConversationAgent - Understands context and generates natural responses
2. ParameterAgent - Intelligently extracts parameters from messages
3. Orchestrator - Coordinates between agents

Each agent uses LLM (GPT-4o-mini) with fallback to rule-based logic.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.config import settings
from app.services.assistant.router import (
    Intent,
    INTENT_PATTERNS,
    INTENT_REQUIRED_PARAMS,
    INTENT_RECOMMENDED_PARAMS,
    PARAM_QUESTIONS,
    RECOMMENDED_PARAM_QUESTIONS,
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for conversation agents."""

    messages: list[dict[str, str]] = field(default_factory=list)
    current_task: str | None = None
    gathered_params: dict[str, Any] = field(default_factory=dict)
    missing_params: list[str] = field(default_factory=list)
    original_request: str | None = None
    company_name: str | None = None
    brand_voice: str | None = None

    def get_summary(self) -> str:
        """Get a summary of the conversation context."""
        parts = []

        if self.current_task:
            parts.append(f"Obecne zadanie: {self.current_task}")
        if self.original_request:
            parts.append(f"Oryginalne zapytanie: {self.original_request}")
        if self.gathered_params:
            params_str = ", ".join(f"{k}={v}" for k, v in self.gathered_params.items())
            parts.append(f"Zebrane parametry: {params_str}")
        if self.missing_params:
            parts.append(f"Brakujące: {', '.join(self.missing_params)}")

        return "\n".join(parts) if parts else "Brak kontekstu"

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """Get messages formatted for LLM."""
        return self.messages[-10:]  # Last 10 messages for context


class ConversationAgent:
    """LLM-powered agent for understanding context and natural conversation.

    Responsibilities:
    - Understand the full context of conversation
    - Generate natural, contextual responses in Polish
    - Maintain conversation flow
    - Handle ambiguous requests intelligently
    """

    SYSTEM_PROMPT = """Jesteś asystentem Agora - platformy AI dla firm.

TWOJA ROLA:
- Rozumiesz kontekst całej konwersacji
- Pamiętasz co użytkownik powiedział wcześniej
- Prowadzisz naturalną rozmowę po polsku
- Zbierasz potrzebne informacje w przyjazny sposób

OBECNY KONTEKST:
{context}

ZEBRANE PARAMETRY:
{params}

BRAKUJĄCE INFORMACJE:
{missing}

STYL:
- Odpowiadaj zwięźle ale przyjaźnie
- Używaj polskiego
- Bądź pomocny i proaktywny
- Jeśli czegoś nie rozumiesz, poproś o wyjaśnienie

ZADANIE:
Na podstawie wiadomości użytkownika, zdecyduj co zrobić:
1. Jeśli użytkownik odpowiada na pytanie - wyekstrahuj wartość
2. Jeśli użytkownik chce coś nowego - rozpoznaj intencję
3. Jeśli coś jest niejasne - dopytaj naturalnie
4. Jeśli wszystko jest jasne - potwierdź i przejdź dalej

Odpowiedz w formacie JSON:
{{
    "understanding": "krótkie podsumowanie co zrozumiałeś",
    "response": "twoja odpowiedź dla użytkownika",
    "extracted_params": {{"param_name": "value"}},
    "next_action": "continue|confirm|execute|clarify|new_task",
    "confidence": 0.0-1.0
}}"""

    def __init__(self):
        """Initialize the conversation agent."""
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.3,
            )
        return self._llm

    async def process(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Process a message with full context understanding.

        Args:
            message: User's message
            context: Full conversation context

        Returns:
            Dictionary with:
            - understanding: What we understood
            - response: Response for user
            - extracted_params: Any extracted parameters
            - next_action: What to do next
            - confidence: Confidence score
        """
        try:
            return await self._process_with_llm(message, context)
        except Exception as e:
            logger.warning(f"LLM processing failed, using fallback: {e}")
            return self._fallback_process(message, context)

    async def _process_with_llm(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Process using LLM."""
        # Format system prompt with context
        system_prompt = self.SYSTEM_PROMPT.format(
            context=context.get_summary(),
            params=json.dumps(context.gathered_params, ensure_ascii=False),
            missing=", ".join(context.missing_params) if context.missing_params else "brak",
        )

        # Build messages
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history
        for msg in context.get_messages_for_llm():
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Add current message
        messages.append(HumanMessage(content=message))

        # Get LLM response
        response = await self.llm.ainvoke(messages)

        # Parse JSON response
        try:
            result = json.loads(response.content)
            return {
                "understanding": result.get("understanding", ""),
                "response": result.get("response", ""),
                "extracted_params": result.get("extracted_params", {}),
                "next_action": result.get("next_action", "continue"),
                "confidence": result.get("confidence", 0.8),
            }
        except json.JSONDecodeError:
            # If LLM didn't return JSON, use the text as response
            return {
                "understanding": "Odpowiedź tekstowa",
                "response": response.content,
                "extracted_params": {},
                "next_action": "continue",
                "confidence": 0.7,
            }

    def _fallback_process(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Fallback to rule-based processing when LLM fails."""
        # Simple pattern matching for known values
        extracted_params = {}
        message_lower = message.lower().strip()

        # Check for tone values
        tone_map = {
            "profesjonalny": "profesjonalny",
            "casualowy": "casualowy",
            "luźny": "casualowy",
            "zabawny": "zabawny",
            "formalny": "formalny",
        }
        for key, value in tone_map.items():
            if key in message_lower:
                extracted_params["tone"] = value
                break

        # Check for platform values
        platform_map = {
            "instagram": "instagram",
            "insta": "instagram",
            "facebook": "facebook",
            "fb": "facebook",
            "linkedin": "linkedin",
        }
        for key, value in platform_map.items():
            if key in message_lower:
                extracted_params["platform"] = value
                break

        # Check for audience values
        audience_map = {
            "młodzi": "młodzi",
            "dorośli": "dorośli",
            "firmy": "firmy",
            "b2b": "firmy",
            "wszyscy": "ogólna",
        }
        for key, value in audience_map.items():
            if key in message_lower:
                extracted_params["target_audience"] = value
                break

        # Determine next action
        if extracted_params:
            next_action = "continue"
            response = "Rozumiem, zapisuję."
        elif len(message.split()) > 10:
            next_action = "new_task"
            response = "Analizuję zapytanie..."
        else:
            next_action = "clarify"
            response = "Możesz powiedzieć więcej?"

        return {
            "understanding": f"Rozpoznano: {extracted_params}" if extracted_params else "Niejednoznaczna odpowiedź",
            "response": response,
            "extracted_params": extracted_params,
            "next_action": next_action,
            "confidence": 0.6 if extracted_params else 0.3,
        }


class ParameterAgent:
    """LLM-powered agent for intelligent parameter extraction.

    Responsibilities:
    - Extract parameters from natural language
    - Validate parameter values
    - Suggest corrections for invalid values
    - Handle context-dependent extraction
    """

    EXTRACTION_PROMPT = """Wyekstrahuj parametry z wiadomości użytkownika.

KONTEKST ZADANIA: {task_type}
POPRZEDNIE PARAMETRY: {existing_params}
BRAKUJĄCE PARAMETRY: {missing}
OSTATNIE PYTANIE: {last_question}

DOSTĘPNE PARAMETRY I ICH MOŻLIWE WARTOŚCI:
- topic: dowolny tekst opisujący temat
- platform: instagram, facebook, linkedin
- tone: profesjonalny, casualowy, zabawny, formalny
- target_audience: młodzi, dorośli, firmy, ogólna
- post_type: post, story, reel
- copy_type: ad, email, slogan, description

WIADOMOŚĆ UŻYTKOWNIKA: {message}

ZADANIE:
Wyekstrahuj wartości parametrów z wiadomości. Jeśli użytkownik odpowiada na pytanie
o konkretny parametr, przypisz wartość do tego parametru.

Zwróć JSON:
{{
    "extracted": {{"param_name": "value"}},
    "needs_clarification": ["param_name"],
    "confidence": 0.0-1.0
}}"""

    def __init__(self):
        """Initialize the parameter agent."""
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1,  # Low temperature for precise extraction
            )
        return self._llm

    async def extract(
        self,
        message: str,
        task_type: str | None,
        existing_params: dict[str, Any],
        missing_params: list[str],
        last_question_param: str | None = None,
    ) -> dict[str, Any]:
        """Extract parameters from a message.

        Args:
            message: User's message
            task_type: Type of task (e.g., "social_media_post")
            existing_params: Already extracted parameters
            missing_params: Parameters still needed
            last_question_param: Parameter the last question was about

        Returns:
            Dictionary with:
            - extracted: Extracted parameter values
            - needs_clarification: Parameters that need clarification
            - confidence: Confidence score
        """
        try:
            return await self._extract_with_llm(
                message, task_type, existing_params, missing_params, last_question_param
            )
        except Exception as e:
            logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extract(message, last_question_param)

    async def _extract_with_llm(
        self,
        message: str,
        task_type: str | None,
        existing_params: dict[str, Any],
        missing_params: list[str],
        last_question_param: str | None,
    ) -> dict[str, Any]:
        """Extract using LLM."""
        # Get the last question text
        last_question = ""
        if last_question_param:
            last_question = RECOMMENDED_PARAM_QUESTIONS.get(
                last_question_param,
                PARAM_QUESTIONS.get(last_question_param, "")
            )

        prompt = self.EXTRACTION_PROMPT.format(
            task_type=task_type or "unknown",
            existing_params=json.dumps(existing_params, ensure_ascii=False),
            missing=", ".join(missing_params) if missing_params else "brak",
            last_question=last_question or "brak",
            message=message,
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            result = json.loads(response.content)
            return {
                "extracted": result.get("extracted", {}),
                "needs_clarification": result.get("needs_clarification", []),
                "confidence": result.get("confidence", 0.8),
            }
        except json.JSONDecodeError:
            return self._fallback_extract(message, last_question_param)

    def _fallback_extract(
        self,
        message: str,
        last_question_param: str | None,
    ) -> dict[str, Any]:
        """Fallback extraction when LLM fails."""
        extracted = {}
        message_lower = message.lower().strip()

        # Direct value mapping
        value_maps = {
            "tone": {
                "profesjonalny": "profesjonalny",
                "casualowy": "casualowy",
                "luźny": "casualowy",
                "zabawny": "zabawny",
                "formalny": "formalny",
            },
            "platform": {
                "instagram": "instagram",
                "insta": "instagram",
                "ig": "instagram",
                "facebook": "facebook",
                "fb": "facebook",
                "linkedin": "linkedin",
            },
            "target_audience": {
                "młodzi": "młodzi",
                "młodych": "młodzi",
                "dorośli": "dorośli",
                "firmy": "firmy",
                "b2b": "firmy",
                "wszyscy": "ogólna",
                "ogólna": "ogólna",
            },
            "post_type": {
                "post": "post",
                "story": "story",
                "stories": "story",
                "reel": "reel",
                "reels": "reel",
            },
        }

        # If we asked about a specific param, try to map the answer
        if last_question_param and last_question_param in value_maps:
            for key, value in value_maps[last_question_param].items():
                if key in message_lower:
                    extracted[last_question_param] = value
                    break
            # If no match but short message, assume it's the value
            if not extracted and len(message.split()) <= 3:
                extracted[last_question_param] = message.strip()

        # Also check for any recognized values
        for param, value_map in value_maps.items():
            if param not in extracted:
                for key, value in value_map.items():
                    if key in message_lower:
                        extracted[param] = value
                        break

        return {
            "extracted": extracted,
            "needs_clarification": [],
            "confidence": 0.7 if extracted else 0.3,
        }


class Orchestrator:
    """Orchestrator for coordinating multi-agent interactions.

    Responsibilities:
    - Decide which agent to use
    - Coordinate between agents
    - Manage overall conversation flow
    - Handle errors and fallbacks
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.conversation_agent = ConversationAgent()
        self.parameter_agent = ParameterAgent()

    async def process(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Process a message using the appropriate agents.

        Args:
            message: User's message
            context: Conversation context

        Returns:
            Combined result from agents with:
            - response: Response for user
            - extracted_params: Extracted parameters
            - next_action: What to do next
            - confidence: Overall confidence
        """
        # First, use parameter agent if we're gathering
        if context.missing_params or context.current_task:
            param_result = await self.parameter_agent.extract(
                message=message,
                task_type=context.current_task,
                existing_params=context.gathered_params,
                missing_params=context.missing_params,
                last_question_param=context.missing_params[0] if context.missing_params else None,
            )

            # Update context with extracted params
            for key, value in param_result.get("extracted", {}).items():
                context.gathered_params[key] = value
                if key in context.missing_params:
                    context.missing_params.remove(key)

        # Then use conversation agent for response
        conv_result = await self.conversation_agent.process(message, context)

        # Merge extracted params
        all_params = {
            **conv_result.get("extracted_params", {}),
        }
        if context.missing_params or context.current_task:
            all_params.update(param_result.get("extracted", {}))

        return {
            "response": conv_result.get("response", ""),
            "understanding": conv_result.get("understanding", ""),
            "extracted_params": all_params,
            "next_action": conv_result.get("next_action", "continue"),
            "confidence": (
                conv_result.get("confidence", 0.5) +
                param_result.get("confidence", 0.5) if 'param_result' in dir() else conv_result.get("confidence", 0.5)
            ) / 2,
            "needs_clarification": param_result.get("needs_clarification", []) if 'param_result' in dir() else [],
        }

    async def interpret_intent(
        self,
        message: str,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Interpret the intent of a message using LLM.

        Args:
            message: User's message
            context: Conversation context

        Returns:
            Intent interpretation with:
            - intent: Detected intent
            - confidence: Confidence score
            - extracted_params: Initial parameters
        """
        # Use conversation agent's understanding
        result = await self.conversation_agent.process(message, context)

        # Map next_action to intent handling
        if result.get("next_action") == "new_task":
            # This is a new request, needs intent detection
            return {
                "is_new_request": True,
                "extracted_params": result.get("extracted_params", {}),
                "confidence": result.get("confidence", 0.5),
            }
        else:
            # This is a continuation
            return {
                "is_new_request": False,
                "extracted_params": result.get("extracted_params", {}),
                "confidence": result.get("confidence", 0.8),
            }


# Singleton instances
conversation_agent = ConversationAgent()
parameter_agent = ParameterAgent()
orchestrator = Orchestrator()
