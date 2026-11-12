"""ShopImpact theme."""
from __future__ import annotations

from pathlib import Path
import streamlit as st

PALETTES = {
    False: dict(page='#F6F5EF', surface='#FFFEFA', inset='#EDEFE7', text='#172D26', muted='#55665D',
                border='#CFD7CD', accent='#23694F', accent_text='#FFFFFF', soft='#E5EDD9',
                grid='#E1E5DB', glow='rgba(134,170,90,.12)', shadow='0 14px 36px -25px rgba(26,54,36,.30)'),
    True: dict(page='#0B1415', surface='#142121', inset='#1C2C2B', text='#F0F5E9', muted='#B0C0B7',
               border='#39504A', accent='#C7F28A', accent_text='#142617', soft='#263F2A',
               grid='#2B3C36', glow='rgba(143,202,104,.07)', shadow='0 14px 36px -25px rgba(0,0,0,.8)'),
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
