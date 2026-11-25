# Session 9 — Orchestration: Dagster

**Syllabus:** topic 7 (orchestration) · **Layer:** cross-cutting (operations)

## Goal

Students understand why orchestration is needed and can express the whole pipeline as dependent
data assets with scheduling, retries, and observability.

## Theory (~40 min)

- **Why orchestration:** dependencies, scheduling, retries, observability, backfill.
- **Software-defined assets** (Dagster) vs. task-based (Airflow) vs. declarative (DLT).
- **Idempotent runs** – re-running an asset should be safe (our layers overwrite deterministically).
- Airflow/DLT as alternatives ("the same DAG elsewhere").

## Practice (~45 min)

You fill in the `# TODO`s in `dagster_project/definitions.py` – wire the graph:

1. `bronze` depends on `raw_data`.
2. Every Silver table (`silver/customers`, `silver/orders`, …) depends on `bronze`.
3. Give each Silver table the asset key `["silver", <table>]`. That is the key dagster-dbt gives
   the dbt source `silver.<table>`, so matching it wires all dbt models to Silver automatically.
4. Schedule the pipeline daily at 04:00 Prague time (`cron_schedule`, `execution_timezone`).
5. **(harder)** Finish the blocking check `customers_contract` on `bronze`: validate the Bronze
   customers against the S8 contract (`validate_contract`) and return an `AssetCheckResult`.

Then run it:

```bash
uv run eshop pipeline                                   # materialize all assets in-process
uv run dagster dev -m dagster_project.definitions       # the Dagster UI → http://localhost:3000
```

### Tour of the UI

1. **Assets → global lineage:** 20 assets in groups `ingest → silver → dbt_staging → dbt_intermediate
   → dbt_marts → dbt_gold` (the serving layer joins the graph in session 12). Every dbt model is its own asset (dagster-dbt), its dbt tests
   are asset checks.
2. **Materialize all**, then open the run: timeline per step, logs, durations.
3. **Open an asset** (e.g. `silver/orders`, `customer_360`): row count, column schema, the first 10
   rows (`preview`), and for Silver the quarantine rate and Delta version. **Plots** chart the numbers
   across runs.
4. **Automation:** the daily schedule and two sensors, all off by default.

### Demos (each is a switch in the UI)

Run config is set in the **Launchpad**: the arrow next to **Materialize all** → *Open launchpad*.

| Demo | How | What you see |
|---|---|---|
| **New business day** | `ops: {raw_data: {config: {new_orders: 500}}}` | the source grows by 500 orders, Bronze lands exactly those (`landed_orders`), counts flow to Gold |
| **Retry** | `ops: {bronze: {config: {simulate_failure: true}}}` | the first attempt fails ("database is locked"), the RetryPolicy re-runs it after 5 s, `retry_number = 1` |
| **Contract blocks bad data** | `ops: {raw_data: {config: {new_orders: 50, schema_drift: true}}}` | `customers.csv` loses `signup_date`, the blocking check `customers_contract` on `bronze` fails, nothing downstream runs, Silver/Gold keep the last good data. The next `raw_data` run without `schema_drift` restores the file (e.g. `new_orders: 50` again) |
| **Event-driven ingest** | turn on `new_orders_sensor`, then `uv run eshop new-orders 200` in a terminal | within ~30 s a run of `bronze` starts by itself |
| **Declarative automation** | turn on `eshop_automation` too | after that `bronze` run, Silver → dbt update themselves in a second run; after a failed contract check they don't |
| **Freshness** | just wait | the Gold `sales_daily` turns **WARN** 5 min after its last refresh (fail after 26 h) |

Launchpad YAML example:

```yaml
ops:
  raw_data:
    config:
      new_orders: 500       # 0 (default) = regenerate everything from the seed
      schema_drift: false
  bronze:
    config:
      simulate_failure: false
```

## Deliverable / checkpoint

- The pipeline runs as a Dagster asset graph (`raw_data → bronze → silver/* → dbt models`), guarded
  by the blocking contract check; the schedule and a retry policy are defined.
- **checkpoint-09** = this state.
