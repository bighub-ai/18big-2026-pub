"""Session 4 – Delta Lake: a transactional table format on top of Parquet.

Parquet alone = files without transactions (no reliable upsert, no history, no safe schema change).
Delta Lake adds a transaction log → ACID, MERGE/upsert, schema evolution, and time travel. Here we
use it for the Silver customer table, maintained incrementally (and later the CDC target, S10).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import polars as pl
from deltalake import DeltaTable, write_deltalake

from eshop.config import settings


def write_delta(path: Path, df: pl.DataFrame, mode: str = "overwrite") -> None:
    """Write a Polars frame as a Delta table (mode: 'overwrite' or 'append')."""
    # write_deltalake takes an Arrow table; df.to_arrow() converts a Polars frame.
    # TODO(4): write df to the Delta table at `path` using the given mode


def upsert_delta(path: Path, df: pl.DataFrame, key: str) -> None:
    """MERGE df into an existing Delta table on `key`: update matches, insert new rows."""
    dt = DeltaTable(str(path))
    # A MERGE matches source (s) to target (t) on the key, then updates matches and inserts the rest.
    # TODO(4): MERGE df into dt on t.<key> = s.<key>; when matched update all, else insert all


def read_delta(path: Path, version: int | None = None) -> pl.DataFrame:
    """Read a Delta table; if `version` is given, time-travel to that historical version."""
    dt = DeltaTable(str(path))
    # Time travel: load an older snapshot of the table by its version number.
    # TODO(4): when version is not None, load that historical version (dt.load_as_version)
    return pl.from_arrow(dt.to_pyarrow_table())


def append_with_evolution(path: Path, df: pl.DataFrame) -> None:
    """Harder: append rows that introduce a NEW column, evolving the table schema safely.

    A plain append would reject a mismatched schema. Delta can evolve the schema on write so old
    rows get NULL for the new column and new rows carry it – all as one atomic, versioned commit.
    """
    # TODO(4): append df with schema evolution enabled (mode="append", schema_mode="merge")


def table_history_len(path: Path) -> int:
    return len(DeltaTable(str(path)).history())


def demo_customers() -> dict:
    """Build the Silver customers Delta table and exercise append + upsert + time travel + evolution."""
    src = pl.read_parquet(settings.bronze_dir / "customers" / "data.parquet")
    path = settings.silver_dir / "customers_delta"
    if path.exists():
        shutil.rmtree(path)

    # v0: initial load
    write_delta(path, src, mode="overwrite")
    v0_rows = read_delta(path, version=0).height

    # simulate a change feed: update 5 existing customers + 1 brand-new customer
    updates = src.head(5).with_columns(pl.lit("updated@example.com").alias("email"))
    new_id = int(src["customer_id"].max()) + 1
    new = src.head(1).with_columns(
        pl.lit(new_id).cast(src["customer_id"].dtype).alias("customer_id")
    )
    upsert_delta(path, pl.concat([updates, new]), key="customer_id")
    after_upsert = read_delta(path)

    # schema evolution: append a small batch carrying a new `loyalty_tier` column
    loyalty = after_upsert.head(3).with_columns(pl.lit("gold").alias("loyalty_tier"))
    append_with_evolution(path, loyalty)
    final = read_delta(path)

    return {
        "v0_rows": v0_rows,
        "v1_rows": after_upsert.height,
        "history_len": table_history_len(path),
        "updated_email_present": (
            after_upsert.filter(pl.col("customer_id") == 1)["email"].item()
            == "updated@example.com"
        ),
        "schema_evolved": "loyalty_tier" in final.columns,
    }
