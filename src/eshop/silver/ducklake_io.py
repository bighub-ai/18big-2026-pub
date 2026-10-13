"""Session 4 (bonus) – DuckLake: the same table-format idea, catalog-in-a-database.

Delta Lake keeps its transaction log as JSON files next to the data (`delta_io.py`). DuckLake keeps
the catalog (table list, schema, snapshot history) as rows in an ordinary SQL database instead – here
a plain SQLite file – with data still landing as Parquet next to it. Same guarantees (ACID, time
travel, schema evolution), zero bespoke log format, zero extra infrastructure.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import polars as pl

from eshop.config import settings


def ducklake_connect(catalog_path: Path, data_path: Path) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection with a DuckLake catalog attached, backed by a SQLite file."""
    con = duckdb.connect()
    con.execute("INSTALL ducklake")
    con.execute("INSTALL sqlite")
    # A DuckLake catalog is just rows in a SQL database (here SQLite) + Parquet files under DATA_PATH.
    # TODO(4): ATTACH a DuckLake catalog backed by SQLite at `catalog_path`, storing data files under `data_path`
    con.execute("USE lake")
    return con


def demo_ducklake() -> dict:
    """Build a DuckLake customers table and exercise insert + update + time travel."""
    catalog_path = settings.silver_dir / "customers_ducklake_catalog.sqlite"
    data_path = settings.silver_dir / "customers_ducklake"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    if catalog_path.exists():
        catalog_path.unlink()
    if data_path.exists():
        shutil.rmtree(data_path)

    src_path = settings.bronze_dir / "customers" / "data.parquet"
    con = ducklake_connect(catalog_path, data_path)

    # initial load – each DDL/DML statement mints a new snapshot; remember this one's id (not
    # necessarily 0: snapshot 0 is the ATTACH itself, creating the empty `main` schema)
    con.execute(
        "CREATE OR REPLACE TABLE customers AS SELECT * FROM read_parquet(?)", [str(src_path)]
    )
    v0_snapshot = con.execute("SELECT max(snapshot_id) FROM ducklake_snapshots('lake')").fetchone()[0]
    v0_rows = con.execute("SELECT count(*) FROM customers").fetchone()[0]

    # simulate a change feed: update 1 existing customer + insert 1 brand-new one (2 more snapshots)
    con.execute("UPDATE customers SET email = 'updated@example.com' WHERE customer_id = 1")
    new_id = con.execute("SELECT max(customer_id) + 1 FROM customers").fetchone()[0]
    con.execute(
        "INSERT INTO customers SELECT * REPLACE (? AS customer_id) FROM customers LIMIT 1",
        [new_id],
    )
    v1_rows = con.execute("SELECT count(*) FROM customers").fetchone()[0]

    # Time travel: read the table as it was right after the initial load, before the update/insert.
    # TODO(4): read `customers` as of `v0_snapshot`, using DuckLake's AT (VERSION => ...) syntax

    n_snapshots = con.execute("SELECT count(*) FROM ducklake_snapshots('lake')").fetchone()[0]
    updated_email_present = (
        con.execute("SELECT email FROM customers WHERE customer_id = 1").fetchone()[0]
        == "updated@example.com"
    )
    con.close()

    return {
        "v0_rows": v0_rows,
        "v1_rows": v1_rows,
        "n_snapshots": n_snapshots,
        "v0_email_unchanged": v0.filter(pl.col("customer_id") == 1)["email"].item()
        != "updated@example.com",
        "updated_email_present": updated_email_present,
    }
