"""A small, explicit decision model and a place to pause before buying."""
from __future__ import annotations

from datetime import date, timedelta
import html
import math
import streamlit as st

from .catalog import CATEGORIES
from .logic import _monthly_frame, _new_wishlist_item, calculate_impact
from .navigation import _navigate_to


def decision_projection(price: float, uses_per_week: float, years: float,
                        monthly_spend: float = 0, monthly_budget: float = 600) -> dict:
    """Cost per use and budget arithmetic; no price, lifespan or carbon prediction."""
    values = [float(v) for v in (price, uses_per_week, years, monthly_spend, monthly_budget)]
    if any(not math.isfinite(v) or v < 0 for v in values) or min(values[1:3]) <= 0 or values[4] <= 0:
        raise ValueError('Use finite non-negative values with positive frequency, lifespan, and budget.')
    price, uses_per_week, years, monthly_spend, monthly_budget = values
    total_uses = uses_per_week * 52 * years
    return {'uses': round(total_uses), 'cost_per_use': round(price / total_uses, 2),
            'remaining': round(monthly_budget - monthly_spend - price, 2),
            'budget_share': round(price / monthly_budget * 100, 1)}


def render_decision_lab(purchases: list[dict]) -> None:
    st.html('<div class="si-kicker">THE SPACE BETWEEN WANTING & BUYING</div>')
    st.title('A little pause. A better decision.')
    st.caption('Explore cost per use, check your budget, and give a purchase time before you decide.')
    left, right = st.columns([1.1, 1], gap='large')
    with left:
        with st.container(border=True, key='decision_assumptions'):
            product = st.text_input('What caught your eye?', placeholder='A jacket. Headphones. Something you will actually use.', key='decision_product', max_chars=150)
            category = st.selectbox('Purchase category', list(CATEGORIES), key='decision_category')
            price = st.number_input('Expected price ($)', min_value=.01, max_value=100000.0, value=120.0, step=5.0, key='decision_price')
            frequency = st.slider('How often will you use it each week?', 1, 14, 3, key='decision_frequency')
            years = st.select_slider('How many years will you keep it?', [.5, 1.0, 2.0, 3.0, 5.0], value=2.0, key='decision_years')
            st.caption('These are your assumptions. Actual use and durability may differ.')
    monthly = _monthly_frame(purchases)
    spent = float(monthly['price'].sum()) if not monthly.empty else 0
    budget = float(st.session_state.get('monthly_budget', 600))
    projection = decision_projection(price, frequency, years, spent, budget)
    with right:
        st.html(f'<div class="si-decision-result"><div class="si-kicker">YOUR COST PER USE</div>'
                f'<div class="si-big">${projection["cost_per_use"]:.2f}</div>'
                f'<p>Across about <strong>{projection["uses"]:,} uses</strong> over {years:g} years.</p>'
                f'<p>{html.escape(product.strip() or "Your next purchase")} could take <strong>{projection["budget_share"]:.1f}%</strong> of your monthly budget.</p></div>')
        c1, c2 = st.columns(2)
        c1.metric('Budget after buying', f'${projection["remaining"]:,.0f}')
        c2.metric('Category estimate', f'{calculate_impact(category, price):.1f} kg')
        if projection['remaining'] < 0:
            st.warning('This would take your recorded spending above your monthly budget.')
        else:
            st.caption('A budget fit is one signal. Check whether you already own something that does the job.')
    with st.container(border=True, key='decision_pause_panel'):
        st.markdown('### Let the impulse settle.')
        st.caption('Save this idea to your wishlist and choose when to revisit it. This sets a date in the app; it does not send a notification.')
        pause = st.segmented_control('Give it some space', ['24 hours', '3 days', '1 week'], default='3 days', key='decision_pause')
        days = {'24 hours': 1, '3 days': 3, '1 week': 7}.get(pause, 3)
        if st.button('Save a pause plan', type='primary', icon=':material/bookmark_add:', key='save_decision'):
            if not product.strip():
                st.error('Give the idea a name before saving it.')
            elif len(st.session_state.setdefault('wishlist', [])) >= 500:
                st.error('Your wishlist is full. Remove an idea before saving another.')
            else:
                item = _new_wishlist_item(product, category, '', price, date.today() + timedelta(days=days), 'Want',
                    f'Decision lab: {frequency} uses/week for {years:g} years; about ${projection["cost_per_use"]:.2f}/use.')
                st.session_state.wishlist.append(item)
                st.success(f'Saved. Revisit on {item["revisit_on"]}.')
        st.button('Open my wishlist', icon=':material/bookmarks:', on_click=_navigate_to, args=('Wishlist',), key='decision_wishlist')
