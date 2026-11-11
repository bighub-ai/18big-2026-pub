# 18BIG – commands (student repo). Run `just` for the list.

default:
    @just --list

# install the course environment
sync:
    uv sync

# generate source data into data/raw/
datagen:
    uv run eshop datagen

# verify the environment and data work
doctor:
    uv run eshop doctor

# open a marimo notebook for live editing, e.g. `just notebook sessions/01-foundations/exercise/sql_basics_notebook.py`
notebook FILE:
    uv run marimo edit {{FILE}}

# run a plain .sql exercise/solution through DuckDB, e.g. `just sql sessions/01-foundations/exercise/explore.sql`
sql FILE:
    uv run eshop sql {{FILE}}

# [S02] land all sources into Bronze (driven by src/eshop/ingestion/sources.yml)
ingest:
    uv run eshop ingest

# [S02] peek at a Bronze table: row count, ingest batches, last rows, e.g. `just bronze orders`
bronze ENTITY="orders":
    uv run eshop bronze {{ENTITY}}

# [S02] simulate new business: append N orders to the SQLite source, then `just ingest`
new-orders N="10":
    uv run eshop new-orders {{N}}

# [S07] the interactive Streamlit dashboard over Gold (run `uv run eshop dbt-build` first)
dashboard:
    uv run streamlit run app/dashboard.py

# [S07] optional: the same Gold as a model-driven Rill dashboard (install: see rill/rill.yaml)
rill:
    rill start rill
