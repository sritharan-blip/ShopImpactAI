"""ShopImpact: a session-based conscious shopping dashboard."""

from __future__ import annotations

import html
import json
from datetime import date, timedelta
import math
from uuid import uuid4

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageDraw, ImageFont


st.set_page_config(
    page_title="ShopImpact | Conscious shopping",
    page_icon=":material/eco:",
    layout="wide",
    initial_sidebar_state="expanded",
)


CATEGORIES = {
    "Electronics": {"factor": 3.5, "level": "High"},
    "Fast fashion / leather": {"factor": 2.8, "level": "High"},
    "Groceries / organic food": {"factor": 0.4, "level": "Low"},
    "Sustainable apparel / second-hand": {"factor": 0.2, "level": "Very low"},
    "Beauty & personal care": {"factor": 1.1, "level": "Medium"},
    "Home & living": {"factor": 1.5, "level": "Medium"},
}

ALTERNATIVE_BRANDS = {
    "Electronics": ["Fairphone", "Back Market", "Framework"],
    "Fast fashion / leather": ["Patagonia Worn Wear", "Vinted", "Veja"],
    "Groceries / organic food": ["Local co-op", "Too Good To Go", "Misfits Market"],
    "Sustainable apparel / second-hand": ["thredUP", "Depop", "Patagonia Worn Wear"],
    "Beauty & personal care": ["Ethique", "Plaine Products", "By Humankind"],
    "Home & living": ["Etsy (vintage)", "Buy Nothing Project", "Avocado"],
}

RISKY_BRAND_TERMS = ("shein", "temu", "boohoo", "fashion nova")
LOW_IMPACT_FACTOR = 0.4
MONTHLY_CO2_TARGET = 25.0
TREE_ABSORPTION_KG_PER_YEAR = 21.77
CAR_EMISSIONS_KG_PER_MILE = 0.404

DEMO_ITEMS = [
    ("Organic market basket", "Groceries / organic food", "Local co-op", 24.00, 32.00),
    ("Pre-loved denim jacket", "Sustainable apparel / second-hand", "Vinted", 42.00, 38.00),
    ("Seasonal produce box", "Groceries / organic food", "Farm share", 38.00, 34.00),
    ("Recycled cotton tee", "Sustainable apparel / second-hand", "Patagonia Worn Wear", 46.00, 40.00),
    ("Fairphone repair parts", "Electronics", "Fairphone", 22.00, 0.00),
    ("Everyday tote", "Fast fashion / leather", "SHEIN", 18.00, 0.00),
    ("Refill pantry staples", "Groceries / organic food", "Bulk store", 16.00, 31.00),
    ("Refill hand wash", "Beauty & personal care", "Ethique", 18.00, 26.00),
    ("Second-hand reading lamp", "Home & living", "Etsy (vintage)", 35.00, 0.00),
]

ECO_TIPS = [
    "Buy fewer, better-used items: extending a product's life often beats replacing it with a new 'eco' version.",
    "For electronics, repair or refurbished can avoid much of the manufacturing footprint.",
    "A short shopping list helps prevent food waste. Store produce so it stays visible and easy to use.",
    "Check the material and care label. Durable natural or recycled fibers can last longer with gentle washing.",
    "Try a refill or concentrate before buying another single-use bottle.",
    "Borrow, rent, or buy second-hand for items you use only occasionally.",
]

PRODUCTS = [
    {
        "id": "refurb-phone",
        "name": "Certified refurbished smartphone",
        "brand": "Loop Mobile",
        "category": "Electronics",
        "price": 329.00,
        "impact_factor": 1.55,
        "icon": "smartphone",
        "tagline": "A second life, fully checked.",
        "description": "Professionally refurbished, unlocked, and quality checked with a 12-month limited warranty.",
        "materials": "Reused aluminum and glass; replacement parts where needed.",
        "care": "Use a protective case and replace the battery when capacity drops.",
        "repairability": "Parts and repair guides available.",
        "rating": 4.8,
        "reviews": 126,
        "stock": 8,
    },
    {
        "id": "modular-laptop",
        "name": "Modular everyday laptop",
        "brand": "Framework",
        "category": "Electronics",
        "price": 749.00,
        "impact_factor": 1.8,
        "icon": "laptop",
        "tagline": "Upgrade parts, not the whole machine.",
        "description": "A repair-first laptop designed for user-replaceable memory, storage, keyboard, and ports.",
        "materials": "Recycled aluminum chassis and replaceable components.",
        "care": "Keep vents clear and install software updates for longer useful life.",
        "repairability": "High: modular parts and public repair guides.",
        "rating": 4.7,
        "reviews": 94,
        "stock": 5,
    },
    {
        "id": "reclaimed-tote",
        "name": "Reclaimed-fabric market tote",
        "brand": "ReMade Studio",
        "category": "Fast fashion / leather",
        "price": 34.00,
        "impact_factor": 0.55,
        "icon": "shopping_bag",
        "tagline": "Made from fabric that already exists.",
        "description": "A sturdy everyday carry-all cut and sewn in small batches from reclaimed deadstock fabric.",
        "materials": "Reclaimed cotton canvas; each run uses a different fabric.",
        "care": "Spot clean or cold wash; air dry.",
        "repairability": "Simple seams can be repaired by a local alterations shop.",
        "rating": 4.9,
        "reviews": 58,
        "stock": 16,
    },
    {
        "id": "repairable-overshirt",
        "name": "Repairable workwear overshirt",
        "brand": "Field & Form",
        "category": "Sustainable apparel / second-hand",
        "price": 88.00,
        "impact_factor": 0.18,
        "icon": "apparel",
        "tagline": "Built for repeat wears and easy mending.",
        "description": "A hard-wearing overshirt with reinforced seams and spare buttons included.",
        "materials": "Certified organic cotton twill.",
        "care": "Wash less often on cold; line dry to preserve the fabric.",
        "repairability": "Spare buttons and reinforced stress points.",
        "rating": 4.6,
        "reviews": 73,
        "stock": 11,
    },
    {
        "id": "pantry-refill",
        "name": "Seasonal pantry refill box",
        "brand": "Local Harvest",
        "category": "Groceries / organic food",
        "price": 42.00,
        "impact_factor": 0.28,
        "icon": "grocery",
        "tagline": "Local staples, packed for a useful week.",
        "description": "A rotating selection of shelf-stable staples sourced from regional producers.",
        "materials": "Reusable or recyclable packaging; contents vary by season.",
        "care": "Store dry goods in airtight containers and plan meals before reordering.",
        "repairability": "Not applicable; choose refill quantities you can use.",
        "rating": 4.8,
        "reviews": 211,
        "stock": 30,
    },
    {
        "id": "refill-cleanser",
        "name": "Concentrated home-cleaning refill",
        "brand": "Common Good",
        "category": "Beauty & personal care",
        "price": 16.00,
        "impact_factor": 0.72,
        "icon": "bottle",
        "tagline": "Refill a bottle you already own.",
        "description": "A compact concentrate to dilute at home; one pouch makes multiple bottles.",
        "materials": "Concentrated formula in a lightweight recyclable pouch.",
        "care": "Follow dilution directions and reuse a clean, compatible bottle.",
        "repairability": "Keep and reuse the dispenser bottle.",
        "rating": 4.5,
        "reviews": 167,
        "stock": 24,
    },
    {
        "id": "secondhand-lamp",
        "name": "Vintage reading lamp",
        "brand": "Good Again Market",
        "category": "Home & living",
        "price": 64.00,
        "impact_factor": 0.52,
        "icon": "lamp",
        "tagline": "A pre-loved original, inspected and rewired.",
        "description": "A one-of-a-kind second-hand lamp, electrically safety checked before listing.",
        "materials": "Existing metal and glass components; LED bulb compatible.",
        "care": "Dust with a soft cloth and use a suitable LED bulb.",
        "repairability": "Replaceable cord, socket, and bulb.",
        "rating": 4.9,
        "reviews": 31,
        "stock": 1,
    },
    {
        "id": "reusable-bottle",
        "name": "Lifetime stainless bottle",
        "brand": "Klean Kanteen",
        "category": "Home & living",
        "price": 32.00,
        "impact_factor": 0.68,
        "icon": "water_bottle",
        "tagline": "Simple, durable, and easy to keep.",
        "description": "A durable single-wall bottle with a replaceable cap and lifetime limited warranty.",
        "materials": "Stainless steel with a replaceable stainless cap.",
        "care": "Hand wash for best finish; replace the cap instead of the bottle.",
        "repairability": "Replacement caps and seals available.",
        "rating": 4.7,
        "reviews": 302,
        "stock": 21,
    },
    {
        "id": "repair-kit",
        "name": "Everyday clothing repair kit",
        "brand": "Mend More",
        "category": "Sustainable apparel / second-hand",
        "price": 19.00,
        "impact_factor": 0.12,
        "icon": "handyman",
        "tagline": "Keep a favorite in rotation.",
        "description": "A beginner-friendly kit with needles, thread, patches, and a quick-start mending guide.",
        "materials": "Reusable metal tools and recycled paper packaging.",
        "care": "Store dry and keep small parts away from children.",
        "repairability": "The product helps repair other items.",
        "rating": 4.8,
        "reviews": 89,
        "stock": 18,
    },
]


def calculate_impact(category: str, price: float) -> float:
    """Estimate purchase emissions using the category's kg CO2e per $10 factor."""
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    price_value = float(price)
    if not math.isfinite(price_value) or price_value < 0:
        raise ValueError("Price must be a finite, non-negative number")
    return round(CATEGORIES[category]["factor"] * price_value / 10, 2)


def check_badges(
    purchases: list[dict],
    as_of: date | None = None,
    monthly_target: float = MONTHLY_CO2_TARGET,
) -> dict:
    """Return badge progress, earned status, and a user level for the ledger."""
    today = as_of or date.today()
    month_items = []
    for item in purchases:
        try:
            item_date = date.fromisoformat(str(item["date"]))
        except (KeyError, TypeError, ValueError):
            continue
        if item_date.year == today.year and item_date.month == today.month:
            month_items.append(item)

    low_count = sum(
        1
        for item in purchases
        if CATEGORIES.get(item.get("category"), {}).get("factor", 99) <= LOW_IMPACT_FACTOR
    )
    month_co2 = sum(float(item.get("co2", 0)) for item in month_items)
    month_green_savings = sum(float(item.get("green_savings", 0)) for item in month_items)

    badges = [
        {
            "key": "novice",
            "name": "Eco Novice",
            "description": "Log your first purchase and start building a clearer footprint.",
            "icon": "leaf",
            "earned": len(purchases) >= 1,
            "progress": min(len(purchases), 1),
            "target": 1,
        },
        {
            "key": "guardian",
            "name": "Green Guardian",
            "description": "Choose five or more low-impact purchases.",
            "icon": "forest",
            "earned": low_count >= 5,
            "progress": min(low_count, 5),
            "target": 5,
        },
        {
            "key": "hero",
            "name": "Zero-Emission Hero",
            "description": f"Keep this month's estimated footprint under {monthly_target:.0f} kg CO2e.",
            "icon": "spark",
            "earned": bool(month_items) and month_co2 < monthly_target,
            "progress": max(0, min(month_co2, monthly_target)),
            "target": monthly_target,
        },
        {
            "key": "saver",
            "name": "Eco Saver of the Month",
            "description": "Record over $100 in savings from greener choices this month.",
            "icon": "trophy",
            "earned": month_green_savings > 100,
            "progress": min(month_green_savings, 100),
            "target": 100,
        },
    ]
    earned_count = sum(1 for badge in badges if badge["earned"])
    level = (
        "Impact champion"
        if earned_count == 4
        else "Green explorer"
        if earned_count >= 2
        else "Eco starter"
        if earned_count == 1
        else "New shopper"
    )
    return {"badges": badges, "level": level, "low_impact_count": low_count}


def get_alternatives(
    category: str,
    price: float,
    brand: str = "",
    force: bool = False,
) -> list[dict]:
    """Suggest lower-footprint brands for high-impact categories or flagged brands."""
    factor = CATEGORIES.get(category, {}).get("factor", 0)
    flagged_brand = any(term in brand.casefold() for term in RISKY_BRAND_TERMS)
    if factor < 2.8 and not flagged_brand and not force:
        return []

    alternatives = ALTERNATIVE_BRANDS.get(category, ["A certified local retailer", "A quality second-hand shop"])
    estimated_savings = max(0.0, (factor - LOW_IMPACT_FACTOR) * float(price) / 10)
    if flagged_brand and factor < 2.8:
        estimated_savings = max(estimated_savings, float(price) * 0.12)
    return [
        {
            "brand": name,
            "estimated_savings": round(estimated_savings, 2),
            "reason": "Lower-impact, repairable, refill, or second-hand option",
        }
        for name in alternatives[:3]
    ]


def draw_badge_graphic(title: str, icon: str, dark_mode: bool = False) -> Image.Image:
    """Draw a compact custom badge with Pillow; the image never touches disk."""
    background = (22, 38, 34) if dark_mode else (238, 248, 242)
    ink = (238, 250, 244) if dark_mode else (23, 53, 43)
    muted = (167, 195, 181) if dark_mode else (79, 112, 95)
    image = Image.new("RGB", (720, 300), background)
    draw = ImageDraw.Draw(image)

    for x in range(720):
        blend = x / 719
        start = (16, 185, 129) if not dark_mode else (5, 100, 78)
        end = (124, 58, 237) if not dark_mode else (69, 39, 120)
        color = tuple(round(start[i] * (1 - blend) + end[i] * blend) for i in range(3))
        draw.line((x, 0, x, 10), fill=color)

    draw.rounded_rectangle((28, 34, 150, 156), radius=38, fill=(16, 185, 129))
    if icon == "forest":
        draw.polygon([(89, 48), (55, 102), (123, 102)], fill=(244, 255, 249))
        draw.polygon([(89, 72), (61, 119), (117, 119)], fill=(216, 249, 232))
        draw.rectangle((84, 116, 94, 137), fill=(70, 50, 32))
    elif icon == "trophy":
        draw.rounded_rectangle((67, 55, 111, 106), radius=8, fill=(255, 226, 133))
        draw.arc((48, 58, 82, 102), 70, 285, fill=(255, 226, 133), width=8)
        draw.arc((97, 58, 131, 102), 255, 110, fill=(255, 226, 133), width=8)
        draw.rectangle((82, 106, 96, 128), fill=(255, 226, 133))
        draw.rounded_rectangle((68, 128, 110, 138), radius=4, fill=(255, 226, 133))
    elif icon == "spark":
        draw.polygon([(89, 45), (98, 82), (132, 94), (98, 103), (89, 140), (80, 103), (46, 94), (80, 82)], fill=(255, 244, 200))
    else:
        draw.ellipse((62, 66, 116, 120), outline=(240, 255, 247), width=6)
        draw.arc((66, 57, 112, 112), 195, 335, fill=(240, 255, 247), width=6)
        draw.line((89, 78, 89, 113), fill=(240, 255, 247), width=5)
        draw.line((89, 94, 105, 81), fill=(240, 255, 247), width=5)

    try:
        title_font = ImageFont.truetype("segoeui.ttf", 33)
        label_font = ImageFont.truetype("segoeui.ttf", 17)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    draw.text((178, 65), title, font=title_font, fill=ink)
    draw.text((180, 119), "SHOPIMPACT  /  MILESTONE UNLOCKED", font=label_font, fill=muted)
    draw.rounded_rectangle((178, 174, 660, 230), radius=22, outline=(16, 185, 129), width=2)
    draw.text((199, 191), "A better choice, made visible.", font=label_font, fill=ink)
    return image


def draw_shopping_illustration() -> Image.Image:
    """Create a small editorial shopping illustration without external assets."""
    scale = 2
    image = Image.new("RGB", (920 * scale, 500 * scale), "#EAF5EF")
    draw = ImageDraw.Draw(image)

    def point(x: int, y: int) -> tuple[int, int]:
        return (x * scale, y * scale)

    draw.ellipse((570 * scale, -75 * scale, 980 * scale, 335 * scale), fill="#E5D9FA")
    draw.ellipse((635 * scale, 264 * scale, 735 * scale, 364 * scale), fill="#F6B36B")
    draw.ellipse((682 * scale, 300 * scale, 776 * scale, 394 * scale), fill="#D95D47")
    draw.ellipse((55 * scale, 312 * scale, 157 * scale, 414 * scale), fill="#F1C85B")
    draw.ellipse((93 * scale, 343 * scale, 191 * scale, 441 * scale), fill="#F49A56")

    draw.ellipse((217 * scale, 355 * scale, 722 * scale, 438 * scale), fill="#C9DED1")
    draw.rounded_rectangle((262 * scale, 184 * scale, 676 * scale, 393 * scale), radius=34 * scale, fill="#FFFDF8")
    draw.polygon([point(272, 218), point(666, 218), point(625, 391), point(314, 391)], fill="#FFFDF8")
    draw.arc((358 * scale, 105 * scale, 580 * scale, 280 * scale), 180, 360, fill="#24483A", width=14 * scale)
    draw.line([point(365, 190), point(388, 362)], fill="#24483A", width=12 * scale)
    draw.line([point(571, 190), point(548, 362)], fill="#24483A", width=12 * scale)

    draw.polygon([point(335, 247), point(385, 195), point(394, 127), point(425, 183), point(415, 241)], fill="#14845E")
    draw.polygon([point(400, 230), point(452, 167), point(465, 101), point(485, 169), point(456, 235)], fill="#10A875")
    draw.polygon([point(457, 234), point(512, 191), point(548, 133), point(538, 212), point(493, 250)], fill="#68A95B")
    draw.line([point(365, 249), point(394, 177)], fill="#145C43", width=5 * scale)
    draw.line([point(423, 240), point(466, 140)], fill="#145C43", width=5 * scale)
    draw.line([point(475, 244), point(530, 164)], fill="#145C43", width=5 * scale)
    draw.rounded_rectangle((353 * scale, 267 * scale, 572 * scale, 336 * scale), radius=13 * scale, fill="#E9F3EC")
    draw.line([point(375, 283), point(548, 283)], fill="#315847", width=4 * scale)
    draw.line([point(391, 301), point(532, 301)], fill="#315847", width=4 * scale)
    draw.line([point(412, 319), point(509, 319)], fill="#315847", width=4 * scale)

    draw.rounded_rectangle((731 * scale, 157 * scale, 816 * scale, 312 * scale), radius=22 * scale, fill="#7650BD")
    draw.rounded_rectangle((750 * scale, 136 * scale, 797 * scale, 169 * scale), radius=10 * scale, fill="#4F3588")
    draw.rounded_rectangle((746 * scale, 218 * scale, 801 * scale, 268 * scale), radius=11 * scale, fill="#F4EDF9")
    draw.ellipse((752 * scale, 228 * scale, 795 * scale, 258 * scale), fill="#10A875")
    draw.line([point(760, 245), point(773, 233), point(789, 248)], fill="#F4EDF9", width=4 * scale)

    try:
        label_font = ImageFont.truetype("segoeui.ttf", 16 * scale)
    except OSError:
        label_font = ImageFont.load_default()
    draw.text(point(376, 364), "GOOD THINGS, CHOSEN WELL", font=label_font, fill="#315847")
    return image.resize((920, 500), Image.Resampling.LANCZOS)


def apply_custom_css(dark_mode: bool, high_contrast: bool) -> None:
    """Apply the explicitly requested small design-system layer."""
    if dark_mode:
        page = "#0F172A"
        surface = "#1E293B"
        text = "#F8FAFC"
        muted = "#CBD5E1"
        border = "#475569"
        shadow = "0 12px 30px -10px rgba(0,0,0,.40)"
        glass = "rgba(15, 23, 42, .72)"
        glass_hover = "rgba(30, 41, 59, .88)"
        glass_border = "rgba(226, 232, 240, .16)"
        sidebar_background = "linear-gradient(180deg, rgba(30,41,59,.94), rgba(15,23,42,.92))"
    else:
        page = "#F3F7F4"
        surface = "#FFFFFF"
        text = "#172B27"
        muted = "#4F615C"
        border = "rgba(15, 23, 42, 0.08)"
        shadow = "0 18px 38px -18px rgba(18, 52, 39, 0.22)"
        glass = "rgba(255, 255, 255, 0.72)"
        glass_hover = "rgba(255, 255, 255, 0.96)"
        glass_border = "rgba(15, 23, 42, 0.08)"
        sidebar_background = "linear-gradient(180deg, rgba(255,255,255,.78), rgba(255,255,255,.42))"
    if high_contrast:
        text = "#000000" if not dark_mode else "#FFFFFF"
        muted = text
        border = "#111827" if not dark_mode else "#FFFFFF"
        glass = surface
        glass_hover = surface
        glass_border = border
        sidebar_background = f"linear-gradient(180deg, {surface}, {page})"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        :root {{
            --si-green: #059669;
            --si-mint: #10B981;
            --si-violet: #7C3AED;
            --si-page: {page};
            --si-surface: {surface};
            --si-text: {text};
            --si-muted: {muted};
            --si-border: {border};
            --si-shadow: {shadow};
            --si-glass: {glass};
            --si-glass-hover: {glass_hover};
            --si-glass-border: {glass_border};
            --si-sidebar-background: {sidebar_background};
            --background-color: {page};
            --secondary-background-color: {surface};
            --text-color: {text};
            --primary-color: #087F5B;
            --border-color: {border};
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(ellipse at 84% 0%, rgba(16,185,129,.13), transparent 34rem),
                radial-gradient(ellipse at 8% 30%, rgba(124,58,237,.07), transparent 30rem),
                var(--si-page);
            color: var(--si-text);
            font-family: "DM Sans", sans-serif;
            transition: background-color .45s ease, color .35s ease;
        }}
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
            color: var(--si-text);
        }}
        [data-testid="stHeader"] {{
            background: var(--si-glass);
            border-bottom: 1px solid var(--si-glass-border);
            backdrop-filter: blur(18px) saturate(155%);
            -webkit-backdrop-filter: blur(18px) saturate(155%);
        }}
        .block-container {{ max-width: 1440px; padding-top: 4.1rem; padding-bottom: 3rem; }}
        [data-testid="stSidebar"] {{
            border-right: 1px solid var(--si-glass-border);
            transition: background-color .45s ease, border-color .45s ease;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            background: var(--si-sidebar-background), var(--si-glass);
            border-right: 1px solid var(--si-glass-border);
            backdrop-filter: blur(24px) saturate(155%);
            -webkit-backdrop-filter: blur(24px) saturate(155%);
        }}
        .st-key-theme_floating {{
            position: relative; z-index: 2; margin-left: auto;
            width: max-content; padding: 5px 12px; border: 1px solid var(--si-glass-border);
            border-radius: 999px; background: var(--si-glass); box-shadow: var(--si-shadow);
            backdrop-filter: blur(18px) saturate(155%);
            -webkit-backdrop-filter: blur(18px) saturate(155%);
            transition: background-color .45s ease, border-color .45s ease, box-shadow .3s ease;
        }}
        .st-key-theme_floating [data-testid="stToggle"] {{ min-height: 30px; }}
        [class*="st-key-page_transition_"] {{ animation: si-page-enter .46s cubic-bezier(.2,.75,.25,1) both; }}
        @keyframes si-page-enter {{
            from {{ opacity: 0; transform: translateY(13px); filter: blur(3px); }}
            to {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
        }}
        [data-testid="stMetric"] {{
            background: var(--si-surface); border: 1px solid var(--si-border);
            border-radius: 14px; padding: 16px 18px; box-shadow: var(--si-shadow);
            transition: transform .22s ease, border-color .35s ease, background-color .45s ease, box-shadow .35s ease;
        }}
        [data-testid="stMetric"]:hover {{ transform: translateY(-2px); border-color: #10B981; }}
        [data-testid="stMetricLabel"] p {{ color: var(--si-muted); font-size: .82rem; }}
        [data-testid="stMetricValue"] {{ color: var(--si-text); font-weight: 700; }}
        [data-testid="stButton"] button:not([kind="primary"]), [data-testid="stFormSubmitButton"] button:not([kind="primary"]) {{
            color: var(--si-text) !important; background: var(--si-surface) !important;
            border-color: var(--si-border) !important;
        }}
        [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {{
            color: #FFFFFF !important; background: #087F5B !important; border-color: #087F5B !important;
        }}
        [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {{
            border-radius: 999px; transition: transform .18s ease, box-shadow .18s ease, color .2s ease, background-color .2s ease;
        }}
        [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover {{
            transform: translateY(-1px); box-shadow: 0 7px 18px rgba(16,185,129,.18);
        }}
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"], [data-testid="stSegmentedControl"] button {{
            color: var(--si-text) !important; background: var(--si-surface) !important;
            border: 1px solid var(--si-border) !important; border-radius: 999px !important;
            transition: color .2s ease, background-color .2s ease, border-color .2s ease, box-shadow .2s ease;
        }}
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"], [data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
            color: #FFFFFF !important; background: #087F5B !important; border-color: #087F5B !important;
            box-shadow: 0 4px 12px rgba(8,127,91,.22);
        }}
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"]:hover, [data-testid="stSegmentedControl"] button:hover {{
            border-color: #10B981 !important;
        }}
        [data-testid="stButton"] button:not([kind="primary"]),
        [data-testid="stFormSubmitButton"] button:not([kind="primary"]),
        [data-testid="stDownloadButton"] button,
        [data-testid="stSegmentedControl"] button,
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{
            background: var(--si-glass) !important;
            border: 1px solid var(--si-glass-border) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.48), 0 5px 16px rgba(21,58,43,.07);
            backdrop-filter: blur(16px) saturate(150%);
            -webkit-backdrop-filter: blur(16px) saturate(150%);
        }}
        [data-testid="stButton"] button[kind="primary"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {{
            background: linear-gradient(135deg, rgba(5,150,105,.94), rgba(8,127,91,.9)) !important;
            border: 1px solid rgba(255,255,255,.36) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.32), 0 8px 20px rgba(8,127,91,.2);
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }}
        [data-testid="stButton"] button:not([disabled]):hover,
        [data-testid="stFormSubmitButton"] button:not([disabled]):hover,
        [data-testid="stDownloadButton"] button:not([disabled]):hover,
        [data-testid="stSegmentedControl"] button:hover,
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"]:hover {{
            background: var(--si-glass-hover) !important;
            border-color: rgba(16,185,129,.48) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.65), 0 9px 24px rgba(16,185,129,.15);
        }}
        [data-testid="stSegmentedControl"] button[aria-pressed="true"],
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {{
            color: #FFFFFF !important;
            background: linear-gradient(135deg, rgba(5,150,105,.88), rgba(8,127,91,.84)) !important;
            border-color: rgba(255,255,255,.38) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.34), 0 5px 15px rgba(8,127,91,.2);
            backdrop-filter: blur(12px) saturate(145%);
            -webkit-backdrop-filter: blur(12px) saturate(145%);
        }}
        [data-testid="stButton"] button[kind="primary"]:not([disabled]):hover,
        [data-testid="stFormSubmitButton"] button[kind="primary"]:not([disabled]):hover {{
            background: linear-gradient(135deg, #10A875, #087F5B) !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            color: var(--si-text) !important;
            background: var(--si-glass) !important;
            border-color: var(--si-glass-border) !important;
            border-radius: 14px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.42), 0 4px 14px rgba(21,58,43,.05);
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
            transition: background-color .25s ease, border-color .25s ease, box-shadow .25s ease;
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stTimeInput"] input:focus,
        [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {{
            border-color: rgba(16,185,129,.72) !important;
            box-shadow: 0 0 0 3px rgba(16,185,129,.14), inset 0 1px 0 rgba(255,255,255,.56);
        }}
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] [data-baseweb="menu"] {{
            color: var(--si-text);
            background: var(--si-glass-hover);
            border: 1px solid var(--si-glass-border);
            border-radius: 16px;
            box-shadow: 0 18px 44px rgba(12,35,26,.18);
            backdrop-filter: blur(22px) saturate(160%);
            -webkit-backdrop-filter: blur(22px) saturate(160%);
        }}
        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="popover"] [role="option"][aria-selected="true"] {{
            background: rgba(16,185,129,.13);
        }}
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {{
            gap: 7px;
        }}
        [data-testid="stSidebar"] [data-testid="stRadio"] label,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"] {{
            border: 1px solid transparent;
            border-radius: 14px;
            background: transparent;
            padding: 9px 11px;
            transition: background-color .2s ease, border-color .2s ease, transform .2s ease, box-shadow .2s ease;
        }}
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"]:hover {{
            background: var(--si-glass);
            border-color: var(--si-glass-border);
            transform: translateX(2px);
        }}
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"][aria-checked="true"] {{
            color: var(--si-text);
            background: linear-gradient(115deg, rgba(16,185,129,.14), rgba(16,185,129,.04)), var(--si-glass);
            border-color: rgba(16,185,129,.24);
            box-shadow: inset 3px 0 0 #10A875, 0 4px 12px rgba(21,58,43,.05);
            backdrop-filter: blur(12px) saturate(135%);
            -webkit-backdrop-filter: blur(12px) saturate(135%);
        }}
        [data-testid="stRadio"] [role="radiogroup"] label {{
            border: 1px solid var(--si-glass-border);
            border-radius: 13px;
            background: var(--si-glass);
            transition: background-color .2s ease, border-color .2s ease, box-shadow .2s ease;
        }}
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(115deg, rgba(16,185,129,.12), rgba(255,255,255,.42)), var(--si-glass);
            border-color: rgba(16,185,129,.26);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.56), 0 4px 14px rgba(21,58,43,.04);
            backdrop-filter: blur(12px) saturate(140%);
            -webkit-backdrop-filter: blur(12px) saturate(140%);
        }}
        [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
            border: 1px solid var(--si-glass-border);
            border-radius: 999px;
            background: linear-gradient(120deg, rgba(16,185,129,.15), rgba(124,58,237,.08));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.42);
        }}
        [data-testid="stCheckbox"] label,
        [data-testid="stToggle"] label {{
            border-radius: 12px;
            transition: background-color .2s ease, color .2s ease;
        }}
        [data-testid="stCheckbox"] label:hover,
        [data-testid="stToggle"] label:hover {{
            background: var(--si-glass);
        }}
        [data-testid="stFileUploader"] section,
        [data-testid="stCameraInput"] section {{
            background: var(--si-glass);
            border: 1px solid var(--si-glass-border);
            border-radius: 18px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.46);
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }}
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
        [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] p {{
            transition: color .3s ease;
        }}
        [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
        [data-testid="stRadio"] [role="radio"],
        [data-testid="stCheckbox"], [data-testid="stToggle"],
        [data-testid="stSelectbox"], [data-testid="stMultiSelect"],
        [data-testid="stSlider"], [data-testid="stNumberInput"],
        [data-testid="stTextInput"], [data-testid="stTextArea"],
        [data-testid="stDateInput"], [data-testid="stFileUploader"],
        [data-testid="stExpander"] {{
            color: var(--si-text);
        }}
        [data-testid="stCaptionContainer"] {{
            color: var(--si-muted);
        }}
        h1, h2, h3 {{ font-family: "Manrope", "DM Sans", sans-serif; }}
        .si-masthead {{ padding: 8px 0 18px; }}
        .si-kicker {{ color: #7C3AED; font-size: .74rem; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }}
        .si-masthead h1 {{ color: var(--si-text); font-family: "Manrope", sans-serif; font-size: 2.55rem; line-height: 1.1; margin: 8px 0; }}
        .si-masthead p {{ color: var(--si-muted); margin: 0; max-width: 590px; font-size: 1.02rem; }}
        .si-section-label {{ color: var(--si-muted); font-size: .76rem; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }}
        .si-action {{ color: #059669; font-weight: 700; }}
        [data-testid="stSegmentedControl"] {{ margin: 2px 0 18px; }}
        [data-testid="stImage"] img {{ border-radius: 8px; }}
        .si-swap {{ border-left: 5px solid #7C3AED; border-radius: 12px; padding: 18px 22px;
            background: linear-gradient(100deg, rgba(124,58,237,.12), rgba(16,185,129,.09)); margin: 12px 0 20px; }}
        .si-swap strong {{ color: var(--si-text); }}
        .si-muted {{ color: var(--si-muted); }}
        .si-tip {{ border-radius: 14px; border: 1px solid var(--si-border); background: var(--si-surface);
            padding: 18px 20px; box-shadow: var(--si-shadow); }}
        .si-qty {{ text-align: center; padding: 6px 0; font-weight: 700; }}
        [data-testid="stRadio"] label {{ font-weight: 600; }}
        @media (max-width: 700px) {{
            .block-container {{ padding: 1.1rem 1rem 2rem; }}
            .si-masthead h1 {{ font-size: 1.9rem; }}
        }}
        @media (max-width: 700px) {{
            .st-key-theme_floating {{ padding: 3px 8px; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{ transition: none !important; animation: none !important; scroll-behavior: auto !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _new_purchase(
    product: str,
    category: str,
    brand: str,
    price: float,
    purchased_on: date,
    green_savings: float = 0,
    co2_override: float | None = None,
) -> dict:
    return {
        "id": str(uuid4()),
        "date": purchased_on.isoformat(),
        "product": product.strip(),
        "category": category,
        "brand": brand.strip(),
        "price": round(float(price), 2),
        "co2": (
            calculate_impact(category, float(price))
            if co2_override is None
            else round(float(co2_override), 2)
        ),
        "impact_level": CATEGORIES[category]["level"],
        "green_savings": round(float(green_savings), 2),
    }


def _load_demo_data() -> None:
    today = date.today()
    purchases = []
    for index, (product, category, brand, price, savings) in enumerate(DEMO_ITEMS):
        purchased_on = today - timedelta(days=index if index < 7 else 35 + index)
        purchases.append(_new_purchase(product, category, brand, price, purchased_on, savings))
    st.session_state.purchases = purchases
    st.session_state.last_added_id = purchases[5]["id"]


def _make_monthly_report(purchases: list[dict], today: date) -> dict:
    rows = []
    for item in purchases:
        try:
            item_date = date.fromisoformat(str(item["date"]))
        except (KeyError, TypeError, ValueError):
            continue
        if item_date.year == today.year and item_date.month == today.month:
            rows.append(item)
    return {
        "month": today.strftime("%B %Y"),
        "purchase_count": len(rows),
        "total_spend": round(sum(float(item.get("price", 0)) for item in rows), 2),
        "estimated_co2_kg": round(sum(float(item.get("co2", 0)) for item in rows), 2),
        "green_choice_savings": round(sum(float(item.get("green_savings", 0)) for item in rows), 2),
        "tree_years_to_offset": round(
            sum(float(item.get("co2", 0)) for item in rows) / TREE_ABSORPTION_KG_PER_YEAR, 2
        ),
        "method_note": "Category averages in kg CO2e per $10 spent; estimates are directional, not product LCAs.",
    }


def _plot_layout(dark_mode: bool) -> dict:
    background = "#1E293B" if dark_mode else "#FFFFFF"
    foreground = "#F8FAFC" if dark_mode else "#25352E"
    return {
        "template": "plotly_dark" if dark_mode else "plotly_white",
        "paper_bgcolor": background,
        "plot_bgcolor": background,
        "font": {"family": "DM Sans, Segoe UI, sans-serif", "color": foreground},
        "margin": {"l": 12, "r": 12, "t": 42, "b": 12},
        "legend": {"orientation": "h", "y": -0.22},
    }


def _purchase_frame(purchases: list[dict]) -> pd.DataFrame:
    if not purchases:
        return pd.DataFrame(columns=["id", "date", "product", "category", "brand", "price", "co2", "impact_level", "green_savings"])
    frame = pd.DataFrame(purchases).copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce").fillna(0)
    frame["co2"] = pd.to_numeric(frame["co2"], errors="coerce").fillna(0)
    if "green_savings" not in frame:
        frame["green_savings"] = 0.0
    frame["green_savings"] = pd.to_numeric(frame["green_savings"], errors="coerce").fillna(0)
    return frame.dropna(subset=["date"])


def _monthly_frame(purchases: list[dict], today: date | None = None) -> pd.DataFrame:
    frame = _purchase_frame(purchases)
    reference_date = today or date.today()
    if frame.empty:
        return frame
    return frame[(frame["date"].dt.year == reference_date.year) & (frame["date"].dt.month == reference_date.month)]


def _month_end_forecast(month_co2: float, today: date, monthly_target: float) -> dict:
    """Project this month's emissions at the current daily pace."""
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - today.replace(day=1)).days
    projected_co2 = float(month_co2) / today.day * days_in_month if month_co2 else 0.0
    days_remaining = days_in_month - today.day
    remaining_target = max(0.0, float(monthly_target) - float(month_co2))
    return {
        "projected_co2": round(projected_co2, 1),
        "remaining_target": round(remaining_target, 1),
        "daily_allowance": round(remaining_target / days_remaining, 2) if days_remaining else 0.0,
        "days_remaining": days_remaining,
    }


def _month_end_spend_forecast(month_spend: float, today: date, monthly_budget: float) -> dict:
    """Project monthly spend at the current daily pace and remaining budget."""
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - today.replace(day=1)).days
    days_remaining = days_in_month - today.day
    remaining_budget = max(0.0, float(monthly_budget) - float(month_spend))
    return {
        "projected_spend": round(float(month_spend) / today.day * days_in_month, 2) if month_spend else 0.0,
        "remaining_budget": round(remaining_budget, 2),
        "daily_allowance": round(remaining_budget / days_remaining, 2) if days_remaining else 0.0,
        "days_remaining": days_remaining,
    }


def _weekly_green_challenge(purchases: list[dict], today: date | None = None, target: int = 3) -> dict:
    """Count low-impact purchases for the current Monday-to-Sunday challenge."""
    reference_date = today or date.today()
    week_start = reference_date - timedelta(days=reference_date.weekday())
    count = 0
    for item in purchases:
        try:
            item_date = date.fromisoformat(str(item["date"]))
        except (KeyError, TypeError, ValueError):
            continue
        if week_start <= item_date <= reference_date and CATEGORIES.get(item.get("category"), {}).get("factor", 99) <= LOW_IMPACT_FACTOR:
            count += 1
    return {"progress": min(count, target), "count": count, "target": target, "week_start": week_start, "complete": count >= target}


def _navigate_to(view: str) -> None:
    st.session_state.view = view


def _parse_purchase_csv(uploaded_file) -> tuple[list[dict], list[str]]:
    """Validate an imported ledger and recalculate emissions from trusted categories."""
    try:
        source = pd.read_csv(uploaded_file)
    except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as error:
        return [], [f"Could not read this CSV: {error}"]
    source.columns = [str(column).strip().casefold() for column in source.columns]
    required = {"product", "category", "price"}
    missing = required - set(source.columns)
    if missing:
        return [], [f"Missing required columns: {', '.join(sorted(missing))}"]
    if len(source) > 5000:
        return [], ["Import is limited to 5,000 rows at a time."]

    accepted: list[dict] = []
    issues: list[str] = []
    for index, row in source.iterrows():
        row_number = index + 2
        product_value = row.get("product")
        product = "" if pd.isna(product_value) else str(product_value).strip()
        category_value = row.get("category")
        category = "" if pd.isna(category_value) else str(category_value).strip()
        price_value = pd.to_numeric(row.get("price"), errors="coerce")
        if not product:
            issues.append(f"Row {row_number}: product is blank.")
            continue
        if category not in CATEGORIES:
            issues.append(f"Row {row_number}: unrecognized category '{category}'.")
            continue
        if pd.isna(price_value) or not math.isfinite(float(price_value)) or float(price_value) < 0:
            issues.append(f"Row {row_number}: price must be a finite, non-negative number.")
            continue

        date_value = row.get("date")
        purchased_on = date.today()
        if pd.notna(date_value):
            parsed_date = pd.to_datetime(date_value, errors="coerce")
            if pd.isna(parsed_date) or parsed_date.date() > date.today():
                issues.append(f"Row {row_number}: date is invalid or in the future.")
                continue
            purchased_on = parsed_date.date()
        brand_value = row.get("brand")
        brand = "" if pd.isna(brand_value) else str(brand_value).strip()
        accepted.append(_new_purchase(product, category, brand, float(price_value), purchased_on))
    return accepted, issues[:20]


def _new_wishlist_item(
    product: str,
    category: str,
    brand: str,
    price: float,
    revisit_on: date,
    priority: str,
    note: str = "",
) -> dict:
    return {
        "id": str(uuid4()),
        "product": product.strip(),
        "category": category,
        "brand": brand.strip(),
        "price": round(float(price), 2),
        "added_on": date.today().isoformat(),
        "revisit_on": revisit_on.isoformat(),
        "priority": priority,
        "note": note.strip(),
        "estimated_co2": calculate_impact(category, float(price)),
    }


def _make_data_backup(purchases: list[dict], wishlist: list[dict]) -> bytes:
    """Serialize the portable, user-owned parts of the session without derived estimates."""
    payload = {
        "schema_version": 1,
        "exported_on": date.today().isoformat(),
        "purchases": purchases,
        "wishlist": wishlist,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def _parse_data_backup(uploaded_file) -> tuple[dict | None, list[str]]:
    """Validate an exported backup and recalculate trusted category estimates."""
    try:
        raw_data = uploaded_file.getvalue()
        if len(raw_data) > 5 * 1024 * 1024:
            return None, ["Backup files are limited to 5 MB."]
        payload = json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as error:
        return None, [f"Could not read this backup: {error}"]

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return None, ["This is not a supported ShopImpact backup."]
    purchases_source = payload.get("purchases")
    wishlist_source = payload.get("wishlist")
    if not isinstance(purchases_source, list) or not isinstance(wishlist_source, list):
        return None, ["The backup must contain purchase and wishlist lists."]
    if len(purchases_source) > 5000 or len(wishlist_source) > 500:
        return None, ["This backup exceeds the supported size (5,000 purchases and 500 wishlist items)."]

    purchases = []
    wishlist = []
    issues = []
    for index, row in enumerate(purchases_source, start=1):
        if not isinstance(row, dict):
            issues.append(f"Purchase {index}: expected an object.")
            continue
        product = str(row.get("product", "")).strip()
        category = str(row.get("category", "")).strip()
        price = pd.to_numeric(row.get("price"), errors="coerce")
        try:
            purchased_on = date.fromisoformat(str(row.get("date", "")))
        except ValueError:
            purchased_on = None
        if (
            not product
            or category not in CATEGORIES
            or pd.isna(price)
            or not math.isfinite(float(price))
            or float(price) < 0
            or purchased_on is None
            or purchased_on > date.today()
        ):
            issues.append(f"Purchase {index}: invalid product, category, price, or date.")
            continue
        green_savings = pd.to_numeric(row.get("green_savings", 0), errors="coerce")
        if pd.isna(green_savings) or not math.isfinite(float(green_savings)) or float(green_savings) < 0:
            issues.append(f"Purchase {index}: invalid greener-choice savings.")
            continue
        purchase = _new_purchase(
            product,
            category,
            str(row.get("brand", "")),
            float(price),
            purchased_on,
            float(green_savings),
        )
        purchases.append(purchase)

    valid_priorities = {"Need", "Want"}
    for index, row in enumerate(wishlist_source, start=1):
        if not isinstance(row, dict):
            issues.append(f"Wishlist item {index}: expected an object.")
            continue
        product = str(row.get("product", "")).strip()
        category = str(row.get("category", "")).strip()
        price = pd.to_numeric(row.get("price"), errors="coerce")
        try:
            revisit_on = date.fromisoformat(str(row.get("revisit_on", "")))
        except ValueError:
            revisit_on = None
        if (
            not product
            or category not in CATEGORIES
            or pd.isna(price)
            or not math.isfinite(float(price))
            or float(price) <= 0
            or revisit_on is None
        ):
            issues.append(f"Wishlist item {index}: invalid product, category, price, or revisit date.")
            continue
        wishlist.append(
            _new_wishlist_item(
                product,
                category,
                str(row.get("brand", "")),
                float(price),
                revisit_on,
                str(row.get("priority", "Want")) if row.get("priority") in valid_priorities else "Want",
                str(row.get("note", "")),
            )
        )
    return {"purchases": purchases, "wishlist": wishlist}, issues[:20]


def _render_wishlist() -> None:
    st.markdown('<div class="si-kicker">Mindful wishlist</div>', unsafe_allow_html=True)
    st.title("Pause now. Choose with intention.")
    st.caption("Save ideas, let the urge cool, and see the budget and footprint before you decide.")

    wishlist = st.session_state.setdefault("wishlist", [])
    today = date.today()
    planned_spend = sum(float(item.get("price", 0)) for item in wishlist)
    planned_co2 = sum(float(item.get("estimated_co2", 0)) for item in wishlist)
    ready_count = sum(
        1 for item in wishlist
        if date.fromisoformat(str(item.get("revisit_on", today.isoformat()))) <= today
    )
    metric_cols = st.columns(3)
    metric_cols[0].metric("Ideas on your list", len(wishlist), border=True)
    metric_cols[1].metric("Planned spend", f"${planned_spend:,.2f}", border=True)
    metric_cols[2].metric("Ready to revisit", ready_count, border=True)

    with st.expander("Add an idea to your wishlist", expanded=not wishlist, icon=":material/bookmark_add:"):
        with st.form("wishlist_form", border=True):
            product = st.text_input("What are you considering?", placeholder="e.g. A new winter coat")
            category = st.selectbox("Category", list(CATEGORIES), key="wishlist_category")
            brand, price = st.columns(2)
            with brand:
                brand_name = st.text_input("Brand or shop (optional)", key="wishlist_brand")
            with price:
                expected_price = st.number_input("Expected price ($)", min_value=0.01, max_value=100000.0, value=50.0, step=5.0, key="wishlist_price")
            revisit_on = st.date_input(
                "Remind me to revisit",
                value=today + timedelta(days=7),
                min_value=today,
                max_value=today + timedelta(days=365),
                help="A short cooling-off period can help separate a passing impulse from something useful.",
            )
            priority = st.radio("Is it a need or a want?", ["Need", "Want"], horizontal=True)
            note = st.text_input("What would make this worth buying?", placeholder="e.g. Only if my current one cannot be repaired")
            submitted = st.form_submit_button("Save to wishlist", type="primary", icon=":material/bookmark_add:")
        if submitted:
            if not product.strip():
                st.error("Add a product name before saving this idea.")
            else:
                wishlist.append(
                    _new_wishlist_item(
                        product, category, brand_name, expected_price, revisit_on, priority, note
                    )
                )
                st.toast(f"{product.strip()} added to your wishlist.", icon=":material/bookmark_added:")
                st.rerun()

    if not wishlist:
        st.info("Your wishlist is empty. Add an idea above when something catches your eye.")
        return

    budget = float(st.session_state.get("monthly_budget", 600.0))
    month_spend = float(_monthly_frame(st.session_state.get("purchases", []))["price"].sum())
    st.progress(
        min(month_spend / budget, 1.0),
        text=f"This month's tracked spend: ${month_spend:,.2f} of ${budget:,.2f} budget · wishlist is planned, not spent",
    )
    st.caption(
        f"If every listed item were bought, its category-average estimate would be {planned_co2:.1f} kg CO2e. "
        "Wishlist estimates are not included in your purchase totals."
    )

    ordered = sorted(
        wishlist,
        key=lambda item: (
            date.fromisoformat(str(item.get("revisit_on", today.isoformat()))) > today,
            date.fromisoformat(str(item.get("revisit_on", today.isoformat()))),
            item.get("priority") != "Need",
        ),
    )
    st.markdown("### Your ideas")
    for item in ordered:
        revisit_on = date.fromisoformat(str(item.get("revisit_on", today.isoformat())))
        ready = revisit_on <= today
        with st.container(border=True):
            title_col, info_col = st.columns([1.8, 1])
            with title_col:
                st.markdown(f"**{html.escape(str(item.get('product', 'Wishlist item')))}**  ·  {item.get('priority', 'Want')}")
                st.caption(
                    f"{html.escape(str(item.get('category', '')))}"
                    + (f" · {html.escape(str(item.get('brand', '')))}" if item.get("brand") else "")
                    + f" · Revisit {'now' if ready else revisit_on.strftime('%b %d, %Y')}"
                )
                if item.get("note"):
                    st.caption(f"Your reason: {html.escape(str(item['note']))}")
            with info_col:
                st.metric("Planned", f"${float(item.get('price', 0)):,.2f}")
                st.caption(f"~{float(item.get('estimated_co2', 0)):.1f} kg CO2e")
            action_cols = st.columns([1, 1, 1, 2])
            with action_cols[0]:
                if st.button(
                    "Log purchase",
                    key=f"wishlist_buy_{item['id']}",
                    icon=":material/add_shopping_cart:",
                    disabled=not ready,
                ):
                    purchase = _new_purchase(
                        str(item.get("product", "")),
                        str(item.get("category", "")),
                        str(item.get("brand", "")),
                        float(item.get("price", 0)),
                        today,
                    )
                    st.session_state.purchases.append(purchase)
                    st.session_state.last_added_id = purchase["id"]
                    st.session_state.wishlist = [entry for entry in wishlist if entry["id"] != item["id"]]
                    st.toast("Wishlist item moved to your purchase log.", icon=":material/check_circle:")
                    st.rerun()
            with action_cols[1]:
                if st.button("Snooze 7 days", key=f"wishlist_snooze_{item['id']}", icon=":material/snooze:"):
                    item["revisit_on"] = (max(today, revisit_on) + timedelta(days=7)).isoformat()
                    st.rerun()
            with action_cols[2]:
                if st.button("Remove", key=f"wishlist_remove_{item['id']}", icon=":material/delete_outline:"):
                    st.session_state.wishlist = [entry for entry in wishlist if entry["id"] != item["id"]]
                    st.rerun()

    st.download_button(
        "Export wishlist",
        data=pd.DataFrame(ordered).drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="shopimpact-wishlist.csv",
        mime="text/csv",
        icon=":material/download:",
        key="download_wishlist",
        on_click="ignore",
    )


def _find_product(product_id: str) -> dict | None:
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def _product_impact(product: dict, quantity: int = 1) -> float:
    return round(float(product["price"]) * float(product["impact_factor"]) / 10 * quantity, 2)


def _render_catalog(purchases: list[dict]) -> None:
    st.markdown('<div class="si-kicker">Conscious marketplace</div>', unsafe_allow_html=True)
    st.title("Find things made to last.")
    st.caption("A curated demo catalog of repairable, reused, refillable, and thoughtfully sourced goods.")

    frame = _purchase_frame(purchases)
    profile = st.session_state.get("profile") or {}
    if frame.empty or not profile.get("personalization", True):
        preferred_category = None
    else:
        historical = frame.groupby("category")["co2"].sum().sort_values(ascending=False)
        preferred_category = str(historical.index[0]) if not historical.empty else None
    recommendations = [
        product for product in PRODUCTS
        if product["category"] == preferred_category
    ] if preferred_category else []
    if not recommendations:
        recommendations = sorted(PRODUCTS, key=lambda product: product["impact_factor"] / CATEGORIES[product["category"]]["factor"])
    st.markdown("**Picked for your impact profile**")
    st.caption(
        f"Based on your highest-footprint logged category ({preferred_category})"
        if preferred_category
        else (
            "Personalization is off; showing a starter mix of lower-impact picks."
            if profile and not profile.get("personalization", True)
            else "A starter mix of highly repairable and lower-impact picks. Recommendations run locally from catalog and ledger data."
        )
    )
    recommend_cols = st.columns(min(3, len(recommendations)))
    for index, product in enumerate(recommendations[:3]):
        with recommend_cols[index]:
            with st.container(border=True):
                st.markdown(f"**{html.escape(product['name'])}**")
                st.caption(product["tagline"])
                st.markdown(f"${product['price']:,.2f} · ~{_product_impact(product):.1f} kg CO2e")
                if st.button("View pick", key=f"recommend_{product['id']}", icon=":material/arrow_forward:"):
                    st.session_state.selected_product = product["id"]
                    st.session_state.catalog_search = product["name"]
                    st.rerun()

    st.markdown("### Browse the catalog")
    search_col, category_col, sort_col = st.columns([1.5, 1, 1])
    with search_col:
        search_term = st.text_input(
            "Search products",
            placeholder="Try refurbished, refill, cotton…",
            key="catalog_search",
        )
    with category_col:
        category_filter = st.selectbox(
            "Category", ["All categories", *CATEGORIES.keys()], key="catalog_category_filter"
        )
    with sort_col:
        sort_order = st.selectbox(
            "Sort by", ["Recommended", "Price: low to high", "Price: high to low", "Top rated"],
            key="catalog_sort",
        )
    max_price = st.slider(
        "Maximum price", min_value=0, max_value=800, value=800, step=10, format="$%d"
    )
    available_only = st.checkbox("Show in-stock items only", value=True, key="catalog_available")

    filtered = [
        product for product in PRODUCTS
        if product["price"] <= max_price
        and (category_filter == "All categories" or product["category"] == category_filter)
        and (not available_only or product["stock"] > 0)
        and (
            not search_term.strip()
            or search_term.strip().casefold() in " ".join(
                str(product[field]) for field in
                ("name", "brand", "category", "tagline", "description", "materials")
            ).casefold()
        )
    ]
    if sort_order == "Price: low to high":
        filtered.sort(key=lambda product: product["price"])
    elif sort_order == "Price: high to low":
        filtered.sort(key=lambda product: product["price"], reverse=True)
    elif sort_order == "Top rated":
        filtered.sort(key=lambda product: product["rating"], reverse=True)
    st.caption(f"{len(filtered)} product{'s' if len(filtered) != 1 else ''} found")

    if not filtered:
        st.info("No products match those filters. Try widening your search or price range.")
    else:
        for start in range(0, len(filtered), 3):
            cols = st.columns(3)
            for col, product in zip(cols, filtered[start : start + 3]):
                with col:
                    with st.container(border=True):
                        st.markdown(f"#### {html.escape(product['name'])}")
                        st.caption(f"{html.escape(product['brand'])} · {product['category']}")
                        st.markdown(f"**${product['price']:,.2f}**  ·  {product['rating']:.1f} ★ ({product['reviews']} reviews)")
                        st.markdown(product["tagline"])
                        st.caption(f"Estimated { _product_impact(product):.1f} kg CO2e · {product['repairability']}")
                        if st.button("Product details", key=f"product_{product['id']}", width="stretch"):
                            st.session_state.selected_product = product["id"]
                            st.rerun()

    selected = _find_product(str(st.session_state.get("selected_product", "")))
    if selected is not None:
        st.divider()
        st.markdown(f"## {html.escape(selected['name'])}")
        detail_cols = st.columns([1.2, 1])
        with detail_cols[0]:
            st.markdown(f"**{selected['brand']}** · {selected['rating']:.1f} ★ from {selected['reviews']} reviews")
            st.write(selected["description"])
            st.markdown(f"**Materials**  \n{selected['materials']}")
            st.markdown(f"**Care**  \n{selected['care']}")
            st.markdown(f"**Repairability**  \n{selected['repairability']}")
            st.caption(f"{selected['stock']} available in this demo catalog · Ships in 2–4 business days (illustrative)")
        with detail_cols[1]:
            conventional = calculate_impact(selected["category"], selected["price"])
            product_impact = _product_impact(selected)
            st.metric("Price", f"${selected['price']:,.2f}")
            st.metric("Estimated footprint", f"{product_impact:.1f} kg CO2e")
            st.metric(
                "Compared with category average",
                f"{max(0.0, conventional - product_impact):.1f} kg lower",
                help="Directional estimate based on a catalog factor versus ShopImpact's category-average factor, not an independently verified lifecycle assessment.",
            )
            add_quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=max(1, min(10, int(selected["stock"]))),
                value=1,
                disabled=selected["stock"] <= 0,
                key="product_quantity",
            )
            if st.button(
                "Add to cart",
                type="primary",
                icon=":material/add_shopping_cart:",
                disabled=selected["stock"] <= 0,
                key=f"add_cart_{selected['id']}",
            ):
                cart = st.session_state.setdefault("cart", {})
                cart[selected["id"]] = min(
                    int(cart.get(selected["id"], 0)) + int(add_quantity),
                    int(selected["stock"]),
                )
                st.toast(f"{selected['name']} added to your cart.", icon=":material/check_circle:")
                st.rerun()


def _cart_totals(cart: dict) -> dict:
    subtotal = sum(
        float(product["price"]) * int(quantity)
        for product_id, quantity in cart.items()
        if (product := _find_product(product_id)) is not None
    )
    shipping = 0.0 if subtotal == 0 or subtotal >= 75 else 4.95
    estimated_co2 = sum(
        _product_impact(product, int(quantity))
        for product_id, quantity in cart.items()
        if (product := _find_product(product_id)) is not None
    )
    return {
        "subtotal": round(subtotal, 2),
        "shipping": shipping,
        "total": round(subtotal + shipping, 2),
        "estimated_co2": round(estimated_co2, 2),
    }


def _render_cart() -> None:
    st.markdown('<div class="si-kicker">Your bag</div>', unsafe_allow_html=True)
    st.title("Your shopping cart")
    st.caption("Cart items stay available while this browser session is open. Demo checkout never charges a payment method.")
    cart = st.session_state.setdefault("cart", {})
    for product_id in list(cart):
        if _find_product(product_id) is None or int(cart[product_id]) <= 0:
            cart.pop(product_id, None)
    if not cart:
        st.info("Your cart is waiting for something useful and long-lasting.")
        st.button("Explore the catalog", icon=":material/storefront:", on_click=_navigate_to, args=("Discover",), key="cart_discover")
        return

    for product_id, quantity in list(cart.items()):
        product = _find_product(product_id)
        if product is None:
            continue
        with st.container(border=True):
            name_col, price_col, quantity_col, remove_col = st.columns([2.2, 1, 1.2, 0.7])
            with name_col:
                st.markdown(f"**{html.escape(product['name'])}**")
                st.caption(f"{product['brand']} · {product['category']}")
            with price_col:
                st.markdown(f"${product['price'] * quantity:,.2f}")
                st.caption(f"${product['price']:,.2f} each")
            with quantity_col:
                minus_col, count_col, plus_col = st.columns([1, 1, 1])
                with minus_col:
                    if st.button("−", key=f"cart_minus_{product_id}", disabled=quantity <= 1):
                        cart[product_id] = quantity - 1
                        st.rerun()
                with count_col:
                    st.markdown(f"<div class='si-qty'>{quantity}</div>", unsafe_allow_html=True)
                with plus_col:
                    if st.button("+", key=f"cart_plus_{product_id}", disabled=quantity >= product["stock"]):
                        cart[product_id] = quantity + 1
                        st.rerun()
            with remove_col:
                if st.button("Remove", key=f"cart_remove_{product_id}", icon=":material/delete_outline:"):
                    cart.pop(product_id, None)
                    st.rerun()

    totals = _cart_totals(cart)
    summary_col, action_col = st.columns([1, 1])
    with summary_col:
        with st.container(border=True):
            st.markdown("### Order summary")
            st.markdown(f"Subtotal  ·  **${totals['subtotal']:,.2f}**")
            st.markdown(f"Demo shipping  ·  **{'Free' if totals['shipping'] == 0 else f'${totals['shipping']:.2f}'}**")
            st.markdown(f"Estimated total  ·  **${totals['total']:,.2f}**")
            st.caption(
                f"Estimated impact: {totals['estimated_co2']:.1f} kg CO2e. "
                f"Free illustrative shipping over $75; ${max(0, 75 - totals['subtotal']):,.2f} away."
            )
    with action_col:
        st.markdown("### Ready when you are")
        if not st.session_state.get("profile"):
            st.info("Set up a local demo profile before checkout.")
            st.button("Set up profile", type="primary", on_click=_navigate_to, args=("Profile",), key="cart_profile")
        else:
            st.caption("Fast demo checkout · no card number collected · no real order or payment is sent.")
            with st.form("demo_checkout", border=True):
                city = st.text_input("Delivery city", key="checkout_city")
                postal_code = st.text_input("Postal code", key="checkout_postal")
                payment_method = st.selectbox(
                    "Demo payment method",
                    ["Demo card (not charged)", "Demo wallet (not connected)", "Pay on delivery (simulation)"],
                )
                confirm_order = st.checkbox("I understand this is a non-binding demo order.")
                submitted = st.form_submit_button(
                    "Place demo order", type="primary", icon=":material/lock_open:"
                )
            if submitted:
                if not city.strip() or not postal_code.strip():
                    st.error("Enter a city and postal code to complete this demo checkout.")
                elif not confirm_order:
                    st.error("Confirm that you understand this checkout is only a simulation.")
                else:
                    order_id = f"SI-{date.today():%y%m%d}-{uuid4().hex[:6].upper()}"
                    order_items = []
                    purchases = st.session_state.setdefault("purchases", [])
                    for product_id, quantity in list(cart.items()):
                        product = _find_product(product_id)
                        if product is None:
                            continue
                        quantity = int(quantity)
                        line_co2 = _product_impact(product, quantity)
                        line_total = round(product["price"] * quantity, 2)
                        order_items.append({
                            "line_id": str(uuid4()),
                            "product_id": product_id,
                            "product": product["name"],
                            "brand": product["brand"],
                            "category": product["category"],
                            "quantity": quantity,
                            "unit_price": product["price"],
                            "line_total": line_total,
                            "co2": line_co2,
                        })
                        green_savings = max(
                            0.0,
                            (CATEGORIES[product["category"]]["factor"] - product["impact_factor"])
                            * product["price"] * quantity / 10,
                        )
                        purchases.append(_new_purchase(
                            product["name"] + (f" (x{quantity})" if quantity > 1 else ""),
                            product["category"],
                            product["brand"],
                            line_total,
                            date.today(),
                            green_savings,
                            line_co2,
                        ))
                    order = {
                        "id": order_id,
                        "created_on": date.today().isoformat(),
                        "status": "Order placed (demo)",
                        "status_index": 0,
                        "city": city.strip(),
                        "postal_code": postal_code.strip(),
                        "payment_method": payment_method,
                        "items": order_items,
                        **totals,
                    }
                    st.session_state.setdefault("orders", []).insert(0, order)
                    st.session_state.cart = {}
                    st.session_state.pending_view = "My orders"
                    st.toast("Demo order placed; no payment was processed.", icon=":material/check_circle:")
                    st.rerun()


def _render_profile() -> None:
    st.markdown('<div class="si-kicker">Your local profile</div>', unsafe_allow_html=True)
    st.title("Make this space yours.")
    st.caption("No password or payment details are stored. This profile lives in the current Streamlit session only; it is not a real account.")
    profile = st.session_state.get("profile")
    if profile:
        st.success(f"Welcome, {html.escape(profile['name'])}. Your demo profile is active for this session.")
    with st.form("profile_form", border=True):
        name = st.text_input("Your name", value=profile.get("name", "") if profile else "")
        email = st.text_input("Email for your demo order summary", value=profile.get("email", "") if profile else "")
        personalization = st.checkbox(
            "Use my purchase history to personalize local recommendations",
            value=profile.get("personalization", True) if profile else True,
        )
        submitted = st.form_submit_button(
            "Save local profile" if not profile else "Update profile",
            type="primary",
            icon=":material/person:",
        )
    if submitted:
        clean_email = email.strip()
        if not name.strip():
            st.error("Please enter your name.")
        elif "@" not in clean_email or "." not in clean_email.rsplit("@", 1)[-1]:
            st.error("Enter a valid email address.")
        else:
            st.session_state.profile = {
                "name": name.strip(),
                "email": clean_email,
                "personalization": personalization,
            }
            st.toast("Your local profile is ready.", icon=":material/check_circle:")
            st.rerun()
    if profile and st.button("Remove local profile", icon=":material/logout:"):
        st.session_state.profile = None
        st.rerun()


def _render_orders() -> None:
    st.markdown('<div class="si-kicker">Order desk</div>', unsafe_allow_html=True)
    st.title("Orders & tracking")
    st.caption("All orders here are local demo records. No warehouse, carrier, or payment provider is connected.")
    orders = st.session_state.setdefault("orders", [])
    if not orders:
        st.info("Your order desk is clear. Your cart and wishlist are ready whenever you are.")
        st.button("Browse products", icon=":material/storefront:", on_click=_navigate_to, args=("Discover",), key="orders_discover")
        return
    stages = ["Order placed", "Preparing", "In transit", "Delivered"]
    for order in orders:
        with st.container(border=True):
            order_id = str(order.get("id", "SI-demo"))
            header_cols = st.columns([2, 1])
            with header_cols[0]:
                st.markdown(f"### {order_id}")
                st.caption(f"Placed {order.get('created_on', '')} · {order.get('city', '')} {order.get('postal_code', '')}")
            with header_cols[1]:
                st.metric("Demo status", stages[min(int(order.get("status_index", 0)), len(stages) - 1)])
            status_index = min(int(order.get("status_index", 0)), len(stages) - 1)
            st.progress(status_index / (len(stages) - 1), text="Illustrative demo tracking timeline · not a live shipment")
            st.caption("  →  ".join(
                f"**{stage}**" if index == status_index else stage
                for index, stage in enumerate(stages)
            ))
            items = order.get("items", [])
            if items:
                st.dataframe(
                    pd.DataFrame(items)[["product", "quantity", "line_total", "co2"]].rename(
                        columns={"product": "Product", "quantity": "Qty", "line_total": "Total", "co2": "Est. kg CO2e"}
                    ),
                    hide_index=True,
                    column_config={
                        "Total": st.column_config.NumberColumn("Total", format="$%.2f"),
                        "Est. kg CO2e": st.column_config.NumberColumn("Est. kg CO2e", format="%.2f kg"),
                    },
                    alt=f"Items in demo order {order_id}",
                )
            total_col, action_col = st.columns([1, 2])
            with total_col:
                st.markdown(f"**Demo total: ${float(order.get('total', 0)):,.2f}**")
            with action_col:
                next_stage = status_index + 1
                if next_stage < len(stages) and st.button(
                    f"Advance demo to {stages[next_stage].lower()}",
                    key=f"advance_order_{order_id}",
                    icon=":material/fast_forward:",
                ):
                    order["status_index"] = next_stage
                    order["status"] = f"{stages[next_stage]} (demo)"
                    st.rerun()


def _render_help_and_returns() -> None:
    st.markdown('<div class="si-kicker">Help & care</div>', unsafe_allow_html=True)
    st.title("Here for the whole journey.")
    st.caption("Returns and customer-care requests are recorded locally for this demo. They are not sent to a retailer or support team.")
    returns_tab, support_tab = st.tabs(["Returns & exchanges", "Customer support"])
    with returns_tab:
        orders = st.session_state.setdefault("orders", [])
        returnable = [order for order in orders if order.get("items")]
        if not returnable:
            st.info("A demo order with items will appear here if you want to try the self-service return flow.")
        else:
            with st.form("return_form", border=True):
                order_id = st.selectbox(
                    "Choose an order",
                    [str(order["id"]) for order in returnable],
                )
                selected_order = next(order for order in returnable if str(order["id"]) == order_id)
                selected_item_id = st.selectbox(
                    "Choose an item",
                    [item["line_id"] for item in selected_order["items"]],
                    format_func=lambda line_id: next(
                        item["product"] for item in selected_order["items"] if item["line_id"] == line_id
                    ),
                )
                resolution = st.radio("What would you prefer?", ["Return", "Exchange"], horizontal=True)
                reason = st.selectbox(
                    "Reason",
                    ["Not as expected", "Arrived damaged (demo)", "Wrong size or fit", "Changed my mind", "Other"],
                )
                note = st.text_input("Anything else to add? (optional)")
                submitted = st.form_submit_button("Create demo request", type="primary", icon=":material/assignment_return:")
            if submitted:
                request_id = f"RET-{uuid4().hex[:6].upper()}"
                st.session_state.setdefault("return_requests", []).append({
                    "id": request_id,
                    "order_id": order_id,
                    "line_id": selected_item_id,
                    "resolution": resolution,
                    "reason": reason,
                    "note": note.strip(),
                    "created_on": date.today().isoformat(),
                    "status": "Request saved in this session (demo)",
                })
                st.success(f"Demo request {request_id} saved. It has not been sent to a retailer.")
        for request in st.session_state.setdefault("return_requests", []):
            st.caption(
                f"{request['id']} · Order {request['order_id']} · {request['resolution']} · "
                f"{request['reason']} · {request['status']}"
            )
    with support_tab:
        profile = st.session_state.get("profile") or {}
        with st.form("support_form", border=True):
            contact = st.text_input("Reply-to email", value=profile.get("email", ""))
            topic = st.selectbox(
                "What can we help with?",
                ["Product question", "Order or delivery", "Returns and exchanges", "Impact estimate", "Something else"],
            )
            message = st.text_area("Tell us a little more", max_chars=1500)
            submitted = st.form_submit_button("Save demo support request", type="primary", icon=":material/support_agent:")
        if submitted:
            if "@" not in contact.strip():
                st.error("Add a reply-to email address.")
            elif len(message.strip()) < 10:
                st.error("Please add a little more detail (at least 10 characters).")
            else:
                ticket_id = f"HELP-{uuid4().hex[:6].upper()}"
                st.session_state.setdefault("support_requests", []).append({
                    "id": ticket_id,
                    "email": contact.strip(),
                    "topic": topic,
                    "message": message.strip(),
                    "created_on": date.today().isoformat(),
                    "status": "Saved locally (demo)",
                })
                st.success(f"Demo support request {ticket_id} saved. No support team was contacted.")
        for request in st.session_state.setdefault("support_requests", []):
            st.caption(f"{request['id']} · {request['topic']} · {request['status']}")


def _render_overview(
    purchases: list[dict],
    dark_mode: bool,
    monthly_budget: float,
    monthly_target: float,
) -> None:
    today = date.today()
    frame = _purchase_frame(purchases)
    month_frame = _monthly_frame(purchases, today)
    spend = float(month_frame["price"].sum()) if not month_frame.empty else 0.0
    month_co2 = float(month_frame["co2"].sum()) if not month_frame.empty else 0.0
    green_choices = int(month_frame["category"].map(lambda category: CATEGORIES.get(category, {}).get("factor", 99) <= LOW_IMPACT_FACTOR).sum()) if not month_frame.empty else 0
    eco_score = round(max(0, min(100, 65 * (1 - min(month_co2 / monthly_target, 1)) + 35 * (green_choices / len(month_frame) if not month_frame.empty else 0))))
    total_co2 = float(frame["co2"].sum()) if not frame.empty else 0.0

    art_col, intro_col = st.columns([1.03, 1], vertical_alignment="center")
    with art_col:
        st.image(draw_shopping_illustration(), alt="Illustration of a reusable shopping bag with leafy produce and a refill bottle", width="stretch")
    with intro_col:
        st.markdown('<div class="si-kicker">Your conscious shopping dashboard</div>', unsafe_allow_html=True)
        st.markdown("# Small choices. Real momentum.")
        st.markdown("Your everyday shopping, made easier to understand and better to improve.")
        st.caption(f"{today.strftime('%A, %B %d')}  ·  {len(purchases)} purchase{'s' if len(purchases) != 1 else ''} tracked")
        cta_left, cta_right = st.columns(2)
        cta_left.button("Log a purchase", type="primary", icon=":material/add_shopping_cart:", on_click=_navigate_to, args=("Log purchase",), key="overview_log", width="stretch")
        cta_right.button("Browse mindful picks", icon=":material/storefront:", on_click=_navigate_to, args=("Discover",), key="overview_discover", width="stretch")
        cta_left.button("Find a better swap", icon=":material/compare_arrows:", on_click=_navigate_to, args=("Swap studio",), key="overview_swap", width="stretch")
        cta_right.button("Open wishlist", icon=":material/bookmark:", on_click=_navigate_to, args=("Wishlist",), key="overview_wishlist", width="stretch")

    st.markdown('<div class="si-section-label">This month at a glance</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Shopping spend", f"${spend:,.2f}", delta=f"of ${monthly_budget:,.0f} budget", border=True)
    metric_cols[1].metric("Footprint", f"{month_co2:.1f} kg", delta=f"{monthly_target:.0f} kg goal", border=True)
    metric_cols[2].metric("Lower-impact picks", f"{green_choices}", delta=f"of {len(month_frame)} this month", border=True)
    metric_cols[3].metric("Eco score", f"{eco_score}/100", delta=f"{total_co2:.1f} kg all-time", border=True)

    goal_cols = st.columns(2)
    goal_cols[0].progress(min(spend / monthly_budget, 1.0), text=f"Spend plan · ${spend:,.2f} of ${monthly_budget:,.0f}")
    goal_cols[1].progress(min(month_co2 / monthly_target, 1.0), text=f"Carbon goal · {month_co2:.1f} of {monthly_target:.0f} kg CO2e")
    if spend >= monthly_budget:
        st.warning("You have reached this month's shopping budget. Review the basket before your next checkout.")
    elif spend >= monthly_budget * 0.8:
        st.info("You're close to your monthly shopping budget. Keep an eye on the remaining spend.")
    if month_co2 >= monthly_target:
        st.warning("Your estimated footprint is over this month's goal. The swap studio can help compare lower-impact options.")

    left, right = st.columns([1.35, 1])
    with left:
        with st.container(border=True):
            st.markdown("**Your six-month footprint**")
            months = pd.date_range(end=today.replace(day=1), periods=6, freq="MS")
            if frame.empty:
                chart_frame = pd.DataFrame({"Month": months, "kg CO2e": [0.0] * len(months)})
            else:
                month_totals = frame.assign(month=frame["date"].dt.to_period("M").dt.to_timestamp()).groupby("month")["co2"].sum()
                chart_frame = pd.DataFrame({"Month": months})
                chart_frame["kg CO2e"] = chart_frame["Month"].map(month_totals).fillna(0.0)
            chart = px.area(chart_frame, x="Month", y="kg CO2e", markers=True, color_discrete_sequence=["#059669"])
            chart.update_layout(**_plot_layout(dark_mode), height=260, showlegend=False)
            chart.update_traces(line={"width": 3}, fillcolor="rgba(16,185,129,.16)")
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False}, alt="Six-month estimated purchase emissions trend")
    with right:
        with st.container(border=True):
            st.markdown("**Your recent activity**")
            if frame.empty:
                st.markdown("Your ledger is ready when you are.")
                st.button("Add your first purchase", icon=":material/add:", on_click=_navigate_to, args=("Log purchase",), key="empty_log")
            else:
                recent = frame.sort_values("date", ascending=False).head(4).copy()
                recent["date"] = recent["date"].dt.strftime("%b %d")
                recent = recent.rename(columns={"date": "Date", "product": "Item", "category": "Category", "price": "Spend"})
                st.dataframe(
                    recent[["Date", "Item", "Category", "Spend"]],
                    hide_index=True,
                    column_config={"Spend": st.column_config.NumberColumn("Spend", format="$%.2f")},
                    alt="Four most recent purchases",
                )
                st.button("View all purchases", icon=":material/receipt_long:", on_click=_navigate_to, args=("Log purchase",), key="overview_history")


def _render_swap_studio() -> None:
    st.markdown('<div class="si-kicker">Swap studio</div>', unsafe_allow_html=True)
    st.title("Keep the thing. Lower the impact.")
    st.caption("Compare a conventional purchase with repair, refill, certified, and pre-loved alternatives.")

    with st.container(border=True):
        left, right = st.columns([1.15, 0.85])
        with left:
            product = st.text_input("What are you shopping for?", placeholder="e.g. everyday headphones", key="swap_product")
            category = st.selectbox("Current category", list(CATEGORIES), index=0, key="swap_category")
        with right:
            price = st.number_input("Expected spend ($)", min_value=1.0, max_value=100000.0, value=80.0, step=5.0, key="swap_price")
            quantity = st.number_input("Quantity", min_value=1, max_value=50, value=1, step=1, key="swap_quantity")
            st.caption("Estimates use category-average emissions per $10 spent.")

    alternatives = get_alternatives(category, price, force=True)
    current_co2 = calculate_impact(category, price)
    lower_factor = min(LOW_IMPACT_FACTOR, CATEGORIES[category]["factor"])
    alternative_co2 = round(lower_factor * price / 10, 2)
    saved = max(0.0, round(current_co2 - alternative_co2, 2))

    st.markdown("### Your comparison")
    compare_cols = st.columns(3)
    compare_cols[0].metric("Typical new purchase", f"{current_co2:.1f} kg CO2e", delta=CATEGORIES[category]["level"] + " impact", border=True)
    compare_cols[1].metric("Lower-impact option", f"{alternative_co2:.1f} kg CO2e", delta="repair / refill / resale estimate", border=True)
    compare_cols[2].metric("Potential reduction", f"{saved:.1f} kg CO2e", delta=f"{saved / CAR_EMISSIONS_KG_PER_MILE:.0f} car miles equivalent", border=True)
    if st.button("Add this scenario to the basket", icon=":material/add_shopping_cart:", key="add_comparison_item"):
        st.session_state.setdefault("comparison_basket", []).append(
            {
                "id": str(uuid4()),
                "product": product.strip() or category,
                "category": category,
                "quantity": int(quantity),
                "price": float(price),
                "current_co2": round(current_co2 * quantity, 2),
                "alternative_co2": round(alternative_co2 * quantity, 2),
                "saved_kg": round(saved * quantity, 2),
            }
        )
        st.toast("Added to your comparison basket.", icon=":material/check_circle:")

    comparison_basket = st.session_state.setdefault("comparison_basket", [])
    if comparison_basket:
        st.markdown("### Basket impact preview")
        basket_current = sum(item["current_co2"] for item in comparison_basket)
        basket_alternative = sum(item["alternative_co2"] for item in comparison_basket)
        basket_saved = sum(item["saved_kg"] for item in comparison_basket)
        basket_cols = st.columns(3)
        basket_cols[0].metric("Basket as planned", f"{basket_current:.1f} kg CO2e", border=True)
        basket_cols[1].metric("Basket with swaps", f"{basket_alternative:.1f} kg CO2e", border=True)
        basket_cols[2].metric("Potential basket reduction", f"{basket_saved:.1f} kg CO2e", border=True)
        basket_view = pd.DataFrame(comparison_basket).drop(columns=["id", "current_co2", "alternative_co2"])
        st.dataframe(basket_view, hide_index=True, alt="Items in the impact comparison basket")
        remove_basket_id = st.selectbox(
            "Remove a basket item",
            [item["id"] for item in comparison_basket],
            format_func=lambda item_id: next(item["product"] for item in comparison_basket if item["id"] == item_id),
            key="remove_basket_id",
        )
        if st.button("Remove from basket", icon=":material/remove_shopping_cart:", key="remove_basket_item"):
            st.session_state.comparison_basket = [item for item in comparison_basket if item["id"] != remove_basket_id]
            st.rerun()

    st.markdown("### Places to start")
    cols = st.columns(3)
    for index, option in enumerate(alternatives):
        with cols[index]:
            with st.container(border=True):
                st.markdown(f"**{option['brand']}**")
                st.caption(option["reason"])
                st.metric("Estimated at this price", f"{alternative_co2:.1f} kg", delta=f"up to {saved:.1f} kg less")
                saved_swaps = st.session_state.setdefault("saved_swaps", [])
                already_saved = any(item.get("brand") == option["brand"] and item.get("category") == category and item.get("product") == product for item in saved_swaps)
                if st.button("Saved" if already_saved else "Save this swap", key=f"save_swap_{index}_{option['brand']}", icon=":material/bookmark:", disabled=already_saved):
                    saved_swaps.append({"product": product.strip() or "Shopping idea", "category": category, "brand": option["brand"], "budget": float(price), "estimated_co2": alternative_co2, "saved_kg": saved})
                    st.toast(f"{option['brand']} added to your shortlist.", icon=":material/bookmark_added:")

    st.markdown("### Your saved swaps")
    saved_swaps = st.session_state.setdefault("saved_swaps", [])
    if not saved_swaps:
        st.caption("Save an option above to build a personal shortlist.")
    else:
        st.dataframe(pd.DataFrame(saved_swaps), hide_index=True, alt="Your saved lower-impact shopping alternatives")
        st.download_button("Download shortlist", data=pd.DataFrame(saved_swaps).to_csv(index=False), file_name="shopimpact-swap-shortlist.csv", mime="text/csv", icon=":material/download:", on_click="ignore")
        if st.button("Clear shortlist", icon=":material/delete_sweep:", key="clear_swaps"):
            st.session_state.saved_swaps = []
            st.rerun()


def _render_swap(purchase: dict) -> None:
    suggestions = get_alternatives(
        str(purchase.get("category", "")),
        float(purchase.get("price", 0)),
        str(purchase.get("brand", "")),
    )
    if not suggestions:
        return
    names = ", ".join(html.escape(option["brand"]) for option in suggestions)
    saved = max(option["estimated_savings"] for option in suggestions)
    st.markdown(
        f"""
        <div class="si-swap">
          <strong>Quick-swap idea for {html.escape(str(purchase.get('product', 'your item')))}</strong><br>
          Next time, explore {names}. A similar-price lower-impact choice could save about
          <strong>{saved:.1f} kg CO2e</strong> by this category estimate.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_purchase_view(purchases: list[dict], dark_mode: bool) -> None:
    st.subheader("Log a purchase", anchor=False)
    st.caption("A quick estimate today makes your next choice easier to compare.")

    with st.expander("Import an existing purchase log", icon=":material/upload_file:"):
        st.caption("CSV columns: product, category, price. Optional columns: date, brand. CO2e is recalculated using ShopImpact category factors.")
        template = pd.DataFrame(columns=["date", "product", "category", "brand", "price"])
        st.download_button("Get CSV template", data=template.to_csv(index=False), file_name="shopimpact-import-template.csv", mime="text/csv", icon=":material/download:", key="download_import_template", on_click="ignore")
        uploaded_file = st.file_uploader("Choose a purchase CSV", type=["csv"], key="purchase_csv_upload")
        if uploaded_file is not None and st.button("Validate and import", icon=":material/fact_check:", key="import_purchases"):
            imported, issues = _parse_purchase_csv(uploaded_file)
            if imported:
                st.session_state.purchases.extend(imported)
                st.toast(f"Imported {len(imported)} purchase(s).", icon=":material/check_circle:")
            if issues:
                st.warning("Some rows were skipped: " + " ".join(issues[:5]))
            if not imported and not issues:
                st.info("This CSV contains no purchase rows to import.")

    templates = [
        ("Organic pantry", "Seasonal produce box", "Groceries / organic food", "Local co-op", 24.0),
        ("Pre-loved find", "Second-hand jacket", "Sustainable apparel / second-hand", "Vinted", 42.0),
        ("Refill care", "Refill hand wash", "Beauty & personal care", "Ethique", 18.0),
    ]
    with st.container(horizontal=True):
        for index, template in enumerate(templates):
            if st.button(template[0], key=f"template_{index}", icon=":material/add_shopping_cart:"):
                st.session_state.log_product = template[1]
                st.session_state.log_category = template[2]
                st.session_state.log_brand = template[3]
                st.session_state.log_price = template[4]

    st.session_state.setdefault("log_product", "")
    st.session_state.setdefault("log_category", "Groceries / organic food")
    st.session_state.setdefault("log_brand", "")
    st.session_state.setdefault("log_price", 25.0)
    st.session_state.setdefault("log_date", date.today())
    st.session_state.setdefault("log_green_choice", False)

    with st.form("purchase_form", border=True, clear_on_submit=False):
        product = st.text_input("Product", key="log_product", placeholder="e.g. Oat milk or wireless headphones")
        category = st.selectbox("Category", list(CATEGORIES), key="log_category")
        col_brand, col_price, col_date = st.columns([1.2, 0.8, 0.9])
        with col_brand:
            brand = st.text_input("Brand or shop", key="log_brand", placeholder="Optional")
        with col_price:
            price = st.number_input("Price ($)", min_value=0.01, max_value=100000.0, step=1.0, key="log_price")
        with col_date:
            purchased_on = st.date_input("Purchase date", key="log_date", max_value=date.today())
        greener_choice = st.checkbox(
            "I chose a greener alternative",
            key="log_green_choice",
            help="Adds a directional estimate to your greener-choice savings total.",
        )
        submitted = st.form_submit_button(
            "Add to my impact log", type="primary", icon=":material/add_circle:"
        )

    estimated_co2 = calculate_impact(category, price)
    impact_color = "#EF4444" if CATEGORIES[category]["level"] == "High" else "#F59E0B" if CATEGORIES[category]["level"] == "Medium" else "#059669"
    st.markdown(
        f"<span class='si-muted'>Estimate preview:</span> <strong>{estimated_co2:.2f} kg CO2e</strong> "
        f"<span style='color:{impact_color};font-weight:700'>· {CATEGORIES[category]['level']} impact</span>",
        unsafe_allow_html=True,
    )

    if submitted:
        if not product.strip():
            st.error("Add a product name before saving this purchase.")
        elif purchased_on > date.today():
            st.error("Purchase date cannot be in the future.")
        else:
            green_savings = (
                max(0.0, (CATEGORIES[category]["factor"] - LOW_IMPACT_FACTOR) * float(price) / 10)
                if greener_choice
                else 0.0
            )
            purchase = _new_purchase(product, category, brand, price, purchased_on, green_savings)
            st.session_state.purchases.append(purchase)
            st.session_state.last_added_id = purchase["id"]
            st.toast(f"{product.strip()} added to your impact log.", icon=":material/check_circle:")

    last_id = st.session_state.get("last_added_id")
    last_purchase = next((item for item in reversed(purchases) if item.get("id") == last_id), None)
    if last_purchase:
        _render_swap(last_purchase)

    st.subheader("Recent purchases", anchor=False)
    frame = _purchase_frame(purchases)
    if frame.empty:
        st.markdown("Your ledger is ready. Add an item above or load demo data from the sidebar.")
        return

    st.markdown("**Purchase history**")
    filter_cols = st.columns([1.2, 1, 0.9])
    with filter_cols[0]:
        search_term = st.text_input("Search purchases", placeholder="Product or brand", key="history_search")
    with filter_cols[1]:
        category_filter = st.selectbox("Category filter", ["All categories", *list(CATEGORIES)], key="history_category")
    with filter_cols[2]:
        sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Highest footprint", "Highest spend"], key="history_sort")

    filtered = frame.copy()
    if search_term.strip():
        match = filtered["product"].str.contains(search_term.strip(), case=False, na=False) | filtered["brand"].str.contains(search_term.strip(), case=False, na=False)
        filtered = filtered[match]
    if category_filter != "All categories":
        filtered = filtered[filtered["category"] == category_filter]
    sort_config = {
        "Newest first": ("date", False),
        "Oldest first": ("date", True),
        "Highest footprint": ("co2", False),
        "Highest spend": ("price", False),
    }
    sort_column, ascending = sort_config[sort_order]
    filtered = filtered.sort_values(sort_column, ascending=ascending)
    if filtered.empty:
        st.caption("No purchases match those filters.")
        return

    display = filtered.head(20).copy()
    display["date"] = display["date"].dt.strftime("%b %d, %Y")
    display = display.rename(
        columns={"date": "Date", "product": "Product", "category": "Category", "brand": "Brand", "price": "Spend", "co2": "CO2e (kg)", "impact_level": "Impact"}
    )
    st.dataframe(
        display[["Date", "Product", "Category", "Brand", "Spend", "CO2e (kg)", "Impact"]],
        hide_index=True,
        column_config={
            "Spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
            "CO2e (kg)": st.column_config.NumberColumn("CO2e (kg)", format="%.2f kg"),
        },
        alt="Most recent purchases with category, spend, and estimated emissions",
    )
    remove_col, remove_action_col = st.columns([1.5, 1])
    with remove_col:
        remove_id = st.selectbox(
            "Remove a purchase",
            filtered["id"].tolist(),
            format_func=lambda purchase_id: next(
                f"{row.product} · {row.date:%b %d} · ${row.price:.2f}"
                for row in filtered.itertuples()
                if row.id == purchase_id
            ),
            key="remove_purchase_id",
        )
    with remove_action_col:
        st.write("")
        if st.button("Remove selected", icon=":material/delete_outline:", key="remove_purchase"):
            st.session_state.purchases = [item for item in purchases if item.get("id") != remove_id]
            if st.session_state.get("last_added_id") == remove_id:
                st.session_state.last_added_id = None
            st.rerun()
    csv_data = frame.drop(columns=["green_savings"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export purchase log",
        data=csv_data,
        file_name="shopimpact-purchases.csv",
        mime="text/csv",
        icon=":material/download:",
        key="download_purchases",
        on_click="ignore",
    )


def _impact_opportunities(frame: pd.DataFrame) -> pd.DataFrame:
    """Rank categories by historical footprint and same-spend swap potential."""
    opportunities = frame.groupby("category", as_index=False).agg(
        Purchases=("id", "count"),
        Spend=("price", "sum"),
        **{"Estimated impact (kg)": ("co2", "sum")},
    )
    opportunities["Same-spend reduction (kg)"] = opportunities.apply(
        lambda row: max(
            0.0,
            (CATEGORIES[row["category"]]["factor"] - LOW_IMPACT_FACTOR)
            * row["Spend"]
            / 10,
        ),
        axis=1,
    ).round(1)
    opportunities["Next step"] = opportunities["category"].map(
        {
            "Electronics": "Repair or refurbished",
            "Fast fashion / leather": "Repair, resale, or certified",
            "Groceries / organic food": "Local, seasonal, less waste",
            "Sustainable apparel / second-hand": "Wear longer, repair, resale",
            "Beauty & personal care": "Refill or concentrate",
            "Home & living": "Vintage, repair, or refill",
        }
    )
    return opportunities.sort_values("Estimated impact (kg)", ascending=False)


def _open_swap_plan(category: str, price: float) -> None:
    st.session_state["swap_category"] = category
    st.session_state["swap_price"] = max(1.0, round(float(price), 2))
    st.session_state["swap_product"] = f"{category} purchase"
    st.session_state["view"] = "Swap studio"


def _render_analytics(
    purchases: list[dict],
    dark_mode: bool,
    monthly_target: float = MONTHLY_CO2_TARGET,
    monthly_budget: float = 600.0,
) -> None:
    today = date.today()
    frame = _purchase_frame(purchases)
    month_start = today.replace(day=1)
    month_rows = frame[(frame["date"].dt.year == today.year) & (frame["date"].dt.month == today.month)] if not frame.empty else frame
    month_spend = float(month_rows["price"].sum()) if not month_rows.empty else 0.0
    month_co2 = float(month_rows["co2"].sum()) if not month_rows.empty else 0.0
    previous_month_end = month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    comparable_end = previous_month_start + timedelta(days=min(today.day, previous_month_end.day) - 1)
    previous_rows = frame[(frame["date"] >= pd.Timestamp(previous_month_start)) & (frame["date"] <= pd.Timestamp(comparable_end))] if not frame.empty else frame
    previous_spend = float(previous_rows["price"].sum()) if not previous_rows.empty else 0.0
    previous_co2 = float(previous_rows["co2"].sum()) if not previous_rows.empty else 0.0
    total_co2 = float(frame["co2"].sum()) if not frame.empty else 0.0
    total_spend = float(frame["price"].sum()) if not frame.empty else 0.0
    month_green_count = int(month_rows["category"].map(lambda category: CATEGORIES.get(category, {}).get("factor", 99) <= LOW_IMPACT_FACTOR).sum()) if not month_rows.empty else 0
    green_share = month_green_count / len(month_rows) if not month_rows.empty else 0.0
    eco_score = round(max(0, min(100, 65 * (1 - min(month_co2 / monthly_target, 1)) + 35 * green_share)))
    trees = total_co2 / TREE_ABSORPTION_KG_PER_YEAR
    green_savings = float(month_rows["green_savings"].sum()) if not month_rows.empty else 0.0
    avoided_miles = green_savings / CAR_EMISSIONS_KG_PER_MILE

    st.subheader("Your impact, at a glance", anchor=False)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total spend", f"${total_spend:,.2f}", delta=f"${month_spend:,.2f} this month", border=True)
    metric_cols[1].metric("Estimated footprint", f"{total_co2:,.1f} kg", delta=f"{month_co2:.1f} kg this month", border=True)
    metric_cols[2].metric("Tree-years to offset", f"{trees:.2f}", help="Uses 21.77 kg CO2e absorbed per tree-year as a simple reference.", border=True)
    metric_cols[3].metric(
        "Eco score",
        f"{eco_score}/100",
        delta="Monthly footprint + low-impact mix",
        help="65% is progress against your monthly carbon goal; 35% is the share of this month's purchases in low-impact categories.",
        border=True,
    )

    st.markdown("**Compared with the same days last month**")
    comparison_cols = st.columns(2)
    comparison_cols[0].metric("Spend month-to-date", f"${month_spend:,.2f}", delta=f"${month_spend - previous_spend:+,.2f} vs ${previous_spend:,.2f}", delta_color="inverse", border=True)
    comparison_cols[1].metric("Footprint month-to-date", f"{month_co2:.1f} kg", delta=f"{month_co2 - previous_co2:+.1f} kg vs {previous_co2:.1f} kg", delta_color="inverse", border=True)

    forecast = _month_end_forecast(month_co2, today, monthly_target)
    st.markdown("**Month-end pace check**")
    pace_cols = st.columns(3)
    pace_cols[0].metric("Projected footprint", f"{forecast['projected_co2']:.1f} kg", delta=f"{forecast['projected_co2'] - monthly_target:+.1f} kg vs goal", delta_color="inverse", border=True)
    pace_cols[1].metric("Goal remaining", f"{forecast['remaining_target']:.1f} kg", border=True)
    pace_cols[2].metric("Daily allowance", f"{forecast['daily_allowance']:.2f} kg", delta=f"{forecast['days_remaining']} days left", border=True)
    st.caption("Month-end projection extends your average daily emissions so far across the full month; it is a pacing signal, not a product-level prediction.")

    spend_forecast = _month_end_spend_forecast(month_spend, today, monthly_budget)
    st.markdown("**Shopping budget pace**")
    budget_cols = st.columns(3)
    budget_cols[0].metric("Projected month-end spend", f"${spend_forecast['projected_spend']:,.2f}", delta=f"${spend_forecast['projected_spend'] - monthly_budget:+,.2f} vs budget", delta_color="inverse", border=True)
    budget_cols[1].metric("Budget remaining", f"${spend_forecast['remaining_budget']:,.2f}", border=True)
    budget_cols[2].metric("Daily spend allowance", f"${spend_forecast['daily_allowance']:,.2f}", delta=f"{spend_forecast['days_remaining']} days left", border=True)

    offset_cols = st.columns(2)
    offset_cols[0].progress(min(month_co2 / monthly_target, 1.0), text=f"Monthly target: {month_co2:.1f} / {monthly_target:.0f} kg CO2e")
    offset_cols[1].caption(f"Your recorded greener-choice savings equate to about **{avoided_miles:.0f} car miles** at 0.404 kg CO2e per mile.")

    chart_cols = st.columns([1.45, 1])
    with chart_cols[0]:
        with st.container(border=True):
            st.markdown("**Footprint over time**")
            months = pd.date_range(end=month_start, periods=6, freq="MS")
            if frame.empty:
                monthly = pd.DataFrame({"Month": months, "Estimated CO2e (kg)": [0.0] * len(months)})
            else:
                monthly_source = frame.assign(month=frame["date"].dt.to_period("M").dt.to_timestamp())
                totals = monthly_source.groupby("month")["co2"].sum()
                monthly = pd.DataFrame({"Month": months})
                monthly["Estimated CO2e (kg)"] = monthly["Month"].map(totals).fillna(0.0)
            figure = px.area(monthly, x="Month", y="Estimated CO2e (kg)", markers=True, color_discrete_sequence=["#10B981"])
            figure.update_layout(**_plot_layout(dark_mode), height=310, showlegend=False)
            figure.update_traces(line={"width": 3}, fillcolor="rgba(16,185,129,.18)")
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False}, alt="Estimated monthly emissions for the most recent six months")

    with chart_cols[1]:
        with st.container(border=True):
            st.markdown("**Where your footprint comes from**")
            if frame.empty:
                category_data = pd.DataFrame({"Category": ["No purchases yet"], "Estimated CO2e (kg)": [0.0]})
            else:
                category_data = frame.groupby("category", as_index=False)["co2"].sum().rename(columns={"category": "Category", "co2": "Estimated CO2e (kg)"}).sort_values("Estimated CO2e (kg)", ascending=True)
            figure = px.bar(category_data, x="Estimated CO2e (kg)", y="Category", orientation="h", color="Category", color_discrete_sequence=["#10B981", "#7C3AED", "#F59E0B", "#EF4444", "#A855F7", "#059669"])
            figure.update_layout(**_plot_layout(dark_mode), height=310, showlegend=False)
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False}, alt="Estimated emissions by purchase category")

    st.markdown("**Your highest-leverage next moves**")
    if frame.empty:
        st.caption("Log a few purchases to see which categories offer the biggest same-spend reduction opportunities.")
    else:
        opportunities = _impact_opportunities(frame)
        st.dataframe(
            opportunities.head(5),
            hide_index=True,
            column_config={
                "Spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
                "Estimated impact (kg)": st.column_config.NumberColumn("Estimated impact", format="%.1f kg"),
                "Same-spend reduction (kg)": st.column_config.NumberColumn("Swap potential", format="%.1f kg"),
            },
            alt="Purchase categories ranked by footprint with estimated lower-impact swap opportunities",
        )
        top_opportunity = opportunities.iloc[0]
        st.caption("Swap potential is a what-if estimate using the same historical spend and the app's category averages; it is not measured savings.")
        st.button(
            f"Plan a {top_opportunity['category']} swap",
            icon=":material/compare_arrows:",
            on_click=_open_swap_plan,
            args=(str(top_opportunity["category"]), float(top_opportunity["Spend"]) / int(top_opportunity["Purchases"])),
            key="plan_top_swap",
        )

    st.caption("Estimates use category-average kg CO2e per $10 spent. Product-level footprints vary; tree and car equivalents are illustrative comparisons.")
    with st.expander("How ShopImpact estimates impact", icon=":material/science:"):
        st.markdown("**Purchase estimate** = category factor × price ÷ 10. The factors are broad spending-based averages, not product-specific lifecycle assessments.")
        factor_frame = pd.DataFrame(
            [
                {"Category": category, "kg CO2e per $10": details["factor"], "Typical impact": details["level"]}
                for category, details in CATEGORIES.items()
            ]
        ).sort_values("kg CO2e per $10", ascending=False)
        st.dataframe(
            factor_frame,
            hide_index=True,
            column_config={"kg CO2e per $10": st.column_config.NumberColumn("kg CO2e per $10", format="%.1f kg")},
            alt="ShopImpact category emissions factors used for directional purchase estimates",
        )
        st.caption("The month-end projections extend your current daily average. Real footprints depend on materials, production, shipping, durability, and how an item is used or disposed of.")

    if purchases:
        report = _make_monthly_report(purchases, today)
        st.download_button(
            "Download monthly report",
            data=json.dumps(report, indent=2),
            file_name=f"shopimpact-{today:%Y-%m}-report.json",
            mime="application/json",
            icon=":material/description:",
            key="download_monthly_report",
            on_click="ignore",
        )


def _render_rewards(
    purchases: list[dict],
    dark_mode: bool,
    monthly_target: float = MONTHLY_CO2_TARGET,
) -> None:
    reward_state = check_badges(purchases, monthly_target=monthly_target)
    earned = [badge for badge in reward_state["badges"] if badge["earned"]]
    st.subheader("Eco rewards", anchor=False)
    st.markdown(f"**{reward_state['level']}**  ·  {len(earned)} of {len(reward_state['badges'])} milestones unlocked")

    challenge = _weekly_green_challenge(purchases)
    st.markdown("**This week's low-impact challenge**")
    st.progress(
        challenge["progress"] / challenge["target"],
        text=f"{challenge['progress']} of {challenge['target']} low-impact purchases · week of {challenge['week_start']:%b %d}",
    )
    if challenge["complete"]:
        st.success("Challenge complete. Your lower-impact choices are adding up.")
    else:
        remaining = challenge["target"] - challenge["progress"]
        st.caption(f"{remaining} more lower-impact purchase{'s' if remaining != 1 else ''} to finish this week.")
        st.button("Log a lower-impact pick", icon=":material/add_shopping_cart:", on_click=_navigate_to, args=("Log purchase",), key="weekly_challenge_log")

    if earned:
        badge_cols = st.columns(2)
        for index, badge in enumerate(earned):
            with badge_cols[index % 2]:
                image = draw_badge_graphic(badge["name"], badge["icon"], dark_mode)
                st.image(image, caption=badge["description"], width="stretch", alt=f"Custom ShopImpact graphic for the {badge['name']} milestone")
    else:
        st.info("Your first milestone is one purchase away. Your rewards will appear here as you log choices.")

    st.markdown("**Milestone progress**")
    for badge in reward_state["badges"]:
        left, right = st.columns([1.8, 1])
        with left:
            marker = "Unlocked" if badge["earned"] else "In progress"
            st.markdown(f"**{badge['name']}**  ·  {marker}")
            st.caption(badge["description"])
        with right:
            st.progress(float(badge["progress"]) / float(badge["target"]), text=f"{badge['progress']:.1f} / {badge['target']:.0f}")

    st.markdown("**A small idea for today**")
    st.session_state.setdefault("tip_index", date.today().timetuple().tm_yday % len(ECO_TIPS))
    tip_index = st.session_state.tip_index % len(ECO_TIPS)
    st.markdown(f'<div class="si-tip">{html.escape(ECO_TIPS[tip_index])}</div>', unsafe_allow_html=True)
    if st.button("Next eco tip", icon=":material/arrow_forward:", key="next_tip"):
        st.session_state.tip_index = (tip_index + 1) % len(ECO_TIPS)
        st.rerun()


def main() -> None:
    st.session_state.setdefault("purchases", [])
    st.session_state.setdefault("last_added_id", None)
    st.session_state.setdefault("wishlist", [])
    st.session_state.setdefault("cart", {})
    st.session_state.setdefault("orders", [])
    st.session_state.setdefault("return_requests", [])
    st.session_state.setdefault("support_requests", [])
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("high_contrast", False)
    apply_custom_css(st.session_state.dark_mode, st.session_state.high_contrast)

    views = [
        "Overview",
        "Discover",
        "Log purchase",
        "Wishlist",
        "Cart & checkout",
        "My orders",
        "Impact analytics",
        "Swap studio",
        "Eco rewards",
        "Help & returns",
        "Profile",
    ]
    view_labels = {
        "Overview": "Overview",
        "Discover": "Discover products",
        "Log purchase": "Log a purchase",
        "Wishlist": f"Mindful wishlist · {len(st.session_state.wishlist)}",
        "Cart & checkout": f"Cart & checkout · {sum(st.session_state.cart.values())}",
        "My orders": f"Orders & tracking · {len(st.session_state.orders)}",
        "Impact analytics": "Impact analytics",
        "Swap studio": "Swap studio",
        "Eco rewards": "Eco rewards",
        "Help & returns": "Help & returns",
        "Profile": "My profile",
    }
    pending_view = st.session_state.pop("pending_view", None)
    if pending_view in views:
        st.session_state.view = pending_view
    if st.session_state.get("view") not in views:
        st.session_state.view = "Overview"

    with st.sidebar:
        st.markdown("## :material/eco: ShopImpact")
        st.caption("Your conscious-shopping HQ")
        st.markdown("**Your pages**")
        st.radio(
            "Navigate ShopImpact",
            views,
            key="view",
            format_func=lambda value: view_labels[value],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.toggle("High contrast", key="high_contrast", help="Strengthens text and border contrast.")
        st.markdown("**Your monthly goals**")
        monthly_budget = st.number_input("Shopping budget ($)", min_value=25.0, max_value=100000.0, value=600.0, step=25.0, key="monthly_budget")
        monthly_target = st.number_input("CO2e goal (kg)", min_value=1.0, max_value=1000.0, value=MONTHLY_CO2_TARGET, step=1.0, key="monthly_target")
        st.markdown("**Demo controls**")
        if st.button("Load demo data", icon=":material/auto_awesome:", width="stretch", key="load_demo"):
            _load_demo_data()
            st.toast("Demo purchases loaded. Explore all five views.", icon=":material/check_circle:")
        if st.button("Clear my ledger", icon=":material/delete_outline:", width="stretch", key="clear_ledger"):
            st.session_state.purchases = []
            st.session_state.last_added_id = None
            st.toast("Your session ledger is clear.", icon=":material/delete_outline:")
        with st.expander("Data backup", icon=":material/backup:"):
            st.caption("Backups include your purchase ledger and mindful wishlist. They stay on your device unless you choose to download them.")
            st.download_button(
                "Download ledger + wishlist",
                data=_make_data_backup(
                    st.session_state.purchases, st.session_state.wishlist
                ),
                file_name="shopimpact-backup.json",
                mime="application/json",
                icon=":material/download:",
                key="download_data_backup",
                on_click="ignore",
            )
            backup_file = st.file_uploader(
                "Restore a ShopImpact backup",
                type=["json"],
                key="restore_backup_upload",
            )
            replace_confirmed = st.checkbox(
                "I understand restore replaces my current ledger and wishlist.",
                key="confirm_backup_restore",
                disabled=backup_file is None,
            )
            if st.button(
                "Validate and restore",
                icon=":material/restore:",
                disabled=backup_file is None or not replace_confirmed,
                key="restore_data_backup",
            ):
                restored, backup_issues = _parse_data_backup(backup_file)
                if backup_issues:
                    st.error("Nothing was restored. " + " ".join(backup_issues[:5]))
                elif restored is not None:
                    st.session_state.purchases = restored["purchases"]
                    st.session_state.wishlist = restored["wishlist"]
                    st.session_state.last_added_id = None
                    st.toast("Ledger and wishlist restored.", icon=":material/check_circle:")
                    st.rerun()
        st.markdown("---")
        st.caption("Estimates are directional. Commerce, payments, tracking, and support are local demo flows.")

    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.container(key="theme_floating"):
            st.toggle(
                "Light mode" if st.session_state.dark_mode else "Dark mode",
                key="dark_mode",
                help="Switch between light and dark appearance.",
            )

    view = st.session_state.view
    purchases = st.session_state.purchases
    transition_key = f"page_transition_{view.replace(' ', '_').replace('&', 'and')}"
    with st.container(key=transition_key):
        if view == "Overview":
            _render_overview(purchases, st.session_state.dark_mode, monthly_budget, monthly_target)
        elif view == "Discover":
            _render_catalog(purchases)
        elif view == "Wishlist":
            _render_wishlist()
        elif view == "Cart & checkout":
            _render_cart()
        elif view == "My orders":
            _render_orders()
        elif view == "Log purchase":
            _render_purchase_view(purchases, st.session_state.dark_mode)
        elif view == "Impact analytics":
            _render_analytics(purchases, st.session_state.dark_mode, monthly_target, monthly_budget)
        elif view == "Swap studio":
            _render_swap_studio()
        elif view == "Eco rewards":
            _render_rewards(purchases, st.session_state.dark_mode, monthly_target)
        elif view == "Help & returns":
            _render_help_and_returns()
        elif view == "Profile":
            _render_profile()


if __name__ == "__main__":
    main()