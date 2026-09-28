"""Typed data models representing structured content and performance entities.

These models correspond strictly to the objective/factual tables in SQLite.
Semantic memory, agent beliefs, and qualitative feedback are managed separately
via Hindsight.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Brand:
    """Core brand entity."""
    id: str
    name: str
    industry: str
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Platform:
    """Publishing channel / platform (e.g. LinkedIn, Substack, X)."""
    id: str
    name: str
    base_url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ContentFormat:
    """Format archetype per platform (e.g. PDF Carousel, Long-form Breakdown)."""
    id: str
    platform_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ContentPillar:
    """Editorial content category and target distribution share."""
    id: str
    brand_id: str
    name: str
    description: Optional[str] = None
    target_share_pct: float = 0.0
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Post:
    """Factual record of a published content asset."""
    id: str
    brand_id: str
    pillar_id: str
    platform_id: str
    format_id: str
    title: str
    content_text: str
    published_at: datetime
    content_url: Optional[str] = None
    status: str = "PUBLISHED"
    created_at: Optional[datetime] = None


@dataclass
class PerformanceMetric:
    """Quantitative performance snapshot for a published post."""
    post_id: str
    impressions: int = 0
    reach: int = 0
    clicks: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0
    id: Optional[int] = None
    recorded_at: Optional[datetime] = None

    def calculate_engagement_rate(self) -> float:
        """Calculate standardized engagement rate percentage."""
        total_interactions = self.likes + self.comments + self.shares + self.saves
        if self.impressions > 0:
            self.engagement_rate = round((total_interactions / self.impressions) * 100.0, 2)
        else:
            self.engagement_rate = 0.0
        return self.engagement_rate
