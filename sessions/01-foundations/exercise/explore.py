"""Session 1 – first queries over the e-shop data in DuckDB.

Fill in the spots marked with TODO. You don't need any server – DuckDB reads CSV and SQLite
directly. Run with:  uv run python sessions/01-foundations/exercise/explore.py
"""

import duckdb

from eshop.config import settings

con = duckdb.connect()
customers_csv = str(settings.raw_dir / "customers.csv")
products_csv = str(settings.raw_dir / "products.csv")
db = str(settings.source_db)

# 1) How many customers and products do we have?
# TODO(01): write SELECT count(*) over customers.csv and products.csv (read_csv_auto)
n_customers = ...  # TODO
n_products = ...  # TODO
print(f"customers: {n_customers}, products: {n_products}")

# 2) Daily revenue: JOIN orders + order_items (SQLite), sum qty*unit_price per day
# TODO(01): complete the SQL. Hint: sqlite_scan('<db>', 'orders') and '<db>', 'order_items'),
#           date_trunc('day', order_ts::TIMESTAMP), GROUP BY day, ORDER BY day
daily_revenue = con.execute(
    """
    -- TODO(01): SELECT day, SUM(qty*unit_price) AS revenue FROM ... JOIN ... GROUP BY day
    SELECT 1
    """
).pl()
print(daily_revenue.head())

# 3) Top 5 products by revenue
# TODO(01): JOIN order_items with products.csv, SUM(qty*unit_price) AS revenue, LIMIT 5
top_products = con.execute(
    """
    -- TODO(01)
    SELECT 1
    """
).pl()
print(top_products)

# 4) Save daily revenue to Parquet
# TODO(01): daily_revenue.write_parquet(...) into settings.raw_dir / "daily_revenue.parquet"
...
print("done")
