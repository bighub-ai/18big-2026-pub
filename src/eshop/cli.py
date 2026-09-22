"""Course CLI: `uv run eshop <command>`.

Grows over time with commands for individual sessions (ingest, silver, gold, ...).
For now it provides `datagen` (session 1) and `doctor` (environment check).
"""

from __future__ import annotations

import duckdb
import typer
from rich.console import Console
from rich.table import Table

from eshop.config import REPO_ROOT, settings
from eshop.datagen import generate_all

app = typer.Typer(help="18BIG – E-shop Lakehouse CLI", no_args_is_help=True)
console = Console()


@app.command()
def datagen() -> None:
    """Generate synthetic source data into data/raw/ (CSV + SQLite)."""
    console.print(f"[bold]Generating source data[/] (seed={settings.seed}) → {settings.raw_dir}")
    counts = generate_all()
    table = Table("entity", "rows")
    for name, n in counts.items():
        table.add_row(name, f"{n:,}")
    console.print(table)
    console.print("[green]Done.[/] Now try: [bold]uv run eshop doctor[/]")


@app.command()
def ingest() -> None:
    """Ingest raw sources into the Bronze layer (session 2)."""
    from eshop.ingestion.bronze import ingest_all

    console.print(f"[bold]Ingesting sources → Bronze[/] → {settings.bronze_dir}")
    counts = ingest_all()
    table = Table("entity", "rows")
    for name, n in counts.items():
        table.add_row(name, f"{n:,}")
    console.print(table)
    console.print("[green]Done.[/] Bronze layer populated.")


@app.command()
def silver() -> None:
    """Build the Silver layer: clean, enforce contracts, quarantine bad data (session 5)."""
    from eshop.silver.build_silver import build_silver

    console.print(f"[bold]Building Silver[/] → {settings.silver_dir}")
    r = build_silver()
    table = Table("entity", "valid", "quarantine")
    for name, v in r.items():
        table.add_row(name, f"{v['valid']:,}", f"{v['quarantine']:,}")
    console.print(table)
    console.print(f"[green]Done.[/] Bad rows quarantined in {settings.quarantine_dir}")


@app.command()
def pipeline() -> None:
    """Run the whole pipeline end-to-end via Dagster (materialize all assets, session 9)."""
    import sys

    from dagster import materialize

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from dagster_project.definitions import all_assets

    console.print("[bold]Materializing all Dagster assets[/] (raw → bronze → silver → marts)")
    result = materialize(all_assets)
    status = "[green]SUCCESS[/]" if result.success else "[red]FAILED[/]"
    console.print(f"Pipeline: {status}")
    console.print("Tip: [bold]uv run dagster dev -m dagster_project.definitions[/] for the UI.")


@app.command()
def serve() -> None:
    """Serve Gold to consumers: load a KV store and publish an ODS (session 12)."""
    from eshop.serving.kv import load_kv, lookup
    from eshop.serving.ods import publish_ods

    n_kv = load_kv()
    n_ods = publish_ods()
    console.print("[bold]Serving Gold[/]")
    console.print(f"  KV store keys:   {n_kv:,}  (e.g. lookup(1) → {lookup(1)})")
    console.print(f"  ODS (SQLite):    {n_ods:,} rows in customer_360")
    console.print("[green]Done.[/] Analytical lakehouse → operational serving.")


@app.command()
def train() -> None:
    """Train the churn model and log it to local MLflow (session 11)."""
    from eshop.ml.train import train_and_log

    console.print("[bold]Training churn model[/] (features from Gold customer_360)")
    r = train_and_log()
    console.print(f"  ROC AUC:  {r['roc_auc']:.3f}  (train={r['n_train']}, test={r['n_test']})")
    console.print(f"[green]Done.[/] Logged to {settings.data_dir / 'mlflow.db'}")
    console.print("Tip: [bold]uv run mlflow ui --backend-store-uri "
                  f"sqlite:///{settings.data_dir / 'mlflow.db'}[/]")


@app.command()
def drift() -> None:
    """Generate an Evidently data-drift report (session 11)."""
    from eshop.ml.monitor import drift_report

    out = settings.data_dir / "reports" / "drift.html"
    drift_report(out)
    console.print(f"[green]Done.[/] Drift report → {out}")


@app.command()
def stream() -> None:
    """Produce events to a local topic and consume by offset; show idempotent replay (session 10)."""
    from eshop.streaming.log import consume, produce

    produce(200, seed=1)
    first = consume()
    second = consume()  # nothing new – offset already advanced
    console.print(f"[bold]Streaming[/]: produced 200 events")
    console.print(f"  consumed (new):        {first}")
    console.print(f"  consumed again (new):  {second}  (0 = idempotent, offset-based)")


@app.command()
def cdc_demo() -> None:
    """Apply an insert/update/delete change feed to a Delta table via MERGE + delete (session 10)."""
    from eshop.cdc.capture import demo_cdc

    r = demo_cdc()
    console.print("[bold]CDC demo[/] (orders_cdc Delta table)")
    console.print(f"  rows before → after:  {r['before']} → {r['after']}")
    console.print(f"  update applied:       order status now '{r['updated_status']}'")
    console.print(f"  delete applied:       row gone = {r['deleted_gone']}")
    console.print(f"  insert applied:       new row present = {r['inserted_present']}")


@app.command()
def governance() -> None:
    """Validate the customers data contract and write a PII-masked share (session 8)."""
    import polars as pl

    from eshop.governance.contract import load_contract, pii_columns, validate_contract
    from eshop.governance.masking import mask_pii
    from eshop.silver.delta_io import read_delta

    contract = load_contract(REPO_ROOT / "contracts" / "customers.yml")
    df = read_delta(settings.silver_dir / "customers")

    check = validate_contract(df, contract)
    pii = pii_columns(contract)
    masked = mask_pii(df, pii)

    out = settings.gold_dir / "customers_shared.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    masked.write_parquet(out)

    console.print(f"contract '{contract['name']}' owner={contract['owner']} "
                  f"classification={contract['classification']}")
    console.print(f"  schema matches contract: {check['ok']}  missing={check['missing']}")
    console.print(f"  PII columns masked:      {pii}")
    console.print(f"[green]Done.[/] Shareable (masked) copy → {out}")


@app.command()
def dbt_build() -> None:
    """Load Silver into DuckDB and run the dbt star-schema build (session 6)."""
    from eshop.dbt_runner import build_marts

    console.print("[bold]Loading Silver → DuckDB and running dbt build[/]")
    path = build_marts()
    console.print(f"[green]Done.[/] dbt models materialized in {path}")


@app.command()
def delta_demo() -> None:
    """Build the Silver customers Delta table with append + upsert + time travel (session 4)."""
    from eshop.silver.delta_io import demo_customers

    console.print("[bold]Delta Lake demo: Silver customers[/]")
    r = demo_customers()
    console.print(f"  v0 rows:            {r['v0_rows']:,}")
    console.print(f"  v1 rows (upserted): {r['v1_rows']:,}  (+1 new customer)")
    console.print(f"  delta history:      {r['history_len']} versions")
    console.print(f"  time travel works:  v0 preserved, latest has updated email = {r['updated_email_present']}")
    console.print("[green]Done.[/]")


@app.command()
def doctor() -> None:
    """Verify the environment and data work (a DuckDB query over the source data)."""
    if not settings.source_db.exists():
        console.print("[red]No data.[/] Run first: [bold]uv run eshop datagen[/]")
        raise typer.Exit(1)

    con = duckdb.connect()
    n_customers = con.execute(
        f"SELECT count(*) FROM read_csv_auto('{settings.raw_dir / 'customers.csv'}')"
    ).fetchone()[0]
    n_orders = con.execute(
        f"SELECT count(*) FROM sqlite_scan('{settings.source_db}', 'orders')"
    ).fetchone()[0]

    console.print("[green]✓ environment OK[/]")
    console.print(f"  customers (CSV):    {n_customers:,}")
    console.print(f"  orders (SQLite):    {n_orders:,}")


if __name__ == "__main__":
    app()
