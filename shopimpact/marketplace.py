"""ShopImpact marketplace."""
from __future__ import annotations

import html
from datetime import date, timedelta
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from .ui import render_table, product_art
from .recommendations import recommend_products
from .catalog import CATEGORIES, PRODUCTS
from .logic import _cart_totals, _find_product, _new_purchase, _product_impact, _purchase_frame, calculate_impact
from .navigation import _navigate_to


def _render_catalog(purchases: list[dict]) -> None:
    st.markdown('<div class="si-kicker">Conscious marketplace</div>', unsafe_allow_html=True)
    st.title("Find things made to last.")
    st.caption("A curated demo catalog of repairable, reused, refillable, and thoughtfully sourced goods.")

    profile = st.session_state.get("profile") or {}
    with st.container(border=True):
        st.markdown("### A better fit for your everyday")
        intent = st.text_input("Describe what you need", placeholder="A repairable laptop for studying, or a refill for home…", key="match_intent", max_chars=200)
        match_left, match_right = st.columns(2)
        match_category = match_left.selectbox("Match category", ["Any category", *CATEGORIES], key="match_category")
        match_budget = match_right.number_input("Your maximum budget ($)", min_value=0.0, max_value=100000.0, value=800.0, step=10.0, key="match_budget")
        recommendations = recommend_products(intent, purchases,
                            None if match_category == "Any category" else match_category,
                            match_budget, profile.get("personalization", True))
        with st.expander("How your matches work"):
            st.write("A local TF-IDF model matches catalog descriptions to your shopping intent. Ranking also considers your selected category, budget and the catalog's estimated reduction. When you leave intent blank, recent purchase descriptions help personalize the picks. You can disable history personalization in Profile.")
            st.caption("These are explainable matches from a small demo catalog, not a generative AI answer or verified environmental endorsement.")
    st.markdown("### Your smart matches")
    st.caption("Personalization is off. Matches use only your current intent and filters." if not profile.get("personalization", True) else "Matched locally. Your history and shopping intent stay inside this app session.")
    if not recommendations:
        st.info("No catalog items fit these filters. Try a higher budget or another category.")
        return
    recommend_cols = st.columns(min(3, len(recommendations)))
    for index, product in enumerate(recommendations[:3]):
        with recommend_cols[index]:
            with st.container(border=True):
                product_art(product["icon"])
                st.markdown(f"**{html.escape(product['name'])}**")
                st.caption(" · ".join(product["reasons"][:2]))
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
            shipping_label = "Free" if totals["shipping"] == 0 else "${:.2f}".format(totals["shipping"])
            st.markdown(f"Demo shipping  ·  **{shipping_label}**")
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
                        purchases.append(_new_purchase(
                            product["name"] + (f" (x{quantity})" if quantity > 1 else ""),
                            product["category"],
                            product["brand"],
                            line_total,
                            date.today(),
                            co2_override=line_co2,
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
                render_table(
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
