# 18BIG – Big Data Tools and Architecture (student repository)

A hands-on course: over the semester you will progressively build a **local lakehouse** on top
of the *E-shop Lakehouse* project. Everything runs locally, no cloud, dependencies via `uv`.

## Prerequisites

Only **`uv`** is required. Everything else (DuckDB, marimo, dbt, …) is a Python package that
`uv sync` installs for you — no separate installs, no `duckdb` CLI, no Node.js.

- Install `uv`, then restart your terminal:
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - Verify: `uv --version`
- Don't worry about Python itself — `uv` downloads the right version (3.12) automatically the
  first time you run `uv sync`, even on a machine with no Python installed at all.
- `just` (used below) is optional — every `just <cmd>` has a plain `uv run ...` equivalent.

## Quick start

```bash
uv sync                 # installs the course environment
uv run eshop datagen    # generates source data into data/raw/
uv run eshop doctor     # verifies everything works
```

## How the exercises work

- Materials for each session are in `sessions/NN-topic/README.md` (theory + brief).
- You fill in the spots marked `# TODO(NN)` in the pre-prepared code (either in
  `sessions/NN-topic/exercise/…`, or directly in `src/eshop/…` – the session README says where).
- Some sessions also include a runnable **marimo notebook** (`sessions/NN-topic/exercise/*.py`
  opened with `uv run marimo edit <file>`, or `just notebook <file>`) – a live, editable walkthrough,
  not a fill-in exercise. Edit any query and re-run its cell to experiment.
- Run your solution following the instructions in that session's README.

## Structure

```
src/eshop/     pipeline code (you fill in parts of it)
sessions/      session materials and exercises
dbt/, app/     transformations and dashboard (in later sessions)
data/          local data (generated, not committed)
```

New sessions are added during the semester (`git pull`).
