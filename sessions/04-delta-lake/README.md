# Session 4 — Delta Lake: a table format on top of Parquet

**Syllabus:** topic 3 · **Layer:** Silver (mechanics)

## Goal

Students understand **why a Data Lake alone is not enough** and can use a transactional table
format: append, upsert (MERGE), schema evolution, time travel.

## Theory (~40 min)

- **Parquet = files, no transactions:** no ACID, no reliable upsert, no history. What breaks when
  two writers touch the same folder.
- **Delta Lake = a transaction log on top of Parquet:** ACID commits, `MERGE`, schema evolution,
  **time travel**, `OPTIMIZE`/`VACUUM` (conceptually). All local via `deltalake` (delta-rs), no JVM.
- **Where we use it:** incrementally maintained Silver core tables (customers), and later the
  target of CDC merges (session 10).
- Append vs. overwrite vs. **upsert (MERGE)**; why time travel matters (audits, reproducibility, rollback).
- **The table-format landscape.** Delta isn't the only answer to "Parquet has no transactions":
  - **Iceberg** (Netflix/Apache) — the same idea (snapshots + manifests instead of a single JSON
    log), built multi-engine-first: Spark, Trino, Flink, Snowflake all read it natively. Today the
    most common choice when no single vendor owns the whole stack.
  - **Hudi** (Uber) — record-level indexing, optimized for high-frequency upserts and
    streaming-first ingestion, at the cost of more write-side complexity.
  - All three need a **catalog** to answer "what is the current version of table X, and where do
    its files live?" — that's a separate concern from the table format itself. **Unity Catalog**
    (Databricks) is the best-known managed catalog today; it started Delta-only and now also
    speaks Iceberg (via UniForm / the Iceberg REST protocol). Open alternatives exist (Polaris,
    Nessie) but need a running catalog service — that's infrastructure we deliberately skip here.
  - **DuckLake** takes a different shortcut: instead of a bespoke log or a catalog *service*, the
    catalog (table list, schema, snapshot history) is just **rows in an ordinary SQL database**
    (DuckDB, SQLite, Postgres) — data still lands as Parquet files next to it. Same guarantees
    (ACID, time travel, schema evolution), zero extra infrastructure. That's why we exercise it
    directly below, alongside Delta, backed by a plain SQLite file as the catalog.

## Practice (~45 min)

You fill in the `# TODO`s in `src/eshop/silver/delta_io.py`:

1. `write_delta` – write a Polars frame as a Delta table with the given mode.
2. `upsert_delta` – `MERGE` a change set into the table on a key (update matched, insert new).
3. `read_delta` – time-travel to a historical version when `version` is given.
4. **(harder)** `append_with_evolution` – append rows that add a new column, evolving the schema
   (`mode="append", schema_mode="merge"`).

Then run the demo (initial load → upsert → time travel):

```bash
uv run eshop datagen && uv run eshop ingest   # if needed
uv run eshop delta-demo
```

### Extra (bonus): the same idea over DuckLake + SQLite

`src/eshop/silver/ducklake_io.py` builds the **same** customers demo (write → update/insert →
time travel) but through DuckLake, with the catalog stored in a plain SQLite file
(`data/lake/silver/customers_ducklake_catalog.sqlite`) and data as Parquet next to it
(`data/lake/silver/customers_ducklake/`). Fill in the 2 `# TODO`s:

1. `ducklake_connect` – `ATTACH` a DuckLake catalog backed by SQLite at a given path.
2. `demo_ducklake` – read the table back **as of the snapshot right after the initial load**
   (before the later update/insert), using DuckLake's `AT (VERSION => ...)` time-travel syntax, to
   compare against Delta's `load_as_version`. (Snapshot 0 is the `ATTACH` itself, not the table – a
   good "gotcha" to point out: DuckLake versions the whole catalog, not just one table.)

```bash
uv run eshop ducklake-demo
```

Needs internet the first time (DuckDB downloads the `ducklake` and `sqlite` extensions once, then
caches them locally).

## Deliverable / checkpoint

- A `data/lake/silver/customers_delta/` Delta table with ≥ 2 versions; the upsert adds one new
  customer and updates existing ones; version 0 is still readable (time travel).
- (Bonus) A `data/lake/silver/customers_ducklake_catalog.sqlite`-backed DuckLake table showing the
  same append/update/time-travel behavior via a SQL catalog instead of a Delta log.
- **checkpoint-04** = this state (the Delta table is required; the DuckLake bonus is not part of
  the checkpoint test).
