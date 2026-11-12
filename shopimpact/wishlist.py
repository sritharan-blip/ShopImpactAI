"""ShopImpact wishlist."""
from __future__ import annotations

import html
from datetime import date, timedelta
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from .ui import render_table
from .catalog import CATEGORIES
from .logic import _monthly_frame, _new_purchase, _new_wishlist_item


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
