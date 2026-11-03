"""Session 5 – data contracts (Pandera) for the Silver layer.

A data contract declares what "good" data looks like: column types and business rules. We use it
as a gate: after cleaning and routing bad rows to quarantine, the remaining Silver data must
satisfy the contract. `Config.strict = False` (default) lets technical metadata columns pass through.
"""

from __future__ import annotations

import pandera.polars as pa


class Customers(pa.DataFrameModel):
    customer_id: int = pa.Field(ge=0)
    name: str
    email: str = pa.Field(str_contains="@")  # valid emails only reach Silver
    city: str


class Payments(pa.DataFrameModel):
    order_id: int = pa.Field(ge=0)
    amount: float = pa.Field(gt=0)
    method: str = pa.Field(isin=["CARD", "TRANSFER", "CASH"])


class Orders(pa.DataFrameModel):
    order_id: int = pa.Field(ge=0)
    customer_id: int = pa.Field(ge=0)
    status: str = pa.Field(isin=["NEW", "PAID", "SHIPPED", "CANCELLED"])
