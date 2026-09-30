# Session 2 — Data sources and Bronze ingestion

**Syllabus:** topic 2 · **Layer:** Bronze

## Goal

Students understand the types of data sources and integration patterns, and can "land" data into
the Bronze layer without changing the content but adding technical metadata.

## Theory (~40 min)

- **Source types:** files / object storage, relational DB (JDBC), queues (a preview only – detail
  in session 10). What "JDBC-like" means; here SQLite plays the operational system.
- **Integration patterns:** full vs. incremental load, batch vs. stream, push vs. pull.
- **Metadata-driven ingestion:** one generic loader + a source catalogue (`sources.yml`) that says
  which sources exist and how each is loaded. New source = new config entry, not new code.
- **Idempotence** – running ingestion twice must not corrupt Bronze. Why it matters.
- **Schema-on-read** vs. schema-on-write.
- **Bronze = "what arrived, we touch as little as possible."** Why we keep the raw form and only
  add lineage metadata (`_ingested_at`, `_source`, `_batch_id`).

## Practice (~45 min)

You fill in the `# TODO`s in `src/eshop/ingestion/bronze.py`:

1. `_add_ingestion_metadata` – add the lineage columns `_ingested_at`, `_source`, `_batch_id`
   (the `_row_hash` audit column is already there).
2. `ingest_sqlite` – read the whole table from SQLite via DuckDB's `sqlite_scan` (full load).
3. **`ingest_incremental` – the watermark:** take the highest `order_id` already in Bronze and
   read only newer rows from SQLite, this time via DuckDB's `ATTACH ... (TYPE sqlite)`
   (first run: no Bronze yet → read everything).
4. **`ingest_incremental` – the append:** add the new rows to what Bronze already has. Re-running
   with no new data must land **zero** rows. Bronze doesn't compare or deduplicate – that's Silver.
5. **(metadata-driven)** Read `src/eshop/ingestion/sources.yml` and `ingest_source`. Switch
   `order_items` to `load: incremental` with `watermark: order_id` – **no code change** – and
   re-run `eshop ingest`. Why is `order_id` a safe watermark for order items?

Then run and inspect the result (`just <cmd>` or the `uv run eshop ...` equivalent):

```bash
just datagen             # uv run eshop datagen – only if you don't have data/raw/ yet
just ingest              # uv run eshop ingest  – lands every source into data/lake/bronze/
just bronze orders       # row count, ingest batches and the last rows (note the _ columns)
```

Until the `TODO(2)`s in `ingest_incremental` are filled in, `just ingest` fails – `orders` is an
incremental source in `sources.yml`.

**Try the incremental load:**

```bash
just ingest              # 2nd run: orders → 0 rows (nothing above the watermark)
just new-orders 5        # the "operational system" gets 5 new orders
just ingest              # orders → exactly 5 rows
just bronze orders       # two batches: the initial load + the 5 new orders
```

> Re-running `just datagen` rebuilds the source from scratch (ids start at 1 again), while Bronze
> keeps its watermark. To start over, delete `data/lake/bronze/` too.

## Deliverable / checkpoint

- `data/lake/bronze/<entity>/data.parquet` for every source, each with `_ingested_at`,
  `_source`, `_batch_id`.
- **checkpoint-02** = this state.
