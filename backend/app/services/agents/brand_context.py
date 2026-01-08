"""Brand context builder for AI agents.

Konwertuje CompanyKnowledge na strukturyzowany kontekst
dostosowany do potrzeb roznych agentow.
"""

from typing import Literal

AgentType = Literal["instagram", "copywriter", "campaign", "general"]


def build_brand_context(
    knowledge: dict,
    settings: dict,
    agent_type: AgentType = "general",
    max_products: int = 3,
    max_services: int = 3,
) -> str:
    """Build contextual brand information for AI agents.

    Args:
        knowledge: CompanyKnowledge dict from MongoDB
        settings: CompanySettings dict
        agent_type: Type of agent requesting context
        max_products: Maximum products to include
        max_services: Maximum services to include

    Returns:
        Formatted context string optimized for the agent type
    """
    if not knowledge:
        return ""

    # Normalize inputs - handle Pydantic models
    if hasattr(knowledge, "model_dump"):
        knowledge = knowledge.model_dump()
    if hasattr(settings, "model_dump"):
        settings = settings.model_dump()

    # Route to appropriate builder
    if agent_type == "instagram":
        return _build_instagram_context(knowledge, settings, max_products, max_services)
    elif agent_type == "copywriter":
        return _build_copywriter_context(knowledge, settings, max_products, max_services)
    elif agent_type == "campaign":
        return _build_campaign_context(knowledge, settings, max_products, max_services)
    else:
        return _build_general_context(knowledge, settings, max_products, max_services)


def _build_instagram_context(
    knowledge: dict,
    settings: dict,
    max_products: int,
    max_services: int,
) -> str:
    """Build context optimized for Instagram specialist."""
    sections = []

    # Brand profile section
    brand_identity = knowledge.get("brand_identity", {})
    if _has_brand_data(brand_identity):
        section = ["=== PROFIL MARKI ==="]
        if brand_identity.get("personality_traits"):
            section.append(f"Osobowosc: {', '.join(brand_identity['personality_traits'])}")
        if brand_identity.get("values"):
            section.append(f"Wartosci: {', '.join(brand_identity['values'])}")
        if brand_identity.get("unique_value_proposition"):
            section.append(f"Unikalna wartosc: {brand_identity['unique_value_proposition']}")
        if len(section) > 1:
            sections.append("\n".join(section))

    # Target audience section
    target = knowledge.get("target_audience", {})
    if _has_audience_data(target):
        section = ["=== GRUPA DOCELOWA ==="]
        if target.get("age_from") or target.get("age_to"):
            age_from = target.get("age_from", "")
            age_to = target.get("age_to", "")
            if age_from and age_to:
                section.append(f"Wiek: {age_from}-{age_to} lat")
            elif age_from:
                section.append(f"Wiek: od {age_from} lat")
            elif age_to:
                section.append(f"Wiek: do {age_to} lat")
        if target.get("interests"):
            section.append(f"Zainteresowania: {', '.join(target['interests'][:5])}")
        if target.get("where_they_are"):
            section.append(f"Gdzie sa: {', '.join(target['where_they_are'])}")
        if len(section) > 1:
            sections.append("\n".join(section))

    # Communication style section
    comm_style = knowledge.get("communication_style", {})
    if _has_communication_data(comm_style):
        section = ["=== STYL KOMUNIKACJI ==="]
        if comm_style.get("formality_level"):
            level = comm_style["formality_level"]
            level_name = {
                1: "bardzo formalny",
                2: "formalny",
                3: "profesjonalny",
                4: "swobodny",
                5: "bardzo swobodny",
            }.get(level, "profesjonalny")
            section.append(f"Formalnosc: {level}/5 ({level_name})")
        if comm_style.get("emoji_usage"):
            emoji_pl = {
                "none": "brak",
                "minimal": "minimalne",
                "moderate": "umiarkowane",
                "frequent": "czeste",
            }.get(comm_style["emoji_usage"], comm_style["emoji_usage"])
            section.append(f"Emoji: {emoji_pl}")
        if comm_style.get("words_to_use"):
            section.append(f"Uzywaj slow: {', '.join(comm_style['words_to_use'][:5])}")
        if comm_style.get("words_to_avoid"):
            section.append(f"Unikaj slow: {', '.join(comm_style['words_to_avoid'][:5])}")
        if comm_style.get("example_phrases"):
            section.append("Przykladowe frazy:")
            for phrase in comm_style["example_phrases"][:3]:
                section.append(f'- "{phrase}"')
        if len(section) > 1:
            sections.append("\n".join(section))

    # Content preferences section (Instagram-specific)
    content_prefs = knowledge.get("content_preferences", {})
    if _has_content_prefs(content_prefs):
        section = ["=== HASHTAGI I FORMAT ==="]
        if content_prefs.get("hashtag_style"):
            section.append(f"Styl hashtagow: {content_prefs['hashtag_style']}")
        if content_prefs.get("branded_hashtags"):
            section.append(f"Hashtagi firmowe: {' '.join(content_prefs['branded_hashtags'][:5])}")
        if content_prefs.get("preferred_formats"):
            section.append(f"Preferowane formaty: {', '.join(content_prefs['preferred_formats'])}")
        if content_prefs.get("themes"):
            section.append(f"Tematy tresci: {', '.join(content_prefs['themes'][:5])}")
        if len(section) > 1:
            sections.append("\n".join(section))

    # Products/services section
    products_services = _format_products_services_short(
        knowledge.get("products", [])[:max_products],
        knowledge.get("services", [])[:max_services],
    )
    if products_services:
        sections.append(f"=== PRODUKTY/USLUGI (do promowania) ===\n{products_services}")

    return "\n\n".join(sections) if sections else ""


def _build_copywriter_context(
    knowledge: dict,
    settings: dict,
    max_products: int,
    max_services: int,
) -> str:
    """Build context optimized for Copywriter."""
    sections = []

    # Brand profile section (with price positioning)
    brand_identity = knowledge.get("brand_identity", {})
    section = ["=== PROFIL MARKI ==="]
    if brand_identity.get("personality_traits"):
        section.append(f"Osobowosc: {', '.join(brand_identity['personality_traits'])}")
    if brand_identity.get("values"):
        section.append(f"Wartosci: {', '.join(brand_identity['values'])}")
    if brand_identity.get("unique_value_proposition"):
        section.append(f"Unikalna wartosc: {brand_identity['unique_value_proposition']}")
    if knowledge.get("price_positioning"):
        pos_pl = {
            "budget": "ekonomiczny",
            "mid_range": "sredni segment",
            "premium": "premium",
            "luxury": "luksusowy",
        }.get(knowledge["price_positioning"], knowledge["price_positioning"])
        section.append(f"Pozycjonowanie cenowe: {pos_pl}")
    if len(section) > 1:
        sections.append("\n".join(section))

    # Target audience with pain points and goals (Copywriter-specific)
    target = knowledge.get("target_audience", {})
    if _has_audience_data(target) or target.get("pain_points") or target.get("goals"):
        section = ["=== GRUPA DOCELOWA ==="]
        if target.get("age_from") or target.get("age_to"):
            age_from = target.get("age_from", "")
            age_to = target.get("age_to", "")
            if age_from and age_to:
                section.append(f"Wiek: {age_from}-{age_to} lat")
        if target.get("interests"):
            section.append(f"Zainteresowania: {', '.join(target['interests'][:5])}")
        if target.get("pain_points"):
            section.append("Bolaczki klientow:")
            for pain in target["pain_points"][:4]:
                section.append(f"- {pain}")
        if target.get("goals"):
            section.append("Cele klientow:")
            for goal in target["goals"][:4]:
                section.append(f"- {goal}")
        if len(section) > 1:
            sections.append("\n".join(section))

    # Communication style (without emoji for copywriter)
    comm_style = knowledge.get("communication_style", {})
    if _has_communication_data(comm_style):
        section = ["=== STYL KOMUNIKACJI ==="]
        if comm_style.get("formality_level"):
            level = comm_style["formality_level"]
            level_name = {
                1: "bardzo formalny",
                2: "formalny",
                3: "profesjonalny",
                4: "swobodny",
                5: "bardzo swobodny",
            }.get(level, "profesjonalny")
            section.append(f"Formalnosc: {level}/5 ({level_name})")
        if comm_style.get("words_to_use"):
            section.append(f"Uzywaj slow: {', '.join(comm_style['words_to_use'][:5])}")
        if comm_style.get("words_to_avoid"):
            section.append(f"Unikaj slow: {', '.join(comm_style['words_to_avoid'][:5])}")
        if comm_style.get("example_phrases"):
            section.append("Przykladowe frazy:")
            for phrase in comm_style["example_phrases"][:3]:
                section.append(f'- "{phrase}"')
        if len(section) > 1:
            sections.append("\n".join(section))

    # Products/services - full details for copywriter
    products_services = _format_products_services_detailed(
        knowledge.get("products", [])[:max_products],
        knowledge.get("services", [])[:max_services],
    )
    if products_services:
        sections.append(f"=== PRODUKTY/USLUGI ===\n{products_services}")

    # Competitors section (Copywriter-specific)
    competitors = knowledge.get("competitors", [])
    if competitors:
        section = ["=== KONKURENCJA ==="]
        names = [c.get("name", "") for c in competitors[:3] if c.get("name")]
        if names:
            section.append(f"Glowni konkurenci: {', '.join(names)}")

        # Collect our advantages (competitors' weaknesses = our advantages)
        our_advantages = []
        for comp in competitors[:3]:
            for weakness in comp.get("weaknesses", [])[:2]:
                if weakness and weakness not in our_advantages:
                    our_advantages.append(weakness)

        if our_advantages:
            section.append("Nasze przewagi:")
            for adv in our_advantages[:4]:
                section.append(f"- {adv}")

        if len(section) > 1:
            sections.append("\n".join(section))

    return "\n\n".join(sections) if sections else ""


def _build_campaign_context(
    knowledge: dict,
    settings: dict,
    max_products: int,
    max_services: int,
) -> str:
    """Build comprehensive context for campaign service."""
    # Campaign gets the most complete context - combination of both
    instagram_ctx = _build_instagram_context(knowledge, settings, max_products, max_services)

    # Add pain points and goals (from copywriter context)
    target = knowledge.get("target_audience", {})
    extra_sections = []

    if target.get("pain_points") or target.get("goals"):
        section = ["=== DODATKOWY KONTEKST ==="]
        if target.get("pain_points"):
            section.append("Bolaczki klientow:")
            for pain in target["pain_points"][:3]:
                section.append(f"- {pain}")
        if target.get("goals"):
            section.append("Cele klientow:")
            for goal in target["goals"][:3]:
                section.append(f"- {goal}")
        if len(section) > 1:
            extra_sections.append("\n".join(section))

    # Add competitor info
    competitors = knowledge.get("competitors", [])
    if competitors:
        section = ["=== KONKURENCJA ==="]
        for comp in competitors[:2]:
            name = comp.get("name", "")
            if name:
                section.append(f"\n{name}:")
                if comp.get("strengths"):
                    section.append(f"  Mocne strony: {', '.join(comp['strengths'][:3])}")
                if comp.get("weaknesses"):
                    section.append(f"  Slabe strony: {', '.join(comp['weaknesses'][:3])}")

        if len(section) > 1:
            extra_sections.append("\n".join(section))

    if extra_sections:
        return instagram_ctx + "\n\n" + "\n\n".join(extra_sections)

    return instagram_ctx


def _build_general_context(
    knowledge: dict,
    settings: dict,
    max_products: int,
    max_services: int,
) -> str:
    """Build general context for any agent."""
    # Use copywriter context as baseline (most comprehensive for text generation)
    return _build_copywriter_context(knowledge, settings, max_products, max_services)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _has_brand_data(brand_identity: dict) -> bool:
    """Check if brand identity has meaningful data."""
    return bool(
        brand_identity.get("values")
        or brand_identity.get("personality_traits")
        or brand_identity.get("unique_value_proposition")
    )


def _has_audience_data(target: dict) -> bool:
    """Check if target audience has meaningful data."""
    return bool(
        target.get("description")
        or target.get("age_from")
        or target.get("interests")
    )


def _has_communication_data(comm_style: dict) -> bool:
    """Check if communication style has meaningful data."""
    return bool(
        comm_style.get("words_to_use")
        or comm_style.get("words_to_avoid")
        or comm_style.get("example_phrases")
        or (comm_style.get("formality_level") and comm_style.get("formality_level") != 3)
    )


def _has_content_prefs(content_prefs: dict) -> bool:
    """Check if content preferences have meaningful data."""
    return bool(
        content_prefs.get("branded_hashtags")
        or content_prefs.get("preferred_formats")
        or content_prefs.get("themes")
    )


def _format_products_services_short(products: list, services: list) -> str:
    """Format products/services in short form for Instagram."""
    lines = []
    idx = 1

    for p in products:
        if isinstance(p, dict) and p.get("name"):
            name = p.get("name", "")
            price = p.get("price")
            usps = p.get("unique_selling_points", [])

            price_str = f" | {price} PLN" if price else ""
            line = f"{idx}. {name}{price_str}"
            if usps:
                line += f"\n   USP: {usps[0]}"
            lines.append(line)
            idx += 1

    for s in services:
        if isinstance(s, dict) and s.get("name"):
            name = s.get("name", "")
            price_from = s.get("price_from")
            benefits = s.get("benefits", [])

            price_str = f" | od {price_from} PLN" if price_from else ""
            line = f"{idx}. {name}{price_str}"
            if benefits:
                line += f"\n   Korzysc: {benefits[0]}"
            lines.append(line)
            idx += 1

    return "\n".join(lines)


def _format_products_services_detailed(products: list, services: list) -> str:
    """Format products/services with full details for Copywriter."""
    lines = []
    idx = 1

    for p in products:
        if isinstance(p, dict) and p.get("name"):
            name = p.get("name", "")
            desc = p.get("description", "")
            price = p.get("price")
            features = p.get("features", [])
            usps = p.get("unique_selling_points", [])

            lines.append(f"{idx}. {name}")
            if desc:
                lines.append(f"   Opis: {desc[:150]}")
            if features:
                lines.append(f"   Cechy: {', '.join(features[:4])}")
            if usps:
                lines.append(f"   USP: {', '.join(usps[:2])}")
            if price:
                lines.append(f"   Cena: {price} PLN")
            lines.append("")
            idx += 1

    for s in services:
        if isinstance(s, dict) and s.get("name"):
            name = s.get("name", "")
            desc = s.get("description", "")
            price_from = s.get("price_from")
            price_to = s.get("price_to")
            benefits = s.get("benefits", [])

            lines.append(f"{idx}. {name}")
            if desc:
                lines.append(f"   Opis: {desc[:150]}")
            if benefits:
                lines.append(f"   Korzysci: {', '.join(benefits[:3])}")
            if price_from:
                price_str = f"{price_from}"
                if price_to:
                    price_str += f"-{price_to}"
                lines.append(f"   Cena: od {price_str} PLN")
            lines.append("")
            idx += 1

    return "\n".join(lines).strip()


def get_fallback_context(settings: dict) -> tuple[str, str]:
    """Get fallback brand_voice and target_audience from settings.

    Used when knowledge is empty for backward compatibility.

    Returns:
        Tuple of (brand_voice, target_audience)
    """
    if hasattr(settings, "model_dump"):
        settings = settings.model_dump()

    return (
        settings.get("brand_voice", "profesjonalny"),
        settings.get("target_audience", ""),
    )
