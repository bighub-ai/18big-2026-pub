-- Order fact: one row per order with its total amount and item count.
with orders as (
    select * from {{ ref('stg_orders') }}
),
items as (
    select * from {{ ref('stg_order_items') }}
)

-- TODO(6): one row per order with order_amount (sum line_amount) and n_items (count)
