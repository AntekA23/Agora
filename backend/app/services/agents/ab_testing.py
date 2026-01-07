"""A/B Testing Service for content experiments.

Umożliwia:
- Tworzenie eksperymentów z wariantami treści
- Śledzenie wyników (CTR, engagement, conversions)
- Automatyczne wybieranie zwycięzcy
"""

import random
from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    """Status of an A/B experiment."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantMetrics(BaseModel):
    """Metrics for a single variant."""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    feedback_count: int = 0
    feedback_sum: float = 0.0

    @property
    def ctr(self) -> float:
        """Click-through rate."""
        return (self.clicks / self.impressions * 100) if self.impressions > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        """Conversion rate."""
        return (self.conversions / self.impressions * 100) if self.impressions > 0 else 0.0

    @property
    def avg_feedback(self) -> float | None:
        """Average feedback rating."""
        return self.feedback_sum / self.feedback_count if self.feedback_count > 0 else None


class Variant(BaseModel):
    """A variant in an A/B test."""
    id: str
    name: str
    content: dict[str, Any]  # The actual content variant
    weight: float = 0.5  # Traffic allocation (0-1)
    metrics: VariantMetrics = Field(default_factory=VariantMetrics)


class Experiment(BaseModel):
    """An A/B testing experiment."""
    id: str
    name: str
    description: str = ""
    company_id: str
    agent: str  # Which agent this experiment is for
    variants: list[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    winner_variant_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    min_sample_size: int = 100  # Minimum impressions per variant
    confidence_level: float = 0.95  # Statistical confidence required


class ABTestingService:
    """Service for managing A/B testing experiments."""

    def __init__(self):
        pass

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        company_id: str,
        agent: str,
        variants: list[dict[str, Any]],
        description: str = "",
        min_sample_size: int = 100,
    ) -> Experiment:
        """Create a new A/B testing experiment.

        Args:
            experiment_id: Unique experiment ID
            name: Experiment name
            company_id: Company ID
            agent: Agent name (instagram_specialist, copywriter, etc.)
            variants: List of variant definitions with content
            description: Optional description
            min_sample_size: Minimum samples per variant before declaring winner
        """
        # Normalize weights
        num_variants = len(variants)
        default_weight = 1.0 / num_variants

        experiment_variants = []
        for i, var in enumerate(variants):
            experiment_variants.append(Variant(
                id=var.get("id", f"variant_{i}"),
                name=var.get("name", f"Variant {chr(65 + i)}"),  # A, B, C...
                content=var.get("content", {}),
                weight=var.get("weight", default_weight),
            ))

        return Experiment(
            id=experiment_id,
            name=name,
            description=description,
            company_id=company_id,
            agent=agent,
            variants=experiment_variants,
            created_at=datetime.utcnow(),
            min_sample_size=min_sample_size,
        )

    def select_variant(self, experiment: Experiment) -> Variant:
        """Select a variant for a user based on traffic allocation.

        Uses weighted random selection based on variant weights.
        """
        if experiment.status != ExperimentStatus.RUNNING:
            # Return first variant if not running
            return experiment.variants[0]

        if experiment.winner_variant_id:
            # Return winner if determined
            for var in experiment.variants:
                if var.id == experiment.winner_variant_id:
                    return var

        # Weighted random selection
        weights = [v.weight for v in experiment.variants]
        return random.choices(experiment.variants, weights=weights, k=1)[0]

    def record_impression(self, experiment: Experiment, variant_id: str) -> None:
        """Record an impression for a variant."""
        for variant in experiment.variants:
            if variant.id == variant_id:
                variant.metrics.impressions += 1
                break

    def record_click(self, experiment: Experiment, variant_id: str) -> None:
        """Record a click for a variant."""
        for variant in experiment.variants:
            if variant.id == variant_id:
                variant.metrics.clicks += 1
                break

    def record_conversion(self, experiment: Experiment, variant_id: str) -> None:
        """Record a conversion for a variant."""
        for variant in experiment.variants:
            if variant.id == variant_id:
                variant.metrics.conversions += 1
                break

    def record_feedback(
        self,
        experiment: Experiment,
        variant_id: str,
        rating: int,
    ) -> None:
        """Record feedback for a variant."""
        for variant in experiment.variants:
            if variant.id == variant_id:
                variant.metrics.feedback_count += 1
                variant.metrics.feedback_sum += rating
                break

    def calculate_statistics(
        self,
        experiment: Experiment,
    ) -> dict[str, Any]:
        """Calculate statistics for the experiment.

        Returns performance metrics and statistical significance.
        """
        stats = {
            "experiment_id": experiment.id,
            "status": experiment.status,
            "variants": [],
            "has_winner": False,
            "winner": None,
            "ready_for_decision": False,
        }

        # Check if we have enough samples
        min_impressions = min(
            v.metrics.impressions for v in experiment.variants
        )
        stats["ready_for_decision"] = min_impressions >= experiment.min_sample_size

        best_variant = None
        best_score = -1

        for variant in experiment.variants:
            metrics = variant.metrics
            variant_stats = {
                "id": variant.id,
                "name": variant.name,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "conversions": metrics.conversions,
                "ctr": round(metrics.ctr, 2),
                "conversion_rate": round(metrics.conversion_rate, 2),
                "avg_feedback": round(metrics.avg_feedback, 2) if metrics.avg_feedback else None,
            }

            # Calculate composite score (weighted combination)
            # CTR: 30%, Conversion: 40%, Feedback: 30%
            score = 0
            if metrics.impressions > 0:
                score += metrics.ctr * 0.3
                score += metrics.conversion_rate * 0.4
                if metrics.avg_feedback:
                    score += (metrics.avg_feedback / 5 * 100) * 0.3

            variant_stats["score"] = round(score, 2)
            stats["variants"].append(variant_stats)

            if score > best_score:
                best_score = score
                best_variant = variant

        # Determine winner if ready
        if stats["ready_for_decision"] and best_variant:
            # Simple approach: best score wins
            # In production, you'd want proper statistical significance testing
            stats["has_winner"] = True
            stats["winner"] = {
                "id": best_variant.id,
                "name": best_variant.name,
                "score": best_score,
            }

        return stats

    def determine_winner(self, experiment: Experiment) -> str | None:
        """Determine the winning variant.

        Returns variant ID of the winner, or None if not enough data.
        """
        stats = self.calculate_statistics(experiment)

        if stats["has_winner"] and stats["winner"]:
            return stats["winner"]["id"]

        return None

    def get_experiment_summary(self, experiment: Experiment) -> dict[str, Any]:
        """Get a summary of the experiment for display."""
        stats = self.calculate_statistics(experiment)

        total_impressions = sum(v.metrics.impressions for v in experiment.variants)
        total_clicks = sum(v.metrics.clicks for v in experiment.variants)
        total_conversions = sum(v.metrics.conversions for v in experiment.variants)

        return {
            "id": experiment.id,
            "name": experiment.name,
            "status": experiment.status,
            "agent": experiment.agent,
            "variants_count": len(experiment.variants),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "overall_ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "overall_conversion_rate": round(total_conversions / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "ready_for_decision": stats["ready_for_decision"],
            "has_winner": stats["has_winner"],
            "winner": stats.get("winner"),
            "created_at": experiment.created_at.isoformat(),
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
        }


# Singleton instance
ab_testing_service = ABTestingService()
