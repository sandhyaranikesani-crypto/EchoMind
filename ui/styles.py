"""UI styling and visual design tokens for EchoMind.

Designed for an internal analytics tool aesthetic:
- Responsive, theme-aware CSS using CSS variables and Streamlit design tokens.
- No hardcoded hex colors; supports Light, Dark, and System modes seamlessly.
- Strict WCAG AA contrast compliance in both modes.
- Restrained 4/8px spacing, subtle borders, no gratuitous glow or neon effects.
"""

import streamlit as st


def apply_custom_styles() -> None:
    """Inject restrained, theme-adaptive CSS design tokens."""
    st.markdown(
        """
        <style>
        /* Base typography scale and reset */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color);
            font-weight: 600;
            letter-spacing: -0.01em;
            margin-bottom: 0.5rem;
        }

        p, span, label, li {
            color: var(--text-color);
            font-size: 0.925rem;
            line-height: 1.5;
        }

        /* Container constraints and spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        /* Restrained Page Header */
        .em-header {
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }
        .em-header-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-color);
            margin: 0;
        }
        .em-header-subtitle {
            font-size: 0.875rem;
            color: rgba(128, 128, 128, 0.9);
            margin-top: 0.25rem;
            margin-bottom: 0;
        }

        /* Badges & Status Chips */
        .em-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1.4;
            color: var(--text-color);
            background-color: rgba(128, 128, 128, 0.08);
            border: 1px solid rgba(128, 128, 128, 0.25);
        }
        .em-badge-neutral {
            background-color: rgba(128, 128, 128, 0.08);
            border-color: rgba(128, 128, 128, 0.25);
        }
        .em-badge-success {
            background-color: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.4);
        }
        .em-badge-warning {
            background-color: rgba(245, 158, 11, 0.12);
            border-color: rgba(245, 158, 11, 0.4);
        }
        .em-badge-danger {
            background-color: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.4);
        }
        .em-badge-info {
            background-color: rgba(37, 99, 235, 0.12);
            border-color: rgba(37, 99, 235, 0.4);
        }
        .em-badge-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }

        /* Restrained Cards & Panels */
        .em-card {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 6px;
            padding: 1rem;
            background-color: var(--secondary-background-color);
            margin-bottom: 1rem;
        }
        .em-card-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-color);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Diff comparison container */
        .em-diff-box {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 6px;
            padding: 1rem;
            background-color: var(--secondary-background-color);
            height: 100%;
        }

        /* Tables and Dataframes subtle border */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 4px;
        }

        /* Metrics cards */
        [data-testid="stMetric"] {
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 6px;
            padding: 12px 16px;
        }

        /* Expander borders */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 6px;
            background-color: var(--secondary-background-color);
        }

        /* Forms and Buttons */
        .stButton > button {
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.875rem;
            transition: all 0.15s ease-in-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str = "") -> None:
    """Render a clean, restrained page header with sentence-case copy."""
    subtitle_html = f'<p class="em-header-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="em-header">
            <h1 class="em-header-title">{title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_html(text: str, variant: str = "neutral", dot: bool = False) -> str:
    """Return an HTML badge string with consistent styling."""
    dot_html = '<span class="em-badge-dot"></span>' if dot else ""
    return f'<span class="em-badge em-badge-{variant}">{dot_html}{text}</span>'
