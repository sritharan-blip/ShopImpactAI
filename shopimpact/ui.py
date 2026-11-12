"""Escaped, theme-aware UI pieces. All artwork is local inline vector geometry."""
from __future__ import annotations

from datetime import date
import html
import pandas as pd
import streamlit as st


def render_hero(count: int) -> None:
    st.html(f'''<section class="si-hero" aria-label="ShopImpact dashboard introduction">
      <div><span class="si-status">A LITTLE MORE INTENTIONAL</span>
      <h1>Good choices.<br><em>Better everyday.</em></h1>
      <p>Know what you spend. Explore your footprint.<br>Find more meaning in what you bring home.</p>
      <small>{date.today():%A, %d %B} &nbsp; / &nbsp; {count} purchases tracked</small></div>
      <div class="si-hero-art" aria-hidden="true">
      <svg viewBox="0 0 360 300" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="180" cy="150" r="125" fill="var(--si-soft)"/>
      <g class="si-orbit"><ellipse cx="180" cy="150" rx="155" ry="90" stroke="var(--si-border)" stroke-dasharray="3 7"/><circle cx="335" cy="150" r="7" fill="currentColor"/></g>
      <g class="si-bag"><path d="M112 100h138l-13 150H125z" fill="var(--si-accent)"/>
      <path d="M149 106V81c0-45 64-45 64 0v25" stroke="var(--si-text)" stroke-width="9" stroke-linecap="round"/>
      <path d="M180 202c-32-8-39-34-27-58 27 1 46 24 27 58Z" fill="var(--si-accent-text)"/>
      <path d="M180 202c2-39 23-58 47-54 0 31-20 47-47 54Z" fill="var(--si-accent-text)" opacity=".65"/>
      <path d="M180 216v-43" stroke="var(--si-accent-text)" stroke-width="3"/>
      <path d="M131 235h101" stroke="var(--si-accent-text)" opacity=".3"/></g>
      <g class="si-orbit-card"><rect x="22" y="90" width="78" height="57" rx="12" fill="var(--si-surface)" stroke="var(--si-border)"/>
      <path d="m43 118 11 9 21-23" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="254" y="42" width="65" height="56" rx="12" fill="var(--si-surface)" stroke="var(--si-border)"/>
      <path d="M273 78V66m12 12V59m12 19V53" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></g>
      </svg><div class="si-hero-note"><strong>Less impulse.</strong><br>More intention.</div></div></section>''')


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
    st.html(f'<div class="si-product-art" aria-hidden="true"><svg viewBox="0 0 100 90" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{geometry}</svg></div>')


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
