"""Session 8 – PII masking / pseudonymization.

We don't need an enterprise tool to practice governance: a stable pseudonymous hash lets analysts
join on a value without ever seeing the real PII (email, name).
"""

from __future__ import annotations

import polars as pl


def mask_pii(df: pl.DataFrame, pii_cols: list[str]) -> pl.DataFrame:
    """Replace each PII column with a stable pseudonymous hash (same input → same token)."""
    return df.with_columns(
        [pl.col(c).cast(pl.Utf8).hash(0).cast(pl.Utf8).alias(c) for c in pii_cols]
    )
