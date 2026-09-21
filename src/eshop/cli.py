"""Course CLI: `uv run eshop <command>`.

Grows over time with commands for individual sessions (ingest, silver, gold, ...).
For now it provides `datagen` (session 1) and `doctor` (environment check).
"""

from __future__ import annotations

import duckdb
import typer
from rich.console import Console
from rich.table import Table

from eshop.config import settings
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
