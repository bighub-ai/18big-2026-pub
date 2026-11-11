"""Session 7 – interactive Streamlit dashboard over the Gold layer.

Run with:  uv run streamlit run app/dashboard.py

Interactions (cross-filtering):
  - the time slider filters the category chart and the top products,
  - clicking a category bar filters the top products and the revenue trend,
  - clicking a product bar filters the revenue trend to that product,
  ("Clear selection" or a double-click on a chart clears it).

Note: "BI doesn't have to be a database" – the Gold layer is a data product (Parquet), and this
dashboard is just one consumer of it.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

try:  # works both as `streamlit run app/dashboard.py` and as an imported package
    from app.queries import date_range, revenue_by_category, revenue_over_time, top_products
except ModuleNotFoundError:
    from queries import date_range, revenue_by_category, revenue_over_time, top_products

PURPLE, GREY = "#6c4ce0", "#d9d4ea"

st.set_page_config(page_title="E-shop Lakehouse", layout="wide")
st.title("E-shop Lakehouse — Gold dashboard")

# --- Filter 1: time window ------------------------------------------------------------------
lo, hi = date_range()
start, end = st.slider("Time window", min_value=lo, max_value=hi, value=(lo, hi), format="YYYY-MM-DD")

left, right = st.columns(2)

# --- Filter 2: click a category -------------------------------------------------------------
with left:
    st.subheader("Revenue by category")
    st.caption("Click a bar to filter the other charts.")
    # Altair can't clear a selection from Python. A new widget key re-creates the chart empty.
    st.session_state.setdefault("chart_version", 0)
    pick = alt.selection_point(fields=["category"], name="pick", clear="dblclick")
    cat_chart = (
        alt.Chart(revenue_by_category(start, end).to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("revenue:Q", title="Revenue"),
            y=alt.Y("category:N", sort="-x", title=None),
            color=alt.when(pick).then(alt.value(PURPLE)).otherwise(alt.value(GREY)),
            tooltip=["category", alt.Tooltip("revenue:Q", format=",.0f")],
        )
        .add_params(pick)
    )
    event = st.altair_chart(
        cat_chart, on_select="rerun", key=f"category_chart_{st.session_state.chart_version}", width="stretch"
    )
    picked = event.get("selection", {}).get("pick") or []
    category = picked[0].get("category") if picked else None

# --- Top products: reacts to both filters; click a product to filter the trend -------------
with right:
    st.subheader(f"Top products — {category or 'all categories'}")
    st.caption("Click a product to see its revenue over time.")
    top = top_products(10, category=category, start=start, end=end)
    pick_product = alt.selection_point(fields=["product_name"], name="pick_product", clear="dblclick")
    product_chart = (
        alt.Chart(top.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("revenue:Q", title="Revenue"),
            y=alt.Y("product_name:N", sort="-x", title=None),
            color=alt.when(pick_product).then(alt.value(PURPLE)).otherwise(alt.value(GREY)),
            tooltip=["product_name", alt.Tooltip("revenue:Q", format=",.0f")],
        )
        .add_params(pick_product)
    )
    # The category is part of the key: picking another category starts with no product selected.
    product_event = st.altair_chart(
        product_chart,
        on_select="rerun",
        key=f"product_chart_{st.session_state.chart_version}_{category}",
        width="stretch",
    )
    picked = product_event.get("selection", {}).get("pick_product") or []
    product = picked[0].get("product_name") if picked else None

if st.button("Clear selection", disabled=category is None and product is None):
    st.session_state.chart_version += 1
    st.rerun()

# --- Trend: reacts to the category, shows the time window as a band ---------------------------
st.subheader(f"Revenue over time — {product or category or 'all categories'}")
trend = alt.Chart(revenue_over_time(category, product).to_pandas()).mark_line(color=PURPLE).encode(
    x=alt.X("day:T", title=None), y=alt.Y("revenue:Q", title="Revenue")
)
window = (
    alt.Chart(alt.Data(values=[{"start": str(start), "end": str(end)}]))
    .mark_rect(opacity=0.12, color=PURPLE)
    .encode(x="start:T", x2="end:T")
)
st.altair_chart(window + trend, width="stretch")
