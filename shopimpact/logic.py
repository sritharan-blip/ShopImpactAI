"""ShopImpact logic."""
from __future__ import annotations

from datetime import date, timedelta
import math
from uuid import uuid4
import pandas as pd
from .catalog import ALTERNATIVE_BRANDS, CATEGORIES, LOW_IMPACT_FACTOR, MONTHLY_CO2_TARGET, PRODUCTS, RISKY_BRAND_TERMS, TREE_ABSORPTION_KG_PER_YEAR


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
    month_carbon_saved_kg = sum(float(item.get("carbon_saved_kg", 0)) for item in month_items)

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
            "name": "Carbon Pacekeeper",
            "description": f"Keep this month's estimated footprint under {monthly_target:.0f} kg CO2e.",
            "icon": "spark",
            "earned": bool(month_items) and month_co2 < monthly_target,
            "progress": max(0, monthly_target - month_co2) if month_items else 0,
            "target": monthly_target,
        },
        {
            "key": "saver",
            "name": "Eco Saver of the Month",
            "description": "Record at least 10 kg CO2e in estimated reductions this month.",
            "icon": "trophy",
            "earned": month_carbon_saved_kg >= 10,
            "progress": min(month_carbon_saved_kg, 10),
            "target": 10,
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
    return [
        {
            "brand": name,
            "estimated_savings": round(estimated_savings, 2),
            "reason": "Lower-impact, repairable, refill, or second-hand option",
        }
        for name in alternatives[:3]
    ]


def _new_purchase(
    product: str,
    category: str,
    brand: str,
    price: float,
    purchased_on: date,
    *,
    co2_override: float | None = None,
) -> dict:
    price = round(float(price), 2)
    baseline = calculate_impact(category, price)
    co2 = baseline if co2_override is None else round(float(co2_override), 2)
    if not product.strip() or not math.isfinite(co2) or co2 < 0:
        raise ValueError("Product and finite non-negative emissions are required")
    # Reductions share the same unit and comparison baseline as the footprint.
    carbon_saved_kg = max(0.0, round(baseline - co2, 2))
    return {
        "id": str(uuid4()),
        "date": purchased_on.isoformat(),
        "product": product.strip(),
        "category": category,
        "brand": brand.strip(),
        "price": round(float(price), 2),
        "co2": co2,
        "baseline_co2": baseline,
        "estimate_method": "category-v1" if co2_override is None else "snapshot-v1",
        "impact_level": CATEGORIES[category]["level"],
        "carbon_saved_kg": round(float(carbon_saved_kg), 2),
    }


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
        "carbon_saved_kg": round(sum(float(item.get("carbon_saved_kg", 0)) for item in rows), 2),
        "tree_years_to_offset": round(
            sum(float(item.get("co2", 0)) for item in rows) / TREE_ABSORPTION_KG_PER_YEAR, 2
        ),
        "method_note": "Category averages in kg CO2e per $10 spent; estimates are directional, not product LCAs.",
    }


def _purchase_frame(purchases: list[dict]) -> pd.DataFrame:
    if not purchases:
        return pd.DataFrame(columns=["id", "date", "product", "category", "brand", "price", "co2", "impact_level", "carbon_saved_kg"])
    frame = pd.DataFrame(purchases).copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce").fillna(0)
    frame["co2"] = pd.to_numeric(frame["co2"], errors="coerce").fillna(0)
    if "carbon_saved_kg" not in frame:
        frame["carbon_saved_kg"] = 0.0
    frame["carbon_saved_kg"] = pd.to_numeric(frame["carbon_saved_kg"], errors="coerce").fillna(0)
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


def _find_product(product_id: str) -> dict | None:
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def _product_impact(product: dict, quantity: int = 1) -> float:
    return round(float(product["price"]) * float(product["impact_factor"]) / 10 * quantity, 2)


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
