"""Session 5 – build the Silver layer: clean, enforce contracts, quarantine bad data.

Silver = conformed, clean, trustworthy data. We clean each Bronze entity, split it into `valid`
(→ Silver Delta) and `quarantine` (→ data/quarantine/), and assert the valid part satisfies the
data contract (Pandera). Bad data never flows downstream.
"""

from __future__ import annotations

import polars as pl

from eshop.config import settings
from eshop.quality.contracts import Customers, Orders, Payments
from eshop.silver.clean_orders import clean_orders
from eshop.silver.delta_io import write_delta


def _quarantine(entity: str, df: pl.DataFrame) -> None:
    settings.quarantine_dir.mkdir(parents=True, exist_ok=True)
    df.write_parquet(settings.quarantine_dir / f"{entity}.parquet")


def _bronze(entity: str) -> pl.DataFrame:
    return pl.read_parquet(settings.bronze_dir / entity / "data.parquet")


def build_silver() -> dict:
    results: dict[str, dict] = {}

    # --- customers: dedup, then route rows with a malformed email to quarantine ---
    customers = _bronze("customers").unique(subset=["customer_id"], keep="first")
    # A valid customer must have a plausible email address (contains '@').
    email_ok = pl.col("email").str.contains("@")
    good = customers.filter(email_ok)
    bad = customers.filter(~email_ok)
    Customers.validate(good, lazy=True)  # contract gate – must pass
    write_delta(settings.silver_dir / "customers", good.cast({"customer_id": pl.Int64}))
    _quarantine("customers", bad)
    results["customers"] = {"valid": good.height, "quarantine": bad.height}

    # --- payments: dedup exact duplicates, quarantine non-positive amounts ---
    payments = _bronze("payments").unique(subset=["order_id", "amount", "method"], keep="first")
    # A valid payment must have a strictly positive amount (a refund/typo is not revenue here).
    amount_ok = pl.col("amount") > 0
    good_p = payments.filter(amount_ok)
    bad_p = payments.filter(~amount_ok)
    Payments.validate(good_p, lazy=True)
    write_delta(settings.silver_dir / "payments", good_p.cast({"order_id": pl.Int64}))
    _quarantine("payments", bad_p)
    results["payments"] = {"valid": good_p.height, "quarantine": bad_p.height}

    # --- orders: cast + dedup (clean_orders), then enforce referential integrity ---
    orders = clean_orders(_bronze("orders"))
    # Harder: an order that points to a customer we quarantined is a broken reference. Keep only
    # orders whose customer_id exists among the *valid* customers; quarantine the rest.
    known_customers = good["customer_id"].to_list()
    orders_ok = orders.filter(pl.col("customer_id").is_in(known_customers))
    orders_bad = orders.filter(~pl.col("customer_id").is_in(known_customers))
    Orders.validate(orders_ok, lazy=True)
    write_delta(settings.silver_dir / "orders", orders_ok)
    _quarantine("orders", orders_bad)
    results["orders"] = {"valid": orders_ok.height, "quarantine": orders_bad.height}

    # --- products & order_items: conformed pass-through (needed for the dbt star schema, S6) ---
    products = _bronze("products").unique(subset=["product_id"], keep="first")
    write_delta(settings.silver_dir / "products", products.cast({"product_id": pl.Int64}))
    results["products"] = {"valid": products.height, "quarantine": 0}

    items = _bronze("order_items").unique(keep="first")
    write_delta(
        settings.silver_dir / "order_items",
        items.cast({"order_id": pl.Int64, "product_id": pl.Int64}),
    )
    results["order_items"] = {"valid": items.height, "quarantine": 0}

    return results
