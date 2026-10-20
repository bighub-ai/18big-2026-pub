"""Example of Bronze -> Silver cleaning (session 5) using the marker convention for scaffolds.

Blocks between `# >>> EXERCISE NN:` and `# <<< EXERCISE` are what students fill in.
`scripts/gen_exercises.py 05` turns them into a version with `# TODO(05): <hint>`.
See docs/TEACHING-GUIDE.md for details.
"""

from __future__ import annotations

import polars as pl


def clean_orders(df: pl.DataFrame) -> pl.DataFrame:
    """Cast columns, drop incomplete and duplicate orders."""
    # TODO(5): cast order_id/customer_id to Int64, order_ts to Datetime

    # TODO(5): drop rows with NULL order_id and deduplicate by order_id

    return df
