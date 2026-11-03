-- One row per customer with their order count and total revenue.
with orders as (
    select * from {{ ref('stg_orders') }}
),
items as (
    select * from {{ ref('stg_order_items') }}
)

-- TODO(6): aggregate per customer_id: order_count (distinct orders) and revenue (sum line_amount)
