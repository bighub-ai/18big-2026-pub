"""Example of Bronze -> Silver cleaning (session 5) using the marker convention for scaffolds.

Blocks between `# >>> EXERCISE NN:` and `# <<< EXERCISE` are what students fill in.
`scripts/gen_exercises.py 05` turns them into a version with `# TODO(05): <hint>`.
See docs/TEACHING-GUIDE.md for details.
"""

from __future__ import annotations

import polars as pl


def clean_orders(df: pl.DataFrame) -> pl.DataFrame:
    """Cast columns, drop incomplete and duplicate orders."""
    df = df.with_columns(
        pl.col("order_id").cast(pl.Int64),
        pl.col("customer_id").cast(pl.Int64),
        pl.col("order_ts").str.to_datetime(strict=False),
    )

    df = df.drop_nulls(subset=["order_id"]).unique(subset=["order_id"], keep="first")

    return df
