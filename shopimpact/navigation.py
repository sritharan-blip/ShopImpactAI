"""ShopImpact navigation."""
from __future__ import annotations

from datetime import date, timedelta
import streamlit as st
from .catalog import DEMO_ITEMS
from .logic import _new_purchase


def _navigate_to(view: str) -> None:
    st.session_state.view = view


def _load_demo_data() -> None:
    today = date.today()
    purchases = []
    for index, (product, category, brand, price, savings) in enumerate(DEMO_ITEMS):
        purchased_on = today - timedelta(days=index if index < 7 else 35 + index)
        baseline = _new_purchase(product, category, brand, price, purchased_on)
        factor = 0.7 if savings else 1.0
        purchases.append(_new_purchase(product, category, brand, price, purchased_on,
                                      co2_override=round(baseline["co2"] * factor, 2)))
    st.session_state.purchases = purchases
    st.session_state.last_added_id = purchases[5]["id"]
