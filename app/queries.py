"""Session 7 – data access for the dashboard (Gold layer via DuckDB).

Kept separate from the Streamlit UI so it stays testable: pure functions that read the Gold
Parquet data products and return Polars frames. The dashboard's filters (category, time window)
arrive here as plain arguments and become a parameterized SQL WHERE clause.
"""

from __future__ import annotations

from datetime import date

import duckdb
import polars as pl

from eshop.config import settings


def _gold(name: str) -> str:
    return str(settings.gold_dir / f"{name}.parquet")


def _query(sql: str, params: list | None = None) -> pl.DataFrame:
    # A fresh in-memory connection per call: cheap, and safe across Streamlit's threads.
    with duckdb.connect() as con:
        return con.execute(sql, params or []).pl()


def _where(
    category: str | None = None,
    start: date | None = None,
    end: date | None = None,
    product: str | None = None,
) -> tuple[str, list]:
    """Build a WHERE clause + bound parameters from the active filters (None = no filter).

    Values are passed as `?` parameters, never pasted into the SQL string (no SQL injection).
    """
    clauses: list[str] = []
    params: list = []
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if start is not None:
        clauses.append("day >= ?")
        params.append(start)
    if end is not None:
        clauses.append("day <= ?")
        params.append(end)
    if product is not None:
        clauses.append("product_name = ?")
        params.append(product)
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params


def date_range() -> tuple[date, date]:
    """First and last day available in Gold (bounds for the time filter)."""
    row = _query(f"SELECT min(day) AS lo, max(day) AS hi FROM read_parquet('{_gold('sales_daily')}')")
    return row["lo"][0], row["hi"][0]


def revenue_over_time(category: str | None = None, product: str | None = None) -> pl.DataFrame:
    """Daily revenue for a line chart, optionally for one category and/or one product only."""
    where, params = _where(category=category, product=product)
    return _query(
        f"SELECT day, sum(revenue) AS revenue "
        f"FROM read_parquet('{_gold('sales_product_daily')}') {where} "
        f"GROUP BY day ORDER BY day",
        params,
    )


def top_products(
    n: int = 10, category: str | None = None, start: date | None = None, end: date | None = None
) -> pl.DataFrame:
    """Top N products by revenue within the active filters (category and/or time window)."""
    where, params = _where(category, start, end)
    # Gold has one row per (day, product): sum it up per product, then keep the best n.
    # TODO(7): from sales_product_daily, apply `where`, sum revenue per product_name, top n desc


def revenue_by_category(start: date | None = None, end: date | None = None) -> pl.DataFrame:
    """Total revenue per product category within the time window."""
    where, params = _where(start=start, end=end)
    # Same product, coarser view: roll (day, product) rows up to category level.
    # TODO(7): from sales_product_daily, apply `where`, sum revenue per category, highest first
