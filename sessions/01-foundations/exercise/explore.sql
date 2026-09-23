-- Session 1 – first queries over the e-shop data in DuckDB (pure SQL version).
--
-- Fill in each TODO. This is plain SQL – no Python to write – but it still runs through
-- `uv run`, via the `duckdb` Python package already in the project (no separate DuckDB
-- CLI install needed). Run from the repo root (paths below are hardcoded to data/raw/):
--   uv run eshop sql sessions/01-foundations/exercise/explore.sql
--   (or:  just sql sessions/01-foundations/exercise/explore.sql)
--
-- Reference cheatsheet:
--   - CSV:    read_csv_auto('data/raw/file.csv')
--   - SQLite: sqlite_scan('data/raw/shop.sqlite', 'table_name')
--   - join:   ... JOIN ... USING (order_id)

-- --- Task 1: how many customers and products do we have? -----------------------
-- Count the rows in each CSV. Use read_csv_auto(...) and count(*).
-- TODO(01): count rows in customers.csv and products.csv (two columns, one row)
SELECT 1;

-- --- Task 2: daily revenue -----------------------------------------------------
-- Join orders to order_items (both in SQLite) and sum qty*unit_price per calendar day.
-- Cast the text timestamp with order_ts::TIMESTAMP and bucket it with date_trunc('day', ...).
-- TODO(01): SELECT day, SUM(qty*unit_price) AS revenue ... GROUP BY day ORDER BY day
SELECT 1;

-- --- Task 3: top 5 products by revenue -----------------------------------------
-- Join order_items to products.csv (USING product_id), sum revenue, order desc, LIMIT 5.
-- TODO(01): top 5 products by SUM(qty*unit_price)
SELECT 1;

-- --- Task 4: how many orders are in each status? -------------------------------
-- A simple GROUP BY over the orders table (status column).
-- TODO(01): count orders per status, most frequent first
SELECT 1;

-- --- Task 5: average order value (AOV) -----------------------------------------
-- First compute each order's total (sum of its items), then average those totals.
-- Tip: a CTE  WITH per_order AS (SELECT order_id, SUM(...) AS order_total ... GROUP BY order_id)
-- TODO(01): average of per-order totals
SELECT 1;

-- --- Task 6: save daily revenue to Parquet -------------------------------------
-- Wrap the Task 2 query in COPY (...) TO 'data/raw/daily_revenue.parquet' (FORMAT PARQUET).
-- TODO(01): write daily revenue to Parquet
SELECT 1;

-- --- Task 7 (harder): month-over-month revenue growth --------------------------
-- Aggregate revenue per MONTH, then use the window function lag(revenue) OVER (ORDER BY month)
-- to compute the growth vs. the previous month as a percentage.
-- Structure: WITH monthly AS (SELECT date_trunc('month', ...) AS month, SUM(...) AS revenue ...)
--            SELECT month, revenue, 100.0*(revenue - lag(revenue) OVER (ORDER BY month))
--                                    / lag(revenue) OVER (ORDER BY month) AS growth_pct ...
-- TODO(01): monthly revenue + growth_pct using lag() over month
SELECT 1;
