# Session 7 — Gold marts and visualization

**Syllabus:** topic 10 · **Layer:** Gold

## Goal

Students can create business marts (data products) and connect a consumer (dashboard) to them.
They understand that *"BI doesn't have to be a database"* – Gold is a data product.

## Theory (~40 min)

- **Gold = business marts / data products:** `sales_daily`, `customer_360`, `product_performance`.
- **Semantics for consumers** – aggregated, named, stable; a data product vs. an ad-hoc report.
- **Gold as Parquet:** our Gold dbt models materialize as **external** Parquet files (data products
  any tool can read), not rows locked inside a database.
- **Local viz vs. enterprise:** Streamlit + DuckDB locally; Power BI Desktop (Windows) would connect
  to the same Gold Parquet as the enterprise equivalent.

## Practice (~45 min)

You fill in the `# TODO`s:

1. `models/gold/sales_daily.sql` – daily revenue + order count from `fct_orders`.
2. `models/gold/customer_360.sql` – classify each customer as `active`/`prospect`.
3. **(harder)** `models/gold/product_performance.sql` – `revenue_share_pct` via a window
   (`sum(...) over ()`).
4. `app/queries.py` – top products **within the active filters** (category + time window), from
   `sales_product_daily`.
5. `app/queries.py` – revenue per category within the time window.

The dashboard is interactive: a time slider; clicking a category bar cross-filters the top
products and the revenue trend; clicking a product shows its own revenue trend
(`st.altair_chart(..., on_select="rerun")`, "Clear selection" resets both). The UI and the
`_where()` filter builder are given – you only write the two queries.

Then build Gold and run the dashboard:

```bash
uv run eshop dbt-build                          # (re)builds marts + Gold Parquet
uv run streamlit run app/dashboard.py           # local dashboard over Gold
ls data/lake/gold/                              # sales_daily, customer_360, product_performance, star_*
```

## Deliverable / checkpoint

- Gold Parquet data products in `data/lake/gold/` and a working Streamlit dashboard.
- **checkpoint-07** = this state.
