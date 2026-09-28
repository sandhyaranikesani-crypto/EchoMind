"""Data access repository for factual content and performance metrics in SQLite.

Provides typed query operations for brands, platforms, pillars, posts,
and deterministic analytical aggregations for the strategy layer.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import sqlite3

from database.db import get_connection


class ContentRepository:
    """Repository managing structured SQL queries."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    # -------------------------------------------------------------------------
    # Core Entity Retrieval
    # -------------------------------------------------------------------------
    def get_brand(self, brand_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            cursor = conn.execute("SELECT * FROM brands WHERE id = ?", (brand_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_brands(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cursor = conn.execute("SELECT * FROM brands ORDER BY name ASC")
            return [dict(r) for r in cursor.fetchall()]

    def list_platforms(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cursor = conn.execute("SELECT * FROM platforms ORDER BY name ASC")
            return [dict(r) for r in cursor.fetchall()]

    def list_pillars(self, brand_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM content_pillars WHERE brand_id = ? AND is_active = 1 ORDER BY name ASC",
                (brand_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def list_formats(self, platform_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            if platform_id:
                cursor = conn.execute(
                    "SELECT f.*, p.name as platform_name FROM content_formats f "
                    "JOIN platforms p ON f.platform_id = p.id "
                    "WHERE f.platform_id = ? ORDER BY f.name ASC",
                    (platform_id,),
                )
            else:
                cursor = conn.execute(
                    "SELECT f.*, p.name as platform_name FROM content_formats f "
                    "JOIN platforms p ON f.platform_id = p.id ORDER BY p.name, f.name ASC"
                )
            return [dict(r) for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Posts & Performance
    # -------------------------------------------------------------------------
    def get_recent_posts(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                p.id as post_id,
                p.title,
                p.content_text,
                p.published_at,
                cp.name as pillar_name,
                cp.id as pillar_id,
                plat.name as platform_name,
                plat.id as platform_id,
                cf.name as format_name,
                cf.id as format_id,
                COALESCE(m.impressions, 0) as impressions,
                COALESCE(m.clicks, 0) as clicks,
                COALESCE(m.likes, 0) as likes,
                COALESCE(m.comments, 0) as comments,
                COALESCE(m.shares, 0) as shares,
                COALESCE(m.saves, 0) as saves,
                COALESCE(m.conversions, 0) as conversions,
                COALESCE(m.engagement_rate, 0.0) as engagement_rate
            FROM posts p
            JOIN content_pillars cp ON p.pillar_id = cp.id
            JOIN platforms plat ON p.platform_id = plat.id
            JOIN content_formats cf ON p.format_id = cf.id
            LEFT JOIN performance_metrics m ON p.id = m.post_id
            WHERE p.brand_id = ?
        """
        params: List[Any] = [brand_id]
        if platform_id:
            query += " AND p.platform_id = ?"
            params.append(platform_id)

        query += " ORDER BY p.published_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            cursor = conn.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Strategy & Aggregations
    # -------------------------------------------------------------------------
    def get_pillar_distribution_and_performance(self, brand_id: str) -> List[Dict[str, Any]]:
        """Calculates actual vs target pillar distribution and performance averages."""
        query = """
            SELECT 
                cp.id as pillar_id,
                cp.name as pillar_name,
                cp.target_share_pct,
                COUNT(p.id) as post_count,
                MAX(p.published_at) as last_published_at,
                COALESCE(AVG(m.engagement_rate), 0.0) as avg_engagement_rate,
                COALESCE(AVG(m.impressions), 0.0) as avg_impressions,
                COALESCE(AVG(m.clicks), 0.0) as avg_clicks,
                COALESCE(SUM(m.conversions), 0) as total_conversions
            FROM content_pillars cp
            LEFT JOIN posts p ON cp.id = p.pillar_id AND p.brand_id = ?
            LEFT JOIN performance_metrics m ON p.id = m.post_id
            WHERE cp.brand_id = ? AND cp.is_active = 1
            GROUP BY cp.id, cp.name, cp.target_share_pct
            ORDER BY cp.name ASC
        """
        with self._conn() as conn:
            cursor = conn.execute(query, (brand_id, brand_id))
            rows = [dict(r) for r in cursor.fetchall()]

        total_posts = sum(r["post_count"] for r in rows)
        for r in rows:
            r["actual_share_pct"] = round((r["post_count"] / total_posts * 100.0), 1) if total_posts > 0 else 0.0
            r["share_delta_pct"] = round(r["actual_share_pct"] - r["target_share_pct"], 1)
            r["avg_engagement_rate"] = round(r["avg_engagement_rate"], 2)
            r["avg_impressions"] = int(round(r["avg_impressions"]))
            r["avg_clicks"] = int(round(r["avg_clicks"]))

        return rows

    def get_format_performance(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Calculates performance averages per format archetype."""
        query = """
            SELECT 
                cf.id as format_id,
                cf.name as format_name,
                plat.name as platform_name,
                COUNT(p.id) as post_count,
                COALESCE(AVG(m.engagement_rate), 0.0) as avg_engagement_rate,
                COALESCE(AVG(m.impressions), 0.0) as avg_impressions,
                COALESCE(AVG(m.clicks), 0.0) as avg_clicks,
                COALESCE(SUM(m.conversions), 0) as total_conversions
            FROM content_formats cf
            JOIN platforms plat ON cf.platform_id = plat.id
            LEFT JOIN posts p ON cf.id = p.format_id AND p.brand_id = ?
            LEFT JOIN performance_metrics m ON p.id = m.post_id
            WHERE 1=1
        """
        params: List[Any] = [brand_id]
        if platform_id:
            query += " AND cf.platform_id = ?"
            params.append(platform_id)

        query += " GROUP BY cf.id, cf.name, plat.name ORDER BY avg_engagement_rate DESC"

        with self._conn() as conn:
            cursor = conn.execute(query, params)
            rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            r["avg_engagement_rate"] = round(r["avg_engagement_rate"], 2)
            r["avg_impressions"] = int(round(r["avg_impressions"]))
            r["avg_clicks"] = int(round(r["avg_clicks"]))

        return rows
