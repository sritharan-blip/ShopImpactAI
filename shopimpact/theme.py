"""ShopImpact theme."""
from __future__ import annotations

from pathlib import Path
import streamlit as st

PALETTES = {
    False: dict(page='#EEF3FD', surface='#FAFCFF', inset='#E6EDF9', text='#17223B', muted='#4C5F7D',
                border='#BBCBE3', accent='#3153D5', accent_text='#FFFFFF', soft='#DCE7FF',
                grid='#D7E2F3', glow='rgba(77,129,255,.16)', shadow='0 18px 50px -22px rgba(44,70,124,.28)',
                glass='rgba(250,252,255,.78)', glass_strong='rgba(250,252,255,.94)',
                glass_border='rgba(255,255,255,.92)', violet='#7450DA', mint='#117D78',
                orb_one='rgba(78,145,255,.30)', orb_two='rgba(175,125,255,.22)', orb_three='rgba(59,211,200,.23)',
                impact_high='#B62039', impact_medium='#8A5A00', impact_low='#126A52'),
    True: dict(page='#070C19', surface='#111D32', inset='#192943', text='#F2F6FF', muted='#BDCBE2',
               border='#405578', accent='#80E7FF', accent_text='#071728', soft='#203B58',
               grid='#293D5B', glow='rgba(87,185,255,.15)', shadow='0 24px 60px -24px rgba(0,0,0,.70)',
               glass='rgba(17,29,50,.80)', glass_strong='rgba(17,29,50,.96)',
               glass_border='rgba(168,201,255,.23)', violet='#C5ADFF', mint='#82EAD0',
               orb_one='rgba(49,103,230,.26)', orb_two='rgba(131,64,230,.24)', orb_three='rgba(20,164,170,.17)',
               impact_high='#FF9EA8', impact_medium='#FFD58A', impact_low='#82EAD0'),
}


def apply_custom_css(dark_mode: bool, high_contrast: bool = False, reduce_motion: bool = False) -> None:
    palette = dict(PALETTES[dark_mode])
    if high_contrast:
        palette.update(text='#FFFFFF' if dark_mode else '#102019',
                       muted='#FFFFFF' if dark_mode else '#102019',
                       border='#B7D3C5' if dark_mode else '#335644')
    variables = ';'.join(f'--si-{key.replace("_", "-")}:{value}' for key, value in palette.items())
    css = (Path(__file__).parent / 'assets' / 'app.css').read_text(encoding='utf-8')
    motion = '*,:before,:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}' if reduce_motion else ''
    st.html(f'<style>:root{{{variables};color-scheme:{"dark" if dark_mode else "light"}}}{css}{motion}</style>')
    st.html('<div class="si-ambient" aria-hidden="true"><i></i><i></i><i></i></div>')


def _plot_layout(dark_mode: bool) -> dict:
    background = PALETTES[dark_mode]['surface']
    foreground = PALETTES[dark_mode]['text']
    return {
        "template": "plotly_dark" if dark_mode else "plotly_white",
        "paper_bgcolor": background,
        "plot_bgcolor": background,
        "font": {"family": "Segoe UI, sans-serif", "color": foreground},
        "transition": {"duration": 350, "easing": "cubic-in-out"},
        "xaxis": {"gridcolor": PALETTES[dark_mode]['grid'], "zerolinecolor": PALETTES[dark_mode]['grid']},
        "yaxis": {"gridcolor": PALETTES[dark_mode]['grid'], "zerolinecolor": PALETTES[dark_mode]['grid']},
        "margin": {"l": 12, "r": 12, "t": 42, "b": 12},
        "legend": {"orientation": "h", "y": -0.22},
    }
