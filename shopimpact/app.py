"""ShopImpact app."""
from __future__ import annotations

import html
from datetime import date, timedelta
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from .catalog import MONTHLY_CO2_TARGET
from .navigation import _load_demo_data
from .data import _make_data_backup, _parse_data_backup
from .insights import _render_analytics, _render_overview, _render_rewards, _render_swap_studio
from .marketplace import _render_cart, _render_catalog, _render_help_and_returns, _render_orders, _render_profile
from .ledger import _render_purchase_view
from .wishlist import _render_wishlist
from .theme import apply_custom_css


def _keep_appearance_selected() -> None:
    """Segment controls can be deselected; keep appearance a two-way choice."""
    mode = st.session_state.get('appearance')
    if mode is None:
        st.session_state.appearance = st.session_state.get('last_appearance', 'Daylight')
    else:
        st.session_state.last_appearance = mode
    st.session_state.dark_mode = st.session_state.appearance == 'Midnight'


def main() -> None:
    st.set_page_config(page_title="ShopImpact | A little more intentional", page_icon=":material/eco:",
                       layout="wide", initial_sidebar_state="expanded")
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
    st.session_state.setdefault("reduce_motion", False)
    # Paint the active palette before emitting any interactive UI on each rerun.
    st.session_state.dark_mode = st.session_state.get('appearance', 'Daylight') == 'Midnight'
    apply_custom_css(st.session_state.dark_mode, st.session_state.high_contrast, st.session_state.reduce_motion)
    heading, quick, appearance = st.columns([1.35, .7, 1])
    with heading:
        st.html('<div class="si-topline"><span class="si-live-dot"></span>SHOPIMPACT <span>/</span> YOUR PERSONAL IMPACT SPACE</div>')
    with quick:
        with st.popover('Quick actions', icon=':material/bolt:', width='stretch'):
            from .navigation import _navigate_to
            for destination, label in [('Log purchase', 'Log a purchase'), ('Discover', 'Explore smart matches'),
                                       ('Decision lab', 'Open Decision lab'), ('Wishlist', 'Open wishlist')]:
                st.button(label, key='quick_' + destination, on_click=_navigate_to, args=(destination,), width='stretch')
    with appearance:
        mode = st.segmented_control("Appearance", ["Daylight", "Midnight"], default="Daylight",
                                    key="appearance", selection_mode="single", width="stretch",
                                    on_change=_keep_appearance_selected)

    views = [
        "Overview",
        "Discover",
        "Decision lab",
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
        "Decision lab": "Decision lab",
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
        st.html('<div class="si-logo"><span class="si-logo-mark">✳</span>ShopImpact<span style="color:var(--si-accent)">.</span></div><div class="si-wordmark">Live a little lighter</div>')
        st.markdown("**Your pages**")
        st.radio(
            "Navigate ShopImpact",
            views,
            key="view",
            format_func=lambda value: view_labels[value],
            label_visibility="collapsed",
        )
        st.markdown("---")
        with st.expander("Display & accessibility", icon=":material/tune:"):
            st.toggle("High contrast", key="high_contrast", help="Strengthens text and border contrast.")
            st.toggle("Reduce motion", key="reduce_motion", help="Pause decorative animations and transitions. Your operating-system preference is also respected.")
        st.markdown("**Your monthly goals**")
        monthly_budget = st.number_input("Shopping budget ($)", min_value=25.0, max_value=100000.0, value=600.0, step=25.0, key="monthly_budget")
        monthly_target = st.number_input("CO2e goal (kg)", min_value=1.0, max_value=1000.0, value=MONTHLY_CO2_TARGET, step=1.0, key="monthly_target")
        st.markdown("**Demo controls**")
        if st.button("Load demo data", icon=":material/auto_awesome:", width="stretch", key="load_demo"):
            _load_demo_data()
            st.toast("Demo purchases loaded. Explore your shopping studio.", icon=":material/check_circle:")
        if st.button("Clear my ledger", icon=":material/delete_outline:", width="stretch", key="clear_ledger"):
            st.session_state.purchases = []
            st.session_state.last_added_id = None
            st.toast("Your session ledger is clear.", icon=":material/delete_outline:")
        with st.expander("Data backup", icon=":material/backup:"):
            st.caption("Download a portable copy of your ledger and wishlist, including their recorded footprint estimates.")
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

    view = st.session_state.view
    purchases = st.session_state.purchases
    transition_key = f"page_transition_{view.replace(' ', '_').replace('&', 'and')}"
    with st.container(key=transition_key):
        if view == "Overview":
            _render_overview(purchases, st.session_state.dark_mode, monthly_budget, monthly_target)
        elif view == "Discover":
            _render_catalog(purchases)
        elif view == "Decision lab":
            from .decisions import render_decision_lab
            render_decision_lab(purchases)
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
