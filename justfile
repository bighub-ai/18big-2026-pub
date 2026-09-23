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
