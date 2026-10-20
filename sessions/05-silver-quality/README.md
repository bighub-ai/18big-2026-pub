# Session 5 — Silver: cleaning, data contracts and quality

**Syllabus:** topic 5 (quality) · **Layer:** Silver

## Goal

Students can design a Silver pipeline that cleans data and **does not let bad data through**
(contract + quarantine).

## Theory (~40 min)

- **What Silver is:** conformed, clean, trustworthy data.
- **Cleaning:** deduplication, type casting, normalization, business rules.
- **Data contracts** – declare the shape of "good" data; validate as a gate. Why a contract beats
  scattered manual `if` checks.
- **"Shift-left" quality** – catch problems early, at the boundary.
- **The valid / quarantine (dead-letter) pattern** – bad rows are captured, not silently dropped,
  and never flow downstream.

## Practice (~45 min)

*Brief: "A dirty dataset arrives in Bronze. Design a Silver pipeline that catches and rejects the
bad data."* You fill in the `# TODO`s across three files:

1. `src/eshop/silver/clean_orders.py` – cast columns to their types.
2. `src/eshop/silver/clean_orders.py` – drop NULL `order_id` and deduplicate orders.
3. `src/eshop/quality/contracts.py` – the Pandera rule that a payment `amount` must be positive.
4. `src/eshop/silver/build_silver.py` – valid customers have an email containing `@`.
5. `src/eshop/silver/build_silver.py` – valid payments have `amount > 0`.
6. **(harder)** `src/eshop/silver/build_silver.py` – referential integrity: quarantine orders whose
   `customer_id` isn't among the valid customers.

Then run and inspect the split:

```bash
uv run eshop datagen && uv run eshop ingest   # if needed
uv run eshop silver
ls data/quarantine/                            # rejected rows land here
```

## Deliverable / checkpoint

- Silver Delta tables for customers/payments/orders; rejected rows in `data/quarantine/`.
- The Pandera contract passes on the cleaned data (the run doesn't raise).
- **checkpoint-05** = this state.
