-- ============================================================================
-- EchoMind: Structured Database Schema (SQLite)
-- Purpose: Factual, objective content metadata and performance metrics.
-- Note: Semantic memory, beliefs, and preferences are stored in Hindsight.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Brands
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS brands (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    website TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Platforms (Distribution Channels)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Content Formats (Archetypes per platform)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS content_formats (
    id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 4. Content Pillars (Editorial themes & target share allocations)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS content_pillars (
    id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    target_share_pct REAL DEFAULT 0.0,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5. Published Posts (Factual ledger of content assets)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    pillar_id TEXT NOT NULL,
    platform_id TEXT NOT NULL,
    format_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_url TEXT,
    published_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'PUBLISHED' CHECK (status IN ('PUBLISHED', 'ARCHIVED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    FOREIGN KEY (pillar_id) REFERENCES content_pillars(id) ON DELETE RESTRICT,
    FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE RESTRICT,
    FOREIGN KEY (format_id) REFERENCES content_formats(id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 6. Performance Metrics (Quantitative post performance snapshots)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    engagement_rate REAL DEFAULT 0.0,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- Analytical Indexes for Fast Strategy Queries & Cadence Calculations
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_posts_brand_published 
    ON posts(brand_id, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_posts_pillar 
    ON posts(pillar_id);

CREATE INDEX IF NOT EXISTS idx_posts_platform_format 
    ON posts(platform_id, format_id);

CREATE INDEX IF NOT EXISTS idx_metrics_post 
    ON performance_metrics(post_id);

CREATE INDEX IF NOT EXISTS idx_pillars_brand_active 
    ON content_pillars(brand_id, is_active);
