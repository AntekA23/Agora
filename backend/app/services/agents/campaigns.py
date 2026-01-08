"""Multi-Agent Campaign Service - współpraca między agentami.

Orkiestruje wiele agentów do realizacji złożonych kampanii:
- Social Media Campaign: Instagram + Copywriter + Image Generator
- Full Marketing Package: Research + Copy + Visuals + Posts
"""

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.services.agents.marketing.instagram import generate_instagram_post
from app.services.agents.marketing.copywriter import generate_marketing_copy
from app.services.agents.tools.image_generator import image_service
from app.services.agents.memory import memory_service, MemoryType
from app.services.agents.brand_context import build_brand_context


class CampaignType:
    """Types of multi-agent campaigns."""
    SOCIAL_MEDIA = "social_media"  # Instagram + Image
    FULL_MARKETING = "full_marketing"  # Copy + Instagram + Image
    PRODUCT_LAUNCH = "product_launch"  # Full package for new product
    PROMO_CAMPAIGN = "promo_campaign"  # Promotional content set


class CampaignService:
    """Service for orchestrating multi-agent campaigns."""

    async def create_social_media_campaign(
        self,
        company_id: str,
        brief: str,
        platforms: list[str] = None,
        brand_voice: str = "profesjonalny",
        target_audience: str = "",
        include_image: bool = True,
        knowledge: dict = None,
        settings: dict = None,
    ) -> dict[str, Any]:
        """Create a complete social media campaign.

        Orchestrates:
        1. Instagram Specialist - creates post content
        2. Image Generator - creates matching visual

        Args:
            company_id: ID firmy
            brief: Opis kampanii
            platforms: Platformy docelowe (domyślnie instagram)
            brand_voice: Głos marki
            target_audience: Grupa docelowa
            include_image: Czy generować obraz
            knowledge: CompanyKnowledge dict for brand context
            settings: CompanySettings dict for brand context

        Returns:
            Dictionary with all campaign outputs
        """
        platforms = platforms or ["instagram"]

        # Build brand context if knowledge provided
        brand_context = ""
        if knowledge:
            brand_context = build_brand_context(
                knowledge=knowledge,
                settings=settings or {},
                agent_type="campaign",
            )

        results = {
            "campaign_type": CampaignType.SOCIAL_MEDIA,
            "brief": brief,
            "created_at": datetime.utcnow().isoformat(),
            "platforms": platforms,
            "outputs": {},
            "agents_used": [],
            "used_brand_context": bool(brand_context),
        }

        # Step 1: Generate post content with brand context
        try:
            post_result = await generate_instagram_post(
                brief=brief,
                brand_voice=brand_voice,
                target_audience=target_audience,
                include_hashtags=True,
                post_type="post",
                company_id=company_id,
                brand_context=brand_context,
            )
            results["outputs"]["post"] = post_result
            results["agents_used"].append("instagram_specialist")
        except Exception as e:
            results["outputs"]["post"] = {"error": str(e)}

        # Step 2: Generate image based on post content
        if include_image and "post" in results["outputs"]:
            try:
                # Use the image prompt from post if available
                post_output = results["outputs"]["post"]
                image_prompt = post_output.get("image_prompt", brief)

                # Generate image for primary platform
                primary_platform = platforms[0] if platforms else "instagram"
                image_result = await image_service.generate_post_image(
                    description=image_prompt,
                    brand_style=brand_voice,
                    platform=primary_platform,
                )
                results["outputs"]["image"] = image_result
                results["agents_used"].append("image_generator")
            except Exception as e:
                results["outputs"]["image"] = {"error": str(e)}

        return results

    async def create_full_marketing_campaign(
        self,
        company_id: str,
        brief: str,
        campaign_name: str = "",
        brand_voice: str = "profesjonalny",
        target_audience: str = "",
        copy_types: list[str] = None,
        platforms: list[str] = None,
        knowledge: dict = None,
        settings: dict = None,
    ) -> dict[str, Any]:
        """Create a full marketing campaign package.

        Orchestrates:
        1. Copywriter - creates various marketing texts
        2. Instagram Specialist - creates social media posts
        3. Image Generator - creates visuals for each platform

        Args:
            company_id: ID firmy
            brief: Główny brief kampanii
            campaign_name: Nazwa kampanii
            brand_voice: Głos marki
            target_audience: Grupa docelowa
            copy_types: Typy tekstów (ad, email, landing, slogan)
            platforms: Platformy social media
            knowledge: CompanyKnowledge dict for brand context
            settings: CompanySettings dict for brand context

        Returns:
            Complete campaign package
        """
        copy_types = copy_types or ["ad", "slogan"]
        platforms = platforms or ["instagram", "facebook"]

        # Build brand contexts for different agent types
        instagram_context = ""
        copywriter_context = ""
        if knowledge:
            instagram_context = build_brand_context(
                knowledge=knowledge,
                settings=settings or {},
                agent_type="instagram",
            )
            copywriter_context = build_brand_context(
                knowledge=knowledge,
                settings=settings or {},
                agent_type="copywriter",
            )

        results = {
            "campaign_type": CampaignType.FULL_MARKETING,
            "campaign_name": campaign_name or f"Kampania {datetime.now().strftime('%Y-%m-%d')}",
            "brief": brief,
            "created_at": datetime.utcnow().isoformat(),
            "outputs": {
                "copy": {},
                "social_posts": {},
                "images": {},
            },
            "agents_used": [],
            "summary": {},
            "used_brand_context": bool(knowledge),
        }

        # Step 1: Generate marketing copy for each type with brand context
        for copy_type in copy_types:
            try:
                copy_result = await generate_marketing_copy(
                    brief=brief,
                    copy_type=copy_type,
                    brand_voice=brand_voice,
                    target_audience=target_audience,
                    company_id=company_id,
                    brand_context=copywriter_context,
                )
                results["outputs"]["copy"][copy_type] = copy_result
                if "copywriter" not in results["agents_used"]:
                    results["agents_used"].append("copywriter")
            except Exception as e:
                results["outputs"]["copy"][copy_type] = {"error": str(e)}

        # Step 2: Generate social posts for each platform with brand context
        for platform in platforms:
            try:
                post_type = "post"
                if platform == "instagram":
                    post_type = "post"

                post_result = await generate_instagram_post(
                    brief=brief,
                    brand_voice=brand_voice,
                    target_audience=target_audience,
                    include_hashtags=True,
                    post_type=post_type,
                    company_id=company_id,
                    brand_context=instagram_context,
                )
                results["outputs"]["social_posts"][platform] = post_result
                if "instagram_specialist" not in results["agents_used"]:
                    results["agents_used"].append("instagram_specialist")
            except Exception as e:
                results["outputs"]["social_posts"][platform] = {"error": str(e)}

        # Step 3: Generate images for each platform
        for platform in platforms:
            try:
                # Use post image prompt if available
                post = results["outputs"]["social_posts"].get(platform, {})
                image_prompt = post.get("image_prompt", brief)

                image_result = await image_service.generate_post_image(
                    description=image_prompt,
                    brand_style=brand_voice,
                    platform=platform,
                )
                results["outputs"]["images"][platform] = image_result
                if "image_generator" not in results["agents_used"]:
                    results["agents_used"].append("image_generator")
            except Exception as e:
                results["outputs"]["images"][platform] = {"error": str(e)}

        # Generate summary
        results["summary"] = {
            "copy_variants": len([c for c in results["outputs"]["copy"].values() if "error" not in c]),
            "social_posts": len([p for p in results["outputs"]["social_posts"].values() if "error" not in p]),
            "images_generated": len([i for i in results["outputs"]["images"].values() if "error" not in i]),
            "total_agents": len(results["agents_used"]),
        }

        return results

    async def create_product_launch_campaign(
        self,
        company_id: str,
        product_name: str,
        product_description: str,
        key_features: list[str] = None,
        brand_voice: str = "profesjonalny",
        target_audience: str = "",
        price: str = "",
        knowledge: dict = None,
        settings: dict = None,
    ) -> dict[str, Any]:
        """Create a complete product launch campaign.

        Specialized campaign for launching a new product with:
        - Product description copy
        - Ad copy
        - Social media posts
        - Product visuals
        """
        key_features = key_features or []

        # Build comprehensive brief
        features_text = ", ".join(key_features) if key_features else ""
        brief = f"""Wprowadzenie produktu: {product_name}

Opis: {product_description}

Kluczowe cechy: {features_text}

{"Cena: " + price if price else ""}

Stwórz materiały marketingowe podkreślające unikalne wartości produktu."""

        # Use full marketing campaign with brand context
        return await self.create_full_marketing_campaign(
            company_id=company_id,
            brief=brief,
            campaign_name=f"Launch: {product_name}",
            brand_voice=brand_voice,
            target_audience=target_audience,
            copy_types=["description", "ad", "slogan"],
            platforms=["instagram", "facebook"],
            knowledge=knowledge,
            settings=settings,
        )

    async def create_promo_campaign(
        self,
        company_id: str,
        promo_type: str,  # "discount", "sale", "event", "seasonal"
        promo_details: str,
        valid_until: str = "",
        brand_voice: str = "profesjonalny",
        target_audience: str = "",
        knowledge: dict = None,
        settings: dict = None,
    ) -> dict[str, Any]:
        """Create promotional campaign materials.

        Specialized for time-limited promotions with urgency messaging.
        """
        urgency = f"Oferta ważna do: {valid_until}" if valid_until else "Oferta ograniczona czasowo!"

        promo_type_polish = {
            "discount": "Promocja rabatowa",
            "sale": "Wyprzedaż",
            "event": "Wydarzenie specjalne",
            "seasonal": "Oferta sezonowa",
        }.get(promo_type, "Promocja")

        brief = f"""{promo_type_polish}

{promo_details}

{urgency}

Stwórz materiały marketingowe z naciskiem na pilność i wartość dla klienta."""

        return await self.create_social_media_campaign(
            company_id=company_id,
            brief=brief,
            platforms=["instagram", "facebook"],
            brand_voice=brand_voice,
            target_audience=target_audience,
            include_image=True,
            knowledge=knowledge,
            settings=settings,
        )


# Singleton instance
campaign_service = CampaignService()


async def get_campaign_service() -> CampaignService:
    """Get the campaign service instance."""
    return campaign_service
