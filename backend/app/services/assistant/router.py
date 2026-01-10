"""Assistant Router - AI-powered intent detection and agent routing.

Converts natural language requests into agent actions without requiring
users to know about departments or specific agents.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import settings


class Intent(str, Enum):
    """Detected user intents mapped to agent capabilities."""

    # Marketing
    SOCIAL_MEDIA_POST = "social_media_post"
    MARKETING_COPY = "marketing_copy"
    CAMPAIGN = "campaign"

    # Finance
    INVOICE = "invoice"
    CASHFLOW_ANALYSIS = "cashflow_analysis"

    # HR
    JOB_POSTING = "job_posting"
    INTERVIEW_QUESTIONS = "interview_questions"
    ONBOARDING = "onboarding"

    # Sales
    SALES_PROPOSAL = "sales_proposal"
    LEAD_SCORING = "lead_scoring"
    FOLLOWUP_EMAIL = "followup_email"

    # Legal
    CONTRACT_REVIEW = "contract_review"
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    GDPR_CHECK = "gdpr_check"

    # Support
    TICKET_RESPONSE = "ticket_response"
    FAQ = "faq"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

    # General
    UNKNOWN = "unknown"


@dataclass
class QuickAction:
    """Quick action button for common tasks."""

    id: str
    label: str
    icon: str
    description: str
    intent: Intent
    default_params: dict = field(default_factory=dict)


@dataclass
class IntentResult:
    """Result of intent detection."""

    intent: Intent
    confidence: float
    suggested_agents: list[str]
    missing_info: list[str]
    follow_up_questions: list[str]
    can_auto_execute: bool
    extracted_params: dict = field(default_factory=dict)
    quick_action_id: str | None = None
    # New: recommended params that improve quality but aren't required
    recommended_missing: list[str] = field(default_factory=list)
    recommended_questions: list[str] = field(default_factory=list)


# Keyword patterns for intent detection
INTENT_PATTERNS: dict[Intent, list[str]] = {
    # Marketing intents
    Intent.SOCIAL_MEDIA_POST: [
        r"post\s+(na\s+)?(instagram|facebook|linkedin|social)",
        r"instagram|insta|ig\b",
        r"social\s*media",
        r"stories?|reels?",
        r"publikacj[aę]|opublikuj",
        # Polish patterns for "create a post about X"
        r"(stw[oó]rz|napisz|przygotuj|zr[oó]b)\s+post",
    ],
    Intent.MARKETING_COPY: [
        r"copy|kopi",
        r"tekst\s+(reklamowy|marketingowy|promocyjny)",
        r"reklam[aę]|slogan|hasło",
        r"opis\s+(produktu|usługi|na\s+stronę)",
        r"email\s+marketing",
        r"newsletter",
    ],
    Intent.CAMPAIGN: [
        r"kampani[aę]",
        r"launch|wprowadzenie\s+produktu",
        r"promocj[aę]|promo",
        r"pełny\s+pakiet|komplet\s+materiałów",
    ],

    # Finance intents
    Intent.INVOICE: [
        r"faktur[aęy]",
        r"rachunek",
        r"wystawienie|wystaw",
        r"rozliczenie",
    ],
    Intent.CASHFLOW_ANALYSIS: [
        r"cashflow|cash\s*flow",
        r"przepływy?\s+(finansow|pieniężn)",
        r"analiz[aę]\s+(finansow|przychodów|wydatków)",
        r"bilans|budżet",
        r"przychody?\s+(i|oraz)\s+wydatki?",
    ],

    # HR intents
    Intent.JOB_POSTING: [
        r"ogłoszenie\s+o\s+prac[ęy]",
        r"ofert[aę]\s+pracy",
        r"rekrutacj[aę]|rekrutuj",
        r"zatrudni[ćę]|szukam\s+pracownika",
        r"job\s*posting",
    ],
    Intent.INTERVIEW_QUESTIONS: [
        r"pytania?\s+(rekrutacyjn|na\s+rozmowę)",
        r"rozmow[aę]\s+(kwalifikacyjn|rekrutacyjn)",
        r"interview",
    ],
    Intent.ONBOARDING: [
        r"onboarding",
        r"wdrożenie\s+pracownika",
        r"pierwszy\s+dzień\s+(pracy|w\s+firmie)",
        r"materiały?\s+(powitalne|dla\s+nowego)",
    ],

    # Sales intents
    Intent.SALES_PROPOSAL: [
        r"ofert[aę](\s+handlow)?",
        r"propozycj[aę]|proposal",
        r"wycen[aę]",
        r"cennik",
    ],
    Intent.LEAD_SCORING: [
        r"lead|leady",
        r"ocen[aę]\s+(klienta|kontaktu)",
        r"scoring",
        r"kwalifikacj[aę]\s+kontaktów",
    ],
    Intent.FOLLOWUP_EMAIL: [
        r"follow\s*up|followup",
        r"przypomnienie\s+dla\s+klienta",
        r"email\s+do\s+klienta",
        r"kontakt\s+z\s+klientem",
    ],

    # Legal intents
    Intent.CONTRACT_REVIEW: [
        r"umow[aęy]",
        r"kontrakt",
        r"analiz[aę]\s+umowy",
        r"sprawdź\s+umowę",
    ],
    Intent.PRIVACY_POLICY: [
        r"polityk[aę]\s+prywatności",
        r"privacy\s*policy",
        r"ochrona?\s+danych",
    ],
    Intent.TERMS_OF_SERVICE: [
        r"regulamin",
        r"warunki\s+(korzystania|użytkowania|usługi)",
        r"terms",
        r"tos\b",
    ],
    Intent.GDPR_CHECK: [
        r"rodo|gdpr",
        r"zgodno[śc]+\s+(z\s+)?rodo",
        r"dane\s+osobowe",
    ],

    # Support intents
    Intent.TICKET_RESPONSE: [
        r"zgłoszeni[ae]|ticket",
        r"odpowied[źz]\s+(na\s+)?(reklamacj|pytanie|zgłoszenie)",
        r"obsługa?\s+klienta",
    ],
    Intent.FAQ: [
        r"faq",
        r"często\s+zadawane\s+pytania",
        r"baza?\s+wiedzy",
        r"help\s*(artykuł|article)?",
    ],
    Intent.SENTIMENT_ANALYSIS: [
        r"sentyment|sentiment",
        r"opini[ae]|recenzj[ae]",
        r"nastroj|nastrój\s+klientów",
        r"feedback",
    ],
}

# Agent mapping for each intent
INTENT_TO_AGENTS: dict[Intent, list[str]] = {
    Intent.SOCIAL_MEDIA_POST: ["instagram_specialist", "image_generator"],
    Intent.MARKETING_COPY: ["copywriter"],
    Intent.CAMPAIGN: ["campaign_service", "copywriter", "instagram_specialist", "image_generator"],
    Intent.INVOICE: ["invoice_specialist"],
    Intent.CASHFLOW_ANALYSIS: ["cashflow_analyst"],
    Intent.JOB_POSTING: ["hr_recruiter"],
    Intent.INTERVIEW_QUESTIONS: ["hr_interviewer"],
    Intent.ONBOARDING: ["hr_onboarding"],
    Intent.SALES_PROPOSAL: ["sales_proposal"],
    Intent.LEAD_SCORING: ["lead_scorer"],
    Intent.FOLLOWUP_EMAIL: ["crm_assistant"],
    Intent.CONTRACT_REVIEW: ["contract_reviewer"],
    Intent.PRIVACY_POLICY: ["gdpr_assistant"],
    Intent.TERMS_OF_SERVICE: ["terms_generator"],
    Intent.GDPR_CHECK: ["gdpr_assistant"],
    Intent.TICKET_RESPONSE: ["ticket_handler"],
    Intent.FAQ: ["faq_generator"],
    Intent.SENTIMENT_ANALYSIS: ["sentiment_analyst"],
    Intent.UNKNOWN: [],
}

# Required parameters for each intent
INTENT_REQUIRED_PARAMS: dict[Intent, list[str]] = {
    Intent.SOCIAL_MEDIA_POST: ["topic"],
    Intent.MARKETING_COPY: ["topic", "copy_type"],
    Intent.CAMPAIGN: ["topic"],
    Intent.INVOICE: ["client_name", "items"],
    Intent.CASHFLOW_ANALYSIS: ["income", "expenses"],
    Intent.JOB_POSTING: ["position", "requirements"],
    Intent.INTERVIEW_QUESTIONS: ["position"],
    Intent.ONBOARDING: ["position"],
    Intent.SALES_PROPOSAL: ["product_or_service", "client_name"],
    Intent.LEAD_SCORING: ["lead_info"],
    Intent.FOLLOWUP_EMAIL: ["client_name", "context"],
    Intent.CONTRACT_REVIEW: ["contract_text"],
    Intent.PRIVACY_POLICY: ["company_type", "data_collected"],
    Intent.TERMS_OF_SERVICE: ["service_type"],
    Intent.GDPR_CHECK: ["data_processing_description"],
    Intent.TICKET_RESPONSE: ["ticket_content"],
    Intent.FAQ: ["topic_or_tickets"],
    Intent.SENTIMENT_ANALYSIS: ["feedback_text"],
    Intent.UNKNOWN: [],
}

# Follow-up questions for missing params
PARAM_QUESTIONS: dict[str, str] = {
    "topic": "O czym ma być treść?",
    "copy_type": "Jaki typ tekstu potrzebujesz? (reklama, email, opis, slogan)",
    "client_name": "Jak nazywa się klient/firma?",
    "items": "Jakie pozycje mają być na fakturze?",
    "income": "Jakie masz przychody w tym okresie?",
    "expenses": "Jakie są wydatki do analizy?",
    "position": "Na jakie stanowisko?",
    "requirements": "Jakie są główne wymagania?",
    "product_or_service": "Jaki produkt lub usługę oferujesz?",
    "lead_info": "Opowiedz o tym kontakcie - skąd pochodzi, co wiesz?",
    "context": "Jaki jest kontekst tej wiadomości?",
    "contract_text": "Wklej treść umowy do analizy",
    "company_type": "Jaki rodzaj działalności prowadzisz?",
    "data_collected": "Jakie dane osobowe zbierasz?",
    "service_type": "Jaki rodzaj usługi/produktu oferujesz?",
    "data_processing_description": "Opisz jak przetwarzasz dane osobowe",
    "ticket_content": "Wklej treść zgłoszenia",
    "topic_or_tickets": "Na jaki temat? (lub wklej przykładowe pytania klientów)",
    "feedback_text": "Wklej tekst opinii do analizy",
}

# Recommended parameters - improve quality but not strictly required
INTENT_RECOMMENDED_PARAMS: dict[Intent, list[str]] = {
    Intent.SOCIAL_MEDIA_POST: ["platform", "tone", "target_audience"],
    Intent.MARKETING_COPY: ["tone", "target_audience"],
    Intent.CAMPAIGN: ["tone", "target_audience", "campaign_goal"],
    Intent.JOB_POSTING: ["salary_range", "location", "remote_option"],
    Intent.INVOICE: ["due_date", "payment_terms"],
    Intent.SALES_PROPOSAL: ["tone", "key_benefits"],
    Intent.FOLLOWUP_EMAIL: ["tone", "urgency"],
}

# Questions for recommended params
RECOMMENDED_PARAM_QUESTIONS: dict[str, str] = {
    "platform": "Na jaką platformę? (Instagram/Facebook/LinkedIn)",
    "tone": "Jaki styl/ton? (profesjonalny/casualowy/zabawny/formalny)",
    "target_audience": "Dla jakiej grupy docelowej? (młodzi/dorośli/firmy/wszyscy)",
    "campaign_goal": "Jaki cel kampanii? (sprzedaż/świadomość/zaangażowanie)",
    "salary_range": "Jaki przedział wynagrodzenia?",
    "location": "Jaka lokalizacja pracy?",
    "remote_option": "Czy możliwa praca zdalna? (tak/nie/hybrydowa)",
    "due_date": "Jaki termin płatności?",
    "payment_terms": "Jakie warunki płatności?",
    "key_benefits": "Jakie główne korzyści podkreślić?",
    "urgency": "Jak pilna jest sprawa? (pilna/normalna/niska)",
}

# Default values for recommended params (when user skips)
DEFAULT_INTENT_PARAMS: dict[Intent, dict[str, Any]] = {
    Intent.SOCIAL_MEDIA_POST: {
        "platform": "instagram",
        "tone": "profesjonalny",
        "target_audience": "ogólna",
    },
    Intent.MARKETING_COPY: {
        "tone": "profesjonalny",
        "target_audience": "ogólna",
    },
    Intent.CAMPAIGN: {
        "tone": "profesjonalny",
        "target_audience": "ogólna",
        "campaign_goal": "zaangażowanie",
    },
    Intent.JOB_POSTING: {
        "salary_range": "do uzgodnienia",
        "location": "Polska",
        "remote_option": "hybrydowa",
    },
    Intent.INVOICE: {
        "due_date": "14 dni",
        "payment_terms": "przelew",
    },
    Intent.SALES_PROPOSAL: {
        "tone": "profesjonalny",
        "key_benefits": "",
    },
    Intent.FOLLOWUP_EMAIL: {
        "tone": "przyjazny",
        "urgency": "normalna",
    },
}


# Quick actions for Command Center
QUICK_ACTIONS: list[QuickAction] = [
    QuickAction(
        id="social_post",
        label="Post Social Media",
        icon="instagram",
        description="Stwórz post z grafiką na Instagram, Facebook lub LinkedIn",
        intent=Intent.SOCIAL_MEDIA_POST,
        default_params={"platform": "instagram"},
    ),
    QuickAction(
        id="marketing_copy",
        label="Tekst Reklamowy",
        icon="pen",
        description="Napisz tekst reklamowy, slogan lub email marketingowy",
        intent=Intent.MARKETING_COPY,
    ),
    QuickAction(
        id="invoice",
        label="Faktura",
        icon="file-text",
        description="Wygeneruj profesjonalną fakturę VAT",
        intent=Intent.INVOICE,
    ),
    QuickAction(
        id="cashflow",
        label="Analiza Cashflow",
        icon="trending-up",
        description="Przeanalizuj przepływy finansowe i otrzymaj rekomendacje",
        intent=Intent.CASHFLOW_ANALYSIS,
    ),
    QuickAction(
        id="campaign",
        label="Kampania",
        icon="rocket",
        description="Stwórz kompletną kampanię marketingową",
        intent=Intent.CAMPAIGN,
    ),
    QuickAction(
        id="job_posting",
        label="Ogłoszenie o pracę",
        icon="briefcase",
        description="Stwórz profesjonalne ogłoszenie rekrutacyjne",
        intent=Intent.JOB_POSTING,
    ),
]


class AssistantRouter:
    """AI-powered router that detects intent and routes to appropriate agents."""

    def __init__(self):
        """Initialize the router."""
        self._llm = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
            )
        return self._llm

    def detect_intent_from_patterns(self, message: str) -> tuple[Intent, float]:
        """Detect intent using regex patterns.

        Args:
            message: User's natural language message

        Returns:
            Tuple of (Intent, confidence_score)
        """
        message_lower = message.lower()

        best_intent = Intent.UNKNOWN
        best_score = 0.0

        for intent, patterns in INTENT_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    matches += 1

            if matches > 0:
                # Score based on number of pattern matches
                score = min(0.9, 0.5 + (matches * 0.2))
                if score > best_score:
                    best_score = score
                    best_intent = intent

        return best_intent, best_score

    def extract_params_from_message(
        self,
        message: str,
        intent: Intent,
        is_followup: bool = False,
    ) -> dict[str, Any]:
        """Extract parameters from the message based on intent.

        Args:
            message: User's message
            intent: Detected intent
            is_followup: If True, this is a response to a question (skip topic extraction)

        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        message_lower = message.lower()

        # Extract topic (general - works for most intents)
        # BUT: Skip topic extraction for short followup responses
        # to avoid overriding the original topic
        if not is_followup or len(message.split()) > 10:
            topic = message
            for patterns in INTENT_PATTERNS.values():
                for pattern in patterns:
                    topic = re.sub(pattern, "", topic, flags=re.IGNORECASE)
            topic = topic.strip()
            if topic and len(topic) > 5:
                params["topic"] = topic

        # Extract specific parameters based on intent
        if intent == Intent.SOCIAL_MEDIA_POST:
            # Platform detection
            if re.search(r"instagram|insta|ig\b", message_lower):
                params["platform"] = "instagram"
            elif re.search(r"facebook|fb\b", message_lower):
                params["platform"] = "facebook"
            elif re.search(r"linkedin", message_lower):
                params["platform"] = "linkedin"

            # Post type
            if re.search(r"stories?|story", message_lower):
                params["post_type"] = "story"
            elif re.search(r"reels?|reel", message_lower):
                params["post_type"] = "reel"
            else:
                params["post_type"] = "post"

        elif intent == Intent.MARKETING_COPY:
            # Copy type detection
            if re.search(r"email|newsletter", message_lower):
                params["copy_type"] = "email"
            elif re.search(r"slogan|hasło", message_lower):
                params["copy_type"] = "slogan"
            elif re.search(r"opis\s+(produktu|na\s+stronę)", message_lower):
                params["copy_type"] = "description"
            elif re.search(r"reklam[aę]", message_lower):
                params["copy_type"] = "ad"

        elif intent == Intent.CAMPAIGN:
            # Campaign type
            if re.search(r"launch|wprowadzenie|now[ey]\s+produkt", message_lower):
                params["campaign_type"] = "product_launch"
            elif re.search(r"promocj[aę]|rabat|zniżk", message_lower):
                params["campaign_type"] = "promo"
            else:
                params["campaign_type"] = "social_media"

        # Extract recommended params (common across intents)
        # Tone detection
        if re.search(r"profesjonaln", message_lower):
            params["tone"] = "profesjonalny"
        elif re.search(r"casualow|luźn|nieformalne", message_lower):
            params["tone"] = "casualowy"
        elif re.search(r"zabawn|śmieszn|humoryst", message_lower):
            params["tone"] = "zabawny"
        elif re.search(r"formaln|oficjaln", message_lower):
            params["tone"] = "formalny"

        # Target audience detection
        if re.search(r"młod|młodzie|nastolatk|gen\s*z", message_lower):
            params["target_audience"] = "młodzi"
        elif re.search(r"dorosł|senior|starszy", message_lower):
            params["target_audience"] = "dorośli"
        elif re.search(r"firm|b2b|biznes|przedsiębiorc", message_lower):
            params["target_audience"] = "firmy"
        elif re.search(r"wszystk|ogóln|szerok", message_lower):
            params["target_audience"] = "ogólna"

        # Platform detection (common)
        if "platform" not in params:
            if re.search(r"instagram|insta|ig\b", message_lower):
                params["platform"] = "instagram"
            elif re.search(r"facebook|fb\b", message_lower):
                params["platform"] = "facebook"
            elif re.search(r"linkedin", message_lower):
                params["platform"] = "linkedin"

        return params

    def get_missing_params(self, intent: Intent, extracted_params: dict) -> list[str]:
        """Get list of missing required parameters.

        Args:
            intent: Detected intent
            extracted_params: Already extracted parameters

        Returns:
            List of missing parameter names
        """
        required = INTENT_REQUIRED_PARAMS.get(intent, [])

        # Topic can substitute for many specific params
        if "topic" in extracted_params:
            # If we have a topic, we can often proceed
            # Filter out params that topic can satisfy
            flexible_params = ["topic", "position", "service_type", "company_type"]
            required = [p for p in required if p not in flexible_params]

        return [p for p in required if p not in extracted_params]

    def get_follow_up_questions(self, missing_params: list[str]) -> list[str]:
        """Generate follow-up questions for missing params.

        Args:
            missing_params: List of missing parameter names

        Returns:
            List of questions in Polish
        """
        return [PARAM_QUESTIONS.get(p, f"Podaj: {p}") for p in missing_params]

    def get_missing_recommended_params(self, intent: Intent, extracted_params: dict) -> list[str]:
        """Get list of missing recommended parameters.

        Args:
            intent: Detected intent
            extracted_params: Already extracted parameters

        Returns:
            List of missing recommended parameter names
        """
        recommended = INTENT_RECOMMENDED_PARAMS.get(intent, [])
        return [p for p in recommended if p not in extracted_params]

    def get_recommended_questions(self, missing_recommended: list[str]) -> list[str]:
        """Generate questions for missing recommended params.

        Args:
            missing_recommended: List of missing recommended parameter names

        Returns:
            List of questions in Polish
        """
        return [RECOMMENDED_PARAM_QUESTIONS.get(p, f"Podaj: {p}") for p in missing_recommended]

    def get_default_params(self, intent: Intent) -> dict[str, Any]:
        """Get default values for recommended params.

        Args:
            intent: The intent to get defaults for

        Returns:
            Dictionary of default parameter values
        """
        return DEFAULT_INTENT_PARAMS.get(intent, {}).copy()

    def is_followup_response(self, message: str, context: dict | None) -> bool:
        """Detect if message is a response to a previous question.

        This prevents short responses like "casualowy" from being treated
        as new requests when we're in the middle of a conversation.

        Args:
            message: User's message
            context: Conversation context with state info

        Returns:
            True if this appears to be a followup response
        """
        if not context:
            return False

        # If we're explicitly awaiting recommendations, it's a followup
        if context.get("awaiting_recommendations"):
            return True

        # If we have a pending intent and message is short, likely a followup
        if context.get("last_intent") and len(message.split()) <= 5:
            return True

        # Check if message matches known parameter values
        param_value_patterns = [
            # Tone values
            r"^(profesjonalny|casualowy|zabawny|formalny|luźny|poważny)$",
            # Platform values
            r"^(instagram|facebook|linkedin|twitter|ig|fb)$",
            # Audience values
            r"^(młodzi|dorośli|firmy|wszyscy|b2b|ogólna)$",
            # Yes/no responses
            r"^(tak|nie|ok|dobrze|jasne|zgoda)$",
        ]

        message_lower = message.lower().strip()
        for pattern in param_value_patterns:
            if re.match(pattern, message_lower):
                return True

        return False

    async def interpret(
        self,
        message: str,
        conversation_context: dict | None = None,
    ) -> IntentResult:
        """Interpret user message and return routing information.

        Supports conversation context to maintain state across messages.
        When user is responding to a question, preserves the original intent.

        Args:
            message: User's natural language request
            conversation_context: Optional context with:
                - messages: Previous messages
                - extracted_params: Already extracted parameters
                - last_intent: Previously detected intent
                - awaiting_recommendations: Whether we asked for more info

        Returns:
            IntentResult with detected intent and routing info
        """
        context = conversation_context or {}

        # Step 0: Check if this is a followup response
        is_followup = self.is_followup_response(message, context)

        if is_followup and context.get("last_intent"):
            # PRESERVE CONTEXT: Use the previous intent instead of detecting new one
            try:
                intent = Intent(context["last_intent"])
                confidence = 1.0  # High confidence since we're continuing
            except ValueError:
                # Fallback to pattern detection if intent is invalid
                intent, confidence = self.detect_intent_from_patterns(message)
                is_followup = False
        else:
            # Step 1: Pattern-based intent detection for new requests
            intent, confidence = self.detect_intent_from_patterns(message)

        # Step 2: If low confidence and not a followup, could use LLM
        if confidence < 0.3 and not is_followup:
            # TODO: Use LLM for ambiguous cases
            pass

        # Step 3: Extract parameters from message
        # For followup responses, skip topic extraction to avoid overwriting
        extracted_params = self.extract_params_from_message(
            message, intent, is_followup=is_followup
        )

        # Step 4: Merge with existing params from context
        if context.get("extracted_params"):
            # Existing params + new params (new params take priority for non-topic)
            merged_params = {**context["extracted_params"]}
            for key, value in extracted_params.items():
                # Don't let short followup responses override topic
                if key == "topic" and is_followup and len(message.split()) <= 10:
                    continue
                merged_params[key] = value
            extracted_params = merged_params

        # Step 5: Determine missing required info
        missing_params = self.get_missing_params(intent, extracted_params)

        # Step 6: Generate follow-up questions for required params
        follow_up_questions = self.get_follow_up_questions(missing_params)

        # Step 7: Determine if we can auto-execute
        # For followup responses with context, we can be more lenient
        if is_followup and context.get("last_intent"):
            can_auto_execute = len(missing_params) == 0
        else:
            can_auto_execute = len(missing_params) == 0 and confidence >= 0.6

        # Step 8: Check recommended params (improve quality but not required)
        recommended_missing = self.get_missing_recommended_params(intent, extracted_params)
        recommended_questions = self.get_recommended_questions(recommended_missing)

        # If we already answered recommendations (followup), don't ask again
        if context.get("recommendations_answered"):
            recommended_missing = []
            recommended_questions = []

        return IntentResult(
            intent=intent,
            confidence=confidence,
            suggested_agents=INTENT_TO_AGENTS.get(intent, []),
            missing_info=missing_params,
            follow_up_questions=follow_up_questions,
            can_auto_execute=can_auto_execute,
            extracted_params=extracted_params,
            recommended_missing=recommended_missing,
            recommended_questions=recommended_questions,
        )

    async def interpret_quick_action(self, action_id: str, params: dict = None) -> IntentResult:
        """Interpret a quick action selection.

        Args:
            action_id: ID of the selected quick action
            params: Optional additional parameters

        Returns:
            IntentResult for the quick action
        """
        params = params or {}

        # Find the quick action
        action = next((a for a in QUICK_ACTIONS if a.id == action_id), None)
        if not action:
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                suggested_agents=[],
                missing_info=[],
                follow_up_questions=["Nieznana akcja. Spróbuj opisać czego potrzebujesz."],
                can_auto_execute=False,
            )

        # Merge default params with provided params
        extracted_params = {**action.default_params, **params}

        # Get missing params
        missing_params = self.get_missing_params(action.intent, extracted_params)

        return IntentResult(
            intent=action.intent,
            confidence=1.0,  # High confidence for explicit action
            suggested_agents=INTENT_TO_AGENTS.get(action.intent, []),
            missing_info=missing_params,
            follow_up_questions=self.get_follow_up_questions(missing_params),
            can_auto_execute=len(missing_params) == 0,
            extracted_params=extracted_params,
            quick_action_id=action_id,
        )


# Singleton instance
assistant_router = AssistantRouter()


def get_quick_actions() -> list[QuickAction]:
    """Get list of available quick actions."""
    return QUICK_ACTIONS
