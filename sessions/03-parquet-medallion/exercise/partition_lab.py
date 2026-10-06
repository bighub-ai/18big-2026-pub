"""Session 3 – columnar storage and partitioning lab.

Fill in each TODO, then run and compare the numbers.
Run with:  uv run python sessions/03-parquet-medallion/exercise/partition_lab.py

Reminders:
  - Polars partitioned write:  df.write_parquet(dir, partition_by=["col", ...])
  - DuckDB reads a partitioned dataset:  read_parquet('dir/**/*.parquet', hive_partitioning=true)
  - Pruning happens when you filter on a partition column.
"""

from __future__ import annotations

import shutil
import time

import duckdb
import polars as pl

from eshop.config import settings


def _time_query(con: duckdb.DuckDBPyConnection, sql: str, repeat: int = 5) -> float:
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        best = min(best, time.perf_counter() - t0)
    return best * 1000  # ms


def main(quiet: bool = False) -> dict:
    bronze_orders = settings.bronze_dir / "orders" / "data.parquet"
    df = pl.read_parquet(bronze_orders).with_columns(
        pl.col("order_ts").str.to_datetime(strict=False).dt.date().alias("order_date")
    )

    # --- Task 1: write a Hive-partitioned copy (one folder per order_date) -------
    part_dir = settings.data_dir / "lab" / "orders_by_date"
    if part_dir.exists():
        shutil.rmtree(part_dir)
    # TODO(03): write df partitioned by order_date into part_dir
    ...

    # --- Task 2: pick a day to filter on (hint: df["order_date"].max()) ----------
    # TODO(03): choose target_day
    target_day = ...

    con = duckdb.connect()
    flat = str(bronze_orders)
    part = f"{part_dir}/**/*.parquet"

    # --- Task 3: full scan vs. partition-pruned scan ----------------------------
    t_flat = _time_query(
        con,
        f"SELECT count(*) FROM read_parquet('{flat}') "
        f"WHERE order_ts::TIMESTAMP::DATE = DATE '{target_day}'",
    )
    # TODO(03): complete the WHERE so it filters on the partition column order_date
    t_part = _time_query(
        con,
        f"SELECT count(*) FROM read_parquet('{part}', hive_partitioning=true) WHERE ...",
    )

    # --- Task 4: CSV vs. Parquet size (compression) -----------------------------
    # Write df out as CSV, then compare the byte sizes of the CSV and the Parquet file.
    csv_path = settings.data_dir / "lab" / "orders.csv"
    # TODO(03): write df to csv_path, then set csv_size / parquet_size from .stat().st_size
    csv_size = ...
    parquet_size = ...
    ratio = round(csv_size / parquet_size, 1)

    # --- Task 5 (harder): two-level year/month partitioning ---------------------
    # Derive order_year and order_month, write partitioned by BOTH, then run a query filtering
    # on year AND month and confirm it is still pruned (fast).
    # TODO(03): add order_year / order_month columns (dt.year(), dt.month())
    df2 = ...
    ym_dir = settings.data_dir / "lab" / "orders_by_year_month"
    if ym_dir.exists():
        shutil.rmtree(ym_dir)
    # TODO(03): write df2 partitioned by ["order_year", "order_month"]
    ...
    y, m = int(df["order_date"].max().year), int(df["order_date"].max().month)
    # TODO(03): count rows for that year+month over the partitioned dataset (pruned)
    t_ym = _time_query(
        con,
        f"SELECT count(*) FROM read_parquet('{ym_dir}/**/*.parquet', hive_partitioning=true) "
        f"WHERE ...",
    )

    result = {
        "target_day": str(target_day),
        "ms_full_scan": round(t_flat, 2),
        "ms_pruned": round(t_part, 2),
        "ms_year_month_pruned": round(t_ym, 2),
        "csv_vs_parquet_ratio": ratio,
        "partition_dir": str(part_dir),
    }
    if not quiet:
        print(result)
    return result


if __name__ == "__main__":
    main()
