"""Session 8 – data contracts as a governance tool.

A YAML contract declares a table's schema, owner, sensitivity, and which columns are PII. We can
load it, list the PII columns to mask, and check that the real data still matches the contract
(missing columns, unexpected columns, and type mismatches).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import yaml

# Maps a contract type name to the Polars dtype family we expect.
_TYPE_FAMILY = {
    "integer": ("Int",),
    "float": ("Float",),
    "string": ("String", "Utf8"),
    "boolean": ("Boolean",),
}


def load_contract(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def pii_columns(contract: dict) -> list[str]:
    """Columns flagged as PII in the contract – these must be masked before sharing."""
    return [name for name, meta in contract["columns"].items() if meta.get("pii")]


def _type_ok(actual_dtype, declared_type: str) -> bool:
    families = _TYPE_FAMILY.get(declared_type)
    if families is None:
        return True  # unknown declared type → don't fail on it
    return str(actual_dtype).startswith(families)


def validate_contract(df: pl.DataFrame, contract: dict) -> dict:
    """Check the data against the contract: missing columns, extra columns, and type mismatches."""
    declared = set(contract["columns"])
    actual = set(df.columns)

    # Every column the contract declares must be present in the data.
    missing = declared - actual

    # Columns present in the data but not declared (ignore technical metadata, prefixed with '_').
    extra = {c for c in (actual - declared) if not c.startswith("_")}

    # Harder: for each declared column present, the actual dtype must match the declared type family.
    schema = df.schema
    type_mismatches = {
        col: str(schema[col])
        for col, meta in contract["columns"].items()
        if col in schema and not _type_ok(schema[col], meta.get("type", ""))
    }

    return {
        "ok": not missing and not type_mismatches,
        "missing": sorted(missing),
        "extra": sorted(extra),
        "type_mismatches": type_mismatches,
    }
