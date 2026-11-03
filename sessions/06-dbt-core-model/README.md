# Session 6 — Core business model and dbt

**Syllabus:** topic 4 · **Layer:** Silver → (preparing Gold)

## Goal

Students can design a dimensional model (facts/dimensions) and implement it declaratively in dbt
with tests and lineage.

## Theory (~40 min)

- **Dimensional modeling:** star schema, facts vs. dimensions, grain, surrogate keys, SCD (briefly).
- **Physical model and DDL SQL** – what a model materializes into.
- **dbt:** models, `source`/`ref`, materializations (view/table), tests, docs, the **lineage graph**.
- **Tool responsibilities:** *Delta* = storage/ACID; *dbt* = declarative SQL transformations. They
  don't overlap. Here dbt reads Silver (loaded into DuckDB) and builds the star schema.

## Practice (~45 min)

You fill in the `# TODO`s in the dbt models:

1. `models/staging/stg_order_items.sql` – compute `line_amount` = `qty * unit_price`.
2. `models/intermediate/int_customer_orders.sql` – aggregate per customer (order count + revenue).
3. `models/marts/fct_orders.sql` – one row per order with amount and item count.
4. **(harder)** `models/marts/dim_customer.sql` – add `revenue_rank` with a window function
   (`rank() over (order by revenue desc)`).

Then build and explore the project:

```bash
uv run eshop datagen && uv run eshop ingest && uv run eshop silver   # if needed
uv run eshop dbt-build                                                # loads Silver → DuckDB, runs dbt build
uv run dbt docs generate --project-dir dbt/eshop_dbt --profiles-dir dbt/eshop_dbt
uv run dbt docs serve   --project-dir dbt/eshop_dbt --profiles-dir dbt/eshop_dbt   # lineage graph
```

## Deliverable / checkpoint

- `dbt build` materializes `stg_*`, `int_customer_orders`, `dim_customer`, `fct_orders` and all
  tests pass (`unique`, `not_null`).
- **checkpoint-06** = this state.
