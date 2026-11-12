"""ShopImpact insights."""
from __future__ import annotations

import html
import json
from datetime import date, timedelta
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from .ui import render_table, render_hero, render_ticker, render_badge
from .catalog import CAR_EMISSIONS_KG_PER_MILE, CATEGORIES, ECO_TIPS, LOW_IMPACT_FACTOR, MONTHLY_CO2_TARGET, TREE_ABSORPTION_KG_PER_YEAR
from .logic import _make_monthly_report, _month_end_forecast, _month_end_spend_forecast, _monthly_frame, _purchase_frame, _weekly_green_challenge, calculate_impact, check_badges, get_alternatives
from .navigation import _navigate_to
from .theme import _plot_layout


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

    render_hero(len(purchases), month_co2, spend, green_choices)
    cta_left, cta_right, cta_swap, cta_wishlist = st.columns(4)
    cta_left.button("Log a purchase", type="primary", icon=":material/add_shopping_cart:", on_click=_navigate_to, args=("Log purchase",), key="overview_log", width="stretch")
    cta_right.button("Discover your next favorite", icon=":material/storefront:", on_click=_navigate_to, args=("Discover",), key="overview_discover", width="stretch")
    cta_swap.button("Try Decision lab", icon=":material/auto_awesome:", on_click=_navigate_to, args=("Decision lab",), key="overview_swap", width="stretch")
    cta_wishlist.button("Your mindful wishlist", icon=":material/bookmark:", on_click=_navigate_to, args=("Wishlist",), key="overview_wishlist", width="stretch")
    render_ticker()

    st.markdown('<div class="si-section-label">This month at a glance</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Shopping spend", f"${spend:,.2f}", delta=f"of ${monthly_budget:,.0f} budget", border=True)
    metric_cols[1].metric("Footprint", f"{month_co2:.1f} kg", delta=f"{monthly_target:.0f} kg goal", border=True)
    metric_cols[2].metric("Lower-impact picks", f"{green_choices}", delta=f"of {len(month_frame)} this month", border=True)
    metric_cols[3].metric("Eco score", f"{eco_score}/100", delta=f"{total_co2:.1f} kg all-time", border=True)

    goal_cols = st.columns(2)
    goal_cols[0].progress(min(spend / monthly_budget, 1.0), text=f"Spend plan · ${spend:,.2f} of ${monthly_budget:,.0f}")
    goal_cols[1].progress(min(month_co2 / monthly_target, 1.0), text=f"Carbon goal · {month_co2:.1f} of {monthly_target:.0f} kg CO2e")
    remaining = max(0, monthly_budget - spend)
    brief = (f'<strong>${remaining:,.0f} left in your monthly plan.</strong> '
             f'{green_choices} of your {len(month_frame)} recorded choices are in lower-impact categories. '
             'Use Decision lab to think through your next purchase before it reaches the cart.') if not month_frame.empty else (
             '<strong>Your next choice starts here.</strong> Log a purchase for a personal snapshot, or load demo data to explore the studio.')
    st.html(f'<aside class="si-brief"><span class="si-brief-icon" aria-hidden="true">✦</span><p>{brief}</p></aside>')
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
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": False}, theme=None)
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
                render_table(
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
    compare_cols[0].metric("Typical new purchase", f"{current_co2 * quantity:.1f} kg CO2e", delta=CATEGORIES[category]["level"] + " impact", border=True)
    compare_cols[1].metric("Lower-impact option", f"{alternative_co2 * quantity:.1f} kg CO2e", delta="repair / refill / resale estimate", border=True)
    compare_cols[2].metric("Potential reduction", f"{saved * quantity:.1f} kg CO2e", delta=f"{saved * quantity / CAR_EMISSIONS_KG_PER_MILE:.0f} car miles equivalent", border=True)
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
        render_table(basket_view, hide_index=True, alt="Items in the impact comparison basket")
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
        render_table(pd.DataFrame(saved_swaps), hide_index=True, alt="Your saved lower-impact shopping alternatives")
        st.download_button("Download shortlist", data=pd.DataFrame(saved_swaps).to_csv(index=False), file_name="shopimpact-swap-shortlist.csv", mime="text/csv", icon=":material/download:", on_click="ignore")
        if st.button("Clear shortlist", icon=":material/delete_sweep:", key="clear_swaps"):
            st.session_state.saved_swaps = []
            st.rerun()


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
    carbon_saved_kg = float(month_rows["carbon_saved_kg"].sum()) if not month_rows.empty else 0.0
    avoided_miles = carbon_saved_kg / CAR_EMISSIONS_KG_PER_MILE

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
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False}, theme=None)

    with chart_cols[1]:
        with st.container(border=True):
            st.markdown("**Where your footprint comes from**")
            if frame.empty:
                category_data = pd.DataFrame({"Category": ["No purchases yet"], "Estimated CO2e (kg)": [0.0]})
            else:
                category_data = frame.groupby("category", as_index=False)["co2"].sum().rename(columns={"category": "Category", "co2": "Estimated CO2e (kg)"}).sort_values("Estimated CO2e (kg)", ascending=True)
            figure = px.bar(category_data, x="Estimated CO2e (kg)", y="Category", orientation="h", color="Category", color_discrete_sequence=["#10B981", "#7C3AED", "#F59E0B", "#EF4444", "#A855F7", "#059669"])
            figure.update_layout(**_plot_layout(dark_mode), height=310, showlegend=False)
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False}, theme=None)

    st.markdown("**Your highest-leverage next moves**")
    if frame.empty:
        st.caption("Log a few purchases to see which categories offer the biggest same-spend reduction opportunities.")
    else:
        opportunities = _impact_opportunities(frame)
        render_table(
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
        render_table(
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
                render_badge(badge)
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
