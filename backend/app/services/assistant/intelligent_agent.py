"""Intelligent Agent - Level 1 Implementation.

Combines:
1.1 Long-term Memory (conversation history + preferences)
1.2 Company Knowledge RAG (products, brand, context)
1.3 LLM-based Intent Detection (no more pattern matching)

This is the brain of Agora - a truly intelligent assistant.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.core.config import settings
from app.services.assistant.router import Intent, INTENT_TO_AGENTS

logger = logging.getLogger(__name__)


@dataclass
class ConversationMemory:
    """Memory of the current conversation."""
    messages: list[dict[str, str]] = field(default_factory=list)
    detected_intent: str | None = None
    gathered_params: dict[str, Any] = field(default_factory=dict)
    company_context: str = ""
    relevant_memories: list[str] = field(default_factory=list)


@dataclass
class IntentDetectionResult:
    """Result of LLM-based intent detection."""
    intent: Intent
    confidence: float
    reasoning: str
    extracted_params: dict[str, Any]
    is_conversational: bool  # True if it's a question/chat, not a task request
    suggested_response: str | None = None


class IntelligentAgent:
    """The intelligent core of Agora assistant.

    Uses LLM for:
    - Understanding user intent (not pattern matching)
    - Generating contextual responses
    - Extracting parameters naturally
    - Maintaining conversation memory
    """

    # Available capabilities for the agent
    CAPABILITIES = {
        "marketing": {
            "name": "Marketing",
            "tasks": ["social_media_post", "marketing_copy", "campaign"],
            "description": "Posty social media, teksty reklamowe, kampanie marketingowe",
            "examples": [
                "Stwórz post na Instagram o nowym produkcie",
                "Napisz tekst reklamowy na promocję",
                "Przygotuj kampanię na Black Friday"
            ]
        },
        "finance": {
            "name": "Finanse",
            "tasks": ["invoice", "cashflow_analysis"],
            "description": "Faktury VAT, analiza przepływów finansowych",
            "examples": [
                "Wygeneruj fakturę dla klienta ABC",
                "Przeanalizuj cashflow za ostatni miesiąc"
            ]
        },
        "hr": {
            "name": "HR",
            "tasks": ["job_posting", "interview_questions", "onboarding"],
            "description": "Ogłoszenia o pracę, rekrutacja, onboarding",
            "examples": [
                "Napisz ogłoszenie o pracę dla programisty",
                "Przygotuj pytania rekrutacyjne na rozmowę"
            ]
        },
        "legal": {
            "name": "Prawo",
            "tasks": ["contract_review", "privacy_policy", "terms_of_service", "gdpr_check"],
            "description": "Umowy, regulaminy, RODO",
            "examples": [
                "Przeanalizuj tę umowę",
                "Stwórz politykę prywatności"
            ]
        },
        "sales": {
            "name": "Sprzedaż",
            "tasks": ["sales_proposal", "lead_scoring", "followup_email"],
            "description": "Oferty handlowe, lead scoring, follow-upy",
            "examples": [
                "Przygotuj ofertę dla klienta XYZ",
                "Napisz email follow-up do klienta"
            ]
        },
        "support": {
            "name": "Obsługa klienta",
            "tasks": ["ticket_response", "faq", "sentiment_analysis"],
            "description": "Odpowiedzi na zgłoszenia, FAQ, analiza sentymentu",
            "examples": [
                "Odpowiedz na tę reklamację",
                "Stwórz FAQ dla produktu"
            ]
        }
    }

    INTENT_DETECTION_PROMPT = """Jesteś inteligentnym asystentem Agora. Przeanalizuj wiadomość użytkownika.

TWOJE MOŻLIWOŚCI:
{capabilities}

KONTEKST ROZMOWY:
{conversation_history}

WIEDZA O FIRMIE:
{company_context}

WIADOMOŚĆ UŻYTKOWNIKA: {message}

ZADANIE:
Przeanalizuj wiadomość i określ:
1. Czy użytkownik chce wykonać konkretne zadanie? Jeśli tak - jakie?
2. Czy to pytanie o Twoje możliwości lub prośba o pomoc?
3. Czy to zwykła rozmowa (powitanie, podziękowanie, itp.)?
4. Jakie parametry można wyciągnąć z wiadomości?

DOSTĘPNE TYPY ZADAŃ:
- social_media_post: posty na social media (Instagram, Facebook, LinkedIn)
- marketing_copy: teksty reklamowe, slogany, opisy
- campaign: kampanie marketingowe
- invoice: faktury
- cashflow_analysis: analiza finansów
- job_posting: ogłoszenia o pracę
- interview_questions: pytania rekrutacyjne
- onboarding: materiały dla nowych pracowników
- contract_review: analiza umów
- privacy_policy: polityka prywatności
- terms_of_service: regulaminy
- gdpr_check: weryfikacja RODO
- ticket_response: odpowiedzi na zgłoszenia
- faq: baza FAQ
- sentiment_analysis: analiza sentymentu
- sales_proposal: oferty handlowe
- lead_scoring: ocena leadów
- followup_email: emaile follow-up

Zwróć JSON:
{{
    "intent": "typ_zadania lub 'conversational' lub 'help' lub 'unknown'",
    "confidence": 0.0-1.0,
    "reasoning": "krótkie wyjaśnienie dlaczego tak sklasyfikowałeś",
    "is_task_request": true/false,
    "extracted_params": {{
        "topic": "temat jeśli wykryty",
        "platform": "platforma jeśli wykryta",
        "tone": "ton jeśli wykryty",
        "target_audience": "grupa docelowa jeśli wykryta"
    }},
    "suggested_response": "jeśli to conversational/help - zaproponuj odpowiedź po polsku"
}}"""

    RESPONSE_GENERATION_PROMPT = """Jesteś Agora - inteligentnym asystentem AI dla firm.

TWOJE MOŻLIWOŚCI:
{capabilities}

KONTEKST ROZMOWY:
{conversation_history}

WIEDZA O FIRMIE:
{company_context}

POPRZEDNIE UDANE ZADANIA:
{relevant_memories}

WIADOMOŚĆ UŻYTKOWNIKA: {message}

TYP INTERAKCJI: {interaction_type}

{additional_instructions}

Odpowiedz naturalnie po polsku. Bądź pomocny, konkretny i przyjazny.
Nie używaj pustych frazesów. Jeśli możesz pomóc - powiedz jak.
Jeśli potrzebujesz więcej informacji - zapytaj konkretnie.

Twoja odpowiedź:"""

    def __init__(self):
        """Initialize the intelligent agent."""
        self._llm = None
        self._embeddings = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.7,
            )
        return self._llm

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Lazy-load embeddings."""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model="text-embedding-ada-002",
            )
        return self._embeddings

    def _format_capabilities(self) -> str:
        """Format capabilities for prompt."""
        lines = []
        for domain, info in self.CAPABILITIES.items():
            lines.append(f"\n**{info['name']}**: {info['description']}")
            lines.append("  Przykłady: " + ", ".join(f'"{ex}"' for ex in info['examples'][:2]))
        return "\n".join(lines)

    def _format_conversation_history(self, messages: list[dict]) -> str:
        """Format recent conversation history."""
        if not messages:
            return "Brak poprzednich wiadomości."

        formatted = []
        for msg in messages[-6:]:  # Last 6 messages
            role = "Użytkownik" if msg.get("role") == "user" else "Agora"
            content = msg.get("content", "")[:200]
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    async def detect_intent(
        self,
        message: str,
        conversation_history: list[dict] = None,
        company_context: str = "",
    ) -> IntentDetectionResult:
        """Detect user intent using LLM (not pattern matching).

        Args:
            message: User's message
            conversation_history: Previous messages
            company_context: Context about the company

        Returns:
            IntentDetectionResult with detected intent and parameters
        """
        try:
            prompt = self.INTENT_DETECTION_PROMPT.format(
                capabilities=self._format_capabilities(),
                conversation_history=self._format_conversation_history(conversation_history or []),
                company_context=company_context or "Brak dodatkowego kontekstu.",
                message=message,
            )

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])

            # Parse JSON response
            try:
                # Try to extract JSON from response
                content = response.content
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No JSON found", content, 0)

                # Map intent string to Intent enum
                intent_str = result.get("intent", "unknown")
                is_task = result.get("is_task_request", False)

                if intent_str == "conversational" or intent_str == "help":
                    intent = Intent.HELP if intent_str == "help" else Intent.GREETING
                    is_conversational = True
                elif intent_str == "unknown" or not is_task:
                    intent = Intent.UNKNOWN
                    is_conversational = not is_task
                else:
                    # Try to match to Intent enum
                    try:
                        intent = Intent(intent_str)
                        is_conversational = False
                    except ValueError:
                        intent = Intent.UNKNOWN
                        is_conversational = True

                return IntentDetectionResult(
                    intent=intent,
                    confidence=result.get("confidence", 0.8),
                    reasoning=result.get("reasoning", ""),
                    extracted_params=result.get("extracted_params", {}),
                    is_conversational=is_conversational,
                    suggested_response=result.get("suggested_response"),
                )

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent detection response: {response.content}")
                return IntentDetectionResult(
                    intent=Intent.UNKNOWN,
                    confidence=0.5,
                    reasoning="Nie udało się przeanalizować odpowiedzi",
                    extracted_params={},
                    is_conversational=True,
                    suggested_response=None,
                )

        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return IntentDetectionResult(
                intent=Intent.UNKNOWN,
                confidence=0.3,
                reasoning=f"Błąd: {str(e)}",
                extracted_params={},
                is_conversational=True,
                suggested_response=None,
            )

    async def generate_response(
        self,
        message: str,
        interaction_type: str,
        conversation_history: list[dict] = None,
        company_context: str = "",
        relevant_memories: list[str] = None,
        additional_instructions: str = "",
    ) -> str:
        """Generate intelligent response using LLM with full context.

        Args:
            message: User's message
            interaction_type: Type of interaction (greeting, help, task, etc.)
            conversation_history: Previous messages
            company_context: Context about the company
            relevant_memories: Relevant past interactions/tasks
            additional_instructions: Extra instructions for this response

        Returns:
            Generated response string
        """
        try:
            prompt = self.RESPONSE_GENERATION_PROMPT.format(
                capabilities=self._format_capabilities(),
                conversation_history=self._format_conversation_history(conversation_history or []),
                company_context=company_context or "Brak dodatkowego kontekstu.",
                relevant_memories="\n".join(relevant_memories or []) or "Brak historii.",
                message=message,
                interaction_type=interaction_type,
                additional_instructions=additional_instructions,
            )

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._fallback_response(interaction_type)

    def _fallback_response(self, interaction_type: str) -> str:
        """Generate fallback response when LLM fails."""
        fallbacks = {
            "greeting": "Cześć! Jestem Agora, Twój asystent biznesowy. Jak mogę Ci pomóc?",
            "help": "Mogę pomóc Ci z marketingiem, finansami, HR i wieloma innymi zadaniami. Po prostu powiedz czego potrzebujesz!",
            "unknown": "Przepraszam, czy możesz opisać dokładniej czego potrzebujesz? Mogę pomóc z postami, fakturami, rekrutacją i wieloma innymi rzeczami.",
        }
        return fallbacks.get(interaction_type, fallbacks["unknown"])

    async def process_message(
        self,
        message: str,
        conversation_history: list[dict] = None,
        company_context: str = "",
        relevant_memories: list[str] = None,
    ) -> dict[str, Any]:
        """Process a message end-to-end with intelligence.

        This is the main entry point that:
        1. Detects intent using LLM
        2. Gathers context from memory
        3. Generates appropriate response

        Args:
            message: User's message
            conversation_history: Previous messages
            company_context: Context about the company
            relevant_memories: Relevant past interactions

        Returns:
            Dictionary with response, intent, and other metadata
        """
        # Step 1: Detect intent
        intent_result = await self.detect_intent(
            message=message,
            conversation_history=conversation_history,
            company_context=company_context,
        )

        # Step 2: Generate response based on intent type
        if intent_result.is_conversational:
            # It's a conversation, not a task - use LLM to respond
            if intent_result.suggested_response:
                response = intent_result.suggested_response
            else:
                response = await self.generate_response(
                    message=message,
                    interaction_type="conversational",
                    conversation_history=conversation_history,
                    company_context=company_context,
                    relevant_memories=relevant_memories,
                    additional_instructions="To jest rozmowa, nie prośba o zadanie. Odpowiedz naturalnie i pomocnie.",
                )

            return {
                "response": response,
                "intent": intent_result.intent.value,
                "is_task": False,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
                "extracted_params": {},
                "needs_more_info": False,
            }

        else:
            # It's a task request
            return {
                "response": None,  # Flow controller will handle task flow
                "intent": intent_result.intent.value,
                "is_task": True,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
                "extracted_params": intent_result.extracted_params,
                "needs_more_info": False,
            }


# Singleton instance
intelligent_agent = IntelligentAgent()
