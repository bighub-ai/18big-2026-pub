"""Session 9 – orchestration with Dagster (software-defined assets).

We wrap the pipeline functions built in earlier sessions as dependent assets. Dagster then gives
us the dependency graph, scheduling, retries, and observability for free. Launch the UI with:

    uv run dagster dev -m dagster_project.definitions

Besides the graph itself, this file shows the Dagster features from the lecture, each with a
switch you can flip in the UI:

- run config        – `raw_data`: append new orders / simulate a schema drift (Launchpad)
- retries           – `bronze`: fail the first attempt on purpose, watch the retry succeed
- asset check       – the customers contract is checked on `bronze`; a failure blocks downstream
- dbt as assets     – every dbt model (and its tests) is its own asset (dagster-dbt)
- sensor            – `new_orders_sensor` ingests new orders as soon as they appear in the source
- automation        – Silver and the dbt models update themselves when their upstream changes
- freshness         – the Gold `sales_daily` product is expected to be refreshed at least daily
"""

import os
import shutil
import sqlite3
import sys
from datetime import timedelta
from pathlib import Path

import polars as pl
import polars.selectors as cs
from dagster import (
    AssetCheckResult,
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    AutomationCondition,
    AutomationConditionSensorDefinition,
    Backoff,
    Config,
    DagsterRunStatus,
    DefaultSensorStatus,
    Definitions,
    FreshnessPolicy,
    MaterializeResult,
    MetadataValue,
    RetryPolicy,
    RunRequest,
    RunsFilter,
    ScheduleDefinition,
    SensorEvaluationContext,
    SkipReason,
    TableColumn,
    TableSchema,
    asset,
    asset_check,
    define_asset_job,
    multi_asset,
    sensor,
)
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
from deltalake import DeltaTable

from eshop.config import REPO_ROOT, settings
from eshop.datagen import append_orders, generate_all
from eshop.dbt_runner import DBT_DIR, SILVER_TABLES, load_silver_to_duckdb
from eshop.governance.contract import load_contract, validate_contract
from eshop.ingestion.bronze import ingest_all
from eshop.silver.build_silver import build_silver

# --- metadata helpers ----------------------------------------------------------------------------
# Dagster never opens our lake itself. It only shows what an asset reports back when it
# materializes, so each asset returns a MaterializeResult with row counts, the column schema and a
# preview of the first rows. Numeric metadata is also plotted across runs in the asset's UI.


def _preview(df: pl.DataFrame, n: int = 10) -> MetadataValue:
    """First `n` rows as a Markdown table (rendered in the asset panel)."""
    head = df.head(n).with_columns(cs.float().round(2))
    lines = ["| " + " | ".join(head.columns) + " |", "|" + " --- |" * head.width]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in head.iter_rows()]
    return MetadataValue.md("\n".join(lines))


def _schema(df: pl.DataFrame) -> TableSchema:
    """Column names + types, shown on the asset's overview page."""
    return TableSchema(columns=[TableColumn(name, str(dtype)) for name, dtype in df.schema.items()])


# Declarative automation: "update me when my upstream changed, but only if upstream passed its
# blocking checks". Evaluated by the automation sensor (off by default – turn it on in the UI).
AUTO = AutomationCondition.eager() & AutomationCondition.all_deps_blocking_checks_passed()


# --- sources --------------------------------------------------------------------------------------


class RawDataConfig(Config):
    """Run config for `raw_data`, editable in the UI Launchpad.

    new_orders = 0 → regenerate all sources from the seed (the default).
    new_orders = N → keep the sources and append N new orders, simulating a new business day.
    schema_drift   → the CRM export "loses" its signup_date column. Reversible: the next run
                     without it restores the original file (works with either new_orders mode).
    """

    new_orders: int = 0
    schema_drift: bool = False


def _apply_schema_drift(context: AssetExecutionContext, drift: bool) -> None:
    """Demo: drop signup_date from customers.csv, or undo it from the backup taken before."""
    path = settings.raw_dir / "customers.csv"
    backup = path.with_name("customers.before_drift.csv")
    if drift:
        if not backup.exists():
            shutil.copy(path, backup)
        pl.read_csv(backup).drop("signup_date").write_csv(path)
        context.log.warning("schema drift: customers.csv no longer has a signup_date column")
    elif backup.exists():
        backup.replace(path)
        context.log.info("schema drift undone: customers.csv restored")


@asset(group_name="ingest")
def raw_data(context: AssetExecutionContext, config: RawDataConfig) -> MaterializeResult:
    """Generate synthetic source data (data/raw/), or append new orders to it."""
    if config.new_orders > 0 and settings.source_db.exists():
        r = append_orders(config.new_orders)
        context.log.info(f"appended: {r}")
        metadata = {
            "dagster/row_count": r["last_id"],  # orders in the source (ids are contiguous)
            "new_orders": r["orders"],
            "new_order_items": r["order_items"],
            "new_order_ids": f"{r['first_id']}–{r['last_id']}",
        }
    else:
        counts = generate_all()
        # a fresh customers.csv was just written, so a backup from an earlier drift is stale
        (settings.raw_dir / "customers.before_drift.csv").unlink(missing_ok=True)
        context.log.info(f"generated: {counts}")
        metadata = {"dagster/row_count": counts["orders"], "new_orders": 0} | {
            f"rows_{entity}": n for entity, n in counts.items()
        }
    _apply_schema_drift(context, config.schema_drift)
    return MaterializeResult(metadata=metadata | {"schema_drift": config.schema_drift})


# --- Bronze ---------------------------------------------------------------------------------------


class BronzeConfig(Config):
    """Demo switch: fail the first attempt on purpose to watch the RetryPolicy kick in."""

    simulate_failure: bool = False


@asset(
    # Bronze reads the raw sources, so it depends on raw_data. A RetryPolicy re-runs the asset on
    # transient failures (network, locks) – ingestion is idempotent, so retries are safe.
    # TODO(9): declare that `bronze` depends on `raw_data`
    retry_policy=RetryPolicy(max_retries=2, delay=5, backoff=Backoff.EXPONENTIAL),  # 5 s, 10 s
    group_name="ingest",
)
def bronze(context: AssetExecutionContext, config: BronzeConfig) -> MaterializeResult:
    """Ingest sources into the Bronze layer."""
    if config.simulate_failure and context.retry_number == 0:
        raise RuntimeError("simulated transient failure: source database is locked")
    counts = ingest_all()
    context.log.info(f"bronze rows: {counts}")
    orders = pl.read_parquet(settings.bronze_dir / "orders" / "data.parquet")
    return MaterializeResult(
        metadata={
            "dagster/row_count": orders.height,  # total Bronze orders (grows with incremental loads)
            "dagster/column_schema": _schema(orders),
            "preview_orders": _preview(orders),
            "retry_number": context.retry_number,
        }
        | {f"landed_{entity}": n for entity, n in counts.items()}  # new rows in *this* run
    )


@asset_check(asset=bronze, blocking=True)
def customers_contract(context) -> AssetCheckResult:
    """The customers data still matches its contract (contracts/customers.yml, session 8).

    Checked where data enters the lakehouse: if a source drifts, nothing downstream runs, and
    Silver/Gold keep yesterday's good data instead of being rebuilt from a broken input.
    """
    contract = load_contract(REPO_ROOT / "contracts" / "customers.yml")
    df = pl.read_parquet(settings.bronze_dir / "customers" / "data.parquet")
    # TODO(9): validate `df` against `contract` (S8) and return an AssetCheckResult


# --- Silver ---------------------------------------------------------------------------------------


@multi_asset(
    # One Silver asset per Delta table, all built by one function (build_silver writes them all).
    specs=[
        AssetSpec(
            # dbt names the asset of a source `silver.<table>` (_sources.yml) ["silver", <table>].
            # Using the same key here is all it takes to wire the dbt models to these assets.
            # TODO(9): the asset key of this Silver table, matching dbt's source key
            # TODO(9): every Silver table depends on the `bronze` asset
            automation_condition=AUTO,
            group_name="silver",
        )
        for table in SILVER_TABLES
    ]
)
def silver(context: AssetExecutionContext):
    """Clean, validate and quarantine → Silver Delta tables."""
    results = build_silver()
    context.log.info(f"silver: {results}")
    for table in SILVER_TABLES:
        path = settings.silver_dir / table
        df = pl.read_delta(str(path))
        valid, quarantined = results[table]["valid"], results[table]["quarantine"]
        yield MaterializeResult(
            asset_key=["silver", table],
            metadata={
                "dagster/row_count": valid,
                "quarantined_rows": quarantined,
                "quarantine_rate_pct": round(100 * quarantined / (valid + quarantined), 2),
                "delta_version": DeltaTable(str(path)).version(),
                "dagster/column_schema": _schema(df),
                "preview": _preview(df.sort(df.columns[0])),
            },
        )


# --- dbt: core model + Gold, one asset per model (dagster-dbt) ------------------------------------
# dbt renders env_var('ESHOP_GOLD') while parsing, so give it a value before the manifest is built.
os.environ.setdefault("ESHOP_DUCKDB", str(settings.data_dir / "eshop.duckdb"))
os.environ.setdefault("ESHOP_GOLD", str(settings.gold_dir))

DBT_PROJECT = DbtProject(project_dir=DBT_DIR, profiles_dir=DBT_DIR)
# Always the dbt-core next to this Python (the project venv), never whatever `dbt` is on PATH
# (e.g. a globally installed dbt Fusion, which has no DuckDB adapter).
DBT_EXECUTABLE = str(Path(sys.executable).parent / "dbt")
DBT_PROJECT.prepare_if_dev()  # `dagster dev` re-parses the dbt project on every reload
if not DBT_PROJECT.manifest_path.exists():  # first run outside `dagster dev` (tests, CLI)
    DbtCliResource(project_dir=DBT_PROJECT, dbt_executable=DBT_EXECUTABLE).cli(
        ["parse", "--quiet"], target_path=DBT_PROJECT.target_path
    ).wait()


# Refreshed daily (04:00 run + slack) → FAIL after 26 h. The warn window is short on purpose,
# so in class you see the asset turn WARN 5 minutes after its last refresh.
SALES_DAILY_FRESHNESS = FreshnessPolicy.time_window(
    fail_window=timedelta(hours=26), warn_window=timedelta(minutes=5)
)


class EshopDbtTranslator(DagsterDbtTranslator):
    """How dbt nodes become Dagster assets."""

    def get_asset_spec(self, manifest, unique_id, project):
        spec = super().get_asset_spec(manifest, unique_id, project)
        if spec.key == AssetKey("sales_daily"):
            # The daily sales data product promises to be fresh: the SLA from its contract (S8).
            spec = spec.replace_attributes(freshness_policy=SALES_DAILY_FRESHNESS)
        return spec

    def get_group_name(self, dbt_resource_props) -> str:
        return f"dbt_{dbt_resource_props['fqn'][1]}"  # staging / intermediate / marts / gold

    def get_automation_condition(self, dbt_resource_props):
        return AUTO


@dbt_assets(manifest=DBT_PROJECT.manifest_path, dagster_dbt_translator=EshopDbtTranslator())
def dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    """Load Silver into DuckDB, then `dbt build` the selected models (+ their tests)."""
    duckdb_path = settings.data_dir / "eshop.duckdb"
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    settings.gold_dir.mkdir(parents=True, exist_ok=True)
    os.environ["ESHOP_DUCKDB"] = str(duckdb_path)
    os.environ["ESHOP_GOLD"] = str(settings.gold_dir)
    load_silver_to_duckdb(duckdb_path)

    for event in dbt.cli(["build"], context=context).stream():
        # Gold models are Parquet files: attach row count, columns and a preview, like our assets.
        # (A model's Output is named after the model, e.g. "customer_360"; checks have no name.)
        name = getattr(event, "output_name", None)
        gold_file = settings.gold_dir / f"{name}.parquet" if name else None
        if gold_file and gold_file.exists():
            df = pl.read_parquet(gold_file)
            event = event.with_metadata(
                {**event.metadata, "dagster/row_count": df.height,
                 "dagster/column_schema": _schema(df), "preview": _preview(df)}
            )
        yield event


# --- jobs, schedule, sensors ----------------------------------------------------------------------

all_assets = [raw_data, bronze, silver, dbt_models]
# The serving layer (KV store + ODS) arrives in session 12, in dagster_project/serving.py.
# TODO(12): import the `serving` asset and add it to `all_assets`
all_checks = [customers_contract]
resources = {
    "dbt": DbtCliResource(project_dir=DBT_PROJECT, dbt_executable=DBT_EXECUTABLE)
}

pipeline_job = define_asset_job("eshop_pipeline", selection="*")
# TODO(9): schedule the pipeline every day at 04:00 Prague time (cron: minute hour * * *)

ingest_job = define_asset_job("ingest_new_orders", selection=[bronze])


ACTIVE_RUN_STATUSES = [
    DagsterRunStatus.QUEUED, DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.STARTING, DagsterRunStatus.STARTED,
]


@sensor(job=ingest_job, minimum_interval_seconds=15, default_status=DefaultSensorStatus.STOPPED)
def new_orders_sensor(context: SensorEvaluationContext):
    """Poll the operational DB; when orders above the last seen id appear, ingest them.

    Event-driven instead of time-driven: try `uv run eshop new-orders 200` while it is on. With the
    automation sensor on as well, Silver → dbt → serving follow by themselves.
    """
    if not settings.source_db.exists():
        return SkipReason("no source database yet")
    con = sqlite3.connect(settings.source_db)
    try:
        max_id = con.execute("SELECT COALESCE(MAX(order_id), 0) FROM orders").fetchone()[0]
    finally:
        con.close()
    last = context.cursor
    context.update_cursor(str(max_id))
    if last is None:
        return SkipReason(f"started watching at order_id {max_id}")
    if max_id <= int(last):  # nothing new (or the source was regenerated)
        return SkipReason(f"no new orders (max order_id {max_id})")
    # A pipeline run started by hand or by the schedule (e.g. Launchpad `new_orders: 50`) ingests
    # these orders itself; a second, concurrent `bronze` run would only race it.
    active = context.instance.get_runs(filters=RunsFilter(statuses=ACTIVE_RUN_STATUSES))
    if any("dagster/sensor_name" not in run.tags for run in active):
        return SkipReason(f"a pipeline run is in progress; it ingests orders up to {max_id} itself")
    return RunRequest(run_key=f"orders-up-to-{max_id}")


automation_sensor = AutomationConditionSensorDefinition(
    "eshop_automation", target="*", default_status=DefaultSensorStatus.STOPPED
)

defs = Definitions(
    assets=all_assets,
    asset_checks=all_checks,
    jobs=[pipeline_job, ingest_job],
    schedules=[daily_schedule],
    sensors=[new_orders_sensor, automation_sensor],
    resources=resources,
)
