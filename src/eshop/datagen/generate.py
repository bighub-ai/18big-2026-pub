"""Deterministic generator of synthetic e-shop source data.

Writes data in two "source-system formats":
  - CSV files (customers, products, payments) -> data/raw/*.csv
  - SQLite database (orders, order_items) -> data/raw/shop.sqlite  (JDBC-like source)

It intentionally injects some "dirt" (duplicates, NULLs, negative amounts, malformed
emails) so the data-quality exercise (session 5) and the quarantine pattern make sense.
"""

from __future__ import annotations

import csv
import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker

from eshop.config import settings


def _writer(path, header):
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open("w", newline="", encoding="utf-8")
    w = csv.writer(f)
    w.writerow(header)
    return f, w


def generate_all() -> dict[str, int]:
    """Generate the complete source dataset. Returns row counts per entity."""
    fake = Faker("en_US")
    Faker.seed(settings.seed)
    rng = random.Random(settings.seed)

    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    # --- customers.csv (contains PII: name, email) ---
    f, w = _writer(settings.raw_dir / "customers.csv",
                   ["customer_id", "name", "email", "city", "signup_date"])
    for cid in range(1, settings.n_customers + 1):
        email = fake.email()
        # ~2% malformed emails -> quarantine later
        if rng.random() < 0.02:
            email = email.replace("@", "")
        w.writerow([cid, fake.name(), email, fake.city(),
                    fake.date_between("-3y", "today").isoformat()])
    f.close()
    counts["customers"] = settings.n_customers

    # --- products.csv ---
    categories = ["Electronics", "Books", "Home", "Sports", "Toys", "Fashion"]
    f, w = _writer(settings.raw_dir / "products.csv",
                   ["product_id", "name", "category", "price"])
    for pid in range(1, settings.n_products + 1):
        w.writerow([pid, fake.catch_phrase(), rng.choice(categories),
                    round(rng.uniform(50, 5000), 2)])
    f.close()
    counts["products"] = settings.n_products

    # --- orders + order_items -> SQLite (operational system) ---
    con = sqlite3.connect(settings.source_db)
    cur = con.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS order_items;
        CREATE TABLE orders(
            order_id INTEGER PRIMARY KEY, customer_id INTEGER,
            order_ts TEXT, status TEXT);
        CREATE TABLE order_items(
            order_id INTEGER, product_id INTEGER, qty INTEGER, unit_price REAL);
        """
    )
    start = datetime.now() - timedelta(days=365)
    statuses = ["NEW", "PAID", "SHIPPED", "CANCELLED"]
    payments = []
    n_items = 0
    for oid in range(1, settings.n_orders + 1):
        cid = rng.randint(1, settings.n_customers)
        ts = start + timedelta(days=rng.randint(0, 365),
                               seconds=rng.randint(0, 86399))
        status = rng.choices(statuses, weights=[1, 5, 3, 1])[0]
        cur.execute("INSERT INTO orders VALUES(?,?,?,?)",
                    (oid, cid, ts.isoformat(sep=" "), status))
        order_total = 0.0
        for _ in range(rng.randint(1, 5)):
            pid = rng.randint(1, settings.n_products)
            qty = rng.randint(1, 4)
            price = round(rng.uniform(50, 5000), 2)
            cur.execute("INSERT INTO order_items VALUES(?,?,?,?)",
                        (oid, pid, qty, price))
            order_total += qty * price
            n_items += 1
        if status in ("PAID", "SHIPPED"):
            amount = order_total
            # ~1% negative amounts -> quarantine later
            if rng.random() < 0.01:
                amount = -amount
            payments.append((oid, round(amount, 2),
                             rng.choice(["CARD", "TRANSFER", "CASH"])))
    con.commit()
    con.close()
    counts["orders"] = settings.n_orders
    counts["order_items"] = n_items

    # --- payments.csv (contains ~1% duplicates) ---
    f, w = _writer(settings.raw_dir / "payments.csv",
                   ["order_id", "amount", "method"])
    for row in payments:
        w.writerow(row)
        if rng.random() < 0.01:  # duplicate payment
            w.writerow(row)
    f.close()
    counts["payments"] = len(payments)

    return counts
