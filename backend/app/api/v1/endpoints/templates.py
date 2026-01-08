"""Templates API - One-Click Templates for common tasks.

Provides predefined templates for social media posts, copywriting,
and other common marketing tasks with auto-recall of previous settings.
"""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database

router = APIRouter(prefix="/templates", tags=["templates"])


# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

SOCIAL_MEDIA_TEMPLATES = [
    {
        "id": "new_product",
        "name": "Nowy produkt/usluga",
        "icon": "package-plus",
        "description": "Oglos nowy produkt lub usluge",
        "fields": [
            {"name": "product_name", "label": "Nazwa produktu/uslugi", "type": "text", "required": True},
            {"name": "key_benefits", "label": "Glowne korzysci (max 3)", "type": "textarea", "required": True},
            {"name": "price", "label": "Cena (opcjonalnie)", "type": "text", "required": False},
            {"name": "cta", "label": "Call to action", "type": "select", "options": ["Kup teraz", "Sprawdz", "Link w bio", "Napisz do nas"], "required": True},
        ],
        "default_prompt": "Stworz post na Instagram oglaszajacy nowy produkt: {product_name}. Korzysci: {key_benefits}. {price_text} CTA: {cta}",
    },
    {
        "id": "promotion",
        "name": "Promocja/Rabat",
        "icon": "percent",
        "description": "Post o promocji lub rabacie",
        "fields": [
            {"name": "product_name", "label": "Co promujesz?", "type": "text", "required": True},
            {"name": "discount", "label": "Rabat", "type": "select", "options": ["10%", "15%", "20%", "25%", "30%", "50%", "Inna wartosc"], "required": True},
            {"name": "discount_custom", "label": "Inna wartosc rabatu", "type": "text", "required": False, "showIf": {"discount": "Inna wartosc"}},
            {"name": "valid_until", "label": "Wazne do", "type": "date", "required": False},
            {"name": "promo_code", "label": "Kod promocyjny (opcjonalnie)", "type": "text", "required": False},
        ],
        "default_prompt": "Stworz post promocyjny na Instagram. Produkt: {product_name}, rabat: {discount_value}. {validity} {promo_code_text}",
    },
    {
        "id": "tip",
        "name": "Porada/Tip",
        "icon": "lightbulb",
        "description": "Podziel sie wiedza z odbiorcami",
        "fields": [
            {"name": "topic", "label": "Temat porady", "type": "text", "required": True},
            {"name": "tip_content", "label": "Tresc porady (glowne punkty)", "type": "textarea", "required": True},
            {"name": "style", "label": "Styl", "type": "select", "options": ["Edukacyjny", "Przyjazny", "Ekspercki", "Humorystyczny"], "required": True},
        ],
        "default_prompt": "Stworz post z porada na temat: {topic}. Glowne punkty: {tip_content}. Styl: {style}.",
    },
    {
        "id": "event",
        "name": "Wydarzenie/News",
        "icon": "calendar",
        "description": "Poinformuj o wydarzeniu lub nowosci",
        "fields": [
            {"name": "event_name", "label": "Nazwa wydarzenia/newsa", "type": "text", "required": True},
            {"name": "event_date", "label": "Data (jesli dotyczy)", "type": "date", "required": False},
            {"name": "event_details", "label": "Szczegoly", "type": "textarea", "required": True},
            {"name": "cta", "label": "Call to action", "type": "select", "options": ["Zapisz sie", "Dolacz do nas", "Sledz nas", "Wiecej info w bio"], "required": True},
        ],
        "default_prompt": "Stworz post o wydarzeniu: {event_name}. {date_text} Szczegoly: {event_details}. CTA: {cta}",
    },
    {
        "id": "behind_scenes",
        "name": "Za kulisami",
        "icon": "clapperboard",
        "description": "Pokaz ludzka strone firmy",
        "fields": [
            {"name": "context", "label": "Co pokazujesz?", "type": "select", "options": ["Zespol", "Proces produkcji", "Biuro/miejsce pracy", "Dzien z zycia", "Przygotowania do eventu"], "required": True},
            {"name": "description", "label": "Opis sytuacji", "type": "textarea", "required": True},
            {"name": "mood", "label": "Nastroj", "type": "select", "options": ["Wesoly", "Profesjonalny", "Inspirujacy", "Autentyczny"], "required": True},
        ],
        "default_prompt": "Stworz post 'za kulisami' pokazujacy: {context}. Opis: {description}. Nastroj: {mood}.",
    },
    {
        "id": "custom",
        "name": "Wlasny temat",
        "icon": "sparkles",
        "description": "Stworz post na dowolny temat",
        "fields": [
            {"name": "topic", "label": "O czym ma byc post?", "type": "textarea", "required": True},
            {"name": "style", "label": "Styl", "type": "select", "options": ["Profesjonalny", "Przyjazny", "Ekspertowy", "Casualowy", "Inspirujacy"], "required": True},
            {"name": "include_cta", "label": "Dodac CTA?", "type": "checkbox", "required": False},
        ],
        "default_prompt": "Stworz post na Instagram na temat: {topic}. Styl: {style}. {cta_instruction}",
    },
]

COPYWRITING_TEMPLATES = [
    {
        "id": "product_ad",
        "name": "Reklama produktu",
        "icon": "megaphone",
        "description": "Tekst reklamowy dla produktu",
        "fields": [
            {"name": "product_name", "label": "Nazwa produktu", "type": "text", "required": True},
            {"name": "key_benefits", "label": "Glowne korzysci", "type": "textarea", "required": True},
            {"name": "target_audience", "label": "Dla kogo?", "type": "text", "required": True},
            {"name": "format", "label": "Format", "type": "select", "options": ["Krotki (1-2 zdania)", "Sredni (akapit)", "Dlugi (kilka akapitow)"], "required": True},
        ],
        "default_prompt": "Napisz tekst reklamowy dla produktu: {product_name}. Korzysci: {key_benefits}. Grupa docelowa: {target_audience}. Format: {format}.",
    },
    {
        "id": "email_marketing",
        "name": "Email marketingowy",
        "icon": "mail",
        "description": "Email do klientow lub subskrybentow",
        "fields": [
            {"name": "email_type", "label": "Typ emaila", "type": "select", "options": ["Newsletter", "Promocja", "Powitanie", "Reaktywacja", "Podziekowanie"], "required": True},
            {"name": "subject_hint", "label": "Temat/kontekst", "type": "text", "required": True},
            {"name": "cta", "label": "Glowne CTA", "type": "text", "required": True},
            {"name": "tone", "label": "Ton", "type": "select", "options": ["Formalny", "Przyjazny", "Pilny", "Entuzjastyczny"], "required": True},
        ],
        "default_prompt": "Napisz email marketingowy typu: {email_type}. Temat: {subject_hint}. CTA: {cta}. Ton: {tone}.",
    },
    {
        "id": "slogan",
        "name": "Slogan/Haslo",
        "icon": "quote",
        "description": "Krotkie, chwytliwe haslo",
        "fields": [
            {"name": "brand_or_product", "label": "Dla czego? (marka/produkt/kampania)", "type": "text", "required": True},
            {"name": "key_message", "label": "Glowny przekaz", "type": "text", "required": True},
            {"name": "style", "label": "Styl", "type": "select", "options": ["Inspirujacy", "Zabawny", "Profesjonalny", "Prowokacyjny", "Prosty"], "required": True},
            {"name": "variants", "label": "Ile wariantow?", "type": "select", "options": ["3", "5", "10"], "required": True},
        ],
        "default_prompt": "Stworz {variants} wersji sloganu/hasla dla: {brand_or_product}. Glowny przekaz: {key_message}. Styl: {style}.",
    },
    {
        "id": "website_copy",
        "name": "Opis na strone",
        "icon": "globe",
        "description": "Tekst na strone www",
        "fields": [
            {"name": "page_type", "label": "Typ strony", "type": "select", "options": ["Strona glowna", "O nas", "Produkt/Usluga", "Kontakt", "Landing page"], "required": True},
            {"name": "content_description", "label": "Co ma zawierac?", "type": "textarea", "required": True},
            {"name": "seo_keywords", "label": "Slowa kluczowe SEO (opcjonalnie)", "type": "text", "required": False},
            {"name": "length", "label": "Dlugosc", "type": "select", "options": ["Krotki (100-200 slow)", "Sredni (200-400 slow)", "Dlugi (400+ slow)"], "required": True},
        ],
        "default_prompt": "Napisz tekst na strone typu: {page_type}. Zawartosc: {content_description}. {seo_text} Dlugosc: {length}.",
    },
    {
        "id": "custom_copy",
        "name": "Wlasny tekst",
        "icon": "pen-tool",
        "description": "Dowolny tekst reklamowy",
        "fields": [
            {"name": "description", "label": "Opisz czego potrzebujesz", "type": "textarea", "required": True},
            {"name": "tone", "label": "Ton", "type": "select", "options": ["Profesjonalny", "Przyjazny", "Ekspertowy", "Casualowy", "Formalny"], "required": True},
            {"name": "length", "label": "Dlugosc", "type": "select", "options": ["Krotki", "Sredni", "Dlugi"], "required": True},
        ],
        "default_prompt": "Napisz tekst: {description}. Ton: {tone}. Dlugosc: {length}.",
    },
]


# ============================================================================
# SCHEMAS
# ============================================================================


class TemplateField(BaseModel):
    """Template field definition."""
    name: str
    label: str
    type: str
    required: bool = True
    options: list[str] = Field(default_factory=list)
    showIf: dict = Field(default_factory=dict)


class Template(BaseModel):
    """Template definition."""
    id: str
    name: str
    icon: str
    description: str
    fields: list[TemplateField]
    default_prompt: str


class TemplateCategory(BaseModel):
    """Category of templates."""
    id: str
    name: str
    icon: str
    templates: list[Template]


class TemplatesResponse(BaseModel):
    """Response with all available templates."""
    categories: list[TemplateCategory]


class TemplateHistoryEntry(BaseModel):
    """Saved template parameters."""
    template_id: str
    category_id: str
    params: dict
    used_at: datetime
    task_id: Optional[str] = None


class SaveTemplateHistoryRequest(BaseModel):
    """Request to save template usage."""
    template_id: str
    category_id: str
    params: dict
    task_id: Optional[str] = None


class TemplateHistoryResponse(BaseModel):
    """Response with template history."""
    template_id: str
    category_id: str
    last_used: Optional[dict] = None
    usage_count: int = 0


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=TemplatesResponse)
async def get_templates(
    current_user: CurrentUser,
) -> TemplatesResponse:
    """Get all available templates organized by category."""
    categories = [
        TemplateCategory(
            id="social_media",
            name="Post Social Media",
            icon="instagram",
            templates=[Template(**t) for t in SOCIAL_MEDIA_TEMPLATES],
        ),
        TemplateCategory(
            id="copywriting",
            name="Tekst Reklamowy",
            icon="file-text",
            templates=[Template(**t) for t in COPYWRITING_TEMPLATES],
        ),
    ]

    return TemplatesResponse(categories=categories)


@router.get("/history/{category_id}/{template_id}", response_model=TemplateHistoryResponse)
async def get_template_history(
    category_id: str,
    template_id: str,
    current_user: CurrentUser,
    db: Database,
) -> TemplateHistoryResponse:
    """Get usage history for a specific template.

    Returns the last used parameters for auto-recall feature.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get last used entry
    last_entry = await db.template_history.find_one(
        {
            "company_id": current_user.company_id,
            "template_id": template_id,
            "category_id": category_id,
        },
        sort=[("used_at", -1)],
    )

    # Get usage count
    usage_count = await db.template_history.count_documents({
        "company_id": current_user.company_id,
        "template_id": template_id,
        "category_id": category_id,
    })

    return TemplateHistoryResponse(
        template_id=template_id,
        category_id=category_id,
        last_used=last_entry.get("params") if last_entry else None,
        usage_count=usage_count,
    )


@router.post("/history")
async def save_template_history(
    data: SaveTemplateHistoryRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Save template usage for auto-recall.

    Stores the parameters used so they can be suggested next time.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    await db.template_history.insert_one({
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "template_id": data.template_id,
        "category_id": data.category_id,
        "params": data.params,
        "task_id": data.task_id,
        "used_at": datetime.utcnow(),
    })

    return {"status": "saved"}


@router.get("/recent", response_model=list[TemplateHistoryEntry])
async def get_recent_templates(
    current_user: CurrentUser,
    db: Database,
    limit: int = 5,
) -> list[TemplateHistoryEntry]:
    """Get recently used templates for quick access."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    cursor = db.template_history.find(
        {"company_id": current_user.company_id},
        sort=[("used_at", -1)],
        limit=limit,
    )

    entries = []
    async for doc in cursor:
        entries.append(TemplateHistoryEntry(
            template_id=doc["template_id"],
            category_id=doc["category_id"],
            params=doc["params"],
            used_at=doc["used_at"],
            task_id=doc.get("task_id"),
        ))

    return entries
