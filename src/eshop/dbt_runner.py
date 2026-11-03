"""Session 6 – run the dbt-duckdb project over the Silver layer.

dbt does declarative SQL transformations (Silver → Gold). Since our Silver tables are Delta, we
first load them (via the deltalake reader, no extension needed) into the DuckDB file that dbt uses,
under the `silver` schema. Then `dbt build` materializes staging/intermediate/marts and runs tests.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
from deltalake import DeltaTable

from eshop.config import REPO_ROOT, settings

DBT_DIR = REPO_ROOT / "dbt" / "eshop_dbt"
SILVER_TABLES = ["customers", "orders", "order_items", "payments", "products"]


def load_silver_to_duckdb(duckdb_path: Path) -> None:
    """Load each Silver Delta table into DuckDB under the `silver` schema (dbt sources)."""
    con = duckdb.connect(str(duckdb_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")
    for name in SILVER_TABLES:
        arrow = DeltaTable(str(settings.silver_dir / name)).to_pyarrow_table()
        con.register("t", arrow)
        con.execute(f"CREATE OR REPLACE TABLE silver.{name} AS SELECT * FROM t")
        con.unregister("t")
    con.close()


def run_dbt(duckdb_path: Path, command: list[str] | None = None) -> None:
    dbt_exe = shutil.which("dbt") or str(Path(sys.executable).parent / "dbt")
    env = {
        **os.environ,
        "ESHOP_DUCKDB": str(duckdb_path),
        "ESHOP_GOLD": str(settings.gold_dir),  # Gold models are written here as Parquet
    }
    subprocess.run(
        [dbt_exe, *(command or ["build"]),
         "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        env=env,
        check=True,
    )


def build_marts() -> Path:
    """Prepare the DuckDB file from Silver and run `dbt build`. Returns the DuckDB path."""
    duckdb_path = settings.data_dir / "eshop.duckdb"
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    settings.gold_dir.mkdir(parents=True, exist_ok=True)  # Gold Parquet target must exist
    load_silver_to_duckdb(duckdb_path)
    run_dbt(duckdb_path)
    return duckdb_path
