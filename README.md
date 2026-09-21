# 18BIG – Big Data Tools and Architecture (student repository)

A hands-on course: over the semester you will progressively build a **local lakehouse** on top
of the *E-shop Lakehouse* project. Everything runs locally, no cloud, dependencies via `uv`.

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
- Run your solution following the instructions in that session's README.

## Structure

```
src/eshop/     pipeline code (you fill in parts of it)
sessions/      session materials and exercises
dbt/, app/     transformations and dashboard (in later sessions)
data/          local data (generated, not committed)
```

New sessions are added during the semester (`git pull`).
