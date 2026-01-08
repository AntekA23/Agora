"""Publishers for social media platforms."""

from app.services.publishers.base import BasePublisher
from app.services.publishers.instagram import InstagramPublisher
from app.services.publishers.facebook import FacebookPublisher
from app.services.publishers.linkedin import LinkedInPublisher

__all__ = [
    "BasePublisher",
    "InstagramPublisher",
    "FacebookPublisher",
    "LinkedInPublisher",
]


def get_publisher(platform: str) -> BasePublisher:
    """Get the appropriate publisher for a platform."""
    publishers = {
        "instagram": InstagramPublisher(),
        "facebook": FacebookPublisher(),
        "linkedin": LinkedInPublisher(),
    }

    publisher = publishers.get(platform)
    if not publisher:
        raise ValueError(f"No publisher available for platform: {platform}")

    return publisher
