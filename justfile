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
