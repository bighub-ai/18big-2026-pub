"""Session 1 – first queries over the e-shop data in DuckDB.

Fill in each TODO. You don't need any server – DuckDB reads CSV and SQLite directly.
Run with:  uv run python sessions/01-foundations/exercise/explore.py

Reference cheatsheet:
  - CSV:    read_csv_auto('path/to/file.csv')
  - SQLite: sqlite_scan('path/to/db.sqlite', 'table_name')
  - join:   ... JOIN ... USING (order_id)
"""

import duckdb

from eshop.config import settings

con = duckdb.connect()
customers_csv = str(settings.raw_dir / "customers.csv")
products_csv = str(settings.raw_dir / "products.csv")
db = str(settings.source_db)

# --- Task 1: how many customers and products do we have? -----------------------
# Count the rows in each CSV. Use read_csv_auto(...) and SELECT count(*).
# TODO(01): count rows in customers.csv
n_customers = ...
# TODO(01): count rows in products.csv
n_products = ...
print(f"customers: {n_customers}, products: {n_products}")

# --- Task 2: daily revenue -----------------------------------------------------
# Join orders to order_items (both in SQLite) and sum qty*unit_price per calendar day.
# Cast the text timestamp with order_ts::TIMESTAMP and bucket it with date_trunc('day', ...).
daily_revenue = con.execute(
    """
    -- TODO(01): SELECT day, SUM(qty*unit_price) AS revenue ... GROUP BY day ORDER BY day
    SELECT 1
    """
).pl()
print(daily_revenue.head())

# --- Task 3: top 5 products by revenue -----------------------------------------
# Join order_items to products.csv (USING product_id), sum revenue, order desc, LIMIT 5.
top_products = con.execute(
    """
    -- TODO(01): top 5 products by SUM(qty*unit_price)
    SELECT 1
    """
).pl()
print(top_products)

# --- Task 4: how many orders are in each status? -------------------------------
# A simple GROUP BY over the orders table (status column).
by_status = con.execute(
    """
    -- TODO(01): count orders per status, most frequent first
    SELECT 1
    """
).pl()
print(by_status)

# --- Task 5: average order value (AOV) -----------------------------------------
# First compute each order's total (sum of its items), then average those totals.
# Tip: a CTE  WITH per_order AS (SELECT order_id, SUM(...) AS order_total ... GROUP BY order_id)
aov = con.execute(
    """
    -- TODO(01): average of per-order totals
    SELECT 1
    """
).fetchone()[0]
print(f"average order value: {aov}")

# --- Task 6: save daily revenue to Parquet -------------------------------------
# Polars frames have .write_parquet(path). Save into settings.raw_dir / "daily_revenue.parquet".
# TODO(01): write daily_revenue to Parquet
out = settings.raw_dir / "daily_revenue.parquet"
...
print(f"saved → {out}")

# --- Task 7 (harder): month-over-month revenue growth --------------------------
# Aggregate revenue per MONTH, then use the window function lag(revenue) OVER (ORDER BY month)
# to compute the growth vs. the previous month as a percentage.
# Structure: WITH monthly AS (SELECT date_trunc('month', ...) AS month, SUM(...) AS revenue ...)
#            SELECT month, revenue, 100.0*(revenue - lag(revenue) OVER (ORDER BY month))
#                                    / lag(revenue) OVER (ORDER BY month) AS growth_pct ...
mom = con.execute(
    """
    -- TODO(01): monthly revenue + growth_pct using lag() over month
    SELECT 1
    """
).pl()
print(mom)
