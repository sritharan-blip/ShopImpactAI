"""Escaped, theme-aware UI pieces. All artwork is local inline vector geometry."""
from __future__ import annotations

from datetime import date
import base64
import html
import re
import pandas as pd
import streamlit as st
from .theme import PALETTES


def _illustrated_html(markup: str) -> None:
    """Streamlit sanitizes inline SVG; self-contained SVG images retain artwork."""
    palette = PALETTES[st.session_state.get('dark_mode', False)]
    motion = '''.si-orbit{transform-origin:180px 150px;animation:orbit 45s linear infinite}
    .si-bag{animation:float 6s ease-in-out infinite}.si-orbit-card{animation:float 5s ease-in-out infinite}
    @keyframes orbit{to{transform:rotate(360deg)}}@keyframes float{50%{transform:translateY(-8px)}}
    @media(prefers-reduced-motion:reduce){*{animation:none!important}}'''
    if st.session_state.get('reduce_motion', False):
        motion = '*{animation:none!important}'
    def encode(match):
        vector = match.group()
        for key, value in palette.items():
            vector = vector.replace(f'var(--si-{key.replace("_", "-")})', value)
        vector = vector.replace('currentColor', palette['accent'])
        if 'xmlns=' not in vector:
            vector = vector.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        vector = vector.replace('>', f'><style>{motion}</style>', 1)
        data = base64.b64encode(vector.encode()).decode()
        return f'<img alt="" aria-hidden="true" src="data:image/svg+xml;base64,{data}">'
    st.html(re.sub(r'<svg\b.*?</svg>', encode, markup, flags=re.S))


def render_hero(count: int, month_co2: float = 0, spend: float = 0, green_choices: int = 0) -> None:
    st.html(f'''<section class="si-hero" aria-label="ShopImpact dashboard introduction">
      <div><span class="si-status">YOUR IMPACT, IN MOTION</span>
      <h1>Your everyday.<br><em>Reimagined.</em></h1>
      <p>A clearer view of what you buy.<br>A lighter footprint for what comes next.</p>
      <small>{date.today():%A, %d %B} &nbsp; / &nbsp; {count} purchases tracked</small></div>
      <div class="si-hero-art" aria-label="Your monthly shopping snapshot">
        <div class="si-sphere" aria-hidden="true"></div><div class="si-orbit-ring" aria-hidden="true"></div>
        <div class="si-float-card one"><small>Monthly footprint</small><strong>{month_co2:.1f} <span>kg CO2e</span></strong><span>Directional estimate</span></div>
        <div class="si-float-card two"><small>Spend tracked</small><strong>${spend:,.0f}</strong><span>This month</span></div>
        <div class="si-float-card three"><small>Lower-impact picks</small><strong>{green_choices} <span>and counting</span></strong>
          <div class="si-mini-bars" aria-hidden="true"><i style="--h:35%;--d:0s"></i><i style="--h:65%;--d:-.5s"></i><i style="--h:50%;--d:-1s"></i><i style="--h:85%;--d:-1.5s"></i><i style="--h:72%;--d:-2s"></i><i style="--h:100%;--d:-2.5s"></i></div></div>
      </div></section>''')


def render_ticker() -> None:
    labels = ['BUY LESS, CHOOSE WELL', 'REPAIR & REUSE', 'MAKE ROOM FOR WHAT MATTERS', 'TRACK YOUR IMPACT', 'SMALL STEPS ADD UP']
    items = ''.join(f'<span>{label} &nbsp; ✳</span>' for label in labels)
    st.html(f'<div class="si-marquee" aria-hidden="true"><div class="si-marquee-track">{items}{items}</div></div>')


ART = {
    'smartphone': '<rect x="30" y="8" width="40" height="70" rx="9"/><path d="M42 16h16M46 70h8"/>',
    'laptop': '<rect x="13" y="13" width="74" height="48" rx="5"/><path d="M6 73h88l-7-12H13zM40 68h20"/>',
    'shopping_bag': '<path d="M20 28h60l-6 50H26zM36 28V19c0-21 28-21 28 0v9M40 48l10 10 15-19"/>',
    'apparel': '<path d="m30 12-23 17 13 18 12-7v38h36V40l12 7 13-18-23-17-10 8H40zM43 12l7 12 7-12M50 28v50"/>',
    'grocery': '<path d="M17 35h66l-9 43H26zM30 35l10-23m30 23L60 12M35 48v17m15-17v17m15-17v17"/>',
    'bottle': '<path d="M35 10h30v13H35zM40 23v10c-13 6-15 12-15 22v23h50V55c0-10-2-16-15-22V23M25 50h50M42 59h16"/>',
    'lamp': '<path d="m34 10-18 36h68L66 10zM50 46v26M28 78h44M63 47v11"/>',
    'water_bottle': '<path d="M40 8h20v13H40zM40 21c0 13-10 11-10 26v30h40V47c0-15-10-13-10-26M30 45h40M40 54h20"/>',
    'handyman': '<path d="M15 24h70v54H15zM35 24V12h30v12M15 42h70M42 38h16v12H42z"/>',
}


def product_art(icon: str) -> None:
    geometry = ART.get(icon, ART['shopping_bag'])
    _illustrated_html(f'<div class="si-product-art" aria-hidden="true"><svg viewBox="0 0 100 90" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{geometry}</svg></div>')


def render_table(data, hide_index=True, column_config=None, alt='Data table', **kwargs) -> None:
    """Theme-safe accessible read-only table, with escaping and bounded rendering."""
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    total = len(frame)
    frame = frame.head(500)
    configs = column_config or {}
    formatted = frame.copy().astype(object)
    for col in formatted.columns:
        fmt = configs.get(col, {}).get('type_config', {}).get('format')
        if fmt:
            def display(value):
                try:
                    return fmt % float(value)
                except (ValueError, TypeError):
                    return value
            formatted[col] = formatted[col].map(display)
    table = formatted.to_html(index=not hide_index, escape=True, border=0, classes='si-table', na_rep='—')
    st.html(f'<div class="si-table-wrap" role="region" aria-label="{html.escape(alt, quote=True)}" tabindex="0">{table}</div>')
    if total > 500:
        st.caption(f'Showing 500 of {total:,} rows. Use the filters or download the full data.')


def render_badge(badge: dict) -> None:
    symbol = {'leaf': '✳', 'forest': '♧', 'spark': '✦', 'trophy': '◇'}.get(badge['icon'], '✳')
    st.html(f'<article class="si-badge"><span class="si-badge-symbol" aria-hidden="true">{symbol}</span>'
            f'<h3>{html.escape(badge["name"])}</h3><p>{html.escape(badge["description"])}</p>'
            '<span class="si-match">MILESTONE UNLOCKED</span></article>')
