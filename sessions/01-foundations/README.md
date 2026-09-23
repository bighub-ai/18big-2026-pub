# Session 1 — Foundations and environment

**Syllabus:** topic 1 (evolution of DWH/Data Lake/Lakehouse, PaaS/IaaS, BDD) · **Layer:** setup

> This session also serves as the **structure template** for all other sessions (see TEACHING-GUIDE.md).

## Goal

Students understand what Big Data is and why the shift DWH → Data Lake → Lakehouse happened,
have a working local environment, and can write a first analytical query in DuckDB.

## Theory (~40 min)

- **What is Big Data:** the 3–5 V's (Volume, Velocity, Variety, Veracity, Value). When data
  is "big" and why a single Excel / relational DWH is not enough.
- **Evolution of architectures:** DWH (schema-on-write, expensive, structured) → Data Lake
  (schema-on-read, cheap, "data swamp" chaos) → **Lakehouse** (the best of both: cheap storage
  + transactions/quality/performance).
- **PaaS vs. IaaS vs. local:** where things run in practice (Databricks/Snowflake/Synapse) and
  why we **learn locally** – the concepts transfer 1:1.
- **Business-Driven Development:** start from a business question, not a technology. The
  question for the whole semester: *"Who are our customers and how is our business doing?"*
- **Stack and project overview** (E-shop Lakehouse, a bird's-eye view of the medallion architecture).

## Practice (~45 min)

Setup and first queries.

```bash
uv sync                 # installs the backbone stack
uv run eshop datagen    # generates source data into data/raw/
uv run eshop doctor     # verifies the environment
```

### SQL basics, live (marimo notebook)

Before the fill-in exercise, walk through six core SQL building blocks — **SELECT/FROM, WHERE,
JOIN, aggregation + GROUP BY, window functions (LAG/LEAD), CTE** — each as task → query → result,
running live against the raw e-shop sources:

```bash
just notebook sessions/01-foundations/exercise/sql_basics_notebook.py
# (equivalent) uv run marimo edit sessions/01-foundations/exercise/sql_basics_notebook.py
```

It opens in the browser; edit any query and re-run its cell to experiment. This is a worked
walkthrough, not a fill-in exercise — the exercise below reuses the same six ideas on new questions.

### Exercise: fill in the `# TODO`s in `sessions/01-foundations/exercise/explore.py`

1. How many customers and products do we have? (SQL over CSV)
2. Daily revenue (SQL over the `orders` + `order_items` tables in SQLite).
3. Top 5 products by revenue.
4. Orders per status (`GROUP BY status`).
5. Average order value (a CTE with per-order totals, then average them).
6. Save daily revenue to Parquet (`data/raw/daily_revenue.parquet`).
7. **(harder)** Month-over-month revenue growth using the window function `lag()`.

Run:

```bash
uv run python sessions/01-foundations/exercise/explore.py
```

## Deliverable / checkpoint

- Working environment (`uv run eshop doctor` passes).
- Completed `explore.py` that prints 3 results and writes a Parquet file.
- **checkpoint-01** = this state.

## Common mistakes / notes for the instructor

- Students without `uv` – point them to installation ahead of time (in the invite to the first
  class); see the "Prerequisites" section in the repo README (just `uv` is required, nothing else).
- `just notebook ...` opens marimo in a new browser tab – if it opens blank, refresh once (the
  server needs a moment to start on the first run).
- DuckDB reads CSV via `read_csv_auto('...')` and SQLite via `sqlite_scan('db','table')` –
  show that **no server is needed**.
- Emphasize that the data is intentionally "dirty" (we'll see in session 5) – ignore it for now.
