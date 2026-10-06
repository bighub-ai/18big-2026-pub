"""Session 2 – ingestion of source systems into the Bronze layer.

Bronze = "land the data as it arrived". We do not change the content; we only add technical
metadata (when, from where, which batch, a content hash for auditing). Sources: CSV files and a
SQLite database (a JDBC-like operational system). Partitioning is added in session 3.

Ingestion is *metadata-driven*: which sources exist and how each is loaded (full / incremental,
watermark column) lives in `sources.yml`, not in code. `ingest_all` just walks that catalogue.
"""

from __future__ import annotations

import datetime as dt
import uuid

from pathlib import Path

import duckdb
import polars as pl
import yaml

from eshop.config import settings

# The source catalogue (metadata) that drives ingestion – see src/eshop/datagen for the sources.
SOURCES_FILE = Path(__file__).with_name("sources.yml")


def load_sources() -> list[dict]:
    """Read the source catalogue: one entry per source, with its type and load mode."""
    return yaml.safe_load(SOURCES_FILE.read_text())["sources"]


def _add_ingestion_metadata(df: pl.DataFrame, source: str, batch_id: str) -> pl.DataFrame:
    """Attach lineage + a content hash so we always know each Bronze row's origin and identity."""
    business_cols = df.columns  # the original columns, before we add anything

    # A content hash as an audit column: Bronze doesn't compare rows, but Silver can use it to dedup.
    # Concatenate all business columns into one string and hash it (deterministic, seed 0).
    df = df.with_columns(
        pl.concat_str([pl.col(c).cast(pl.Utf8) for c in business_cols], separator="|")
        .hash(0)
        .cast(pl.Utf8)  # string, so it survives Delta (which has no unsigned int type)
        .alias("_row_hash")
    )

    # Technical lineage: when did it land, from which source, in which ingest batch.
    df = df.with_columns(
        pl.lit(dt.datetime.now()).alias("_ingested_at"),
        pl.lit(source).alias("_source"),
        pl.lit(batch_id).alias("_batch_id"),
    )
    return df


def _write_bronze(name: str, df: pl.DataFrame) -> None:
    out = settings.bronze_dir / name
    out.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out / "data.parquet")


def ingest_csv(name: str, batch_id: str, file: str | None = None) -> int:
    """Read a CSV source and land it in Bronze (full load)."""
    src = settings.raw_dir / (file or f"{name}.csv")
    df = pl.read_csv(src)
    df = _add_ingestion_metadata(df, src.name, batch_id)
    _write_bronze(name, df)
    return df.height


def ingest_sqlite(table: str, batch_id: str) -> int:
    """Read a SQLite table (JDBC-like source) and land it in Bronze."""
    con = duckdb.connect()
    # DuckDB reads a SQLite table directly – no running DB server needed.
    df = con.execute(f"SELECT * FROM sqlite_scan('{settings.source_db}', '{table}')").pl()
    df = _add_ingestion_metadata(df, f"{settings.source_db.name}:{table}", batch_id)
    _write_bronze(table, df)
    return df.height


def ingest_incremental(table: str = "orders", key: str = "order_id", batch_id: str | None = None) -> int:
    """Harder: an *incremental* SQLite ingest driven by a watermark.

    Instead of re-reading the whole table, remember how far we got – the highest `key` already in
    Bronze is the watermark – and read only rows above it. Works for append-only tables with a
    growing key (it cannot see updates or deletes). New rows are appended as they arrived; Bronze
    doesn't compare or deduplicate, that's Silver's job. Returns the number of newly landed rows.
    """
    batch_id = batch_id or uuid.uuid4().hex[:8]
    out = settings.bronze_dir / table / "data.parquet"
    existing = pl.read_parquet(out) if out.exists() else None

    con = duckdb.connect()
    # Watermark = max(key) already landed; nothing landed yet → read the whole table.
    watermark = existing[key].max() if existing is not None else None
    con.execute(f"ATTACH '{settings.source_db}' AS source (TYPE sqlite)")
    query = f"SELECT * FROM source.{table}"
    if watermark is not None:
        query += f" WHERE {key} > {watermark}"
    incoming = con.execute(query).pl()
    incoming = _add_ingestion_metadata(incoming, f"{settings.source_db.name}:{table}", batch_id)
    # Append: keep what Bronze already has and add the new rows below it (no comparing, no dedup).
    _write_bronze(table, incoming if existing is None else pl.concat([existing, incoming]))
    return incoming.height


def ingest_source(src: dict, batch_id: str) -> int:
    """Land one catalogue entry: pick the loader from its metadata (type + load mode)."""
    if src["type"] == "csv":
        return ingest_csv(src["name"], batch_id, src.get("file"))
    if src["type"] == "sqlite":
        if src.get("load") == "incremental":
            return ingest_incremental(src["table"], src["watermark"], batch_id)
        return ingest_sqlite(src["table"], batch_id)
    raise ValueError(f"unknown source type {src['type']!r} for {src['name']!r}")


def ingest_all() -> dict[str, int]:
    """Ingest every catalogued source into Bronze under one batch id. Returns rows landed per entity."""
    batch_id = uuid.uuid4().hex[:8]
    return {src["name"]: ingest_source(src, batch_id) for src in load_sources()}
