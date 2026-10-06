# Session 3 — Parquet and the medallion architecture

**Syllabus:** topic 3 · **Layer:** Bronze/Silver (storage)

## Goal

Students understand why columnar storage is the foundation of analytics and can use partitioning
and predicate pushdown. They understand the purpose of the medallion layers.

## Theory (~40 min)

- **Row vs. columnar storage** – why analytics loves columns (only read what you select).
- **Parquet internals:** row groups, compression, encoding (dictionary/RLE), column statistics.
- **Projection & predicate pushdown** – the engine reads only the needed columns and skips row
  groups / partitions that can't match the filter.
- **Partitioning** (Hive-style `col=value/` folders) and **partition pruning**.
- **File format vs. table format:** Parquet is just files (preparing for Delta in session 4).
- **Medallion layers:** the purpose of Bronze / Silver / Gold.

## Practice (~45 min)

A measurement lab. You fill in the `# TODO`s in
`sessions/03-parquet-medallion/exercise/partition_lab.py`:

1. Write Bronze orders as a **Hive-partitioned** dataset (one folder per `order_date`).
2. Pick a day to filter on.
3. Complete the pruned query's `WHERE` clause (filter on the partition column).
4. Write the data to CSV and compare CSV vs. Parquet file size (compression ratio).
5. **(harder)** Build a two-level `year/month` partitioning and run a pruned month query.

Then run and compare the timings (full scan vs. partition-pruned):

```bash
uv run eshop datagen && uv run eshop ingest   # if you don't have Bronze yet
uv run python sessions/03-parquet-medallion/exercise/partition_lab.py
```

## Deliverable / checkpoint

- A partitioned dataset under `data/lab/orders_by_date/` and a printed timing comparison.
- **checkpoint-03** = this state.
